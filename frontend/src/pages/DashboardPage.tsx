import React, { useState, useEffect } from 'react';
import { Shield, Briefcase, Activity, History, Flame, FileSearch, UploadCloud, CheckCircle2, ArrowUpRight } from 'lucide-react';
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

  if (isLoading) return <LoadingSpinner message="Fetching ForensicShield system state & telemetry..." />;
  if (error) return <ErrorState code="DASHBOARD_LOAD_ERROR" message={error} onRetry={loadDashboardData} />;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Top Incident Command Banner */}
      <div className="bg-[#111827] p-5 sm:p-6 rounded-2xl border border-[#253044] shadow-card flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2.5">
            <h2 className="text-lg sm:text-xl font-bold text-[#F8FAFC]">Forensic Incident Command Center</h2>
            <span className="bg-[#22D3EE]/10 text-[#22D3EE] border border-[#22D3EE]/30 text-[10px] font-mono font-bold px-2 py-0.5 rounded-full">
              LIVE
            </span>
          </div>
          <p className="text-xs text-[#94A3B8] mt-1">
            Enterprise Digital Forensics & Data Integrity Control Center
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5 text-xs font-mono">
          <div className="bg-[#0B0F19] border border-[#253044] px-3 py-1.5 rounded-xl flex items-center space-x-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-[#34D399]" />
            <span className="text-[#94A3B8]">Safe Mode: <strong className="text-[#34D399]">ACTIVE</strong></span>
          </div>
          <div className="bg-[#0B0F19] border border-[#253044] px-3 py-1.5 rounded-xl flex items-center space-x-2">
            <Shield className="w-3.5 h-3.5 text-[#22D3EE]" />
            <span className="text-[#94A3B8]">Audit Chain: <strong className="text-[#22D3EE]">INTACT</strong></span>
          </div>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-[#111827] p-5 rounded-2xl border border-[#253044] space-y-3 shadow-subtle hover:border-[#22D3EE]/40 transition-colors">
          <div className="flex items-center justify-between text-[#94A3B8]">
            <span className="text-[11px] font-semibold uppercase tracking-wider font-mono">Active Cases</span>
            <Briefcase className="w-4 h-4 text-[#22D3EE]" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-bold text-[#F8FAFC] font-mono">{cases.length}</span>
            <span className="text-[11px] text-[#34D399] font-mono">Total Cases</span>
          </div>
        </div>

        <div className="bg-[#111827] p-5 rounded-2xl border border-[#253044] space-y-3 shadow-subtle hover:border-[#FBBF24]/40 transition-colors">
          <div className="flex items-center justify-between text-[#94A3B8]">
            <span className="text-[11px] font-semibold uppercase tracking-wider font-mono">Background Jobs</span>
            <Activity className="w-4 h-4 text-[#FBBF24]" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-bold text-[#F8FAFC] font-mono">{recentJobs.length}</span>
            <span className="text-[11px] text-[#FBBF24] font-mono">Queued / Running</span>
          </div>
        </div>

        <div className="bg-[#111827] p-5 rounded-2xl border border-[#253044] space-y-3 shadow-subtle hover:border-[#34D399]/40 transition-colors">
          <div className="flex items-center justify-between text-[#94A3B8]">
            <span className="text-[11px] font-semibold uppercase tracking-wider font-mono">Audit Ledger</span>
            <History className="w-4 h-4 text-[#34D399]" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-bold text-[#F8FAFC] font-mono">{recentAudit.length}</span>
            <span className="text-[11px] text-[#34D399] font-mono">Validated Blocks</span>
          </div>
        </div>

        <div className="bg-[#111827] p-5 rounded-2xl border border-[#253044] space-y-3 shadow-subtle hover:border-[#22D3EE]/40 transition-colors">
          <div className="flex items-center justify-between text-[#94A3B8]">
            <span className="text-[11px] font-semibold uppercase tracking-wider font-mono">System Safety</span>
            <CheckCircle2 className="w-4 h-4 text-[#34D399]" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-lg font-bold text-[#34D399] font-mono">PASS</span>
            <span className="text-[11px] text-[#94A3B8] font-mono">Simulated Only</span>
          </div>
        </div>
      </div>

      {/* Quick Launch Operations */}
      <div className="space-y-3">
        <h3 className="text-xs font-bold text-[#94A3B8] uppercase tracking-wider font-mono">
          Quick Launch Operations
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => onNavigate('sanitization')}
            className="p-5 bg-[#111827] hover:bg-[#162032] border border-[#253044] hover:border-[#FB7185]/50 rounded-2xl text-left space-y-2 group transition-all cursor-pointer shadow-subtle"
          >
            <div className="flex items-center justify-between text-[#FB7185]">
              <Flame className="w-5 h-5" />
              <ArrowUpRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity text-[#94A3B8]" />
            </div>
            <h4 className="text-sm font-semibold text-[#F8FAFC] group-hover:text-[#FB7185] transition-colors">
              Drive Sanitization Wizard
            </h4>
            <p className="text-xs text-[#94A3B8] leading-relaxed">
              Safety-gated storage media sanitization & block overwrite with dry-run audit.
            </p>
          </button>

          <button
            onClick={() => onNavigate('evidence')}
            className="p-5 bg-[#111827] hover:bg-[#162032] border border-[#253044] hover:border-[#22D3EE]/50 rounded-2xl text-left space-y-2 group transition-all cursor-pointer shadow-subtle"
          >
            <div className="flex items-center justify-between text-[#22D3EE]">
              <UploadCloud className="w-5 h-5" />
              <ArrowUpRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity text-[#94A3B8]" />
            </div>
            <h4 className="text-sm font-semibold text-[#F8FAFC] group-hover:text-[#22D3EE] transition-colors">
              Evidence Image Intake
            </h4>
            <p className="text-xs text-[#94A3B8] leading-relaxed">
              Read-only streaming SHA-256 ingestion & working copy image setup.
            </p>
          </button>

          <button
            onClick={() => onNavigate('recovery')}
            className="p-5 bg-[#111827] hover:bg-[#162032] border border-[#253044] hover:border-[#FBBF24]/50 rounded-2xl text-left space-y-2 group transition-all cursor-pointer shadow-subtle"
          >
            <div className="flex items-center justify-between text-[#FBBF24]">
              <FileSearch className="w-5 h-5" />
              <ArrowUpRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity text-[#94A3B8]" />
            </div>
            <h4 className="text-sm font-semibold text-[#F8FAFC] group-hover:text-[#FBBF24] transition-colors">
              Recovery & Carving Hub
            </h4>
            <p className="text-xs text-[#94A3B8] leading-relaxed">
              Filesystem extent extraction & signature-based file carving engine.
            </p>
          </button>
        </div>
      </div>

      {/* Recent Audit Ledger Snippet */}
      <div className="bg-[#111827] border border-[#253044] rounded-2xl p-5 space-y-4 shadow-card">
        <div className="flex items-center justify-between border-b border-[#253044] pb-3">
          <div className="flex items-center space-x-2">
            <History className="w-4 h-4 text-[#22D3EE]" />
            <h3 className="text-sm font-semibold text-[#F8FAFC]">Recent Audit Chain Events</h3>
          </div>
          <button
            onClick={() => onNavigate('audit')}
            className="text-xs text-[#22D3EE] hover:text-[#67E8F9] font-medium font-mono cursor-pointer flex items-center space-x-1"
          >
            <span>View Full Ledger</span>
            <span>→</span>
          </button>
        </div>

        <div className="space-y-2 text-xs">
          {recentAudit.map(ev => (
            <div
              key={ev.id}
              className="p-3 bg-[#0B0F19] hover:bg-[#162032] border border-[#253044] rounded-xl flex items-center justify-between gap-4 transition-colors"
            >
              <div className="space-y-0.5 min-w-0">
                <span className="font-mono text-[#22D3EE] font-semibold text-xs">{ev.action}</span>
                <p className="text-[#94A3B8] text-[11px] truncate max-w-xl">{ev.target_summary}</p>
              </div>
              <div className="text-right shrink-0">
                <StatusBadge status={ev.result} />
                <span className="block font-mono text-[10px] text-[#64748B] mt-1">
                  {ev.timestamp.substring(11, 19)} UTC
                </span>
              </div>
            </div>
          ))}
          {recentAudit.length === 0 && (
            <p className="text-[#64748B] text-center py-6 text-xs">No recent audit events recorded.</p>
          )}
        </div>
      </div>
    </div>
  );
};
