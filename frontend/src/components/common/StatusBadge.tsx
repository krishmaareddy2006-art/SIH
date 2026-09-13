import React from 'react';
import { CheckCircle2, HelpCircle, XCircle, AlertOctagon, UserCheck } from 'lucide-react';

export type ClassificationStatus =
  | 'Verified'
  | 'Inconclusive'
  | 'Failed'
  | 'Unsupported'
  | 'Manual Review'
  | 'RECOVERABLE'
  | 'PARTIALLY_RECOVERABLE'
  | 'CORRUPTED'
  | 'UNSUPPORTED'
  | 'HIGH'
  | 'MEDIUM'
  | 'LOW'
  | 'COMPLETED'
  | 'INTEGRITY_FAILURE'
  | string;

interface StatusBadgeProps {
  status: ClassificationStatus;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'sm' }) => {
  const norm = status?.toString().toUpperCase() || '';

  const isVerified = norm === 'VERIFIED' || norm === 'RECOVERABLE' || norm === 'HIGH' || norm === 'COMPLETED';
  const isInconclusive = norm === 'INCONCLUSIVE' || norm === 'PARTIALLY_RECOVERABLE' || norm === 'MEDIUM';
  const isFailed = norm === 'FAILED' || norm === 'CORRUPTED' || norm === 'INTEGRITY_FAILURE';
  const isUnsupported = norm === 'UNSUPPORTED' || norm === 'LOW';
  const isManualReview = norm === 'MANUAL REVIEW' || norm === 'MANUAL_REVIEW' || norm === 'METADATA_ONLY';

  let config = {
    bg: 'bg-slate-800 text-slate-300 border-slate-700',
    icon: <HelpCircle className="w-3.5 h-3.5 mr-1" />,
    label: status,
  };

  if (isVerified) {
    config = {
      bg: 'bg-emerald-950/80 text-emerald-300 border-emerald-500/40',
      icon: <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-emerald-400" />,
      label: 'Verified',
    };
  } else if (isInconclusive) {
    config = {
      bg: 'bg-amber-950/80 text-amber-300 border-amber-500/40',
      icon: <HelpCircle className="w-3.5 h-3.5 mr-1 text-amber-400" />,
      label: 'Inconclusive',
    };
  } else if (isFailed) {
    config = {
      bg: 'bg-red-950/80 text-red-300 border-red-500/40',
      icon: <XCircle className="w-3.5 h-3.5 mr-1 text-red-400" />,
      label: 'Failed',
    };
  } else if (isUnsupported) {
    config = {
      bg: 'bg-purple-950/80 text-purple-300 border-purple-500/40',
      icon: <AlertOctagon className="w-3.5 h-3.5 mr-1 text-purple-400" />,
      label: 'Unsupported',
    };
  } else if (isManualReview) {
    config = {
      bg: 'bg-blue-950/80 text-blue-300 border-blue-500/40',
      icon: <UserCheck className="w-3.5 h-3.5 mr-1 text-blue-400" />,
      label: 'Manual Review',
    };
  }

  const px = size === 'sm' ? 'px-2.5 py-0.5 text-xs' : 'px-3 py-1 text-sm';

  return (
    <span className={`inline-flex items-center font-medium rounded-full border shadow-sm ${config.bg} ${px}`}>
      {config.icon}
      <span>{config.label}</span>
    </span>
  );
};
