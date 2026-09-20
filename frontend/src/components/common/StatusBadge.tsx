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
    container: 'bg-[#101827] text-[#91A0B5] border-[#1E3048]',
    dot: 'bg-[#91A0B5]',
    icon: <HelpCircle className="w-3 h-3 mr-1 text-[#91A0B5]" />,
    label: status || 'Unknown',
  };

  if (isVerified) {
    config = {
      container: 'bg-[#20D69A]/10 text-[#20D69A] border-[#20D69A]/30',
      dot: 'bg-[#20D69A]',
      icon: <CheckCircle2 className="w-3 h-3 mr-1 text-[#20D69A]" />,
      label: norm === 'COMPLETED' ? 'Completed' : norm === 'RECOVERABLE' ? 'Recoverable' : norm === 'HIGH' ? 'High Confidence' : 'Verified',
    };
  } else if (isInconclusive) {
    config = {
      container: 'bg-[#F5B642]/10 text-[#F5B642] border-[#F5B642]/30',
      dot: 'bg-[#F5B642]',
      icon: <HelpCircle className="w-3 h-3 mr-1 text-[#F5B642]" />,
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
      container: 'bg-[#8B6CFF]/10 text-[#8B6CFF] border-[#8B6CFF]/30',
      dot: 'bg-[#8B6CFF]',
      icon: <AlertOctagon className="w-3 h-3 mr-1 text-[#8B6CFF]" />,
      label: norm === 'LOW' ? 'Low Confidence' : 'Unsupported',
    };
  } else if (isManualReview) {
    config = {
      container: 'bg-[#19D3E6]/10 text-[#19D3E6] border-[#19D3E6]/30',
      dot: 'bg-[#19D3E6]',
      icon: <UserCheck className="w-3 h-3 mr-1 text-[#19D3E6]" />,
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
