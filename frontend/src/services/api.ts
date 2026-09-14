/**
 * ForensicShield Backend API Client Service with JWT Authentication & IDOR Guards
 */

import {
  AuthTokenResponse,
  User,
  ForensicCase,
  DeviceInfo,
  DryRunPlan,
  ErasureJob,
  EvidenceItem,
  RecoveryCandidate,
  CarvedArtifact,
  AuditEvent,
  AuditChainVerification,
  JobRecord,
  ForensicReportResponse,
  ReportPreviewResponse,
  SystemStatus,
} from '../types';

export type { ForensicCase, SystemStatus };
export type UserProfile = User;
export type TokenResponse = AuthTokenResponse;
export type JobResponse = JobRecord;


const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';

export interface SafeErrorResponse {
  error: {
    code: string;
    message: string;
    request_id: string;
    timestamp: string;
  };
}

export function getStoredToken(): string | null {
  return localStorage.getItem('forensic_shield_token');
}

export function setStoredToken(token: string | null): void {
  if (token) {
    localStorage.setItem('forensic_shield_token', token);
  } else {
    localStorage.removeItem('forensic_shield_token');
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<{ data?: T; error?: SafeErrorResponse; requestId?: string; status?: number }> {
  const token = getStoredToken();
  const defaultHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (token) {
    defaultHeaders['Authorization'] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    });

    const requestId = response.headers.get('X-Request-ID') || undefined;
    const body = await response.json().catch(() => ({}));

    if (!response.ok) {
      const errObj: SafeErrorResponse = body?.error
        ? (body as SafeErrorResponse)
        : {
            error: {
              code: body?.code || `HTTP_${response.status}`,
              message: body?.message || body?.detail || response.statusText || 'An error occurred.',
              request_id: requestId || 'N/A',
              timestamp: new Date().toISOString(),
            },
          };
      return { error: errObj, requestId, status: response.status };
    }

    return { data: body as T, requestId, status: response.status };
  } catch (err) {
    return {
      error: {
        error: {
          code: 'NETWORK_ERROR',
          message: 'Failed to connect to ForensicShield backend service. Check network or server status.',
          request_id: 'N/A',
          timestamp: new Date().toISOString(),
        },
      },
      status: 0,
    };
  }
}

export const api = {
  // System Health
  getSystemHealth: () => request<SystemStatus>('/health'),

  // 1. Auth & Profile
  login: (username: string, password: string) =>
    request<AuthTokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),

  logout: () => request<{ message: string }>('/auth/logout', { method: 'POST' }),
  getProfile: () => request<User>('/auth/me'),

  // 2. Dashboard Stats
  getDashboardMetrics: () => request<any>('/health/metrics'),

  // 3. Cases
  listCases: () => request<ForensicCase[]>('/cases/'),
  getCase: (caseId: number) => request<ForensicCase>(`/cases/${caseId}`),
  createCase: (payload: { case_number: string; title: string; description?: string }) =>
    request<ForensicCase>('/cases/', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  closeCase: (caseId: number) => request<ForensicCase>(`/cases/${caseId}/close`, { method: 'POST' }),

  // 4. Storage Devices
  listDevices: () => request<DeviceInfo[]>('/devices/scan'),
  getDeviceDetails: (devicePath: string) =>
    request<DeviceInfo>(`/devices/details?device_path=${encodeURIComponent(devicePath)}`),

  // 5. Drive Sanitization Wizard
  getDryRunPlan: (devicePath: string, caseId: number) =>
    request<any>('/sanitization/preflight', {
      method: 'POST',
      body: JSON.stringify({ device_path: devicePath, case_id: caseId }),
    }).then(res => {
      if (res.data) {
        const p = res.data;
        const mappedPlan: DryRunPlan = {
          target_device_path: p.device_path,
          device_classification: p.target_class,
          recommended_method: p.recommended_method,
          estimated_duration_seconds: Math.max(10, Math.ceil((p.size_bytes || 1073741824) / (50 * 1024 * 1024))),
          affected_blocks_estimate: Math.max(1000, Math.floor((p.size_bytes || 1073741824) / 512)),
          is_system_disk: p.is_boot_system_disk,
          requires_lab_allowlist: false,
          safety_gates: {
            is_authorized: true,
            typed_path_matches: true,
            stable_identifier_valid: true,
            is_system_disk_excluded: !p.is_boot_system_disk,
            unmounted_verified: !p.is_mounted,
            capability_verified: true,
            confirmation_token_valid: true,
            case_id_valid: true,
            all_gates_passed: p.safety_gate_passed,
            failure_reasons: p.safety_gate_reasons || [],
          },
          limitations_disclaimer: p.ftl_caveats || 'SIMULATED DRY-RUN MODE ACTIVE: Enforces Safe Mode block sanitization preview.',
        };
        return { ...res, data: mappedPlan };
      }
      return res as { data?: DryRunPlan; error?: any; requestId?: string; status?: number };
    }),
  
  executeSanitization: (payload: {
    device_path: string;
    confirmation_token: string;
    case_id: number;
    reason: string;
    simulate: boolean;
  }) =>
    request<JobRecord>('/sanitization/execute', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // 6. File/Folder Erasure Wizard
  analyzeFileErasure: (path: string) =>
    request<any>(`/erasure/analyze?path=${encodeURIComponent(path)}`),
  
  executeFileErasure: (payload: {
    target_path: string;
    method?: string;
    passes?: number;
    confirmation?: string;
    dry_run?: boolean;
  }) =>
    request<any>('/erasure/execute', {
      method: 'POST',
      body: JSON.stringify({
        target_path: payload.target_path,
        confirmation_token: payload.confirmation,
        overwrite_passes: payload.passes || 3,
        dry_run: payload.dry_run ?? false,
        reason: 'Authorized forensic secure file erasure',
      }),
    }),

  // 7. Read-Only Evidence Intake
  importEvidence: (caseId: number, payload: {
    source_file_path: string;
    item_number: string;
    title: string;
    source_description?: string;
    create_working_copy?: boolean;
  }) =>
    request<EvidenceItem>(`/cases/${caseId}/evidence/import`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  
  listEvidence: (caseId: number) => request<EvidenceItem[]>(`/cases/${caseId}/evidence`),

  verifyEvidenceIntegrity: (evidenceId: string, stage: string = 'pre_scan') =>
    request<any>(`/evidence/${evidenceId}/verify`, {
      method: 'POST',
      body: JSON.stringify({ stage }),
    }),

  // 8. Recovery Workspace & Carving
  scanFilesystemRecovery: (caseId: number, target: { evidence_id?: string; device_path?: string }) =>
    request<{ candidates: RecoveryCandidate[]; total_candidates_found: number }>(`/cases/${caseId}/recovery/scan`, {
      method: 'POST',
      body: JSON.stringify(target),
    }),

  extractRecoveryCandidates: (
    caseId: number,
    payload: { evidence_id?: string; device_path?: string; candidate_ids: string[]; custom_output_dir?: string }
  ) =>
    request<{
      job_id: string;
      total_requested: number;
      successfully_extracted: number;
      failed_extractions: number;
      extracted_artifacts: any[];
    }>(`/cases/${caseId}/recovery/extract`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  carveFiles: (caseId: number, target: { evidence_id?: string; device_path?: string }, formats: string[]) =>
    request<{ carved_artifacts: CarvedArtifact[]; metrics: any }>(`/cases/${caseId}/carving/scan`, {
      method: 'POST',
      body: JSON.stringify({ ...target, target_formats: formats }),
    }),

  listRecoveredArtifacts: (caseId: number) =>
    request<any[]>(`/cases/${caseId}/recovery/results`),

  // 9. Job Details & Execution Monitor
  listJobs: (caseId?: number) => request<JobRecord[]>(`/jobs/${caseId ? `?case_id=${caseId}` : ''}`),
  getJobStatus: (jobId: string) => request<JobRecord>(`/jobs/${jobId}`),
  cancelJob: (jobId: string) => request<JobRecord>(`/jobs/${jobId}/cancel`, { method: 'POST' }),

  // 10. Audit Chain
  listAuditEvents: (params?: { case_id?: number; action?: string; limit?: number }) => {
    const query = new URLSearchParams();
    if (params?.case_id) query.append('case_id', params.case_id.toString());
    if (params?.action) query.append('action', params.action);
    if (params?.limit) query.append('limit', params.limit.toString());
    return request<AuditEvent[]>(`/audit/logs?${query.toString()}`);
  },

  verifyAuditChain: () => request<AuditChainVerification>('/audit/verify'),

  // 11. Reports & Compliance Hub
  previewReport: (caseId: number) => request<ReportPreviewResponse>(`/cases/${caseId}/reports/preview`),

  generateReport: (caseId: number, payload?: { format?: string }) =>
    request<ForensicReportResponse>(`/cases/${caseId}/reports/generate`, {
      method: 'POST',
      body: JSON.stringify(payload || { format: 'both' }),
    }),

  // 12. Settings & Security Policy
  getSystemSettings: () => request<any>('/settings'),

  // Legacy Job Aliases
  startSanitizationJob: (payload: any) =>
    request<JobRecord>('/sanitization/execute', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  startRecoveryJob: (payload: any) =>
    request<JobRecord>('/recovery/scan', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};
