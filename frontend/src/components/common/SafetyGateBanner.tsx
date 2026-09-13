import React from 'react';
import { ShieldAlert, AlertTriangle, ShieldCheck, Lock, AlertOctagon } from 'lucide-react';

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
        <div className="bg-[#1A0E13] border border-[#FB7185]/50 text-[#F8FAFC] p-4 rounded-xl flex items-start space-x-3.5 shadow-card">
          <div className="p-2 bg-[#FB7185]/10 rounded-lg text-[#FB7185] shrink-0">
            <AlertOctagon className="w-5 h-5" />
          </div>
          <div>
            <h4 className="font-bold text-[#FB7185] uppercase tracking-wider text-xs">
              CRITICAL SAFETY GATE VIOLATION: SYSTEM DISK DETECTED
            </h4>
            <p className="text-xs text-[#94A3B8] mt-1 leading-relaxed">
              Target device <span className="font-mono text-[#F8FAFC] bg-[#2A151C] border border-[#FB7185]/30 px-1.5 py-0.5 rounded text-[11px] font-semibold">{devicePath || 'N/A'}</span> is classified as an OS System Disk. Destructive operations on system volumes are permanently prohibited by ForensicShield safety policy.
            </p>
          </div>
        </div>
      )}

      {/* Hardware Safety Policy Status Banner */}
      <div className="bg-[#111827] border border-[#253044] rounded-xl p-3.5 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center space-x-2">
            <Lock className="w-3.5 h-3.5 text-[#34D399]" />
            <span className="text-[#94A3B8] font-medium text-[11px]">Safe Mode:</span>
            <span className={`px-2 py-0.5 rounded-full font-mono text-[10px] font-semibold ${
              safeMode
                ? 'bg-[#34D399]/10 text-[#34D399] border border-[#34D399]/30'
                : 'bg-[#FBBF24]/10 text-[#FBBF24] border border-[#FBBF24]/30'
            }`}>
              {safeMode ? 'ENABLED (Simulated)' : 'DISABLED'}
            </span>
          </div>

          <div className="flex items-center space-x-2">
            <ShieldAlert className="w-3.5 h-3.5 text-[#22D3EE]" />
            <span className="text-[#94A3B8] font-medium text-[11px]">Real Hardware Ops:</span>
            <span className={`px-2 py-0.5 rounded-full font-mono text-[10px] font-semibold ${
              realDeviceOps
                ? 'bg-[#FBBF24]/10 text-[#FBBF24] border border-[#FBBF24]/30'
                : 'bg-[#0B0F19] text-[#64748B] border border-[#253044]'
            }`}>
              {realDeviceOps ? 'ACTIVE' : 'BLOCKED (Default)'}
            </span>
          </div>
        </div>

        {gatePassed !== undefined && (
          <div className="flex items-center space-x-2">
            {gatePassed ? (
              <span className="flex items-center text-[#34D399] font-mono text-[11px] font-medium bg-[#34D399]/10 border border-[#34D399]/30 px-2.5 py-1 rounded-lg">
                <ShieldCheck className="w-3.5 h-3.5 mr-1.5 text-[#34D399]" /> Safety Gate: ALL CHECKS PASSED
              </span>
            ) : (
              <span className="flex items-center text-[#FB7185] font-mono text-[11px] font-medium bg-[#FB7185]/10 border border-[#FB7185]/30 px-2.5 py-1 rounded-lg">
                <AlertTriangle className="w-3.5 h-3.5 mr-1.5 text-[#FB7185]" /> Safety Gate: REJECTED
              </span>
            )}
          </div>
        )}
      </div>

      {/* Detailed Failure Reasons */}
      {failureReasons.length > 0 && (
        <div className="bg-[#1C150A] border border-[#FBBF24]/30 text-[#F8FAFC] p-3 rounded-xl text-xs space-y-1">
          <p className="font-semibold text-[#FBBF24] text-[11px] uppercase tracking-wider">Gate Verification Blocked Reasons:</p>
          <ul className="list-disc list-inside space-y-0.5 text-[#94A3B8] text-[11px] pl-1 font-mono">
            {failureReasons.map((reason, idx) => (
              <li key={idx}>{reason}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
