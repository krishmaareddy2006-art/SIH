import React, { useState, useEffect } from 'react';
import { Flame, Play, CheckCircle2 } from 'lucide-react';
import { api } from '../services/api';
import { DeviceInfo, DryRunPlan, JobRecord } from '../types';
import { useCase } from '../context/CaseContext';
import { useNotification } from '../context/NotificationContext';
import { LoadingSpinner, ErrorState } from '../components/common/StateViews';
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
  const [isSafeMode, setIsSafeMode] = useState(true);
  const [realDeviceOps, setRealDeviceOps] = useState(false);

  const loadDevices = async () => {
    setIsLoading(true);
    setError('');
    const [devRes, healthRes] = await Promise.all([
      api.listDevices(),
      api.getSystemHealth(),
    ]);

    if (healthRes.data) {
      setIsSafeMode(healthRes.data.safe_mode);
      setRealDeviceOps(healthRes.data.real_device_operations);
    }

    if (devRes.data) {
      setDevices(devRes.data);
      if (!targetPath && devRes.data.length > 0) {
        setTargetPath(devRes.data.find(d => !d.is_system_disk)?.device_path || devRes.data[0].device_path);
      }
    } else if (devRes.error) {
      setError(devRes.error.error.message);
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
      simulate: isSafeMode,
    });
    setIsExecuting(false);
    setIsConfirmModalOpen(false);

    if (res.data) {
      setActiveJob(res.data);
      addToast('success', 'Sanitization Initiated', isSafeMode ? `Job ${res.data.job_id} launched cleanly in simulation mode.` : `Job ${res.data.job_id} launched in REAL HARDWARE MODE.`);
    } else if (res.error) {
      addToast('error', 'Sanitization Blocked', res.error.error.message);
    }
  };

  if (isLoading && devices.length === 0) return <LoadingSpinner message="Scanning storage devices & safety policy..." />;
  if (error) return <ErrorState code="SANITIZATION_INIT_ERROR" message={error} onRetry={loadDevices} />;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="bg-[#111827] p-5 sm:p-6 rounded-2xl border border-[#253044] shadow-card flex items-center justify-between">
        <div>
          <h2 className="text-lg sm:text-xl font-bold text-[#F8FAFC] flex items-center">
            <Flame className="w-5 h-5 text-[#FB7185] mr-2.5" />
            Safety-First Storage Drive Sanitization Wizard
          </h2>
          <p className="text-xs text-[#94A3B8] mt-1">
            Block-level storage sanitization, safety gate authorization, and dry-run previewing
          </p>
        </div>
      </div>

      {/* Safety Gate Banner */}
      <SafetyGateBanner
        devicePath={targetPath}
        isSystemDisk={selectedDev?.is_system_disk}
        safeMode={isSafeMode}
        realDeviceOps={realDeviceOps}
      />

      {/* Wizard Form */}
      <div className="bg-[#111827] border border-[#253044] rounded-2xl p-5 sm:p-6 space-y-5 shadow-card">
        <h3 className="text-xs font-bold text-[#94A3B8] uppercase tracking-wider font-mono">
          Step 1: Select Target Device & Justification
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div>
            <label className="block text-[#94A3B8] font-medium mb-1.5">Target Storage Device</label>
            <select
              value={targetPath}
              onChange={e => setTargetPath(e.target.value)}
              className="w-full bg-[#0B0F19] border border-[#253044] font-mono text-[#22D3EE] rounded-xl px-3.5 py-2.5 outline-none focus:border-[#22D3EE] transition-all cursor-pointer shadow-subtle"
            >
              {devices.map(d => (
                <option key={d.device_path} value={d.device_path} className="bg-[#111827] text-[#F8FAFC]">
                  {d.device_path} — {d.device_type} ({d.vendor} {d.model}) {d.is_system_disk ? '[SYSTEM DISK]' : ''}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[#94A3B8] font-medium mb-1.5">Operational Justification / Reason</label>
            <input
              type="text"
              value={reason}
              onChange={e => setReason(e.target.value)}
              placeholder="Case sanitization justification..."
              className="w-full bg-[#0B0F19] border border-[#253044] rounded-xl px-3.5 py-2.5 text-[#F8FAFC] outline-none focus:border-[#22D3EE] transition-all shadow-subtle"
            />
          </div>
        </div>

        {/* Selected Device Preview Box */}
        {selectedDev && (
          <div className="bg-[#0B0F19] border border-[#253044] rounded-xl p-4 space-y-2 text-xs">
            <div className="flex items-center justify-between font-mono">
              <span className="text-[#64748B]">Target Info:</span>
              <span className="text-[#22D3EE] font-bold">{selectedDev.device_path}</span>
            </div>
            <div className="grid grid-cols-3 gap-2 font-mono text-[11px] text-[#94A3B8]">
              <div>Type: <strong className="text-[#F8FAFC]">{selectedDev.device_type}</strong></div>
              <div>Size: <strong className="text-[#F8FAFC]">{(selectedDev.size_bytes / (1024 * 1024 * 1024)).toFixed(2)} GB</strong></div>
              <div>Method: <strong className="text-[#22D3EE]">{selectedDev.recommended_method}</strong></div>
            </div>
          </div>
        )}

        {/* Wizard Action Controls */}
        <div className="flex items-center justify-end space-x-4 border-t border-[#253044] pt-4">
          <button
            onClick={handleGenerateDryRun}
            disabled={!targetPath || selectedDev?.is_system_disk}
            className={`flex items-center space-x-2 px-5 py-2.5 font-bold text-xs rounded-xl shadow-subtle transition-all ${
              targetPath && !selectedDev?.is_system_disk
                ? 'bg-[#22D3EE] hover:bg-[#67E8F9] text-[#080B14] cursor-pointer'
                : 'bg-[#162032] text-[#64748B] border border-[#253044] cursor-not-allowed'
            }`}
          >
            <Play className="w-4 h-4" />
            <span>Generate Dry-Run Execution Plan</span>
          </button>
        </div>
      </div>

      {/* Active Job Progress View */}
      {activeJob && (
        <div className="bg-[#111827] border border-[#22D3EE]/30 rounded-2xl p-6 space-y-4 shadow-card">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-[#22D3EE]/10 text-[#22D3EE] rounded-xl">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <div>
                <h4 className="font-bold text-[#F8FAFC] text-sm">Active Job Execution Monitor</h4>
                <p className="font-mono text-xs text-[#22D3EE]">Job ID: {activeJob.job_id}</p>
              </div>
            </div>
            <span className="bg-[#34D399]/10 text-[#34D399] border border-[#34D399]/30 font-mono font-bold text-xs px-3 py-1 rounded-full">
              {activeJob.status}
            </span>
          </div>

          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs font-mono text-[#94A3B8]">
              <span>{activeJob.progress_stage}</span>
              <span className="text-[#22D3EE] font-bold">{activeJob.progress_percent}%</span>
            </div>
            <div className="w-full bg-[#0B0F19] rounded-full h-2 border border-[#253044] overflow-hidden">
              <div
                className="bg-gradient-to-r from-[#22D3EE] to-[#34D399] h-2 rounded-full transition-all duration-300"
                style={{ width: `${activeJob.progress_percent}%` }}
              />
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
