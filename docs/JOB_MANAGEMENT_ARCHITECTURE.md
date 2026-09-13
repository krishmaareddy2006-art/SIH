# ForensicShield: Reliable Job-Management Layer Architecture

## Executive Summary

ForensicShield implements a persistent, reliable job-management layer designed to orchestrate long-running forensic operations (Drive Sanitization, Filesystem Recovery, Signature Carving, and File Erasure).

Key architectural guarantees include:
- **Persistent Database State**: Every job state transition is committed to the database (`JobRecord`), enabling UI recovery after backend restarts or crashes.
- **Worker Abstraction Layer**: Zero-dependency `InProcessJobWorker` thread pool implementation with a clean `BaseJobWorker` interface for seamless future migration to Celery or RQ.
- **Duplicate Job Prevention**: Active job locking prevents duplicate concurrent destructive operations on the same target.
- **Tamper-Evident Audit Integration**: All state transitions (`JOB_QUEUED`, `JOB_STARTED`, `JOB_PROGRESS`, `JOB_COMPLETED`, `JOB_FAILED`, `JOB_CANCELLED`, `JOB_ABORTED`) emit cryptographic audit events.

---

## 1. Job State Machine & Transition Rules

Jobs transition through 7 explicit states:

```
           ┌──────────┐
           │  queued  │
           └────┬─────┘
                │
                ▼
           ┌──────────┐
           │  running │◄────────────────┐
           └────┬─────┴────────┐        │
                │              │        │
     ┌──────────┴─────┐   ┌────▼───┐    │ (Progress Updates)
     │   cancelling   │   │ failed │────┘
     └──────────┬─────┘   └────────┘
                │
                ▼
           ┌──────────┐      ┌───────────┐      ┌───────────────┐
           │  aborted │      │ completed │      │ manual-review │
           └──────────┘      └───────────┘      └───────────────┘
           (Terminal)         (Terminal)           (Terminal)
```

| Job State | Category | Description |
| :--- | :--- | :--- |
| `queued` | Active | Job submitted and waiting in background worker queue. |
| `running` | Active | Job actively executing on background worker thread. |
| `cancelling` | Transition | Operator requested cancellation; worker checking checkpoint. |
| `completed` | Terminal | Task completed successfully (100.0% progress). |
| `failed` | Terminal | Task encountered an unhandled exception or error. |
| `aborted` | Terminal | Task aborted safely at cancellation checkpoint or server restart. |
| `manual-review` | Terminal | Task finished with structural anomalies requiring investigator review. |

---

## 2. Idempotency & Duplicate Prevention

To prevent race conditions and accidental double-wipes of storage media:
- Before enqueueing a new job, `JobManagementService.prevent_duplicate_active_job()` queries `JobRecord` for matching `target_identifier` and `type` in active states (`queued`, `running`, `cancelling`).
- If an active job exists for that target, the request is rejected with **HTTP 409 Conflict (`DUPLICATE_ACTIVE_JOB`)**.

---

## 3. Estimated vs Exact Progress Reporting

Progress updates include three distinct metadata parameters:
- `progress`: Float value from `0.0` to `100.0`.
- `progress_stage`: Descriptive string (e.g. `"Parsing MFT record 1024/4096"`).
- `is_progress_exact`: Boolean flag. Set to `True` for deterministic operations (e.g., sector count iteration) and `False` for heuristics (e.g., directory extent estimates).

---

## 4. Backend Crash & Startup State Recovery

If the backend server crashes or is restarted during job execution:
1. Upon server startup, `JobManagementService.recover_stale_jobs_on_startup()` scans for orphan records with `status in ["running", "cancelling"]`.
2. Each stale job is updated to `status: "aborted"` with:
   - `finished_at`: Current server startup UTC timestamp.
   - `error_summary`: `"Backend server restarted while job was in progress. Job automatically aborted for safety."`
3. A `JOB_STALE_RECOVERED` audit event is recorded in the tamper-evident audit log.

---

## 5. Background Worker Abstraction & Celery/RQ Migration Path

The architecture decouples job orchestration from the underlying execution worker via `BaseJobWorker`:

```python
class BaseJobWorker(ABC):
    @abstractmethod
    def enqueue_job(self, job_id: str, task_func: Callable, *args, **kwargs) -> bool: pass
    @abstractmethod
    def cancel_job(self, job_id: str) -> bool: pass
    @abstractmethod
    def check_cancellation(self, job_id: str) -> bool: pass
```

### Production Celery/RQ Migration
To transition from the default `InProcessJobWorker` to Redis/RabbitMQ:
1. Implement `CeleryJobWorker(BaseJobWorker)` mapping `enqueue_job` to `celery_app.send_task()`.
2. Map `cancel_job` to `celery_app.control.revoke(task_id, terminate=True)`.
3. Pass `worker=CeleryJobWorker()` when instantiating `JobManagementService`. API endpoints and database models remain 100% unchanged.

---

## 6. Frontend Integration: Polling & Real-Time Design

### 6.1 Short-Polling Strategy (REST)
For web clients using HTTP polling:
1. Client submits job via `POST /api/v1/jobs/submit` (or `/sanitization`, `/recovery`).
2. Client polls `GET /api/v1/jobs/{job_id}` every **2–3 seconds**.
3. When `status` transitions to a terminal state (`completed`, `failed`, `aborted`, `manual-review`), polling stops.

### 6.2 Real-Time Event Streaming Design (WebSocket / SSE)
For high-density dashboards requiring sub-second updates:
- Endpoint: `GET /api/v1/jobs/ws/updates` (Server-Sent Events or WebSockets).
- Event Payload Format:
```json
{
  "event": "JOB_PROGRESS",
  "job_id": "JOB-SAN-20260913-0001",
  "status": "running",
  "progress": 75.0,
  "progress_stage": "Simulating overwrite pass 2/3",
  "is_progress_exact": false,
  "timestamp": "2026-09-13T08:06:00.000000+00:00"
}
```
