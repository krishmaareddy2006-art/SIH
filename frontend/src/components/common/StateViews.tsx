import React from 'react';
import { Loader2, ShieldX, WifiOff, AlertTriangle, Inbox, RefreshCw } from 'lucide-react';

export const LoadingSpinner: React.FC<{ message?: string }> = ({ message = 'Loading forensic data...' }) => (
  <div className="flex flex-col items-center justify-center p-12 space-y-3 text-center animate-fade-in">
    <div className="relative">
      <Loader2 className="w-7 h-7 text-[#22D3EE] animate-spin" />
      <span className="w-2 h-2 rounded-full bg-[#22D3EE]/40 absolute inset-0 m-auto" />
    </div>
    <p className="text-xs font-mono text-[#94A3B8]">{message}</p>
  </div>
);

export const EmptyState: React.FC<{ title: string; message: string; actionLabel?: string; onAction?: () => void }> = ({
  title,
  message,
  actionLabel,
  onAction,
}) => (
  <div className="flex flex-col items-center justify-center p-12 bg-[#111827] border border-[#253044] rounded-2xl text-center space-y-3.5 my-4 shadow-subtle">
    <div className="p-3 bg-[#0B0F19] border border-[#253044] rounded-xl text-[#64748B]">
      <Inbox className="w-7 h-7" />
    </div>
    <div>
      <h4 className="text-sm font-semibold text-[#F8FAFC]">{title}</h4>
      <p className="text-xs text-[#94A3B8] max-w-md mt-1 leading-relaxed">{message}</p>
    </div>
    {actionLabel && onAction && (
      <button
        onClick={onAction}
        className="mt-1 px-4 py-2 bg-[#22D3EE] hover:bg-[#67E8F9] text-[#080B14] font-semibold text-xs rounded-xl transition-all shadow-subtle cursor-pointer"
      >
        {actionLabel}
      </button>
    )}
  </div>
);

export const ErrorState: React.FC<{ code?: string; message: string; onRetry?: () => void }> = ({
  code = 'ERROR',
  message,
  onRetry,
}) => (
  <div className="flex flex-col items-center justify-center p-8 bg-[#1A0E13] border border-[#FB7185]/30 rounded-2xl text-center space-y-3 my-4 shadow-subtle">
    <div className="p-2.5 bg-[#FB7185]/10 border border-[#FB7185]/20 text-[#FB7185] rounded-xl">
      <AlertTriangle className="w-6 h-6" />
    </div>
    <div>
      <span className="text-[10px] font-mono text-[#FB7185] bg-[#2A151C] px-2 py-0.5 rounded border border-[#FB7185]/30 uppercase font-semibold">
        {code}
      </span>
      <h4 className="text-sm font-semibold text-[#F8FAFC] mt-2">{message}</h4>
    </div>
    {onRetry && (
      <button
        onClick={onRetry}
        className="flex items-center space-x-1.5 px-3.5 py-1.5 bg-[#111827] hover:bg-[#162032] text-[#F8FAFC] font-medium text-xs rounded-xl transition-all border border-[#253044] mt-1 cursor-pointer"
      >
        <RefreshCw className="w-3.5 h-3.5 text-[#22D3EE]" />
        <span>Retry Request</span>
      </button>
    )}
  </div>
);

export const OfflineBanner: React.FC = () => (
  <div className="bg-[#1C150A] border-b border-[#FBBF24]/40 text-[#FDE68A] px-4 py-2 flex items-center justify-center space-x-2 text-xs font-mono font-medium shadow-subtle">
    <WifiOff className="w-3.5 h-3.5 text-[#FBBF24]" />
    <span>OFFLINE MODE DETECTED — SYSTEM ACTIONS WILL BE QUEUED OR RESTRICTED</span>
  </div>
);

export const PermissionDeniedState: React.FC<{ requiredRoles?: string[] }> = ({
  requiredRoles = ['Administrator'],
}) => (
  <div className="flex flex-col items-center justify-center p-12 bg-[#111827] border border-[#FB7185]/30 rounded-2xl text-center space-y-4 my-6 shadow-subtle">
    <div className="p-3.5 bg-[#FB7185]/10 border border-[#FB7185]/30 text-[#FB7185] rounded-2xl">
      <ShieldX className="w-8 h-8" />
    </div>
    <div className="space-y-1">
      <h3 className="text-sm font-bold text-[#F8FAFC] uppercase tracking-wider">
        ACCESS DENIED: INSUFFICIENT PERMISSIONS
      </h3>
      <p className="text-xs text-[#94A3B8] max-w-md">
        Your current operator role does not have authorization to access this module.
      </p>
    </div>
    <div className="bg-[#0B0F19] border border-[#253044] px-3 py-1.5 rounded-lg font-mono text-xs text-[#FBBF24]">
      Required Role(s): {requiredRoles.join(' OR ')}
    </div>
  </div>
);
