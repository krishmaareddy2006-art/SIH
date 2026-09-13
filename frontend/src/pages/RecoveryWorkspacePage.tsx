import React, { useState, useEffect } from 'react';
import { FileSearch, Layers, CheckCircle2, AlertTriangle, ShieldCheck, Download, RefreshCw } from 'lucide-react';
import { api } from '../services/api';
import { RecoveryCandidate, CarvedArtifact, EvidenceItem } from '../types';
import { useCase } from '../context/CaseContext';
import { useNotification } from '../context/NotificationContext';
import { LoadingSpinner, ErrorState } from '../components/common/StateViews';
import { StatusBadge } from '../components/common/StatusBadge';
import { TechnicalLimitationsBox } from '../components/common/TechnicalLimitationsBox';

export const RecoveryWorkspacePage: React.FC = () => {
  const { activeCase } = useCase();
  const { addToast } = useNotification();

  const [evidenceItems, setEvidenceItems] = useState<EvidenceItem[]>([]);
  const [selectedEvidenceId, setSelectedEvidenceId] = useState('');
  const [candidates, setCandidates] = useState<RecoveryCandidate[]>([]);
  const [carvedList, setCarvedList] = useState<CarvedArtifact[]>([]);

  const [selectedFormats, setSelectedFormats] = useState<string[]>(['JPEG', 'PNG', 'PDF', 'ZIP']);
  const [isScanning, setIsScanning] = useState(false);
  const [isCarving, setIsCarving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      if (!activeCase) {
        setIsLoading(false);
        return;
      }
      setIsLoading(true);
      const res = await api.listEvidence(activeCase.id);
      if (res.data) {
        setEvidenceItems(res.data);
        if (res.data.length > 0) setSelectedEvidenceId(res.data[0].evidence_id);
      }
      setIsLoading(false);
    }
    loadData();
  }, [activeCase?.id]);

  const handleScanRecovery = async () => {
    if (!activeCase || !selectedEvidenceId) return;
    setIsScanning(true);
    const res = await api.scanFilesystemRecovery(activeCase.id, selectedEvidenceId);
    setIsScanning(false);

    if (res.data) {
      setCandidates(res.data.candidates || []);
      const count = res.data.total_candidates_found ?? res.data.candidates?.length ?? 0;
      addToast('success', 'Filesystem Scan Complete', `Identified ${count} candidate entries.`);
    } else if (res.error) {
      addToast('error', 'Recovery Scan Blocked', res.error.error.message);
    }
  };

  const handleRunCarver = async () => {
    if (!activeCase || !selectedEvidenceId) return;
    setIsCarving(true);
    const res = await api.carveFiles(activeCase.id, selectedEvidenceId, selectedFormats);
    setIsCarving(false);

    if (res.data) {
      setCarvedList(res.data.carved_artifacts || []);
      const count = res.data.carved_artifacts?.length ?? 0;
      addToast('success', 'Signature Carving Complete', `Extracted ${count} carved file artifacts.`);
    } else if (res.error) {
      addToast('error', 'Carving Blocked', res.error.error.message);
    }
  };

  if (!activeCase) return <ErrorState code="NO_ACTIVE_CASE" message="Please select an active forensic case in the header to access recovery workspace." />;
  if (isLoading) return <LoadingSpinner message="Loading recovery engine & evidence bindings..." />;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800 shadow-xl flex items-center justify-between">
        <div>
          <h2 className="text-xl font-extrabold text-slate-100 flex items-center">
            <FileSearch className="w-6 h-6 text-amber-400 mr-2.5" />
            Filesystem Recovery & Signature Carving Hub
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Read-only evidence extents extraction, format validation, and confidence scoring
          </p>
        </div>
      </div>

      {/* Target & Scanner Control Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-xl text-xs">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-slate-300 font-semibold mb-1.5">Bound Evidence Image</label>
            <select
              value={selectedEvidenceId}
              onChange={e => setSelectedEvidenceId(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 font-mono text-cyan-300 rounded-xl px-3.5 py-2.5 outline-none"
            >
              {evidenceItems.map(ev => (
                <option key={ev.id} value={ev.evidence_id}>
                  {ev.evidence_id} - {ev.title} ({ev.item_number})
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-end space-x-3 md:col-span-2">
            <button
              onClick={handleScanRecovery}
              disabled={!selectedEvidenceId || isScanning}
              className="flex items-center space-x-2 bg-amber-600 hover:bg-amber-500 text-white font-bold px-4 py-2.5 rounded-xl shadow-lg shadow-amber-950 transition-all cursor-pointer"
            >
              <FileSearch className="w-4 h-4" />
              <span>{isScanning ? 'Scanning FS...' : 'Run Filesystem Recovery Scan'}</span>
            </button>

            <button
              onClick={handleRunCarver}
              disabled={!selectedEvidenceId || isCarving}
              className="flex items-center space-x-2 bg-cyan-600 hover:bg-cyan-500 text-white font-bold px-4 py-2.5 rounded-xl shadow-lg shadow-cyan-950 transition-all cursor-pointer"
            >
              <Layers className="w-4 h-4" />
              <span>{isCarving ? 'Carving Signatures...' : 'Run Signature File Carver'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Recovered Candidates Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between text-xs text-slate-400 font-semibold uppercase tracking-wider">
          <span>Filesystem Candidates Identified ({candidates.length})</span>
          <span>Bounds Verification: STRICT</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 text-slate-400 font-mono border-b border-slate-800">
              <tr>
                <th className="p-3">Candidate ID</th>
                <th className="p-3">Original Path</th>
                <th className="p-3">Filesystem</th>
                <th className="p-3">Source Offset</th>
                <th className="p-3">Classification</th>
                <th className="p-3">Confidence</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80 font-mono">
              {candidates.map(c => (
                <tr key={c.candidate_id} className="hover:bg-slate-800/40">
                  <td className="p-3 text-cyan-300 font-bold">{c.candidate_id}</td>
                  <td className="p-3 text-slate-100 font-sans">{c.original_path}</td>
                  <td className="p-3 text-slate-300">{c.filesystem_type}</td>
                  <td className="p-3 text-slate-300">{(c.source_offset_bytes || 0).toLocaleString()} B</td>
                  <td className="p-3"><StatusBadge status={c.classification_status} /></td>
                  <td className="p-3 font-bold text-amber-300">{c.confidence_score}/100</td>
                </tr>
              ))}
              {candidates.length === 0 && (
                <tr>
                  <td colSpan={6} className="p-6 text-center text-slate-500 font-sans">
                    No recovery scan executed yet. Click "Run Filesystem Recovery Scan" above.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Carved Artifacts Table */}
      {carvedList.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
          <div className="p-4 border-b border-slate-800 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-400 font-semibold uppercase tracking-wider">
            <span>Carved File Artifacts ({carvedList.length})</span>
            <span className="font-mono text-[11px] text-cyan-400 bg-slate-950 px-2.5 py-1 rounded-lg border border-slate-800 normal-case">
              📁 Saved to: <span className="text-slate-200 font-semibold">tests/qa_framework/golden_manifests/carved_output/case_1</span>
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="p-3">Carved ID</th>
                  <th className="p-3">Format</th>
                  <th className="p-3">Offsets</th>
                  <th className="p-3">Carved SHA-256</th>
                  <th className="p-3">Confidence</th>
                  <th className="p-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {carvedList.map(ca => (
                  <tr key={ca.carved_id} className="hover:bg-slate-800/40">
                    <td className="p-3 text-cyan-300 font-bold">{ca.carved_id}</td>
                    <td className="p-3 text-slate-200">{ca.file_format}</td>
                    <td className="p-3 text-slate-400">{ca.source_start_offset} - {ca.source_end_offset}</td>
                    <td className="p-3 text-amber-300 text-[11px]">{ca.carved_file_hash.substring(0, 16)}...</td>
                    <td className="p-3"><StatusBadge status={ca.confidence_level} /></td>
                    <td className="p-3 text-right">
                      <a
                        href={`http://127.0.0.1:8000/api/v1/carving/${ca.carved_id}/download`}
                        download
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center space-x-1 bg-cyan-600/20 hover:bg-cyan-600/40 text-cyan-300 border border-cyan-500/40 px-2.5 py-1 rounded-lg transition-all font-sans font-semibold text-xs"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>Download</span>
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <TechnicalLimitationsBox />
    </div>
  );
};
