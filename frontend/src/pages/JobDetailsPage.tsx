import React, { useState, useEffect } from 'react';
import { Activity, XCircle, RefreshCw } from 'lucide-react';
import { api } from '../services/api';
import { JobRecord } from '../types';
import { useCase } from '../context/CaseContext';
import { useNotification } from '../context/NotificationContext';
import { LoadingSpinner, ErrorState } from '../components/common/StateViews';
import { StatusBadge } from '../components/common/StatusBadge';

export const JobDetailsPage: React.FC = () => {
  const { activeCase } = useCase();
  const { addToast } = useNotification();

  const [jobs, setJobs] = useState<JobRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const loadJobs = async () => {
    setIsLoading(true);
    setError('');
    const res = await api.listJobs(activeCase?.id);
    if (res.data) {
      setJobs(res.data);
    } else if (res.error) {
      setError(res.error.error.message);
    }
    setIsLoading(false);
  };

  useEffect(() => {
    loadJobs();
  }, [activeCase?.id]);

  const handleCancelJob = async (jobId: string) => {
    const res = await api.cancelJob(jobId);
    if (res.data) {
      addToast('info', 'Cancellation Requested', `Job ${jobId} cancellation checkpoint triggered.`);
      loadJobs();
    } else if (res.error) {
      addToast('error', 'Cancellation Failed', res.error.error.message);
    }
  };

  if (isLoading && jobs.length === 0) return <LoadingSpinner message="Polling background job manager state..." />;
  if (error) return <ErrorState code="JOB_FETCH_ERROR" message={error} onRetry={loadJobs} />;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="bg-[#111827] p-5 sm:p-6 rounded-2xl border border-[#253044] shadow-card flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-lg sm:text-xl font-bold text-[#F8FAFC] flex items-center">
            <Activity className="w-5 h-5 text-[#FBBF24] mr-2.5" />
            Background Job Monitor & Cancellation Checkpoints
          </h2>
          <p className="text-xs text-[#94A3B8] mt-1">
            Real-time async worker state tracking (Queued, Running, Cancelling, Completed, Failed, Aborted)
          </p>
        </div>

        <button
          onClick={loadJobs}
          className="flex items-center space-x-2 bg-[#0B0F19] hover:bg-[#162032] text-[#F8FAFC] text-xs font-semibold px-4 py-2 rounded-xl border border-[#253044] transition-all cursor-pointer shadow-subtle"
        >
          <RefreshCw className="w-3.5 h-3.5 text-[#22D3EE]" />
          <span>Refresh Job Queue</span>
        </button>
      </div>

      {/* Jobs Grid */}
      <div className="space-y-4">
        {jobs.map(job => (
          <div
            key={job.job_id}
            className="bg-[#111827] border border-[#253044] rounded-2xl p-5 space-y-4 shadow-card text-xs hover:border-[#22D3EE]/30 transition-colors"
          >
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="space-y-1">
                <div className="flex items-center space-x-2.5">
                  <span className="font-mono text-[#22D3EE] font-bold text-sm">{job.job_id}</span>
                  <span className="bg-[#0B0F19] text-[#94A3B8] font-mono text-[10px] px-2 py-0.5 rounded-md border border-[#253044]">
                    {job.job_type}
                  </span>
                </div>
                <p className="text-[#64748B] font-mono text-[11px]">Started: {job.created_at?.substring(0, 19)} UTC</p>
              </div>

              <div className="flex items-center space-x-3">
                <StatusBadge status={job.status} />

                {job.status === 'RUNNING' && (
                  <button
                    onClick={() => handleCancelJob(job.job_id)}
                    className="flex items-center space-x-1.5 px-3 py-1.5 bg-[#FB7185]/10 hover:bg-[#FB7185]/20 text-[#FB7185] border border-[#FB7185]/30 font-semibold rounded-xl transition-all cursor-pointer shadow-subtle"
                  >
                    <XCircle className="w-3.5 h-3.5" />
                    <span>Request Cancellation</span>
                  </button>
                )}
              </div>
            </div>

            {/* Progress Bar */}
            <div className="space-y-1.5 bg-[#0B0F19] p-3 rounded-xl border border-[#253044]">
              <div className="flex items-center justify-between font-mono text-[11px]">
                <span className="text-[#94A3B8]">{job.progress_stage}</span>
                <span className="text-[#22D3EE] font-bold">{job.progress_percent}%</span>
              </div>
              <div className="w-full bg-[#111827] rounded-full h-1.5 overflow-hidden border border-[#253044]">
                <div
                  className="bg-gradient-to-r from-[#22D3EE] to-[#34D399] h-1.5 rounded-full transition-all duration-300"
                  style={{ width: `${job.progress_percent}%` }}
                />
              </div>
            </div>
          </div>
        ))}

        {jobs.length === 0 && (
          <div className="p-10 bg-[#111827] border border-[#253044] rounded-2xl text-center text-[#64748B] text-xs shadow-subtle">
            No active or historical background jobs recorded for this case.
          </div>
        )}
      </div>
    </div>
  );
};
