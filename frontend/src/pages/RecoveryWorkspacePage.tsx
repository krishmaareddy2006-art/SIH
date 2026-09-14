import React, { useState, useEffect } from 'react';
import { FileSearch, Layers, Download, HardDrive, Database, CheckCircle2, RefreshCw, ArrowDownToLine, ShieldCheck } from 'lucide-react';
import { api } from '../services/api';
import { RecoveryCandidate, CarvedArtifact, EvidenceItem, DeviceInfo } from '../types';
import { useCase } from '../context/CaseContext';
import { useNotification } from '../context/NotificationContext';
import { LoadingSpinner, ErrorState } from '../components/common/StateViews';
import { StatusBadge } from '../components/common/StatusBadge';
import { TechnicalLimitationsBox } from '../components/common/TechnicalLimitationsBox';

export const RecoveryWorkspacePage: React.FC = () => {
  const { activeCase } = useCase();
  const { addToast } = useNotification();

  const [targetType, setTargetType] = useState<'device' | 'evidence'>('device');
  const [devices, setDevices] = useState<DeviceInfo[]>([]);
  const [selectedDevicePath, setSelectedDevicePath] = useState('');
  const [evidenceItems, setEvidenceItems] = useState<EvidenceItem[]>([]);
  const [selectedEvidenceId, setSelectedEvidenceId] = useState('');

  const [candidates, setCandidates] = useState<RecoveryCandidate[]>([]);
  const [selectedCandidateIds, setSelectedCandidateIds] = useState<string[]>([]);
  const [carvedList, setCarvedList] = useState<CarvedArtifact[]>([]);

  const [selectedFormats] = useState<string[]>(['JPEG', 'PNG', 'PDF', 'ZIP']);
  const [isScanning, setIsScanning] = useState(false);
  const [isCarving, setIsCarving] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Load devices and evidence items
  useEffect(() => {
    async function loadData() {
      if (!activeCase) {
        setIsLoading(false);
        return;
      }
      setIsLoading(true);
      try {
        const [devRes, evRes] = await Promise.all([
          api.listDevices(),
          api.listEvidence(activeCase.id),
        ]);

        if (devRes.data && devRes.data.length > 0) {
          setDevices(devRes.data);
          // Prefer removable USB or secondary disk if available, else first disk
          const preferred = devRes.data.find(d => !d.is_system_disk) || devRes.data[0];
          setSelectedDevicePath(preferred.device_path);
        }

        if (evRes.data && evRes.data.length > 0) {
          setEvidenceItems(evRes.data);
          setSelectedEvidenceId(evRes.data[0].evidence_id);
        }
      } catch (err) {
        console.error('Failed to load targets:', err);
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, [activeCase?.id]);

  const activeTargetPayload = targetType === 'device'
    ? { device_path: selectedDevicePath }
    : { evidence_id: selectedEvidenceId };

  const activeTargetLabel = targetType === 'device' ? selectedDevicePath : selectedEvidenceId;

  const markRecoveredCandidates = (cands: RecoveryCandidate[], recoveredArts: any[]) => {
    const recoveredMap = new Map(recoveredArts.map(a => [a.candidate_id, a]));
    return cands.map(c => {
      if (recoveredMap.has(c.candidate_id)) {
        const art = recoveredMap.get(c.candidate_id);
        return {
          ...c,
          is_recovered: true,
          download_url: `http://127.0.0.1:8000/api/v1/recovery/${art.artifact_id}/download`,
        };
      }
      return c;
    });
  };

  const handleDownload = (downloadUrl: string, filename: string) => {
    const fullUrl = downloadUrl.startsWith('http')
      ? downloadUrl
      : `http://127.0.0.1:8000${downloadUrl}`;

    const link = document.createElement('a');
    link.href = fullUrl;
    link.setAttribute('download', filename);
    link.target = '_blank';
    link.rel = 'noreferrer';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleScanRecovery = async () => {
    if (!activeCase || !activeTargetLabel) return;
    setIsScanning(true);
    try {
      const [scanRes, recRes] = await Promise.all([
        api.scanFilesystemRecovery(activeCase.id, activeTargetPayload),
        api.listRecoveredArtifacts(activeCase.id),
      ]);
      if (scanRes.data) {
        const rawCands = scanRes.data.candidates || [];
        const existingRecovered = recRes.data || [];
        const synced = markRecoveredCandidates(rawCands, existingRecovered);
        setCandidates(synced);
        setSelectedCandidateIds([]);
        const count = scanRes.data.total_candidates_found ?? rawCands.length;
        addToast('success', 'Filesystem Scan Complete', `Identified ${count} deleted file candidates on ${activeTargetLabel}.`);
      } else if (scanRes.error) {
        addToast('error', 'Recovery Scan Blocked', scanRes.error.error.message);
      }
    } catch (err: any) {
      addToast('error', 'Scan Failed', err?.message || 'Failed to scan target');
    } finally {
      setIsScanning(false);
    }
  };

  const handleRunCarver = async () => {
    if (!activeCase || !activeTargetLabel) return;
    setIsCarving(true);
    try {
      const res = await api.carveFiles(activeCase.id, activeTargetPayload, selectedFormats);
      if (res.data) {
        setCarvedList(res.data.carved_artifacts || []);
        const count = res.data.carved_artifacts?.length ?? 0;
        addToast('success', 'Signature Carving Complete', `Extracted ${count} carved file artifacts from ${activeTargetLabel}.`);
      } else if (res.error) {
        addToast('error', 'Carving Blocked', res.error.error.message);
      }
    } catch (err: any) {
      addToast('error', 'Carving Failed', err?.message || 'Failed to run signature carver');
    } finally {
      setIsCarving(false);
    }
  };

  const handleExtractCandidates = async (candidateIdsToExtract: string[]) => {
    if (!activeCase || candidateIdsToExtract.length === 0) return;
    setIsExtracting(true);
    try {
      const payload = {
        ...activeTargetPayload,
        candidate_ids: candidateIdsToExtract,
      };
      const res = await api.extractRecoveryCandidates(activeCase.id, payload);
      if (res.data) {
        const extracted = res.data.extracted_artifacts || [];
        const extractedMap = new Map(extracted.map(a => [a.candidate_id, a]));

        // Update candidates state with exact download URLs
        setCandidates(prev =>
          prev.map(c => {
            if (extractedMap.has(c.candidate_id)) {
              const art = extractedMap.get(c.candidate_id);
              return {
                ...c,
                is_recovered: true,
                download_url: `http://127.0.0.1:8000/api/v1/recovery/${art.artifact_id}/download`,
              };
            }
            return c;
          })
        );

        addToast(
          'success',
          'File Recovery Complete',
          `Successfully recovered ${res.data.successfully_extracted} files from ${activeTargetLabel}. Ready for download.`
        );
      } else if (res.error) {
        addToast('error', 'Extraction Failed', res.error.error.message);
      }
    } catch (err: any) {
      addToast('error', 'Extraction Error', err?.message || 'Error executing file recovery');
    } finally {
      setIsExtracting(false);
    }
  };

  const toggleCandidateSelection = (candidateId: string) => {
    setSelectedCandidateIds(prev =>
      prev.includes(candidateId) ? prev.filter(id => id !== candidateId) : [...prev, candidateId]
    );
  };

  const toggleSelectAll = () => {
    if (selectedCandidateIds.length === candidates.length) {
      setSelectedCandidateIds([]);
    } else {
      setSelectedCandidateIds(candidates.map(c => c.candidate_id));
    }
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes || bytes <= 0) return '0 B';
    if (bytes >= 1024 * 1024 * 1024) return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
    if (bytes >= 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
    if (bytes >= 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return `${bytes} B`;
  };

  if (!activeCase) return <ErrorState code="NO_ACTIVE_CASE" message="Please select an active forensic case in the header to access recovery workspace." />;
  if (isLoading) return <LoadingSpinner message="Loading recovery engine, attached disks, & evidence bindings..." />;

  const currentDevice = devices.find(d => d.device_path === selectedDevicePath);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="bg-[#111827] p-5 sm:p-6 rounded-2xl border border-[#253044] shadow-card flex items-center justify-between">
        <div>
          <h2 className="text-lg sm:text-xl font-bold text-[#F8FAFC] flex items-center">
            <FileSearch className="w-5 h-5 text-[#FBBF24] mr-2.5" />
            Filesystem Recovery & Signature Carving Hub
          </h2>
          <p className="text-xs text-[#94A3B8] mt-1">
            Read-only storage device scanning, deleted directory entries extraction, and raw signature file carving
          </p>
        </div>
        <div className="hidden sm:flex items-center space-x-2 text-xs font-mono text-[#22D3EE] bg-[#0B0F19] px-3 py-1.5 rounded-xl border border-[#253044]">
          <ShieldCheck className="w-4 h-4 text-[#10B981]" />
          <span>STRICT_READ_ONLY: ENFORCED</span>
        </div>
      </div>

      {/* Target & Scanner Control Bar */}
      <div className="bg-[#111827] border border-[#253044] rounded-2xl p-5 sm:p-6 space-y-5 shadow-card text-xs">
        {/* Mode Selector Tabs */}
        <div>
          <div className="flex items-center space-x-3 mb-3">
            <span className="text-[#94A3B8] font-semibold uppercase tracking-wider text-[11px]">Select Target Mode:</span>
            <div className="inline-flex p-1 bg-[#0B0F19] rounded-xl border border-[#253044]">
              <button
                type="button"
                onClick={() => setTargetType('device')}
                className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg font-medium transition-all cursor-pointer ${
                  targetType === 'device'
                    ? 'bg-[#22D3EE]/20 text-[#22D3EE] border border-[#22D3EE]/40 font-bold shadow-sm'
                    : 'text-[#94A3B8] hover:text-[#F8FAFC]'
                }`}
              >
                <HardDrive className="w-3.5 h-3.5" />
                <span>Connected Storage Device / Disk</span>
              </button>
              <button
                type="button"
                onClick={() => setTargetType('evidence')}
                className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg font-medium transition-all cursor-pointer ${
                  targetType === 'evidence'
                    ? 'bg-[#22D3EE]/20 text-[#22D3EE] border border-[#22D3EE]/40 font-bold shadow-sm'
                    : 'text-[#94A3B8] hover:text-[#F8FAFC]'
                }`}
              >
                <Database className="w-3.5 h-3.5" />
                <span>Forensic Evidence Image</span>
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
            <div>
              <label className="block text-[#94A3B8] font-medium mb-1.5">
                {targetType === 'device' ? 'Attached Storage Device / Drive' : 'Bound Evidence Image File'}
              </label>

              {targetType === 'device' ? (
                <select
                  value={selectedDevicePath}
                  onChange={e => setSelectedDevicePath(e.target.value)}
                  className="w-full bg-[#0B0F19] border border-[#253044] font-mono text-[#22D3EE] rounded-xl px-3.5 py-2.5 outline-none focus:border-[#22D3EE] transition-all cursor-pointer shadow-subtle"
                >
                  {devices.map(dev => (
                    <option key={dev.device_path} value={dev.device_path} className="bg-[#111827] text-[#F8FAFC]">
                      {dev.device_path} — {dev.vendor} {dev.model} ({formatFileSize(dev.size_bytes)}) {dev.is_system_disk ? '[SYSTEM]' : ''}
                    </option>
                  ))}
                  {devices.length === 0 && (
                    <option value="" disabled className="bg-[#111827] text-[#64748B]">No storage devices discovered</option>
                  )}
                </select>
              ) : (
                <select
                  value={selectedEvidenceId}
                  onChange={e => setSelectedEvidenceId(e.target.value)}
                  className="w-full bg-[#0B0F19] border border-[#253044] font-mono text-[#22D3EE] rounded-xl px-3.5 py-2.5 outline-none focus:border-[#22D3EE] transition-all cursor-pointer shadow-subtle"
                >
                  {evidenceItems.map(ev => (
                    <option key={ev.id} value={ev.evidence_id} className="bg-[#111827] text-[#F8FAFC]">
                      {ev.evidence_id} — {ev.title} ({ev.item_number})
                    </option>
                  ))}
                  {evidenceItems.length === 0 && (
                    <option value="" disabled className="bg-[#111827] text-[#64748B]">No evidence images bound to case</option>
                  )}
                </select>
              )}
            </div>

            <div className="flex flex-wrap items-center gap-3 md:col-span-2">
              <button
                onClick={handleScanRecovery}
                disabled={!activeTargetLabel || isScanning}
                className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl font-semibold transition-all shadow-subtle ${
                  activeTargetLabel && !isScanning
                    ? 'bg-[#0B0F19] hover:bg-[#162032] text-[#FBBF24] border border-[#FBBF24]/50 cursor-pointer'
                    : 'bg-[#162032] text-[#64748B] border border-[#253044] cursor-not-allowed'
                }`}
              >
                {isScanning ? <RefreshCw className="w-4 h-4 animate-spin text-[#FBBF24]" /> : <FileSearch className="w-4 h-4" />}
                <span>{isScanning ? 'Scanning Deleted Entries...' : 'Run Filesystem Scan'}</span>
              </button>

              <button
                onClick={handleRunCarver}
                disabled={!activeTargetLabel || isCarving}
                className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl font-bold transition-all shadow-subtle ${
                  activeTargetLabel && !isCarving
                    ? 'bg-[#22D3EE] hover:bg-[#67E8F9] text-[#080B14] cursor-pointer'
                    : 'bg-[#162032] text-[#64748B] border border-[#253044] cursor-not-allowed'
                }`}
              >
                {isCarving ? <RefreshCw className="w-4 h-4 animate-spin text-[#080B14]" /> : <Layers className="w-4 h-4" />}
                <span>{isCarving ? 'Carving Signatures...' : 'Run Signature File Carver'}</span>
              </button>

              {currentDevice && targetType === 'device' && (
                <div className="text-[11px] text-[#94A3B8] font-mono flex items-center space-x-2 ml-auto">
                  <span className="px-2 py-0.5 rounded bg-[#0B0F19] border border-[#253044] text-[#22D3EE]">
                    Bus: {currentDevice.bus_type}
                  </span>
                  <span className="px-2 py-0.5 rounded bg-[#0B0F19] border border-[#253044] text-[#10B981]">
                    Mode: READ_ONLY
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Recovered Candidates Table */}
      <div className="bg-[#111827] border border-[#253044] rounded-2xl overflow-hidden shadow-card">
        <div className="p-4 border-b border-[#253044] flex flex-wrap items-center justify-between gap-3 text-xs text-[#94A3B8] font-mono">
          <div className="flex items-center space-x-3">
            <span className="font-bold text-[#F8FAFC]">
              Filesystem Candidates Identified ({candidates.length})
            </span>
            {candidates.length > 0 && (
              <span className="text-[#10B981] bg-[#10B981]/10 px-2.5 py-0.5 rounded-full border border-[#10B981]/30">
                {candidates.filter(c => c.classification_status === 'RECOVERABLE').length} Recoverable
              </span>
            )}
          </div>

          {candidates.length > 0 && (
            <div className="flex items-center space-x-2">
              <button
                onClick={() => handleExtractCandidates(selectedCandidateIds.length > 0 ? selectedCandidateIds : candidates.map(c => c.candidate_id))}
                disabled={isExtracting}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl font-bold font-sans text-xs transition-all shadow-subtle ${
                  !isExtracting
                    ? 'bg-[#10B981] hover:bg-[#34D399] text-[#080B14] cursor-pointer'
                    : 'bg-[#162032] text-[#64748B] cursor-not-allowed'
                }`}
              >
                {isExtracting ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <ArrowDownToLine className="w-3.5 h-3.5" />}
                <span>
                  {selectedCandidateIds.length > 0
                    ? `Recover Selected (${selectedCandidateIds.length})`
                    : `Recover All Files (${candidates.length})`}
                </span>
              </button>
            </div>
          )}
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0B0F19] text-[#64748B] font-mono border-b border-[#253044]">
              <tr>
                <th className="p-3 w-10 text-center">
                  <input
                    type="checkbox"
                    checked={candidates.length > 0 && selectedCandidateIds.length === candidates.length}
                    onChange={toggleSelectAll}
                    className="rounded bg-[#111827] border-[#253044] text-[#22D3EE] focus:ring-0 cursor-pointer"
                  />
                </th>
                <th className="p-3">Candidate ID</th>
                <th className="p-3">Original Filename & Path</th>
                <th className="p-3">Size</th>
                <th className="p-3">Deletion Timestamp</th>
                <th className="p-3">Filesystem</th>
                <th className="p-3">Classification</th>
                <th className="p-3">Confidence</th>
                <th className="p-3 text-right">Recovery Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#253044] font-mono">
              {candidates.map(c => {
                const isSelected = selectedCandidateIds.includes(c.candidate_id);
                const isRecoverable = c.classification_status === 'RECOVERABLE';
                const effectiveSize = c.file_size_bytes || c.declared_size_bytes || 0;
                const effectiveName: string = c.name || c.filename || (c.path ? c.path.split(/[\\/]/).pop() : c.candidate_id) || 'recovered_file';

                return (
                  <tr
                    key={c.candidate_id}
                    className={`transition-colors ${isSelected ? 'bg-[#22D3EE]/5' : 'hover:bg-[#162032]/40'}`}
                  >
                    <td className="p-3 text-center">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggleCandidateSelection(c.candidate_id)}
                        className="rounded bg-[#111827] border-[#253044] text-[#22D3EE] focus:ring-0 cursor-pointer"
                      />
                    </td>
                    <td className="p-3 text-[#22D3EE] font-bold">{c.candidate_id}</td>
                    <td className="p-3 text-[#F8FAFC] font-sans font-medium max-w-xs truncate" title={c.path || c.original_path}>
                      <span className="block text-[#F8FAFC] font-semibold">{effectiveName}</span>
                      <span className="text-[11px] text-[#64748B] font-mono">{c.path || c.original_path}</span>
                    </td>
                    <td className="p-3 text-[#94A3B8]">{formatFileSize(effectiveSize)}</td>
                    <td className="p-3 text-[#94A3B8]">
                      {c.deleted_at ? new Date(c.deleted_at).toLocaleString() : 'N/A'}
                    </td>
                    <td className="p-3 text-[#94A3B8]">{c.filesystem_type}</td>
                    <td className="p-3"><StatusBadge status={c.classification_status} /></td>
                    <td className="p-3 font-bold text-[#FBBF24]">{c.confidence_score || 95}/100</td>
                    <td className="p-3 text-right">
                      {c.is_recovered && c.download_url ? (
                        <button
                          type="button"
                          onClick={() => handleDownload(c.download_url!, effectiveName)}
                          className="inline-flex items-center space-x-1.5 bg-[#10B981]/20 hover:bg-[#10B981]/30 text-[#10B981] border border-[#10B981]/40 px-3 py-1 rounded-lg transition-all font-sans font-semibold text-xs cursor-pointer shadow-subtle"
                          title={`Download exact file: ${effectiveName}`}
                        >
                          <Download className="w-3.5 h-3.5" />
                          <span>Download</span>
                        </button>
                      ) : (
                        <button
                          onClick={() => handleExtractCandidates([c.candidate_id])}
                          disabled={!isRecoverable || isExtracting}
                          className={`inline-flex items-center space-x-1.5 px-3 py-1 rounded-lg transition-all font-sans font-semibold text-xs shadow-subtle ${
                            isRecoverable && !isExtracting
                              ? 'bg-[#22D3EE]/10 hover:bg-[#22D3EE]/20 text-[#22D3EE] border border-[#22D3EE]/30 cursor-pointer'
                              : 'bg-[#162032] text-[#64748B] border border-[#253044] cursor-not-allowed'
                          }`}
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Recover</span>
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
              {candidates.length === 0 && (
                <tr>
                  <td colSpan={9} className="p-10 text-center text-[#64748B] font-sans">
                    <FileSearch className="w-8 h-8 text-[#64748B] mx-auto mb-2 opacity-50" />
                    <p className="text-sm text-[#94A3B8] font-medium">No recovery scan executed yet</p>
                    <p className="text-xs text-[#64748B] mt-1">
                      Select a storage device or evidence image above, then click &quot;Run Filesystem Scan&quot; to discover deleted files.
                    </p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Carved Artifacts Table */}
      {carvedList.length > 0 && (
        <div className="bg-[#111827] border border-[#253044] rounded-2xl overflow-hidden shadow-card animate-fade-in">
          <div className="p-4 border-b border-[#253044] flex flex-wrap items-center justify-between gap-2 text-xs text-[#94A3B8] font-mono">
            <span className="font-bold text-[#F8FAFC]">Carved File Artifacts ({carvedList.length})</span>
            <span className="text-[11px] text-[#22D3EE] bg-[#0B0F19] px-2.5 py-1 rounded-lg border border-[#253044]">
              Target: <span className="text-[#F8FAFC]">{activeTargetLabel}</span>
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-[#0B0F19] text-[#64748B] border-b border-[#253044]">
                <tr>
                  <th className="p-3">Carved ID</th>
                  <th className="p-3">Format</th>
                  <th className="p-3">Offsets</th>
                  <th className="p-3">Carved SHA-256</th>
                  <th className="p-3">Confidence</th>
                  <th className="p-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#253044]">
                {carvedList.map(ca => (
                  <tr key={ca.carved_id} className="hover:bg-[#162032]/40 transition-colors">
                    <td className="p-3 text-[#22D3EE] font-bold">{ca.carved_id}</td>
                    <td className="p-3 text-[#F8FAFC]">{ca.file_format}</td>
                    <td className="p-3 text-[#94A3B8]">{ca.source_start_offset} — {ca.source_end_offset}</td>
                    <td className="p-3 text-[#FBBF24] text-[11px]">{ca.carved_file_hash.substring(0, 16)}...</td>
                    <td className="p-3"><StatusBadge status={ca.confidence_level} /></td>
                    <td className="p-3 text-right">
                      <button
                        type="button"
                        onClick={() =>
                          handleDownload(
                            `http://127.0.0.1:8000/api/v1/carving/${ca.carved_id}/download`,
                            `${ca.carved_id}.${ca.file_format.toLowerCase()}`
                          )
                        }
                        className="inline-flex items-center space-x-1.5 bg-[#22D3EE]/10 hover:bg-[#22D3EE]/20 text-[#22D3EE] border border-[#22D3EE]/30 px-2.5 py-1 rounded-lg transition-all font-sans font-semibold text-xs cursor-pointer shadow-subtle"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>Download</span>
                      </button>
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

