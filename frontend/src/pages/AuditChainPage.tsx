import React, { useState, useEffect } from 'react';
import { History, ShieldCheck, AlertTriangle, Download, RefreshCw, Lock } from 'lucide-react';
import { api } from '../services/api';
import { AuditEvent, AuditChainVerification } from '../types';
import { useCase } from '../context/CaseContext';
import { useNotification } from '../context/NotificationContext';
import { LoadingSpinner, ErrorState } from '../components/common/StateViews';
import { StatusBadge } from '../components/common/StatusBadge';

export const AuditChainPage: React.FC = () => {
  const { activeCase } = useCase();
  const { addToast } = useNotification();

  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [chainVerification, setChainVerification] = useState<AuditChainVerification | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [isVerifying, setIsVerifying] = useState(false);
  const [error, setError] = useState('');

  const loadAuditData = async () => {
    setIsLoading(true);
    setError('');
    const [aRes, vRes] = await Promise.all([
      api.listAuditEvents({ case_id: activeCase?.id, limit: 100 }),
      api.verifyAuditChain(),
    ]);

    if (aRes.data) setAuditEvents(aRes.data);
    if (vRes.data) setChainVerification(vRes.data);

    if (aRes.error && !aRes.data) {
      setError(aRes.error.error.message);
    }
    setIsLoading(false);
  };

  useEffect(() => {
    loadAuditData();
  }, [activeCase?.id]);

  const handleVerifyChain = async () => {
    setIsVerifying(true);
    const res = await api.verifyAuditChain();
    setIsVerifying(false);

    if (res.data) {
      setChainVerification(res.data);
      if (res.data.is_valid) {
        addToast('success', 'Audit Chain Intact', `Cryptographic SHA-256 hash chain verified across ${res.data.total_events} blocks.`);
      } else {
        addToast('error', 'Tampering Detected!', `Broken link detected at block ${res.data.first_broken_event_id}`);
      }
    }
  };

  if (isLoading && auditEvents.length === 0) return <LoadingSpinner message="Verifying tamper-evident SHA-256 audit ledger..." />;
  if (error) return <ErrorState code="AUDIT_LOAD_ERROR" message={error} onRetry={loadAuditData} />;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800 shadow-xl flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-extrabold text-slate-100 flex items-center">
            <History className="w-6 h-6 text-emerald-400 mr-2.5" />
            Tamper-Evident SHA-256 Audit Chain Ledger
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Sequential cryptographic block hashing (Genesis to tip) & tamper attack detection
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleVerifyChain}
            disabled={isVerifying}
            className="flex items-center space-x-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs px-4 py-2.5 rounded-xl shadow-lg shadow-emerald-950 transition-all cursor-pointer"
          >
            <ShieldCheck className="w-4 h-4" />
            <span>{isVerifying ? 'Verifying Chain...' : 'Verify Hash Chain'}</span>
          </button>

          <a
            href="/api/v1/audit/export/json"
            target="_blank"
            rel="noreferrer"
            className="flex items-center space-x-1.5 bg-slate-800 hover:bg-slate-700 text-cyan-300 font-semibold text-xs px-3.5 py-2.5 rounded-xl border border-slate-700"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export JSON</span>
          </a>
        </div>
      </div>

      {/* Verification Status Banner */}
      {chainVerification && (
        <div
          className={`p-4 rounded-2xl border flex items-center justify-between text-xs font-mono shadow-lg ${
            chainVerification.is_valid
              ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-200'
              : 'bg-red-950/80 border-red-500 text-red-200'
          }`}
        >
          <div className="flex items-center space-x-3">
            {chainVerification.is_valid ? (
              <ShieldCheck className="w-6 h-6 text-emerald-400 shrink-0" />
            ) : (
              <AlertTriangle className="w-6 h-6 text-red-400 shrink-0" />
            )}
            <div>
              <h4 className="font-extrabold text-sm uppercase">
                CHAIN STATUS: {chainVerification.chain_status}
              </h4>
              <p className="text-[11px] opacity-90 mt-0.5">
                Verified {chainVerification.total_events} sequential events. Link status: {chainVerification.is_valid ? 'INTACT' : 'TAMPERED'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Audit Event Ledger Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="p-4 border-b border-slate-800 text-xs text-slate-400 font-semibold uppercase tracking-wider">
          Audit Event Blocks ({auditEvents.length})
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="p-3">Event ID</th>
                <th className="p-3">Timestamp (UTC)</th>
                <th className="p-3">Actor / Role</th>
                <th className="p-3">Action</th>
                <th className="p-3">Previous SHA-256 Link</th>
                <th className="p-3">Current SHA-256 Digest</th>
                <th className="p-3">Result</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {auditEvents.map(ev => (
                <tr key={ev.id} className="hover:bg-slate-800/40">
                  <td className="p-3 text-cyan-300 font-bold">{ev.event_id}</td>
                  <td className="p-3 text-slate-300">{ev.timestamp?.substring(0, 19)}</td>
                  <td className="p-3 text-slate-200">{ev.actor} ({ev.role})</td>
                  <td className="p-3 font-bold text-slate-100">{ev.action}</td>
                  <td className="p-3 text-slate-500 text-[10px]">{ev.previous_hash?.substring(0, 16)}...</td>
                  <td className="p-3 text-amber-300 text-[10px]">{ev.current_hash?.substring(0, 16)}...</td>
                  <td className="p-3"><StatusBadge status={ev.result} /></td>
                </tr>
              ))}
              {auditEvents.length === 0 && (
                <tr>
                  <td colSpan={7} className="p-6 text-center text-slate-500 font-sans">
                    No audit log events recorded yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
