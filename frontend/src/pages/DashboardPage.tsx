import React, { useState, useEffect } from 'react';
import { Shield, Briefcase, Activity, History, Flame, FileSearch, UploadCloud, CheckCircle2, AlertTriangle, ArrowUpRight } from 'lucide-react';
import { api } from '../services/api';
import { SystemStatus, ForensicCase, JobRecord, AuditEvent } from '../types';
import { LoadingSpinner, ErrorState } from '../components/common/StateViews';
import { StatusBadge } from '../components/common/StatusBadge';

export const DashboardPage: React.FC<{ onNavigate: (tabId: string) => void }> = ({ onNavigate }) => {
  const [health, setHealth] = useState<SystemStatus | null>(null);
  const [cases, setCases] = useState<ForensicCase[]>([]);
  const [recentJobs, setRecentJobs] = useState<JobRecord[]>([]);
  const [recentAudit, setRecentAudit] = useState<AuditEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const loadDashboardData = async () => {
    setIsLoading(true);
    setError('');
    const [hRes, cRes, jRes, aRes] = await Promise.all([
      api.getSystemHealth(),
      api.listCases(),
      api.listJobs(),
      api.listAuditEvents({ limit: 5 }),
    ]);

    if (hRes.data) setHealth(hRes.data);
    if (cRes.data) setCases(cRes.data);
    if (jRes.data) setRecentJobs(jRes.data);
    if (aRes.data) setRecentAudit(aRes.data);

    if (hRes.error && !hRes.data) {
      setError(hRes.error.error.message);
    }
    setIsLoading(false);
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  if (isLoading) return <LoadingSpinner message="Fetching ForensicShield system state & metrics..." />;
  if (error) return <ErrorState code="DASHBOARD_LOAD_ERROR" message={error} onRetry={loadDashboardData} />;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-900 to-slate-950 p-6 rounded-2xl border border-slate-800 shadow-xl flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-xl font-extrabold text-slate-100">ForensicShield Incident Command Dashboard</h2>
            <span className="bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 text-[10px] font-mono font-bold px-2 py-0.5 rounded-full">
              LIVE
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Enterprise Digital Forensics & Data Integrity Control Center
          </p>
        </div>

        <div className="flex items-center space-x-3 text-xs font-mono">
          <div className="bg-slate-950 border border-slate-800 px-3 py-1.5 rounded-xl flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span className="text-slate-300">Safe Mode: <strong className="text-emerald-300">ACTIVE</strong></span>
          </div>
          <div className="bg-slate-950 border border-slate-800 px-3 py-1.5 rounded-xl flex items-center space-x-2">
            <Shield className="w-4 h-4 text-cyan-400" />
            <span className="text-slate-300">Audit Chain: <strong className="text-cyan-300">INTACT</strong></span>
          </div>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900 p-5 rounded-2xl border border-slate-800 space-y-3">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Active Cases</span>
            <Briefcase className="w-5 h-5 text-cyan-400" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-extrabold text-slate-100">{cases.length}</span>
            <span className="text-xs text-emerald-400 font-mono">Total Cases</span>
          </div>
        </div>

        <div className="bg-slate-900 p-5 rounded-2xl border border-slate-800 space-y-3">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Background Jobs</span>
            <Activity className="w-5 h-5 text-amber-400" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-extrabold text-slate-100">{recentJobs.length}</span>
            <span className="text-xs text-amber-400 font-mono">Active/Queued</span>
          </div>
        </div>

        <div className="bg-slate-900 p-5 rounded-2xl border border-slate-800 space-y-3">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Audit Chain Block</span>
            <History className="w-5 h-5 text-emerald-400" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-extrabold text-slate-100">{recentAudit.length}</span>
            <span className="text-xs text-emerald-400 font-mono">Validated Links</span>
          </div>
        </div>

        <div className="bg-slate-900 p-5 rounded-2xl border border-slate-800 space-y-3">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">System Safety</span>
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-lg font-bold text-emerald-300">PASS</span>
            <span className="text-xs text-slate-400 font-mono">Simulated Only</span>
          </div>
        </div>
      </div>

      {/* Quick Operations Launcher */}
      <div className="space-y-3">
        <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider">Quick Launch Operations</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => onNavigate('sanitization')}
            className="p-4 bg-slate-900 hover:bg-slate-800/80 border border-slate-800 rounded-2xl text-left space-y-2 group transition-all"
          >
            <div className="flex items-center justify-between text-red-400">
              <Flame className="w-6 h-6" />
              <ArrowUpRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity text-slate-400" />
            </div>
            <h4 className="text-sm font-bold text-slate-200 group-hover:text-cyan-400 transition-colors">Drive Sanitization Wizard</h4>
            <p className="text-xs text-slate-400 leading-relaxed">Safety-gated storage media sanitization & block overwrite.</p>
          </button>

          <button
            onClick={() => onNavigate('evidence')}
            className="p-4 bg-slate-900 hover:bg-slate-800/80 border border-slate-800 rounded-2xl text-left space-y-2 group transition-all"
          >
            <div className="flex items-center justify-between text-cyan-400">
              <UploadCloud className="w-6 h-6" />
              <ArrowUpRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity text-slate-400" />
            </div>
            <h4 className="text-sm font-bold text-slate-200 group-hover:text-cyan-400 transition-colors">Evidence Image Intake</h4>
            <p className="text-xs text-slate-400 leading-relaxed">Read-only streaming SHA-256 ingestion & working copy setup.</p>
          </button>

          <button
            onClick={() => onNavigate('recovery')}
            className="p-4 bg-slate-900 hover:bg-slate-800/80 border border-slate-800 rounded-2xl text-left space-y-2 group transition-all"
          >
            <div className="flex items-center justify-between text-amber-400">
              <FileSearch className="w-6 h-6" />
              <ArrowUpRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity text-slate-400" />
            </div>
            <h4 className="text-sm font-bold text-slate-200 group-hover:text-cyan-400 transition-colors">Recovery & Carving Hub</h4>
            <p className="text-xs text-slate-400 leading-relaxed">Filesystem extent extraction & signature-based carving.</p>
          </button>
        </div>
      </div>

      {/* Recent Audit Ledger Snippet */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2">
            <History className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-bold text-slate-200">Recent Audit Chain Events</h3>
          </div>
          <button
            onClick={() => onNavigate('audit')}
            className="text-xs text-cyan-400 hover:text-cyan-300 font-semibold"
          >
            View Full Audit Chain →
          </button>
        </div>

        <div className="space-y-2 text-xs">
          {recentAudit.map(ev => (
            <div key={ev.id} className="p-3 bg-slate-950 border border-slate-800/80 rounded-xl flex items-center justify-between gap-4">
              <div className="space-y-0.5">
                <span className="font-mono text-cyan-300 font-semibold">{ev.action}</span>
                <p className="text-slate-400 text-[11px] truncate max-w-xl">{ev.target_summary}</p>
              </div>
              <div className="text-right shrink-0">
                <StatusBadge status={ev.result} />
                <span className="block font-mono text-[10px] text-slate-500 mt-1">{ev.timestamp.substring(11, 19)} UTC</span>
              </div>
            </div>
          ))}
          {recentAudit.length === 0 && (
            <p className="text-slate-500 text-center py-4">No recent audit events recorded.</p>
          )}
        </div>
      </div>
    </div>
  );
};
