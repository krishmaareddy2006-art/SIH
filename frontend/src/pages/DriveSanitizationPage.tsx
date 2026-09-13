import React, { useState, useEffect } from 'react';
import { Flame, ShieldAlert, Play, AlertTriangle, CheckCircle2, RefreshCw } from 'lucide-react';
import { api } from '../services/api';
import { DeviceInfo, DryRunPlan, JobRecord } from '../types';
import { useCase } from '../context/CaseContext';
import { useNotification } from '../context/NotificationContext';
import { LoadingSpinner, ErrorState, PermissionDeniedState } from '../components/common/StateViews';
import { SafetyGateBanner } from '../components/common/SafetyGateBanner';
import { TypedConfirmationModal } from '../components/common/TypedConfirmationModal';
import { DryRunPreviewModal } from '../components/common/DryRunPreviewModal';
import { TechnicalLimitationsBox } from '../components/common/TechnicalLimitationsBox';

export const DriveSanitizationPage: React.FC<{ selectedDevicePath?: string }> = ({
  selectedDevicePath = '',
}) => {
  const { activeCase } = useCase();
  const { addToast } = useNotification();

  const [devices, setDevices] = useState<DeviceInfo[]>([]);
  const [targetPath, setTargetPath] = useState(selectedDevicePath);
  const [reason, setReason] = useState('Standard DFIR Case Storage Sanitization');

  const [dryRunPlan, setDryRunPlan] = useState<DryRunPlan | null>(null);
  const [isDryRunModalOpen, setIsDryRunModalOpen] = useState(false);
  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);

  const [activeJob, setActiveJob] = useState<JobRecord | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isExecuting, setIsExecuting] = useState(false);
  const [error, setError] = useState('');

  const loadDevices = async () => {
    setIsLoading(true);
    setError('');
    const res = await api.listDevices();
    if (res.data) {
      setDevices(res.data);
      if (!targetPath && res.data.length > 0) {
        setTargetPath(res.data.find(d => !d.is_system_disk)?.device_path || res.data[0].device_path);
      }
    } else if (res.error) {
      setError(res.error.error.message);
    }
    setIsLoading(false);
  };

  useEffect(() => {
    loadDevices();
  }, []);

  const selectedDev = devices.find(d => d.device_path === targetPath);

  const handleGenerateDryRun = async () => {
    if (!targetPath || !activeCase) {
      addToast('warning', 'Missing Parameters', 'Please select a target device and active case.');
      return;
    }

    setIsLoading(true);
    const res = await api.getDryRunPlan(targetPath, activeCase.id);
    setIsLoading(false);

    if (res.data) {
      setDryRunPlan(res.data);
      setIsDryRunModalOpen(true);
    } else if (res.error) {
      addToast('error', 'Dry-Run Failed', res.error.error.message);
    }
  };

  const handleProceedToConfirm = () => {
    setIsDryRunModalOpen(false);
    setIsConfirmModalOpen(true);
  };

  const handleExecuteSanitization = async () => {
    if (!targetPath || !activeCase || !dryRunPlan) return;

    setIsExecuting(true);
    const token = `CONFIRM DESTROY ${targetPath}`;
    const res = await api.executeSanitization({
      device_path: targetPath,
      confirmation_token: token,
      case_id: activeCase.id,
      reason,
      simulate: true,
    });
    setIsExecuting(false);
    setIsConfirmModalOpen(false);

    if (res.data) {
      setActiveJob(res.data);
      addToast('success', 'Sanitization Initiated', `Job ${res.data.job_id} launched cleanly in simulation mode.`);
    } else if (res.error) {
      addToast('error', 'Sanitization Blocked', res.error.error.message);
    }
  };

  if (isLoading && devices.length === 0) return <LoadingSpinner message="Scanning storage devices & safety policy..." />;
  if (error) return <ErrorState code="SANITIZATION_INIT_ERROR" message={error} onRetry={loadDevices} />;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800 shadow-xl flex items-center justify-between">
        <div>
          <h2 className="text-xl font-extrabold text-slate-100 flex items-center">
            <Flame className="w-6 h-6 text-red-500 mr-2.5" />
            Safety-First Storage Drive Sanitization Wizard
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Block-level storage sanitization, safety gate authorization, and dry-run previewing
          </p>
        </div>
      </div>

      {/* Safety Gate Banner */}
      <SafetyGateBanner
        devicePath={targetPath}
        isSystemDisk={selectedDev?.is_system_disk}
        safeMode={true}
        realDeviceOps={false}
      />

      {/* Wizard Form */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-5 shadow-xl">
        <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">Step 1: Select Target Device</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div>
            <label className="block text-slate-300 font-semibold mb-1.5">Target Storage Device</label>
            <select
              value={targetPath}
              onChange={e => setTargetPath(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 font-mono text-cyan-300 rounded-xl px-3.5 py-2.5 outline-none focus:border-cyan-500"
            >
              {devices.map(d => (
                <option key={d.device_path} value={d.device_path}>
                  {d.device_path} - {d.device_type} ({d.vendor} {d.model}) {d.is_system_disk ? '[SYSTEM DISK]' : ''}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-slate-300 font-semibold mb-1.5">Operational Justification / Reason</label>
            <input
              type="text"
              value={reason}
              onChange={e => setReason(e.target.value)}
              placeholder="Case sanitization justification..."
              className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2.5 text-slate-100 outline-none focus:border-cyan-500"
            />
          </div>
        </div>

        {/* Selected Device Preview Box */}
        {selectedDev && (
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-2 text-xs">
            <div className="flex items-center justify-between font-mono">
              <span className="text-slate-400">Target Info:</span>
              <span className="text-cyan-300 font-bold">{selectedDev.device_path}</span>
            </div>
            <div className="grid grid-cols-3 gap-2 font-mono text-[11px] text-slate-300">
              <div>Type: <strong className="text-slate-100">{selectedDev.device_type}</strong></div>
              <div>Size: <strong className="text-slate-100">{(selectedDev.size_bytes / (1024 * 1024 * 1024)).toFixed(2)} GB</strong></div>
              <div>Method: <strong className="text-cyan-400">{selectedDev.recommended_method}</strong></div>
            </div>
          </div>
        )}

        {/* Wizard Action Controls */}
        <div className="flex items-center justify-end space-x-4 border-t border-slate-800 pt-4">
          <button
            onClick={handleGenerateDryRun}
            disabled={!targetPath || selectedDev?.is_system_disk}
            className={`flex items-center space-x-2 px-5 py-2.5 font-bold text-xs rounded-xl shadow-lg transition-all ${
              targetPath && !selectedDev?.is_system_disk
                ? 'bg-cyan-600 hover:bg-cyan-500 text-white shadow-cyan-950 cursor-pointer'
                : 'bg-slate-800 text-slate-500 border border-slate-700 cursor-not-allowed'
            }`}
          >
            <Play className="w-4 h-4" />
            <span>Generate Dry-Run Execution Plan</span>
          </button>
        </div>
      </div>

      {/* Active Job Progress View */}
      {activeJob && (
        <div className="bg-slate-900 border border-cyan-500/40 rounded-2xl p-6 space-y-4 shadow-xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-cyan-500/10 text-cyan-400 rounded-xl">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <div>
                <h4 className="font-bold text-slate-100 text-sm">Active Job Execution Monitor</h4>
                <p className="font-mono text-xs text-cyan-400">Job ID: {activeJob.job_id}</p>
              </div>
            </div>
            <span className="bg-emerald-950 text-emerald-300 border border-emerald-500/40 font-mono font-bold text-xs px-3 py-1 rounded-full">
              {activeJob.status}
            </span>
          </div>

          <div className="space-y-1">
            <div className="flex items-center justify-between text-xs font-mono text-slate-300">
              <span>{activeJob.progress_stage}</span>
              <span>{activeJob.progress_percent}%</span>
            </div>
            <div className="w-full bg-slate-950 rounded-full h-2.5 border border-slate-800 overflow-hidden">
              <div
                className="bg-gradient-to-r from-cyan-500 to-emerald-400 h-2.5 rounded-full transition-all duration-300"
                style={{ width: `${activeJob.progress_percent}%` }}
              ></div>
            </div>
          </div>
        </div>
      )}

      {/* Modals */}
      <DryRunPreviewModal
        isOpen={isDryRunModalOpen}
        onClose={() => setIsDryRunModalOpen(false)}
        onProceedToConfirm={handleProceedToConfirm}
        plan={dryRunPlan}
      />

      <TypedConfirmationModal
        isOpen={isConfirmModalOpen}
        onClose={() => setIsConfirmModalOpen(false)}
        onConfirm={handleExecuteSanitization}
        title="Confirm Drive Sanitization Execution"
        targetDescription={`Sanitize Target Device ${targetPath} (${selectedDev?.device_type})`}
        expectedToken={`CONFIRM DESTROY ${targetPath}`}
        isSubmitting={isExecuting}
        warningDetails={[
          'Execution will simulate block sanitization under safe mode.',
          'All safety gate tokens & cryptographic hashes will be registered in audit ledger.',
        ]}
      />

      {/* Disclaimers */}
      <TechnicalLimitationsBox />
    </div>
  );
};
