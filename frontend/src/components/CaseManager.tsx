import React, { useEffect, useState } from 'react';
import { FolderGit2, Plus, RefreshCw, Briefcase } from 'lucide-react';
import { api, ForensicCase } from '../services/api';

export const CaseManager: React.FC = () => {
  const [cases, setCases] = useState<ForensicCase[]>([]);
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);

  const [caseNumber, setCaseNumber] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');

  const fetchCases = async () => {
    setLoading(true);
    const { data } = await api.listCases();
    setLoading(false);
    if (data) {
      setCases(data);
    }
  };

  useEffect(() => {
    fetchCases();
  }, []);

  const handleCreateCase = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    const { data } = await api.createCase({
      case_number: caseNumber,
      title,
      description,
    });
    setLoading(false);
    if (data) {
      setShowModal(false);
      setCaseNumber('');
      setTitle('');
      setDescription('');
      fetchCases();
    }
  };

  return (
    <div className="glass-panel p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <FolderGit2 className="w-5 h-5 text-cyber-teal" />
          <h2 className="text-lg font-semibold text-white">Forensic Investigation Cases</h2>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={fetchCases}
            disabled={loading}
            className="p-2 rounded-lg bg-dark-700 hover:bg-dark-600 text-slate-300 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setShowModal(true)}
            className="px-3 py-1.5 rounded-lg bg-teal-500/20 hover:bg-teal-500/30 text-teal-300 border border-teal-500/40 text-xs font-semibold flex items-center gap-1.5 transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Case Context
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {cases.length === 0 ? (
          <div className="col-span-full p-8 text-center text-slate-500 border border-dashed border-dark-700 rounded-lg">
            No forensic cases initialized in SQLite database.
          </div>
        ) : (
          cases.map((c) => (
            <div key={c.id} className="p-4 rounded-lg bg-dark-900/80 border border-dark-700 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs px-2 py-0.5 rounded bg-dark-700 text-cyber-teal font-mono font-semibold">
                    {c.case_number}
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">
                    {new Date(c.created_at).toLocaleDateString()}
                  </span>
                </div>
                <h3 className="text-sm font-semibold text-white truncate">{c.title}</h3>
                <p className="text-xs text-slate-400 mt-1 line-clamp-2">{c.description || 'No description provided.'}</p>
              </div>

              <div className="mt-4 pt-3 border-t border-dark-800 flex items-center justify-between text-xs text-slate-400 font-mono">
                <span className="flex items-center gap-1">
                  <Briefcase className="w-3.5 h-3.5 text-slate-500" />
                  Investigator #{c.investigator_id}
                </span>
                <span className="text-teal-400">{c.status || 'ACTIVE'}</span>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Create Case Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="glass-panel p-6 max-w-md w-full">
            <h3 className="text-base font-semibold text-white mb-4">Initialize Forensic Case Context</h3>
            <form onSubmit={handleCreateCase} className="space-y-4">
              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Case Number</label>
                <input
                  type="text"
                  placeholder="CASE-2026-9001"
                  value={caseNumber}
                  onChange={(e) => setCaseNumber(e.target.value)}
                  className="w-full px-3 py-2 rounded bg-dark-900 border border-dark-600 text-sm text-white font-mono focus:border-cyber-teal"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Case Title</label>
                <input
                  type="text"
                  placeholder="Suspect Drive Analysis"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3 py-2 rounded bg-dark-900 border border-dark-600 text-sm text-white focus:border-cyber-teal"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Description</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-3 py-2 rounded bg-dark-900 border border-dark-600 text-sm text-white focus:border-cyber-teal"
                  rows={3}
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 rounded bg-dark-700 text-slate-300 text-xs font-semibold hover:bg-dark-600"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 rounded bg-cyber-teal text-dark-900 text-xs font-semibold hover:bg-teal-300"
                >
                  Create Case
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
