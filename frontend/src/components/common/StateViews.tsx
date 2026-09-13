import React from 'react';
import { Loader2, ShieldX, WifiOff, AlertTriangle, Inbox, RefreshCw } from 'lucide-react';

export const LoadingSpinner: React.FC<{ message?: string }> = ({ message = 'Loading forensic data...' }) => (
  <div className="flex flex-col items-center justify-center p-12 space-y-3 text-center">
    <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
    <p className="text-xs font-mono text-slate-400">{message}</p>
  </div>
);

export const EmptyState: React.FC<{ title: string; message: string; actionLabel?: string; onAction?: () => void }> = ({
  title,
  message,
  actionLabel,
  onAction,
}) => (
  <div className="flex flex-col items-center justify-center p-12 bg-slate-900/60 border border-slate-800 rounded-2xl text-center space-y-3 my-4">
    <div className="p-3 bg-slate-800/80 rounded-2xl text-slate-400">
      <Inbox className="w-8 h-8" />
    </div>
    <h4 className="text-sm font-bold text-slate-200">{title}</h4>
    <p className="text-xs text-slate-400 max-w-md">{message}</p>
    {actionLabel && onAction && (
      <button
        onClick={onAction}
        className="mt-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs rounded-xl transition-all shadow-md shadow-cyan-950"
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
  <div className="flex flex-col items-center justify-center p-8 bg-red-950/30 border border-red-500/30 rounded-2xl text-center space-y-3 my-4">
    <div className="p-3 bg-red-500/10 text-red-400 rounded-2xl">
      <AlertTriangle className="w-8 h-8" />
    </div>
    <div>
      <span className="text-[10px] font-mono text-red-400 bg-red-950 px-2 py-0.5 rounded uppercase border border-red-900">
        {code}
      </span>
      <h4 className="text-sm font-bold text-red-200 mt-2">{message}</h4>
    </div>
    {onRetry && (
      <button
        onClick={onRetry}
        className="flex items-center space-x-1.5 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-xs rounded-xl transition-all border border-slate-700 mt-2"
      >
        <RefreshCw className="w-3.5 h-3.5" />
        <span>Retry Request</span>
      </button>
    )}
  </div>
);

export const OfflineBanner: React.FC = () => (
  <div className="bg-amber-950/90 border-b border-amber-500 text-amber-100 px-4 py-2 flex items-center justify-center space-x-2 text-xs font-semibold shadow-md">
    <WifiOff className="w-4 h-4 text-amber-400" />
    <span>OFFLINE MODE DETECTED — SYSTEM ACTIONS MAY BE QUEUED OR RESTRICTED</span>
  </div>
);

export const PermissionDeniedState: React.FC<{ requiredRoles?: string[] }> = ({
  requiredRoles = ['Administrator'],
}) => (
  <div className="flex flex-col items-center justify-center p-12 bg-slate-900/80 border border-red-500/30 rounded-2xl text-center space-y-4 my-6">
    <div className="p-4 bg-red-500/10 border border-red-500/20 text-red-400 rounded-2xl">
      <ShieldX className="w-10 h-10" />
    </div>
    <div className="space-y-1">
      <h3 className="text-base font-bold text-slate-100">ACCESS DENIED: INSUFFICIENT PERMISSIONS</h3>
      <p className="text-xs text-slate-400 max-w-md">
        Your current operator role does not have authorization to access this module.
      </p>
    </div>
    <div className="bg-slate-950 border border-slate-800 px-3 py-1.5 rounded-lg font-mono text-xs text-amber-300">
      Required Role(s): {requiredRoles.join(' OR ')}
    </div>
  </div>
);
