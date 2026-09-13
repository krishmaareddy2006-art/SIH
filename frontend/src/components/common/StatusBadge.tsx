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
  | 'SUCCESS'
  | 'RUNNING'
  | 'QUEUED'
  | 'CANCELLED'
  | string;

interface StatusBadgeProps {
  status: ClassificationStatus;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'sm' }) => {
  const norm = status?.toString().toUpperCase() || '';

  const isVerified = norm === 'VERIFIED' || norm === 'RECOVERABLE' || norm === 'HIGH' || norm === 'COMPLETED' || norm === 'SUCCESS';
  const isInconclusive = norm === 'INCONCLUSIVE' || norm === 'PARTIALLY_RECOVERABLE' || norm === 'MEDIUM' || norm === 'QUEUED' || norm === 'RUNNING';
  const isFailed = norm === 'FAILED' || norm === 'CORRUPTED' || norm === 'INTEGRITY_FAILURE' || norm === 'CANCELLED';
  const isUnsupported = norm === 'UNSUPPORTED' || norm === 'LOW';
  const isManualReview = norm === 'MANUAL REVIEW' || norm === 'MANUAL_REVIEW' || norm === 'METADATA_ONLY';

  let config = {
    container: 'bg-[#111827] text-[#94A3B8] border-[#253044]',
    dot: 'bg-[#94A3B8]',
    icon: <HelpCircle className="w-3 h-3 mr-1 text-[#94A3B8]" />,
    label: status || 'Unknown',
  };

  if (isVerified) {
    config = {
      container: 'bg-[#34D399]/10 text-[#34D399] border-[#34D399]/30',
      dot: 'bg-[#34D399]',
      icon: <CheckCircle2 className="w-3 h-3 mr-1 text-[#34D399]" />,
      label: norm === 'COMPLETED' ? 'Completed' : norm === 'RECOVERABLE' ? 'Recoverable' : norm === 'HIGH' ? 'High Confidence' : 'Verified',
    };
  } else if (isInconclusive) {
    config = {
      container: 'bg-[#FBBF24]/10 text-[#FBBF24] border-[#FBBF24]/30',
      dot: 'bg-[#FBBF24]',
      icon: <HelpCircle className="w-3 h-3 mr-1 text-[#FBBF24]" />,
      label: norm === 'RUNNING' ? 'Running' : norm === 'QUEUED' ? 'Queued' : norm === 'PARTIALLY_RECOVERABLE' ? 'Partially Recoverable' : 'Inconclusive',
    };
  } else if (isFailed) {
    config = {
      container: 'bg-[#FB7185]/10 text-[#FB7185] border-[#FB7185]/30',
      dot: 'bg-[#FB7185]',
      icon: <XCircle className="w-3 h-3 mr-1 text-[#FB7185]" />,
      label: norm === 'CORRUPTED' ? 'Corrupted' : norm === 'CANCELLED' ? 'Cancelled' : norm === 'INTEGRITY_FAILURE' ? 'Integrity Failure' : 'Failed',
    };
  } else if (isUnsupported) {
    config = {
      container: 'bg-[#A78BFA]/10 text-[#C4B5FD] border-[#A78BFA]/30',
      dot: 'bg-[#A78BFA]',
      icon: <AlertOctagon className="w-3 h-3 mr-1 text-[#A78BFA]" />,
      label: norm === 'LOW' ? 'Low Confidence' : 'Unsupported',
    };
  } else if (isManualReview) {
    config = {
      container: 'bg-[#22D3EE]/10 text-[#22D3EE] border-[#22D3EE]/30',
      dot: 'bg-[#22D3EE]',
      icon: <UserCheck className="w-3 h-3 mr-1 text-[#22D3EE]" />,
      label: 'Manual Review',
    };
  }

  const padding = size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs';

  return (
    <span
      className={`inline-flex items-center font-medium font-mono border rounded-full ${config.container} ${padding} transition-colors select-none`}
    >
      <span className={`w-1.5 h-1.5 rounded-full mr-1.5 ${config.dot} animate-pulse shrink-0`} />
      {config.icon}
      <span>{config.label}</span>
    </span>
  );
};
