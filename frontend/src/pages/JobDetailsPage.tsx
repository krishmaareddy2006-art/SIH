import React, { useState, useEffect } from 'react';
import { Activity, XCircle, RefreshCw, CheckCircle2, Clock, AlertTriangle } from 'lucide-react';
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
      <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800 shadow-xl flex items-center justify-between">
        <div>
          <h2 className="text-xl font-extrabold text-slate-100 flex items-center">
            <Activity className="w-6 h-6 text-amber-400 mr-2.5" />
            Background Job Monitor & Cancellation Checkpoints
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Real-time async worker state tracking (Queued, Running, Cancelling, Completed, Failed, Aborted, Manual Review)
          </p>
        </div>

        <button
          onClick={loadJobs}
          className="flex items-center space-x-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold px-4 py-2.5 rounded-xl border border-slate-700 transition-all"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Job Queue</span>
        </button>
      </div>

      {/* Jobs Grid */}
      <div className="space-y-4">
        {jobs.map(job => (
          <div key={job.job_id} className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-xl text-xs">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="font-mono text-cyan-400 font-extrabold text-sm">{job.job_id}</span>
                  <span className="bg-slate-800 text-slate-300 font-mono text-[10px] px-2 py-0.5 rounded-full border border-slate-700">
                    {job.job_type}
                  </span>
                </div>
                <p className="text-slate-400 font-mono text-[11px]">Started: {job.created_at?.substring(0, 19)} UTC</p>
              </div>

              <div className="flex items-center space-x-3">
                <StatusBadge status={job.status} />

                {job.status === 'RUNNING' && (
                  <button
                    onClick={() => handleCancelJob(job.job_id)}
                    className="flex items-center space-x-1 px-3 py-1.5 bg-red-950/80 hover:bg-red-900 text-red-300 border border-red-500/40 font-semibold rounded-xl transition-all cursor-pointer"
                  >
                    <XCircle className="w-3.5 h-3.5" />
                    <span>Request Cancellation</span>
                  </button>
                )}
              </div>
            </div>

            {/* Progress Bar */}
            <div className="space-y-1 bg-slate-950 p-3 rounded-xl border border-slate-800">
              <div className="flex items-center justify-between font-mono text-[11px]">
                <span className="text-slate-300">{job.progress_stage}</span>
                <span className="text-cyan-300 font-bold">{job.progress_percent}%</span>
              </div>
              <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800">
                <div
                  className="bg-gradient-to-r from-cyan-500 to-amber-400 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${job.progress_percent}%` }}
                ></div>
              </div>
            </div>
          </div>
        ))}

        {jobs.length === 0 && (
          <div className="p-8 bg-slate-900 border border-slate-800 rounded-2xl text-center text-slate-500 text-xs">
            No active or historical background jobs recorded.
          </div>
        )}
      </div>
    </div>
  );
};
