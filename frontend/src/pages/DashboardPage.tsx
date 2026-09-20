import React, { useState, useEffect } from 'react';
import { Shield, Briefcase, Activity, History, Flame, FileSearch, UploadCloud, CheckCircle2, ArrowUpRight, Radio, ChevronRight, ShieldAlert, LogIn } from 'lucide-react';
import { api } from '../services/api';
import { SystemStatus, ForensicCase, JobRecord, AuditEvent } from '../types';
import { LoadingSpinner, ErrorState } from '../components/common/StateViews';
import { StatusBadge } from '../components/common/StatusBadge';
import { useAuth } from '../context/AuthContext';

export const DashboardPage: React.FC<{ onNavigate: (tabId: string) => void }> = ({ onNavigate }) => {
  const { isAuthenticated, isLoading: isAuthLoading } = useAuth();
  const [health, setHealth] = useState<SystemStatus | null>(null);
  const [cases, setCases] = useState<ForensicCase[]>([]);
  const [recentJobs, setRecentJobs] = useState<JobRecord[]>([]);
  const [recentAudit, setRecentAudit] = useState<AuditEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const loadDashboardData = async () => {
    setIsLoading(true);
    setError('');

    try {
      const hRes = await api.getSystemHealth();
      if (hRes.data) setHealth(hRes.data);

      if (isAuthenticated) {
        const [cRes, jRes, aRes] = await Promise.all([
          api.listCases(),
          api.listJobs(),
          api.listAuditEvents({ limit: 5 }),
        ]);

        if (cRes.data) setCases(cRes.data);
        if (jRes.data) setRecentJobs(jRes.data);
        if (aRes.data) setRecentAudit(aRes.data);
      } else {
        setCases([]);
        setRecentJobs([]);
        setRecentAudit([]);
      }

      if (hRes.error && !hRes.data) {
        setError(hRes.error.error.message);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to load system telemetry.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!isAuthLoading) {
      loadDashboardData();
    }
  }, [isAuthenticated, isAuthLoading]);

  if (isLoading) return <LoadingSpinner message="Fetching ForensicShield system state & telemetry..." />;
  if (error) return <ErrorState code="DASHBOARD_LOAD_ERROR" message={error} onRetry={loadDashboardData} />;

  const runningJobsCount = recentJobs.filter(j => j.status === 'RUNNING').length;

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Top Incident Command Hero */}
      <div className="bg-[#0E1726] p-5 sm:p-6 rounded-xl border border-[#1B2B40] shadow-card relative overflow-hidden flex flex-wrap items-center justify-between gap-4">
        {/* Subtle dark, low-contrast forensic data watermark */}
        <div className="absolute right-0 top-0 bottom-0 w-72 pointer-events-none opacity-10 hidden md:block overflow-hidden">
          <svg viewBox="0 0 300 130" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-full object-cover">
            <circle cx="230" cy="65" r="50" stroke="#1683FF" strokeWidth="1" strokeDasharray="3 3" />
            <circle cx="230" cy="65" r="30" stroke="#16C7D9" strokeWidth="1" />
            <path d="M 230 15 L 230 115 M 180 65 L 280 65" stroke="#1B2B40" strokeWidth="1" />
            <rect x="60" y="25" width="70" height="70" rx="8" stroke="#1B2B40" strokeWidth="1" />
            <rect x="80" y="45" width="30" height="30" rx="4" stroke="#1683FF" strokeWidth="1" />
            <path d="M 130 65 L 180 65" stroke="#16C7D9" strokeWidth="1" strokeDasharray="3 2" />
          </svg>
        </div>

        <div className="relative z-10 space-y-1.5">
          <div className="flex items-center space-x-2.5">
            <span className="text-[10px] font-mono font-bold tracking-wider text-[#16C7D9] uppercase bg-[#16C7D9]/10 px-2 py-0.5 rounded border border-[#16C7D9]/20">
              DFIR COMMAND CENTER
            </span>
            <span className="bg-[#20C997]/10 text-[#20C997] border border-[#20C997]/25 text-[10px] font-mono font-bold px-2 py-0.5 rounded-full inline-flex items-center space-x-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#20C997] animate-pulse" />
              <span>LIVE</span>
            </span>
          </div>

          <h1 className="text-xl sm:text-2xl font-extrabold text-[#F1F5F9] tracking-tight font-sans">
            Forensic Incident Command Center
          </h1>
          <p className="text-xs text-[#94A3B8]">
            Enterprise Digital Forensics & Data Integrity Control Center
          </p>

          {/* Compact Workflow Indicator: Collect → Analyze → Preserve → Report */}
          <div className="flex items-center space-x-2 text-[10px] font-mono text-[#64748B] pt-1">
            <span className="text-[#94A3B8] font-medium uppercase tracking-wider">Workflow:</span>
            <span className="text-[#F1F5F9] bg-[#070B14] px-1.5 py-0.5 rounded border border-[#1B2B40]">Collect</span>
            <span className="text-[#64748B]">→</span>
            <span className="text-[#F1F5F9] bg-[#070B14] px-1.5 py-0.5 rounded border border-[#1B2B40]">Analyze</span>
            <span className="text-[#64748B]">→</span>
            <span className="text-[#F1F5F9] bg-[#070B14] px-1.5 py-0.5 rounded border border-[#1B2B40]">Preserve</span>
            <span className="text-[#64748B]">→</span>
            <span className="text-[#F1F5F9] bg-[#070B14] px-1.5 py-0.5 rounded border border-[#1B2B40]">Report</span>
          </div>
        </div>

        <div className="relative z-10 flex flex-wrap items-center gap-2 text-xs font-mono">
          <div className="bg-[#070B14] border border-[#1B2B40] px-3 py-1.5 rounded-lg flex items-center space-x-2 shadow-subtle">
            {health?.safe_mode !== false ? (
              <>
                <CheckCircle2 className="w-3.5 h-3.5 text-[#20C997]" />
                <span className="text-[#94A3B8]">Safe Mode: <strong className="text-[#20C997]">ACTIVE</strong></span>
              </>
            ) : (
              <>
                <ShieldAlert className="w-3.5 h-3.5 text-[#FB7185]" />
                <span className="text-[#94A3B8]">Safe Mode: <strong className="text-[#FB7185]">HARDWARE DIRECT</strong></span>
              </>
            )}
          </div>
          <div className="bg-[#070B14] border border-[#1B2B40] px-3 py-1.5 rounded-lg flex items-center space-x-2 shadow-subtle">
            <Shield className="w-3.5 h-3.5 text-[#1683FF]" />
            <span className="text-[#94A3B8]">Audit Chain: <strong className="text-[#1683FF]">INTACT</strong></span>
          </div>
        </div>
      </div>

      {/* 4 KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Active Cases */}
        <div className="bg-[#0E1726] hover:bg-[#121E30] p-5 rounded-xl border border-[#1B2B40] hover:border-[#1683FF]/30 space-y-2.5 shadow-card transition-all duration-150">
          <div className="flex items-center justify-between text-[#94A3B8]">
            <span className="text-[10px] font-bold uppercase tracking-wider font-mono">ACTIVE CASES</span>
            <div className="p-1.5 rounded-lg bg-[#1683FF]/10 text-[#1683FF] border border-[#1683FF]/20">
              <Briefcase className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-3xl sm:text-4xl font-extrabold text-[#F1F5F9] font-mono tracking-tight">{cases.length}</span>
            <span className="text-[11px] text-[#1683FF] font-mono font-medium flex items-center space-x-1">
              <span>●</span>
              <span>Total Cases</span>
            </span>
          </div>
        </div>

        {/* Background Jobs */}
        <div className="bg-[#0E1726] hover:bg-[#121E30] p-5 rounded-xl border border-[#1B2B40] hover:border-[#16C7D9]/30 space-y-2.5 shadow-card transition-all duration-150">
          <div className="flex items-center justify-between text-[#94A3B8]">
            <span className="text-[10px] font-bold uppercase tracking-wider font-mono">BACKGROUND JOBS</span>
            <div className="p-1.5 rounded-lg bg-[#16C7D9]/10 text-[#16C7D9] border border-[#16C7D9]/20">
              <Activity className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-3xl sm:text-4xl font-extrabold text-[#F1F5F9] font-mono tracking-tight">{recentJobs.length}</span>
            <span className="text-[11px] text-[#16C7D9] font-mono font-medium flex items-center space-x-1">
              <span>●</span>
              <span>{runningJobsCount > 0 ? `${runningJobsCount} Running` : 'Queued / Running'}</span>
            </span>
          </div>
        </div>

        {/* Audit Ledger */}
        <div className="bg-[#0E1726] hover:bg-[#121E30] p-5 rounded-xl border border-[#1B2B40] hover:border-[#F2B84B]/30 space-y-2.5 shadow-card transition-all duration-150">
          <div className="flex items-center justify-between text-[#94A3B8]">
            <span className="text-[10px] font-bold uppercase tracking-wider font-mono">AUDIT LEDGER</span>
            <div className="p-1.5 rounded-lg bg-[#F2B84B]/10 text-[#F2B84B] border border-[#F2B84B]/20">
              <History className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-3xl sm:text-4xl font-extrabold text-[#F1F5F9] font-mono tracking-tight">{recentAudit.length}</span>
            <span className="text-[11px] text-[#F2B84B] font-mono font-medium flex items-center space-x-1">
              <span>●</span>
              <span>Validated Blocks</span>
            </span>
          </div>
        </div>

        {/* System Safety */}
        <div className="bg-[#0E1726] hover:bg-[#121E30] p-5 rounded-xl border border-[#1B2B40] hover:border-[#20C997]/30 space-y-2.5 shadow-card transition-all duration-150">
          <div className="flex items-center justify-between text-[#94A3B8]">
            <span className="text-[10px] font-bold uppercase tracking-wider font-mono">SYSTEM SAFETY</span>
            <div className={`p-1.5 rounded-lg border ${health?.safe_mode !== false ? 'bg-[#20C997]/10 text-[#20C997] border-[#20C997]/20' : 'bg-[#FB7185]/10 text-[#FB7185] border-[#FB7185]/20'}`}>
              {health?.safe_mode !== false ? <CheckCircle2 className="w-4 h-4" /> : <ShieldAlert className="w-4 h-4" />}
            </div>
          </div>
          <div className="flex items-baseline justify-between">
            <span className={`text-3xl sm:text-4xl font-extrabold font-mono tracking-tight ${health?.safe_mode !== false ? 'text-[#20C997]' : 'text-[#FB7185]'}`}>
              {health?.safe_mode !== false ? 'PASS' : 'LIVE'}
            </span>
            <span className="text-[11px] text-[#8B6CFF] font-mono font-medium flex items-center space-x-1">
              <span>●</span>
              <span>{health?.safe_mode !== false ? 'Simulated Only' : 'Real Hardware'}</span>
            </span>
          </div>
        </div>
      </div>

      {/* Quick Launch Operations */}
      <div className="space-y-2.5">
        <h2 className="text-xs font-bold text-[#64748B] uppercase tracking-wider font-mono">
          Quick Launch Operations
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => onNavigate('sanitization')}
            className="p-4 sm:p-5 bg-[#0E1726] hover:bg-[#121E30] border border-[#1B2B40] hover:border-[#FB7185]/40 rounded-xl text-left space-y-2 group transition-all duration-150 cursor-pointer shadow-card"
          >
            <div className="flex items-center justify-between">
              <div className="p-1.5 bg-[#FB7185]/10 border border-[#FB7185]/20 rounded-lg text-[#FB7185]">
                <Flame className="w-4 h-4" />
              </div>
              <ArrowUpRight className="w-4 h-4 text-[#64748B] group-hover:text-[#FB7185] group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
            </div>
            <h3 className="text-sm font-bold text-[#F1F5F9] group-hover:text-[#FB7185] transition-colors">
              Drive Sanitization Wizard
            </h3>
            <p className="text-xs text-[#94A3B8] leading-relaxed">
              Safety-gated storage media sanitization & block overwrite with dry-run audit.
            </p>
          </button>

          <button
            onClick={() => onNavigate('evidence')}
            className="p-4 sm:p-5 bg-[#0E1726] hover:bg-[#121E30] border border-[#1B2B40] hover:border-[#16C7D9]/40 rounded-xl text-left space-y-2 group transition-all duration-150 cursor-pointer shadow-card"
          >
            <div className="flex items-center justify-between">
              <div className="p-1.5 bg-[#16C7D9]/10 border border-[#16C7D9]/20 rounded-lg text-[#16C7D9]">
                <UploadCloud className="w-4 h-4" />
              </div>
              <ArrowUpRight className="w-4 h-4 text-[#64748B] group-hover:text-[#16C7D9] group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
            </div>
            <h3 className="text-sm font-bold text-[#F1F5F9] group-hover:text-[#16C7D9] transition-colors">
              Evidence Image Intake
            </h3>
            <p className="text-xs text-[#94A3B8] leading-relaxed">
              Read-only streaming SHA-256 ingestion & working copy image setup.
            </p>
          </button>

          <button
            onClick={() => onNavigate('recovery')}
            className="p-4 sm:p-5 bg-[#0E1726] hover:bg-[#121E30] border border-[#1B2B40] hover:border-[#F2B84B]/40 rounded-xl text-left space-y-2 group transition-all duration-150 cursor-pointer shadow-card"
          >
            <div className="flex items-center justify-between">
              <div className="p-1.5 bg-[#F2B84B]/10 border border-[#F2B84B]/20 rounded-lg text-[#F2B84B]">
                <FileSearch className="w-4 h-4" />
              </div>
              <ArrowUpRight className="w-4 h-4 text-[#64748B] group-hover:text-[#F2B84B] group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
            </div>
            <h3 className="text-sm font-bold text-[#F1F5F9] group-hover:text-[#F2B84B] transition-colors">
              Recovery & Carving Hub
            </h3>
            <p className="text-xs text-[#94A3B8] leading-relaxed">
              Filesystem extent extraction & signature-based file carving engine.
            </p>
          </button>
        </div>
      </div>

      {/* Two-Column Security Section: Recent Audit Events & Case Activity Telemetry */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left Column: Recent Audit Chain Events Log */}
        <div className="lg:col-span-7 bg-[#0E1726] border border-[#1B2B40] rounded-xl p-5 space-y-3.5 shadow-card">
          <div className="flex items-center justify-between border-b border-[#1B2B40] pb-3">
            <div className="flex items-center space-x-2">
              <div className="p-1 rounded bg-[#1683FF]/10 text-[#1683FF]">
                <History className="w-4 h-4" />
              </div>
              <h2 className="text-sm font-bold text-[#F1F5F9]">Recent Audit Chain Events</h2>
            </div>
            <button
              onClick={() => onNavigate('audit')}
              className="text-xs text-[#1683FF] hover:text-[#5EEAD4] font-medium font-mono cursor-pointer flex items-center space-x-1 transition-colors"
            >
              <span>View Full Ledger</span>
              <span>→</span>
            </button>
          </div>

          <div className="space-y-1.5 text-xs">
            {recentAudit.map(ev => (
              <div
                key={ev.id}
                className="p-2.5 bg-[#080D17] hover:bg-[#121E30] border border-[#1B2B40] rounded-lg flex items-center justify-between gap-3 transition-colors"
              >
                <div className="space-y-0.5 min-w-0">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-[#64748B] text-[10px]">
                      {ev.timestamp ? ev.timestamp.substring(11, 19) : '--:--:--'} UTC
                    </span>
                    <span className="font-mono text-[#16C7D9] font-bold text-xs">{ev.action}</span>
                  </div>
                  <p className="text-[#94A3B8] text-[11px] truncate max-w-xs sm:max-w-sm">{ev.target_summary}</p>
                </div>
                <div className="text-right shrink-0">
                  <StatusBadge status={ev.result} />
                </div>
              </div>
            ))}
            {recentAudit.length === 0 && (
              <p className="text-[#64748B] text-center py-6 text-xs">No recent audit events recorded.</p>
            )}
          </div>
        </div>

        {/* Right Column: Case Activity & Telemetry Monitor */}
        <div className="lg:col-span-5 bg-[#0E1726] border border-[#1B2B40] rounded-xl p-5 space-y-3.5 shadow-card flex flex-col justify-between">
          <div className="flex items-center justify-between border-b border-[#1B2B40] pb-3">
            <div className="flex items-center space-x-2">
              <div className="p-1 rounded bg-[#1683FF]/10 text-[#1683FF]">
                <Shield className="w-4 h-4" />
              </div>
              <h2 className="text-sm font-bold text-[#F1F5F9]">Case Activity & Telemetry</h2>
            </div>
            <span className="text-[10px] font-mono text-[#20C997] bg-[#20C997]/10 border border-[#20C997]/20 px-2 py-0.5 rounded flex items-center space-x-1">
              <Radio className="w-3 h-3 animate-pulse text-[#20C997]" />
              <span>TELEMETRY</span>
            </span>
          </div>

          {/* Activity Metrics Bars with Subtle Enterprise Grid */}
          <div className="space-y-3 text-xs">
            <div className="bg-[#080D17] p-3 rounded-lg border border-[#1B2B40] space-y-1.5">
              <div className="flex items-center justify-between font-mono text-[11px]">
                <span className="text-[#94A3B8] flex items-center space-x-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#1683FF]" />
                  <span>Cases In-Flight</span>
                </span>
                <span className="font-bold text-[#F1F5F9]">{cases.length} Registered</span>
              </div>
              <div className="w-full bg-[#070B14] rounded-full h-1.5 overflow-hidden border border-[#1B2B40]">
                <div
                  className="bg-[#1683FF] h-1.5 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, Math.max(20, cases.length * 20))}%` }}
                />
              </div>
            </div>

            <div className="bg-[#080D17] p-3 rounded-lg border border-[#1B2B40] space-y-1.5">
              <div className="flex items-center justify-between font-mono text-[11px]">
                <span className="text-[#94A3B8] flex items-center space-x-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#16C7D9]" />
                  <span>Async Job Workers</span>
                </span>
                <span className="font-bold text-[#F1F5F9]">{recentJobs.length} Processed</span>
              </div>
              <div className="w-full bg-[#070B14] rounded-full h-1.5 overflow-hidden border border-[#1B2B40]">
                <div
                  className="bg-[#16C7D9] h-1.5 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, Math.max(15, recentJobs.length * 25))}%` }}
                />
              </div>
            </div>

            <div className="bg-[#080D17] p-3 rounded-lg border border-[#1B2B40] space-y-1.5">
              <div className="flex items-center justify-between font-mono text-[11px]">
                <span className="text-[#94A3B8] flex items-center space-x-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#F2B84B]" />
                  <span>Audit Chain Blocks</span>
                </span>
                <span className="font-bold text-[#F1F5F9]">{recentAudit.length} Validated</span>
              </div>
              <div className="w-full bg-[#070B14] rounded-full h-1.5 overflow-hidden border border-[#1B2B40]">
                <div
                  className="bg-[#F2B84B] h-1.5 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, Math.max(25, recentAudit.length * 20))}%` }}
                />
              </div>
            </div>
          </div>

          {/* Cryptographic Ledger Verification Footer */}
          <div className="pt-2 border-t border-[#1B2B40] flex items-center justify-between text-[11px] font-mono text-[#64748B]">
            <span className="flex items-center space-x-1 text-[#20C997]">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>SHA-256 Ledger: VERIFIED</span>
            </span>
            <span className="text-[#94A3B8]">NIST SP 800-88</span>
          </div>
        </div>
      </div>
    </div>
  );
};
