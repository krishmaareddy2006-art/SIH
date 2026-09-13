import React, { useState, useEffect } from 'react';
import { UploadCloud, ShieldCheck, Download } from 'lucide-react';
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
  const [sourceDesc] = useState('1TB SATA HDD physical image acquired in lab');
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
  if (error) return <ErrorState code="EVIDENCE_FETCH_ERROR" message={error} onRetry={loadEvidence} />;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="bg-[#111827] p-5 sm:p-6 rounded-2xl border border-[#253044] shadow-card flex items-center justify-between">
        <div>
          <h2 className="text-lg sm:text-xl font-bold text-[#F8FAFC] flex items-center">
            <UploadCloud className="w-5 h-5 text-[#22D3EE] mr-2.5" />
            Read-Only Forensic Evidence Intake & Provenance
          </h2>
          <p className="text-xs text-[#94A3B8] mt-1">
            Streaming SHA-256 ingestion, immutable read-only handles, and manifest exports for Case #{activeCase.case_number}
          </p>
        </div>
      </div>

      {/* Import Form */}
      <div className="bg-[#111827] border border-[#253044] rounded-2xl p-5 sm:p-6 space-y-4 shadow-card">
        <h3 className="text-xs font-bold text-[#94A3B8] uppercase tracking-wider font-mono">
          Register Source Evidence Image
        </h3>

        <form onSubmit={handleImport} className="space-y-4 text-xs">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-[#94A3B8] font-medium mb-1">Source File / Image Path</label>
              <input
                type="text"
                value={sourceFilePath}
                onChange={e => setSourceFilePath(e.target.value)}
                placeholder="/path/to/evidence.raw"
                required
                className="w-full bg-[#0B0F19] border border-[#253044] font-mono text-[#22D3EE] rounded-xl px-3.5 py-2 outline-none focus:border-[#22D3EE] transition-all shadow-subtle"
              />
            </div>
            <div>
              <label className="block text-[#94A3B8] font-medium mb-1">Item Reference Identifier</label>
              <input
                type="text"
                value={itemNumber}
                onChange={e => setItemNumber(e.target.value)}
                placeholder="EVID-001"
                required
                className="w-full bg-[#0B0F19] border border-[#253044] font-mono text-[#F8FAFC] rounded-xl px-3.5 py-2 outline-none focus:border-[#22D3EE] transition-all shadow-subtle"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-[#94A3B8] font-medium mb-1">Evidence Title</label>
              <input
                type="text"
                value={title}
                onChange={e => setTitle(e.target.value)}
                placeholder="Title description..."
                required
                className="w-full bg-[#0B0F19] border border-[#253044] rounded-xl px-3.5 py-2 text-[#F8FAFC] outline-none focus:border-[#22D3EE] transition-all shadow-subtle"
              />
            </div>
            <div className="flex items-center space-x-2.5 pt-6">
              <input
                type="checkbox"
                id="workingCopy"
                checked={createWorkingCopy}
                onChange={e => setCreateWorkingCopy(e.target.checked)}
                className="rounded border-[#253044] text-[#22D3EE] focus:ring-[#22D3EE] bg-[#0B0F19]"
              />
              <label htmlFor="workingCopy" className="text-[#94A3B8] font-medium cursor-pointer text-xs select-none">
                Create Read-Only Working Copy (Preserves Original Handle)
              </label>
            </div>
          </div>

          <div className="flex items-center justify-end border-t border-[#253044] pt-3">
            <button
              type="submit"
              disabled={isImporting}
              className="flex items-center space-x-2 bg-[#22D3EE] hover:bg-[#67E8F9] text-[#080B14] font-bold px-5 py-2 rounded-xl shadow-subtle transition-all cursor-pointer disabled:opacity-50"
            >
              <ShieldCheck className="w-4 h-4" />
              <span>{isImporting ? 'Ingesting Image...' : 'Ingest & Compute Streaming SHA-256'}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Inventory Table */}
      <div className="bg-[#111827] border border-[#253044] rounded-2xl overflow-hidden shadow-card">
        <div className="p-4 border-b border-[#253044] flex items-center justify-between text-xs text-[#94A3B8] font-mono">
          <span>Ingested Evidence Inventory ({evidenceList.length})</span>
          <a
            href={`/api/v1/cases/${activeCase.id}/evidence/manifest/json`}
            target="_blank"
            rel="noreferrer"
            className="px-2.5 py-1 bg-[#0B0F19] hover:bg-[#162032] rounded-lg text-[#22D3EE] border border-[#253044] flex items-center text-[11px] transition-all"
          >
            <Download className="w-3.5 h-3.5 mr-1" /> JSON Manifest
          </a>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0B0F19] text-[#64748B] font-mono border-b border-[#253044]">
              <tr>
                <th className="p-3">Evidence ID</th>
                <th className="p-3">Item #</th>
                <th className="p-3">Title</th>
                <th className="p-3">Size (Bytes)</th>
                <th className="p-3">SHA-256 Digest</th>
                <th className="p-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#253044] font-mono">
              {evidenceList.map(ev => (
                <tr key={ev.id} className="hover:bg-[#162032]/40 transition-colors">
                  <td className="p-3 text-[#22D3EE] font-bold">{ev.evidence_id}</td>
                  <td className="p-3 text-[#94A3B8]">{ev.item_number}</td>
                  <td className="p-3 text-[#F8FAFC] font-sans font-medium">{ev.title}</td>
                  <td className="p-3 text-[#94A3B8]">{(ev.file_size_bytes || 0).toLocaleString()}</td>
                  <td className="p-3 text-[#FBBF24] text-[11px] truncate max-w-[160px]">{ev.sha256_hash}</td>
                  <td className="p-3">
                    <StatusBadge status={ev.processing_status} />
                  </td>
                </tr>
              ))}
              {evidenceList.length === 0 && (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-[#64748B] font-sans">
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
