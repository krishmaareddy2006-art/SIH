import React, { useState } from 'react';
import { Briefcase, Plus, FolderCheck, Clock, User, CheckCircle2, ShieldAlert } from 'lucide-react';
import { useCase } from '../context/CaseContext';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { useNotification } from '../context/NotificationContext';
import { LoadingSpinner, ErrorState } from '../components/common/StateViews';

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
      <div className="flex flex-wrap items-center justify-between gap-4 bg-slate-900 p-6 rounded-2xl border border-slate-800 shadow-xl">
        <div>
          <h2 className="text-xl font-extrabold text-slate-100 flex items-center">
            <Briefcase className="w-6 h-6 text-cyan-400 mr-2.5" />
            Forensic Case Management Workspace
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Read-only evidence binding & investigator authorization hub
          </p>
        </div>

        {canCreateCase && (
          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center space-x-2 bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs px-4 py-2.5 rounded-xl shadow-lg shadow-cyan-950 transition-all cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Create New Case</span>
          </button>
        )}
      </div>

      {/* Case Grid Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between text-xs text-slate-400 font-semibold uppercase tracking-wider">
          <span>Active Cases Inventory ({cases.length})</span>
          <span>Role Scope: {user?.role?.name || 'Operator'}</span>
        </div>

        <div className="divide-y divide-slate-800/80">
          {cases.map(c => {
            const isActive = activeCase?.id === c.id;
            return (
              <div
                key={c.id}
                className={`p-5 flex flex-wrap items-center justify-between gap-4 transition-colors ${
                  isActive ? 'bg-cyan-950/20 border-l-4 border-cyan-500' : 'hover:bg-slate-800/50'
                }`}
              >
                <div className="space-y-1 max-w-xl">
                  <div className="flex items-center space-x-3">
                    <span className="font-mono text-cyan-400 font-extrabold text-sm">#{c.case_number}</span>
                    <h4 className="font-bold text-slate-100 text-sm">{c.title}</h4>
                    {isActive && (
                      <span className="bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[10px] font-mono px-2 py-0.5 rounded-full font-bold">
                        ACTIVE CASE
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">{c.description || 'No description provided.'}</p>
                </div>

                <div className="flex items-center space-x-4">
                  <div className="text-right text-xs font-mono">
                    <span className="text-slate-400 block">Created:</span>
                    <span className="text-slate-200">{c.created_at?.substring(0, 10)}</span>
                  </div>

                  {!isActive ? (
                    <button
                      onClick={() => setActiveCaseId(c.id)}
                      className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-cyan-300 font-semibold text-xs rounded-xl transition-all border border-slate-700"
                    >
                      Set Active
                    </button>
                  ) : (
                    <span className="px-3 py-1.5 bg-emerald-950/80 text-emerald-300 border border-emerald-500/40 font-semibold text-xs rounded-xl flex items-center">
                      <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Active Target
                    </span>
                  )}
                </div>
              </div>
            );
          })}

          {cases.length === 0 && (
            <div className="p-8 text-center text-slate-500 text-xs">
              No forensic cases registered. Click "Create New Case" above to initiate a case context.
            </div>
          )}
        </div>
      </div>

      {/* New Case Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-slate-100">Initiate New Forensic Case</h3>
            <form onSubmit={handleCreateCase} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-300 font-semibold mb-1">Case Number Identifier</label>
                <input
                  type="text"
                  value={caseNumber}
                  onChange={e => setCaseNumber(e.target.value)}
                  placeholder="e.g. CAS-2026-009"
                  required
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-slate-100 font-mono"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Case Title</label>
                <input
                  type="text"
                  value={title}
                  onChange={e => setTitle(e.target.value)}
                  placeholder="e.g. Incident Response Storage Analysis"
                  required
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-slate-100"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Description / Notes</label>
                <textarea
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                  placeholder="Optional scope description..."
                  rows={3}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-slate-100"
                />
              </div>

              <div className="flex items-center justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 bg-slate-800 text-slate-300 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 bg-cyan-600 hover:bg-cyan-500 text-white font-bold rounded-xl"
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
