import React from 'react';
import { Activity, ShieldCheck, Lock, AlertTriangle, RefreshCw } from 'lucide-react';
import { SystemStatus } from '../services/api';

interface SystemStatusCardProps {
  status: SystemStatus | null;
  loading: boolean;
  onRefresh: () => void;
}

export const SystemStatusCard: React.FC<SystemStatusCardProps> = ({
  status,
  loading,
  onRefresh,
}) => {
  return (
    <div className="glass-panel p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-cyber-teal" />
          <h2 className="text-lg font-semibold text-white">System Security Posture</h2>
        </div>
        <button
          onClick={onRefresh}
          disabled={loading}
          className="p-2 rounded-lg bg-dark-700 hover:bg-dark-600 text-slate-300 transition-colors disabled:opacity-50"
          title="Refresh System Status"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Status Item 1 */}
        <div className="p-4 rounded-lg bg-dark-900/60 border border-dark-700/60 flex items-start gap-3">
          <div className="p-2 rounded bg-teal-500/10 text-teal-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-mono">SAFE_MODE GUARD</p>
            <p className="text-sm font-semibold text-white mt-1">
              {status?.safe_mode ? 'Active (Simulate Only)' : 'Inactive'}
            </p>
            <p className="text-xs text-slate-400 mt-1">
              Blocks destructive storage mutations by default.
            </p>
          </div>
        </div>

        {/* Status Item 2 */}
        <div className="p-4 rounded-lg bg-dark-900/60 border border-dark-700/60 flex items-start gap-3">
          <div className="p-2 rounded bg-amber-500/10 text-amber-400">
            <Lock className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-mono">HARDWARE GATE</p>
            <p className="text-sm font-semibold text-white mt-1">
              {status?.real_device_operations ? 'Real Hardware Access' : 'Disabled (Flag = false)'}
            </p>
            <p className="text-xs text-slate-400 mt-1">
              Prevents raw physical drive read/writes.
            </p>
          </div>
        </div>

        {/* Status Item 3 */}
        <div className="p-4 rounded-lg bg-dark-900/60 border border-dark-700/60 flex items-start gap-3">
          <div className="p-2 rounded bg-cyan-500/10 text-cyan-400">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-mono">AUDIT TRAIL LOGGING</p>
            <p className="text-sm font-semibold text-white mt-1">Structured JSON</p>
            <p className="text-xs text-slate-400 mt-1">
              Emits trace request_id, case_id, user_id.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
