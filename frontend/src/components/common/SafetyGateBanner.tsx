import React from 'react';
import { ShieldAlert, AlertTriangle, ShieldCheck, Lock } from 'lucide-react';

interface SafetyGateBannerProps {
  devicePath?: string;
  isSystemDisk?: boolean;
  safeMode?: boolean;
  realDeviceOps?: boolean;
  gatePassed?: boolean;
  failureReasons?: string[];
}

export const SafetyGateBanner: React.FC<SafetyGateBannerProps> = ({
  devicePath,
  isSystemDisk = false,
  safeMode = true,
  realDeviceOps = false,
  gatePassed,
  failureReasons = [],
}) => {
  return (
    <div className="space-y-3 my-4">
      {/* System Disk Danger Warning */}
      {isSystemDisk && (
        <div className="bg-red-950/80 border-2 border-red-500 text-red-200 p-4 rounded-xl flex items-start space-x-3 shadow-lg shadow-red-950/50">
          <AlertTriangle className="w-6 h-6 text-red-400 shrink-0 mt-0.5" />
          <div>
            <h4 className="font-bold text-red-300 uppercase tracking-wide text-sm">
              CRITICAL SAFETY GATE VIOLATION: SYSTEM DISK DETECTED
            </h4>
            <p className="text-xs text-red-200 mt-1 leading-relaxed">
              Target device <span className="font-mono bg-red-900/60 px-1.5 py-0.5 rounded text-red-100">{devicePath || 'N/A'}</span> is classified as an OS System Disk. Destructive operations on system volumes are permanently prohibited by ForensicShield safety policy.
            </p>
          </div>
        </div>
      )}

      {/* Hardware Safety Policy Status Banner */}
      <div className="bg-slate-900 border border-slate-700/80 rounded-xl p-3.5 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Lock className="w-4 h-4 text-emerald-400" />
            <span className="text-slate-300 font-medium">Safe Mode:</span>
            <span className={`px-2 py-0.5 rounded-full font-semibold ${safeMode ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'}`}>
              {safeMode ? 'ENABLED (Simulated)' : 'DISABLED'}
            </span>
          </div>

          <div className="flex items-center space-x-2">
            <ShieldAlert className="w-4 h-4 text-cyan-400" />
            <span className="text-slate-300 font-medium">Real Hardware Ops:</span>
            <span className={`px-2 py-0.5 rounded-full font-semibold ${realDeviceOps ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' : 'bg-slate-800 text-slate-400 border border-slate-700'}`}>
              {realDeviceOps ? 'ACTIVE' : 'BLOCKED (Default)'}
            </span>
          </div>
        </div>

        {gatePassed !== undefined && (
          <div className="flex items-center space-x-2">
            {gatePassed ? (
              <span className="flex items-center text-emerald-400 font-medium bg-emerald-950/60 border border-emerald-800/80 px-2.5 py-1 rounded-lg">
                <ShieldCheck className="w-4 h-4 mr-1.5 text-emerald-400" /> Safety Gate: ALL CHECKS PASSED
              </span>
            ) : (
              <span className="flex items-center text-red-400 font-medium bg-red-950/60 border border-red-800/80 px-2.5 py-1 rounded-lg">
                <AlertTriangle className="w-4 h-4 mr-1.5 text-red-400" /> Safety Gate: REJECTED
              </span>
            )}
          </div>
        )}
      </div>

      {/* Detailed Failure Reasons */}
      {failureReasons.length > 0 && (
        <div className="bg-amber-950/40 border border-amber-500/30 text-amber-200 p-3 rounded-lg text-xs space-y-1">
          <p className="font-semibold text-amber-300">Gate Verification Blocked Reasons:</p>
          <ul className="list-disc list-inside space-y-0.5 text-amber-200/90 pl-1">
            {failureReasons.map((reason, idx) => (
              <li key={idx}>{reason}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
