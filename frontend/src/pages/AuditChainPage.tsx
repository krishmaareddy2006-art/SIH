import React, { useState, useEffect } from 'react';
import { History, ShieldCheck, AlertTriangle, Download } from 'lucide-react';
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
      <div className="bg-[#111827] p-5 sm:p-6 rounded-2xl border border-[#253044] shadow-card flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-lg sm:text-xl font-bold text-[#F8FAFC] flex items-center">
            <History className="w-5 h-5 text-[#34D399] mr-2.5" />
            Tamper-Evident SHA-256 Audit Chain Ledger
          </h2>
          <p className="text-xs text-[#94A3B8] mt-1">
            Sequential cryptographic block hashing (Genesis to tip) & tamper attack detection
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleVerifyChain}
            disabled={isVerifying}
            className="flex items-center space-x-2 bg-[#34D399] hover:bg-[#6EE7B7] text-[#080B14] font-bold text-xs px-4 py-2 rounded-xl shadow-subtle transition-all cursor-pointer disabled:opacity-50"
          >
            <ShieldCheck className="w-4 h-4" />
            <span>{isVerifying ? 'Verifying Chain...' : 'Verify Hash Chain'}</span>
          </button>

          <a
            href="/api/v1/audit/export/json"
            target="_blank"
            rel="noreferrer"
            className="flex items-center space-x-1.5 bg-[#0B0F19] hover:bg-[#162032] text-[#22D3EE] font-semibold text-xs px-3.5 py-2 rounded-xl border border-[#253044] transition-all shadow-subtle"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export JSON</span>
          </a>
        </div>
      </div>

      {/* Verification Status Banner */}
      {chainVerification && (
        <div
          className={`p-4 rounded-2xl border flex items-center justify-between text-xs font-mono shadow-card animate-fade-in ${
            chainVerification.is_valid
              ? 'bg-[#0E1A16] border-[#34D399]/40 text-[#34D399]'
              : 'bg-[#1A0E13] border-[#FB7185]/50 text-[#FB7185]'
          }`}
        >
          <div className="flex items-center space-x-3">
            {chainVerification.is_valid ? (
              <div className="p-2 bg-[#34D399]/10 rounded-xl">
                <ShieldCheck className="w-5 h-5 text-[#34D399] shrink-0" />
              </div>
            ) : (
              <div className="p-2 bg-[#FB7185]/10 rounded-xl">
                <AlertTriangle className="w-5 h-5 text-[#FB7185] shrink-0" />
              </div>
            )}
            <div>
              <h4 className="font-bold text-sm uppercase tracking-wider text-[#F8FAFC]">
                CHAIN STATUS: {chainVerification.chain_status}
              </h4>
              <p className="text-[11px] text-[#94A3B8] mt-0.5 font-sans">
                Verified {chainVerification.total_events} sequential events. Link status:{' '}
                <strong className={chainVerification.is_valid ? 'text-[#34D399]' : 'text-[#FB7185]'}>
                  {chainVerification.is_valid ? 'INTACT & VALID' : 'COMPROMISED'}
                </strong>
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Audit Event Ledger Table */}
      <div className="bg-[#111827] border border-[#253044] rounded-2xl overflow-hidden shadow-card">
        <div className="p-4 border-b border-[#253044] text-xs text-[#94A3B8] font-mono">
          Audit Event Blocks ({auditEvents.length})
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-[#0B0F19] text-[#64748B] border-b border-[#253044]">
              <tr>
                <th className="p-3">Event ID</th>
                <th className="p-3">Timestamp (UTC)</th>
                <th className="p-3">Actor / Role</th>
                <th className="p-3">Action</th>
                <th className="p-3">Previous Link</th>
                <th className="p-3">Current SHA-256 Digest</th>
                <th className="p-3">Result</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#253044]">
              {auditEvents.map(ev => (
                <tr key={ev.id} className="hover:bg-[#162032]/40 transition-colors">
                  <td className="p-3 text-[#22D3EE] font-bold">{ev.event_id}</td>
                  <td className="p-3 text-[#94A3B8]">{ev.timestamp?.substring(0, 19)}</td>
                  <td className="p-3 text-[#F8FAFC]">{ev.actor} ({ev.role})</td>
                  <td className="p-3 font-semibold text-[#F8FAFC]">{ev.action}</td>
                  <td className="p-3 text-[#64748B] text-[10px]">{ev.previous_hash?.substring(0, 16)}...</td>
                  <td className="p-3 text-[#FBBF24] text-[10px]">{ev.current_hash?.substring(0, 16)}...</td>
                  <td className="p-3"><StatusBadge status={ev.result} /></td>
                </tr>
              ))}
              {auditEvents.length === 0 && (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-[#64748B] font-sans">
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
