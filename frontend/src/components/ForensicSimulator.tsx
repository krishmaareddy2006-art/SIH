import React, { useState } from 'react';
import { Play, ShieldAlert, CheckCircle2, ShieldCheck, AlertTriangle } from 'lucide-react';
import { api, JobResponse, SafeErrorResponse } from '../services/api';

interface ForensicSimulatorProps {
  onLogGenerated: (log: any) => void;
}

export const ForensicSimulator: React.FC<ForensicSimulatorProps> = ({ onLogGenerated }) => {
  const [caseId, setCaseId] = useState(1);
  const [targetIdentifier, setTargetIdentifier] = useState('/evidence/target_partition.raw');
  const [reason, setReason] = useState('Sanitizing temporary evidence cache after hash verification');
  const [confirmationInput, setConfirmationInput] = useState('CONFIRM_SENSITIVE_ACTION');
  const [jobType, setJobType] = useState<'SANITIZATION' | 'RECOVERY'>('SANITIZATION');
  const [simulate, setSimulate] = useState(true);
  const [loading, setLoading] = useState(false);

  const [result, setResult] = useState<JobResponse | null>(null);
  const [errorResult, setErrorResult] = useState<SafeErrorResponse | null>(null);

  const handleRunSensitiveJob = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    setErrorResult(null);

    const payload = {
      case_id: Number(caseId),
      reason,
      target_identifier: targetIdentifier,
      explicit_confirmation: confirmationInput,
      simulate,
    };

    const response = jobType === 'SANITIZATION' 
      ? await api.startSanitizationJob(payload)
      : await api.startRecoveryJob(payload);

    setLoading(false);

    if (response.error) {
      setErrorResult(response.error);
      onLogGenerated({
        timestamp: new Date().toISOString(),
        level: 'WARNING',
        operation: `JOB_${jobType}`,
        status: 'BLOCKED',
        request_id: response.requestId || response.error.error.request_id,
        case_id: `CASE-#${caseId}`,
        message: response.error.error.message,
      });
    } else if (response.data) {
      setResult(response.data);
      onLogGenerated({
        timestamp: new Date().toISOString(),
        level: 'INFO',
        operation: `JOB_${jobType}`,
        status: response.data.status,
        request_id: response.requestId || 'N/A',
        case_id: `CASE-#${caseId}`,
        message: (response.data as any).preview || response.data.progress_stage || 'Job initiated.',
      });
    }
  };

  return (
    <div className="glass-panel p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Play className="w-5 h-5 text-cyber-teal" />
          <h2 className="text-lg font-semibold text-white">Sensitive Action Job Simulator</h2>
        </div>
        <span className="text-xs px-2.5 py-1 rounded bg-teal-500/10 text-teal-300 font-mono flex items-center gap-1 border border-teal-500/30">
          <ShieldCheck className="w-3.5 h-3.5" />
          Server-Side Guard Active
        </span>
      </div>

      <form onSubmit={handleRunSensitiveJob} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-mono text-slate-400 mb-1">Target Case ID</label>
            <input
              type="number"
              value={caseId}
              onChange={(e) => setCaseId(Number(e.target.value))}
              className="w-full px-3 py-2 rounded-lg bg-dark-900 border border-dark-600 text-slate-200 text-sm focus:border-cyber-teal font-mono"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-mono text-slate-400 mb-1">Job Type</label>
            <select
              value={jobType}
              onChange={(e) => setJobType(e.target.value as any)}
              className="w-full px-3 py-2 rounded-lg bg-dark-900 border border-dark-600 text-slate-200 text-sm focus:border-cyber-teal font-mono"
            >
              <option value="SANITIZATION">Sanitization Job (Admin / Operator)</option>
              <option value="RECOVERY">Evidence Recovery Job (Admin / Inv / Op)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-mono text-slate-400 mb-1">Target Identifier</label>
            <input
              type="text"
              value={targetIdentifier}
              onChange={(e) => setTargetIdentifier(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-dark-900 border border-dark-600 text-slate-200 text-sm focus:border-cyber-teal font-mono"
              required
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-mono text-slate-400 mb-1">Audit Justification Reason</label>
          <input
            type="text"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="w-full px-3 py-2 rounded-lg bg-dark-900 border border-dark-600 text-slate-200 text-sm focus:border-cyber-teal font-mono"
            placeholder="Minimum 5 characters requirement..."
            required
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
          <div>
            <label className="block text-xs font-mono text-amber-400 mb-1 flex items-center gap-1">
              <AlertTriangle className="w-3.5 h-3.5" />
              Explicit Confirmation String Requirement
            </label>
            <input
              type="text"
              value={confirmationInput}
              onChange={(e) => setConfirmationInput(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-dark-900 border border-amber-500/40 text-amber-200 text-xs font-mono focus:border-amber-400"
              placeholder="Must type: CONFIRM_SENSITIVE_ACTION"
              required
            />
          </div>

          <div className="flex items-center justify-between pt-5">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={simulate}
                onChange={(e) => setSimulate(e.target.checked)}
                className="w-4 h-4 rounded border-dark-600 bg-dark-900 text-cyber-teal focus:ring-0"
              />
              <span className="text-xs text-slate-300 font-mono">
                Safe Mode Simulation (Dry-Run)
              </span>
            </label>

            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 rounded-lg bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 text-dark-900 font-bold text-xs flex items-center gap-2 transition-all shadow-md shadow-teal-500/20"
            >
              <Play className="w-4 h-4 fill-current" />
              Execute Sensitive Job
            </button>
          </div>
        </div>
      </form>

      {/* Response Previews */}
      {result && (
        <div className="mt-6 p-4 rounded-lg bg-teal-500/10 border border-teal-500/30">
          <div className="flex items-center gap-2 text-teal-400 font-mono text-sm font-semibold mb-2">
            <CheckCircle2 className="w-4 h-4" />
            <span>Sensitive Job Execution ({result.status})</span>
          </div>
          <p className="text-xs font-mono text-slate-300 bg-dark-900/80 p-3 rounded border border-dark-700">
            {(result as any).preview || (result as any).progress_stage || `Job ID: ${result.job_id}`}
          </p>
          <div className="mt-2 text-[11px] font-mono text-slate-400">
            {(result as any).execution_details || `Job Type: ${result.job_type} | Progress: ${result.progress_percent}%`}
          </div>
        </div>
      )}

      {errorResult && (
        <div className="mt-6 p-4 rounded-lg bg-rose-500/10 border border-rose-500/30">
          <div className="flex items-center gap-2 text-rose-400 font-mono text-sm font-semibold mb-2">
            <ShieldAlert className="w-4 h-4" />
            <span>Security Exception Blocked ({errorResult.error.code})</span>
          </div>
          <p className="text-xs font-mono text-rose-200 bg-dark-900/80 p-3 rounded border border-dark-700">
            {errorResult.error.message}
          </p>
          <div className="flex items-center justify-between text-xs text-slate-400 font-mono mt-2">
            <span>Request Correlation ID: {errorResult.error.request_id}</span>
            <span>Timestamp: {new Date(errorResult.error.timestamp).toLocaleTimeString()}</span>
          </div>
        </div>
      )}
    </div>
  );
};
