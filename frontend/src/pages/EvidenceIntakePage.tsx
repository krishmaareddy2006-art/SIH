import React, { useState, useEffect } from 'react';
import { UploadCloud, FileText, CheckCircle2, ShieldCheck, Download, RefreshCw, AlertTriangle } from 'lucide-react';
import { api } from '../services/api';
import { EvidenceItem } from '../types';
import { useCase } from '../context/CaseContext';
import { useNotification } from '../context/NotificationContext';
import { LoadingSpinner, ErrorState } from '../components/common/StateViews';
import { StatusBadge } from '../components/common/StatusBadge';

export const EvidenceIntakePage: React.FC = () => {
  const { activeCase } = useCase();
  const { addToast } = useNotification();

  const [evidenceList, setEvidenceList] = useState<EvidenceItem[]>([]);
  const [sourceFilePath, setSourceFilePath] = useState('c:\\forensics\\evidence_image_001.raw');
  const [itemNumber, setItemNumber] = useState('EVID-2026-001');
  const [title, setTitle] = useState('Primary Suspect Drive Image');
  const [sourceDesc, setSourceDesc] = useState('1TB SATA HDD physical image acquired in lab');
  const [createWorkingCopy, setCreateWorkingCopy] = useState(true);

  const [isLoading, setIsLoading] = useState(true);
  const [isImporting, setIsImporting] = useState(false);
  const [error, setError] = useState('');

  const loadEvidence = async () => {
    if (!activeCase) {
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    setError('');
    const res = await api.listEvidence(activeCase.id);
    if (res.data) {
      setEvidenceList(res.data);
    } else if (res.error) {
      setError(res.error.error.message);
    }
    setIsLoading(false);
  };

  useEffect(() => {
    loadEvidence();
  }, [activeCase?.id]);

  const handleImport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCase) {
      addToast('warning', 'No Active Case', 'Please select or create an active case before importing evidence.');
      return;
    }

    setIsImporting(true);
    const res = await api.importEvidence(activeCase.id, {
      source_file_path: sourceFilePath,
      item_number: itemNumber,
      title,
      source_description: sourceDesc,
      create_working_copy: createWorkingCopy,
    });
    setIsImporting(false);

    if (res.data) {
      addToast('success', 'Evidence Intake Verified', `Evidence item '${res.data.evidence_id}' registered cleanly.`);
      loadEvidence();
    } else if (res.error) {
      addToast('error', 'Evidence Import Blocked', res.error.error.message);
    }
  };

  if (!activeCase) return <ErrorState code="NO_ACTIVE_CASE" message="Please select an active forensic case in the header to manage evidence intake." />;
  if (isLoading && evidenceList.length === 0) return <LoadingSpinner message="Fetching case evidence inventory & SHA-256 digests..." />;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800 shadow-xl flex items-center justify-between">
        <div>
          <h2 className="text-xl font-extrabold text-slate-100 flex items-center">
            <UploadCloud className="w-6 h-6 text-cyan-400 mr-2.5" />
            Read-Only Forensic Evidence Intake & Provenance
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Streaming SHA-256 ingestion, immutable read-only handles, and manifest exports for Case #{activeCase.case_number}
          </p>
        </div>
      </div>

      {/* Import Form */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-xl">
        <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">Register Source Evidence Image</h3>

        <form onSubmit={handleImport} className="space-y-4 text-xs">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-300 font-semibold mb-1">Source File / Image Path</label>
              <input
                type="text"
                value={sourceFilePath}
                onChange={e => setSourceFilePath(e.target.value)}
                placeholder="/path/to/evidence.raw"
                required
                className="w-full bg-slate-950 border border-slate-700 font-mono text-cyan-300 rounded-xl px-3.5 py-2"
              />
            </div>
            <div>
              <label className="block text-slate-300 font-semibold mb-1">Item Reference Number</label>
              <input
                type="text"
                value={itemNumber}
                onChange={e => setItemNumber(e.target.value)}
                placeholder="EVID-001"
                required
                className="w-full bg-slate-950 border border-slate-700 font-mono text-slate-100 rounded-xl px-3.5 py-2"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-300 font-semibold mb-1">Evidence Title</label>
              <input
                type="text"
                value={title}
                onChange={e => setTitle(e.target.value)}
                placeholder="Title description..."
                required
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2 text-slate-100"
              />
            </div>
            <div className="flex items-center space-x-2 pt-6">
              <input
                type="checkbox"
                id="workingCopy"
                checked={createWorkingCopy}
                onChange={e => setCreateWorkingCopy(e.target.checked)}
                className="rounded border-slate-700 text-cyan-600 focus:ring-cyan-500 bg-slate-950"
              />
              <label htmlFor="workingCopy" className="text-slate-300 font-semibold cursor-pointer">
                Create Read-Only Working Copy (Preserves Original Handle)
              </label>
            </div>
          </div>

          <div className="flex items-center justify-end border-t border-slate-800 pt-3">
            <button
              type="submit"
              disabled={isImporting}
              className="flex items-center space-x-2 bg-cyan-600 hover:bg-cyan-500 text-white font-bold px-5 py-2 rounded-xl shadow-lg shadow-cyan-950 transition-all cursor-pointer"
            >
              <ShieldCheck className="w-4 h-4" />
              <span>{isImporting ? 'Ingesting Image...' : 'Ingest & Compute Streaming SHA-256'}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Inventory Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between text-xs text-slate-400 font-semibold uppercase tracking-wider">
          <span>Ingested Evidence Inventory ({evidenceList.length})</span>
          <div className="flex items-center space-x-2 font-normal text-slate-300">
            <a
              href={`/api/v1/cases/${activeCase.id}/evidence/manifest/json`}
              target="_blank"
              rel="noreferrer"
              className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 rounded-lg text-cyan-300 border border-slate-700 flex items-center"
            >
              <Download className="w-3.5 h-3.5 mr-1" /> JSON Manifest
            </a>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 text-slate-400 font-mono border-b border-slate-800">
              <tr>
                <th className="p-3">Evidence ID</th>
                <th className="p-3">Item #</th>
                <th className="p-3">Title</th>
                <th className="p-3">Size (Bytes)</th>
                <th className="p-3">SHA-256 Digest</th>
                <th className="p-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80 font-mono">
              {evidenceList.map(ev => (
                <tr key={ev.id} className="hover:bg-slate-800/40">
                  <td className="p-3 text-cyan-300 font-bold">{ev.evidence_id}</td>
                  <td className="p-3 text-slate-300">{ev.item_number}</td>
                  <td className="p-3 text-slate-100 font-sans">{ev.title}</td>
                  <td className="p-3 text-slate-300">{(ev.file_size_bytes || 0).toLocaleString()}</td>
                  <td className="p-3 text-amber-300 text-[11px] truncate max-w-[160px]">{ev.sha256_hash}</td>
                  <td className="p-3">
                    <StatusBadge status={ev.processing_status} />
                  </td>
                </tr>
              ))}
              {evidenceList.length === 0 && (
                <tr>
                  <td colSpan={6} className="p-6 text-center text-slate-500 font-sans">
                    No evidence items ingested for Case #{activeCase.case_number}.
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
