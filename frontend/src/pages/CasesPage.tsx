import React, { useState } from 'react';
import { Briefcase, Plus, CheckCircle2, X } from 'lucide-react';
import { useCase } from '../context/CaseContext';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { useNotification } from '../context/NotificationContext';
import { LoadingSpinner } from '../components/common/StateViews';

export const CasesPage: React.FC = () => {
  const { cases, activeCase, setActiveCaseId, refreshCases, isLoading } = useCase();
  const { user, hasRole } = useAuth();
  const { addToast } = useNotification();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [caseNumber, setCaseNumber] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const canCreateCase = hasRole(['Administrator', 'Investigator']);

  const handleCreateCase = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    const res = await api.createCase({ case_number: caseNumber, title, description });
    setIsSubmitting(false);

    if (res.data) {
      addToast('success', 'Case Created', `Case #${res.data.case_number} created successfully.`);
      setIsModalOpen(false);
      setCaseNumber('');
      setTitle('');
      setDescription('');
      refreshCases();
    } else if (res.error) {
      addToast('error', 'Case Creation Failed', res.error.error.message);
    }
  };

  if (isLoading) return <LoadingSpinner message="Loading forensic case workspace..." />;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-[#111827] p-5 sm:p-6 rounded-2xl border border-[#253044] shadow-card">
        <div>
          <h2 className="text-lg sm:text-xl font-bold text-[#F8FAFC] flex items-center">
            <Briefcase className="w-5 h-5 text-[#22D3EE] mr-2.5" />
            Forensic Case Management Workspace
          </h2>
          <p className="text-xs text-[#94A3B8] mt-1">
            Read-only evidence binding & investigator authorization hub
          </p>
        </div>

        {canCreateCase && (
          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center space-x-2 bg-[#22D3EE] hover:bg-[#67E8F9] text-[#080B14] font-semibold text-xs px-4 py-2.5 rounded-xl shadow-subtle transition-all cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Create New Case</span>
          </button>
        )}
      </div>

      {/* Case Grid Table */}
      <div className="bg-[#111827] border border-[#253044] rounded-2xl overflow-hidden shadow-card">
        <div className="p-4 border-b border-[#253044] flex items-center justify-between text-xs text-[#94A3B8] font-mono">
          <span>Active Cases Inventory ({cases.length})</span>
          <span className="text-[#64748B]">Role Scope: {user?.role?.name || 'Operator'}</span>
        </div>

        <div className="divide-y divide-[#253044]">
          {cases.map(c => {
            const isActive = activeCase?.id === c.id;
            return (
              <div
                key={c.id}
                className={`p-5 flex flex-wrap items-center justify-between gap-4 transition-colors ${
                  isActive ? 'bg-[#22D3EE]/5 border-l-4 border-[#22D3EE]' : 'hover:bg-[#162032]/40'
                }`}
              >
                <div className="space-y-1 max-w-xl">
                  <div className="flex items-center space-x-3">
                    <span className="font-mono text-[#22D3EE] font-bold text-sm">#{c.case_number}</span>
                    <h4 className="font-semibold text-[#F8FAFC] text-sm">{c.title}</h4>
                    {isActive && (
                      <span className="bg-[#34D399]/10 text-[#34D399] border border-[#34D399]/30 text-[10px] font-mono px-2 py-0.5 rounded-full font-bold">
                        ACTIVE CASE
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-[#94A3B8] leading-relaxed">{c.description || 'No description provided.'}</p>
                </div>

                <div className="flex items-center space-x-4">
                  <div className="text-right text-xs font-mono">
                    <span className="text-[#64748B] block text-[10px]">Created:</span>
                    <span className="text-[#F8FAFC]">{c.created_at?.substring(0, 10)}</span>
                  </div>

                  {!isActive ? (
                    <button
                      onClick={() => setActiveCaseId(c.id)}
                      className="px-3 py-1.5 bg-[#0B0F19] hover:bg-[#162032] text-[#22D3EE] font-medium text-xs rounded-xl transition-all border border-[#253044] cursor-pointer"
                    >
                      Set Active
                    </button>
                  ) : (
                    <span className="px-3 py-1.5 bg-[#34D399]/10 text-[#34D399] border border-[#34D399]/30 font-medium text-xs rounded-xl flex items-center">
                      <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-[#34D399]" /> Active Context
                    </span>
                  )}
                </div>
              </div>
            );
          })}

          {cases.length === 0 && (
            <div className="p-8 text-center text-[#64748B] text-xs">
              No forensic cases registered. Click &quot;Create New Case&quot; above to initiate a case context.
            </div>
          )}
        </div>
      </div>

      {/* New Case Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#080B14]/85 backdrop-blur-md animate-fade-in">
          <div className="bg-[#111827] border border-[#253044] rounded-2xl max-w-md w-full p-6 space-y-4 shadow-elevated">
            <div className="flex items-center justify-between border-b border-[#253044] pb-3">
              <h3 className="text-sm font-bold text-[#F8FAFC]">Initiate New Forensic Case</h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-[#64748B] hover:text-[#F8FAFC] p-1 rounded-lg"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateCase} className="space-y-4 text-xs">
              <div>
                <label className="block text-[#94A3B8] font-medium mb-1">Case Number Identifier</label>
                <input
                  type="text"
                  value={caseNumber}
                  onChange={e => setCaseNumber(e.target.value)}
                  placeholder="e.g. CAS-2026-009"
                  required
                  className="w-full bg-[#0B0F19] border border-[#253044] focus:border-[#22D3EE] rounded-xl px-3 py-2 text-[#F8FAFC] font-mono outline-none transition-all"
                />
              </div>

              <div>
                <label className="block text-[#94A3B8] font-medium mb-1">Case Title</label>
                <input
                  type="text"
                  value={title}
                  onChange={e => setTitle(e.target.value)}
                  placeholder="e.g. Incident Response Storage Analysis"
                  required
                  className="w-full bg-[#0B0F19] border border-[#253044] focus:border-[#22D3EE] rounded-xl px-3 py-2 text-[#F8FAFC] outline-none transition-all"
                />
              </div>

              <div>
                <label className="block text-[#94A3B8] font-medium mb-1">Description / Notes</label>
                <textarea
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                  placeholder="Scope description, incident context..."
                  rows={3}
                  className="w-full bg-[#0B0F19] border border-[#253044] focus:border-[#22D3EE] rounded-xl p-3 text-[#F8FAFC] outline-none transition-all"
                />
              </div>

              <div className="flex items-center justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 bg-[#0B0F19] hover:bg-[#162032] border border-[#253044] text-[#94A3B8] hover:text-[#F8FAFC] rounded-xl transition-all cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 bg-[#22D3EE] hover:bg-[#67E8F9] text-[#080B14] font-bold rounded-xl transition-all shadow-subtle cursor-pointer disabled:opacity-50"
                >
                  {isSubmitting ? 'Creating...' : 'Initiate Case'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
