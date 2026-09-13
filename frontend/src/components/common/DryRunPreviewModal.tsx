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
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in"
      role="dialog"
      aria-modal="true"
    >
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-5">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-cyan-500/10 border border-cyan-500/30 rounded-xl text-cyan-400">
              <Play className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-100">
                Simulation & Dry-Run Execution Plan
              </h3>
              <p className="text-xs text-cyan-400 font-medium">PRE-EXECUTION AUDIT & CAPACITY ESTIMATE</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 p-1 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Plan Highlights */}
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
            <span className="text-slate-400">Target Path:</span>
            <p className="font-mono text-slate-200 font-semibold mt-0.5">{plan.target_device_path}</p>
          </div>
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
            <span className="text-slate-400">Classification:</span>
            <p className="font-mono text-cyan-300 font-semibold mt-0.5">{plan.device_classification}</p>
          </div>
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 flex items-center space-x-2">
            <Clock className="w-4 h-4 text-emerald-400 shrink-0" />
            <div>
              <span className="text-slate-400">Est. Duration:</span>
              <p className="font-semibold text-emerald-300">{plan.estimated_duration_seconds} sec (~{Math.ceil(plan.estimated_duration_seconds / 60)} min)</p>
            </div>
          </div>
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 flex items-center space-x-2">
            <Database className="w-4 h-4 text-amber-400 shrink-0" />
            <div>
              <span className="text-slate-400">Affected Sectors:</span>
              <p className="font-semibold text-amber-300">{plan.affected_blocks_estimate.toLocaleString()} blocks</p>
            </div>
          </div>
        </div>

        {/* Safety Gate Checklist */}
        <div className="space-y-2">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center">
            <Lock className="w-3.5 h-3.5 text-cyan-400 mr-1.5" /> Safety Gate Verification Matrix
          </h4>
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 grid grid-cols-2 gap-2 text-xs">
            <div className="flex items-center space-x-2">
              <span className={plan.safety_gates.is_authorized ? 'text-emerald-400' : 'text-red-400'}>
                {plan.safety_gates.is_authorized ? '✓ Authorized Role' : '✗ Unauthorized'}
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <span className={plan.safety_gates.is_system_disk_excluded ? 'text-emerald-400' : 'text-red-400'}>
                {plan.safety_gates.is_system_disk_excluded ? '✓ System Disk Excluded' : '✗ System Disk Detected'}
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <span className={plan.safety_gates.unmounted_verified ? 'text-emerald-400' : 'text-amber-400'}>
                {plan.safety_gates.unmounted_verified ? '✓ Partition Unmounted' : '⚠ Mounted Volume'}
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <span className={plan.safety_gates.capability_verified ? 'text-emerald-400' : 'text-slate-400'}>
                {plan.safety_gates.capability_verified ? '✓ Capability Verified' : '⚠ Standard Overwrite'}
              </span>
            </div>
          </div>
        </div>

        {/* Technical Limitation Disclaimer */}
        <div className="bg-amber-950/40 border border-amber-500/30 rounded-xl p-3 text-xs text-amber-200/90 leading-relaxed flex items-start space-x-2">
          <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-amber-300">Technical Scope Disclaimer: </span>
            {plan.limitations_disclaimer}
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center justify-end space-x-3 pt-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-slate-300 hover:text-slate-100 bg-slate-800 hover:bg-slate-700 rounded-xl transition-all"
          >
            Cancel
          </button>
          <button
            onClick={onProceedToConfirm}
            disabled={!plan.safety_gates.all_gates_passed}
            className={`flex items-center space-x-2 px-5 py-2 text-xs font-bold rounded-xl transition-all shadow-lg ${
              plan.safety_gates.all_gates_passed
                ? 'bg-cyan-600 hover:bg-cyan-500 text-white shadow-cyan-900/50 cursor-pointer'
                : 'bg-slate-800 text-slate-500 border border-slate-700 cursor-not-allowed'
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
