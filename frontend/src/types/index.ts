/**
 * Comprehensive TypeScript Type Definitions for ForensicShield Frontend.
 * Matches backend FastAPI / Pydantic models & API specifications.
 */

export type UserRole = string | {
  id: number;
  name: string;
  description?: string;
};

export interface User {
  id: number;
  username: string;
  email: string;
  role: UserRole;
  permissions?: string[];
  is_active: boolean;
  created_at?: string;
}

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
  expires_in?: number;
  username?: string;
  role?: string;
  permissions?: string[];
  user?: User;
}

export interface ForensicCase {
  id: number;
  case_number: string;
  title: string;
  description?: string;
  status: 'OPEN' | 'IN_PROGRESS' | 'COMPLETED' | 'ARCHIVED';
  investigator_id: number;
  created_at: string;
  updated_at?: string;
}

export interface DeviceInfo {
  device_path: string;
  device_type: 'HDD' | 'SSD' | 'NVMe' | 'USB' | 'VIRTUAL' | 'UNKNOWN';
  size_bytes: number;
  vendor: string;
  model: string;
  serial_number: string;
  is_system_disk: boolean;
  is_mounted: boolean;
  bus_type: string;
  mount_point?: string;
  recommended_method: string;
  confidence_level: 'HIGH' | 'MEDIUM' | 'LOW';
  in_allowlist: boolean;
}

export interface SanitizationSafetyGateCheck {
  is_authorized: boolean;
  typed_path_matches: boolean;
  stable_identifier_valid: boolean;
  is_system_disk_excluded: boolean;
  unmounted_verified: boolean;
  capability_verified: boolean;
  confirmation_token_valid: boolean;
  case_id_valid: boolean;
  all_gates_passed: boolean;
  failure_reasons: string[];
}

export interface DryRunPlan {
  target_device_path: string;
  device_classification: string;
  recommended_method: string;
  estimated_duration_seconds: number;
  affected_blocks_estimate: number;
  is_system_disk: boolean;
  requires_lab_allowlist: boolean;
  safety_gates: SanitizationSafetyGateCheck;
  limitations_disclaimer: string;
}

export interface ErasureJob {
  erasure_id: string;
  target_path: string;
  method: string;
  passes_requested: number;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'ABORTED';
  pre_hash?: string;
  post_hash?: string;
  bytes_processed: number;
  verification_passed?: boolean;
}

export interface EvidenceItem {
  id: number;
  evidence_id: string;
  case_id: number;
  item_number: string;
  title: string;
  original_filename: string;
  file_path: string;
  working_copy_path?: string;
  sha256_hash: string;
  file_size_bytes: number;
  import_time: string;
  source_description?: string;
  operator_username: string;
  tool_version: string;
  processing_status: 'IMPORTED' | 'VERIFIED' | 'INTEGRITY_FAILURE' | 'PROCESSING' | 'COMPLETED';
  last_verified_at?: string;
  status: string;
}

export interface RecoveryCandidate {
  candidate_id: string;
  name?: string;
  filename?: string;
  original_path?: string;
  path?: string;
  record_identifier?: string;
  declared_size_bytes?: number;
  file_size_bytes?: number;
  created_at?: string;
  modified_at?: string;
  deleted_at?: string;
  timestamps?: {
    created?: string;
    modified?: string;
    accessed?: string;
  };
  filesystem_type: string;
  inode_record_id?: string;
  source_offset_bytes?: number;
  data_extents_count?: number;
  classification_status: 'RECOVERABLE' | 'PARTIALLY_RECOVERABLE' | 'METADATA_ONLY' | 'CORRUPTED' | 'UNSUPPORTED' | string;
  confidence_score?: number;
  bounds_check_valid?: boolean;
  notes?: string;
  is_recovered?: boolean;
  download_url?: string;
}

export interface CarvedArtifact {
  id: number;
  carved_id: string;
  case_id: number;
  source_evidence_id: string;
  file_format: 'JPEG' | 'PNG' | 'PDF' | 'ZIP';
  output_file_path: string;
  carved_file_hash: string;
  source_image_hash: string;
  source_start_offset: number;
  source_end_offset: number;
  file_size_bytes: number;
  confidence_level: 'HIGH' | 'MEDIUM' | 'LOW';
  validation_details?: string;
  operator_username: string;
  carved_at: string;
}

export interface AuditEvent {
  id: number;
  event_id: string;
  timestamp: string;
  actor: string;
  role: string;
  case_id?: number;
  evidence_id?: string;
  action: string;
  target_summary: string;
  result: string;
  tool_version: string;
  previous_hash: string;
  current_hash: string;
}

export interface AuditChainVerification {
  is_valid: boolean;
  total_events: number;
  chain_status: 'INTACT' | 'BROKEN_CHAIN_DETECTED';
  first_broken_event_id?: string;
  broken_index?: number;
  reason?: string;
  affected_event_ids?: string[];
}

export interface JobRecord {
  job_id: string;
  case_id: number;
  job_type: string;
  status: 'QUEUED' | 'RUNNING' | 'CANCELLING' | 'COMPLETED' | 'FAILED' | 'ABORTED' | 'MANUAL_REVIEW';
  progress_percent: number;
  progress_stage: string;
  error_summary?: string;
  created_at: string;
  started_at?: string;
  finished_at?: string;
  cancellation_requested: boolean;
}

export interface ReportSummary {
  evidence_count: number;
  total_evidence_bytes: number;
  carved_artifacts_count: number;
  recovered_artifacts_count: number;
  audit_events_count: number;
  audit_chain_status: string;
}

export interface StatusClassificationCounts {
  verified: number;
  inconclusive: number;
  failed: number;
  unsupported: number;
  manual_review: number;
}

export interface ForensicReportResponse {
  report_id: string;
  case_id: number;
  generated_at: string;
  pdf_sha256: string;
  json_sha256: string;
  audit_event_id: string;
  pdf_download_url?: string;
  json_download_url?: string;
  summary: ReportSummary;
  classifications: StatusClassificationCounts;
}

export interface ReportPreviewResponse {
  case_id: number;
  case_number: string;
  case_title: string;
  summary: ReportSummary;
  classifications: StatusClassificationCounts;
  audit_chain_valid: boolean;
  evidence_count: number;
  artifact_count: number;
}

export interface SystemStatus {
  project_name: string;
  version: string;
  environment: string;
  safe_mode: boolean;
  real_device_operations: boolean;
  active_jobs_count: number;
  audit_chain_intact: boolean;
}
