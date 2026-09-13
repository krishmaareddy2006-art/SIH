"""Background Job Worker Abstraction & In-Process Implementation for ForensicShield.

Provides an abstract BaseJobWorker interface and InProcessJobWorker (thread pool execution)
with cancellation checkpoints. Enables seamless future migration to Celery or RQ.
"""

import threading
from abc import ABC, abstractmethod
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Callable, Dict, Optional


class JobCancelledException(Exception):
    """Exception raised when a job cancellation checkpoint is triggered."""
    pass


class BaseJobWorker(ABC):
    """Abstract base class for background job execution workers."""

    @abstractmethod
    def enqueue_job(self, job_id: str, task_func: Callable, *args, **kwargs) -> bool:
        """Enqueues task_func for asynchronous background execution."""
        pass

    @abstractmethod
    def cancel_job(self, job_id: str) -> bool:
        """Flags job for cancellation."""
        pass

    @abstractmethod
    def check_cancellation(self, job_id: str) -> bool:
        """
        Cancellation checkpoint helper called inside long-running tasks.
        Raises JobCancelledException if cancellation was requested for job_id.
        """
        pass

    @abstractmethod
    def get_active_jobs_count(self) -> int:
        """Returns total active running jobs."""
        pass


class InProcessJobWorker(BaseJobWorker):
    """In-process thread pool worker implementation for zero-dependency execution."""

    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="ForensicJobWorker")
        self._cancellation_events: Dict[str, threading.Event] = {}
        self._futures: Dict[str, Future] = {}
        self._lock = threading.Lock()

    def enqueue_job(self, job_id: str, task_func: Callable, *args, **kwargs) -> bool:
        """Enqueues task_func into thread pool executor."""
        with self._lock:
            cancel_event = threading.Event()
            self._cancellation_events[job_id] = cancel_event

            future = self.executor.submit(self._task_wrapper, job_id, task_func, cancel_event, *args, **kwargs)
            self._futures[job_id] = future
            future.add_done_callback(lambda f: self._cleanup_job(job_id))
            return True

    def _task_wrapper(self, job_id: str, task_func: Callable, cancel_event: threading.Event, *args, **kwargs):
        """Wrapper wrapping task execution with cancellation awareness."""
        return task_func(job_id, cancel_event, *args, **kwargs)

    def cancel_job(self, job_id: str) -> bool:
        """Triggers cancellation event for specified job_id."""
        with self._lock:
            event = self._cancellation_events.get(job_id)
            if event:
                event.set()
                return True
            return False

    def check_cancellation(self, job_id: str) -> bool:
        """
        Checks if cancellation event is set for job_id.
        If set, raises JobCancelledException to abort execution safely.
        """
        with self._lock:
            event = self._cancellation_events.get(job_id)
            if event and event.is_set():
                raise JobCancelledException(f"Job '{job_id}' cancellation requested by operator.")
        return False

    def _cleanup_job(self, job_id: str) -> None:
        """Removes job references from worker registry upon task completion."""
        with self._lock:
            self._cancellation_events.pop(job_id, None)
            self._futures.pop(job_id, None)

    def get_active_jobs_count(self) -> int:
        """Returns total active running jobs."""
        with self._lock:
            return len(self._futures)
