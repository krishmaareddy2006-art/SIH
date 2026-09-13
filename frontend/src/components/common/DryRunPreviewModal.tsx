import React from 'react';
import { Play, X, ShieldCheck, AlertCircle, Clock, Database, Lock } from 'lucide-react';
import { DryRunPlan } from '../../types';

interface DryRunPreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  onProceedToConfirm: () => void;
  plan: DryRunPlan | null;
}

export const DryRunPreviewModal: React.FC<DryRunPreviewModalProps> = ({
  isOpen,
  onClose,
  onProceedToConfirm,
  plan,
}) => {
  if (!isOpen || !plan) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#080B14]/85 backdrop-blur-md animate-fade-in"
      role="dialog"
      aria-modal="true"
    >
      <div className="bg-[#111827] border border-[#253044] rounded-2xl max-w-2xl w-full p-6 shadow-elevated space-y-5">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-[#253044] pb-4">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-[#22D3EE]/10 border border-[#22D3EE]/30 rounded-xl text-[#22D3EE]">
              <Play className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-[#F8FAFC]">
                Simulation & Dry-Run Execution Plan
              </h3>
              <p className="text-[11px] text-[#22D3EE] font-mono font-medium tracking-wide">
                PRE-EXECUTION AUDIT & CAPACITY ESTIMATE
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-[#94A3B8] hover:text-[#F8FAFC] p-1.5 rounded-lg hover:bg-[#162032] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Plan Highlights */}
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="bg-[#0B0F19] p-3 rounded-xl border border-[#253044]">
            <span className="text-[#94A3B8] text-[11px]">Target Path:</span>
            <p className="font-mono text-[#F8FAFC] font-semibold mt-0.5 break-all">{plan.target_device_path}</p>
          </div>
          <div className="bg-[#0B0F19] p-3 rounded-xl border border-[#253044]">
            <span className="text-[#94A3B8] text-[11px]">Classification:</span>
            <p className="font-mono text-[#22D3EE] font-semibold mt-0.5">{plan.device_classification}</p>
          </div>
          <div className="bg-[#0B0F19] p-3 rounded-xl border border-[#253044] flex items-center space-x-2.5">
            <Clock className="w-4 h-4 text-[#34D399] shrink-0" />
            <div>
              <span className="text-[#94A3B8] text-[11px]">Est. Duration:</span>
              <p className="font-semibold text-[#34D399]">{plan.estimated_duration_seconds} sec (~{Math.ceil(plan.estimated_duration_seconds / 60)} min)</p>
            </div>
          </div>
          <div className="bg-[#0B0F19] p-3 rounded-xl border border-[#253044] flex items-center space-x-2.5">
            <Database className="w-4 h-4 text-[#FBBF24] shrink-0" />
            <div>
              <span className="text-[#94A3B8] text-[11px]">Affected Sectors:</span>
              <p className="font-semibold text-[#FBBF24]">{plan.affected_blocks_estimate.toLocaleString()} blocks</p>
            </div>
          </div>
        </div>

        {/* Safety Gate Checklist */}
        <div className="space-y-2">
          <h4 className="text-[11px] font-bold text-[#94A3B8] uppercase tracking-wider flex items-center">
            <Lock className="w-3.5 h-3.5 text-[#22D3EE] mr-1.5" /> Safety Gate Verification Matrix
          </h4>
          <div className="bg-[#0B0F19] border border-[#253044] rounded-xl p-3 grid grid-cols-2 gap-2 text-xs font-mono">
            <div className="flex items-center space-x-2">
              <span className={plan.safety_gates.is_authorized ? 'text-[#34D399]' : 'text-[#FB7185]'}>
                {plan.safety_gates.is_authorized ? '✓ Authorized Role' : '✗ Unauthorized'}
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <span className={plan.safety_gates.is_system_disk_excluded ? 'text-[#34D399]' : 'text-[#FB7185]'}>
                {plan.safety_gates.is_system_disk_excluded ? '✓ System Disk Excluded' : '✗ System Disk Detected'}
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <span className={plan.safety_gates.unmounted_verified ? 'text-[#34D399]' : 'text-[#FBBF24]'}>
                {plan.safety_gates.unmounted_verified ? '✓ Partition Unmounted' : '⚠ Mounted Volume'}
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <span className={plan.safety_gates.capability_verified ? 'text-[#34D399]' : 'text-[#94A3B8]'}>
                {plan.safety_gates.capability_verified ? '✓ Capability Verified' : '⚠ Standard Overwrite'}
              </span>
            </div>
          </div>
        </div>

        {/* Technical Limitation Disclaimer */}
        <div className="bg-[#1C150A] border border-[#FBBF24]/30 rounded-xl p-3 text-xs text-[#FDE68A] leading-relaxed flex items-start space-x-2">
          <AlertCircle className="w-4 h-4 text-[#FBBF24] shrink-0 mt-0.5" />
          <div className="text-[11px]">
            <span className="font-semibold text-[#FBBF24]">Technical Scope Disclaimer: </span>
            {plan.limitations_disclaimer}
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center justify-end space-x-3 pt-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-[#94A3B8] hover:text-[#F8FAFC] bg-[#0B0F19] hover:bg-[#162032] border border-[#253044] rounded-xl transition-all cursor-pointer"
          >
            Cancel
          </button>
          <button
            onClick={onProceedToConfirm}
            disabled={!plan.safety_gates.all_gates_passed}
            className={`flex items-center space-x-2 px-5 py-2 text-xs font-bold rounded-xl transition-all shadow-subtle ${
              plan.safety_gates.all_gates_passed
                ? 'bg-[#22D3EE] hover:bg-[#67E8F9] text-[#080B14] cursor-pointer'
                : 'bg-[#162032] text-[#64748B] border border-[#253044] cursor-not-allowed'
            }`}
          >
            <ShieldCheck className="w-4 h-4" />
            <span>Proceed to Confirmation</span>
          </button>
        </div>
      </div>
    </div>
  );
};
