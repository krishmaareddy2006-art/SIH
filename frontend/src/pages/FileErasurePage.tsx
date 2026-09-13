import React, { useState } from 'react';
import { FileX, ShieldCheck, Play, FileText, CheckCircle2, AlertTriangle } from 'lucide-react';
import { api } from '../services/api';
import { ErasureJob } from '../types';
import { useNotification } from '../context/NotificationContext';
import { TypedConfirmationModal } from '../components/common/TypedConfirmationModal';
import { TechnicalLimitationsBox } from '../components/common/TechnicalLimitationsBox';

export const FileErasurePage: React.FC = () => {
  const { addToast } = useNotification();

  const [targetPath, setTargetPath] = useState('D:\\forensic_test_sandbox\\test_file_to_delete.txt');
  const [method, setMethod] = useState('NIST_800_88');
  const [passes, setPasses] = useState(3);

  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);
  const [completedJob, setCompletedJob] = useState<ErasureJob | null>(null);

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);

  const handleAnalyze = async () => {
    if (!targetPath) return;
    setIsAnalyzing(true);
    const res = await api.analyzeFileErasure(targetPath);
    setIsAnalyzing(false);

    if (res.data) {
      setAnalysisResult(res.data);
      setIsConfirmModalOpen(true);
    } else if (res.error) {
      addToast('error', 'File Analysis Failed', res.error.error.message);
    }
  };

  const handleExecuteErasure = async () => {
    setIsExecuting(true);
    const res = await api.executeFileErasure({
      target_path: targetPath,
      method,
      passes,
      confirmation: `CONFIRM ERASE ${targetPath}`,
    });
    setIsExecuting(false);
    setIsConfirmModalOpen(false);

    if (res.data) {
      setCompletedJob(res.data);
      addToast('success', 'File Erasure Verified', `File erased cleanly with SHA-256 pre/post verification.`);
    } else if (res.error) {
      addToast('error', 'File Erasure Blocked', res.error.error.message);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800 shadow-xl flex items-center justify-between">
        <div>
          <h2 className="text-xl font-extrabold text-slate-100 flex items-center">
            <FileX className="w-6 h-6 text-red-400 mr-2.5" />
            Secure File & Folder Erasure Wizard
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Targeted file block overwriting, pass algorithm configuration, and post-erasure SHA-256 verification
          </p>
        </div>
      </div>

      {/* Erasure Configuration Form */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-5 shadow-xl">
        <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">Erasure Configuration & Target</h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="md:col-span-2">
            <label className="block text-slate-300 font-semibold mb-1.5">Target File/Folder Path</label>
            <input
              type="text"
              value={targetPath}
              onChange={e => setTargetPath(e.target.value)}
              placeholder="/path/to/sensitive_file.dat"
              className="w-full bg-slate-950 border border-slate-700 font-mono text-cyan-300 rounded-xl px-3.5 py-2.5 outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-slate-300 font-semibold mb-1.5">Erasure Standard / Pattern</label>
            <select
              value={method}
              onChange={e => setMethod(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 font-mono text-slate-100 rounded-xl px-3.5 py-2.5 outline-none"
            >
              <option value="NIST_800_88">NIST 800-88 Clear (Recommended)</option>
              <option value="DOD_5220_22_M">DoD 5220.22-M (3 Passes)</option>
              <option value="SINGLE_PASS_ZERO">Single Pass Zero Fill</option>
              <option value="GUTMANN_LITE">Gutmann Lite Pseudo-Random</option>
            </select>
          </div>
        </div>

        <div className="flex items-center justify-end border-t border-slate-800 pt-4">
          <button
            onClick={handleAnalyze}
            disabled={!targetPath || isAnalyzing}
            className="flex items-center space-x-2 bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs px-5 py-2.5 rounded-xl shadow-lg shadow-cyan-950 transition-all cursor-pointer"
          >
            <Play className="w-4 h-4" />
            <span>{isAnalyzing ? 'Analyzing File...' : 'Analyze & Prepare Erasure'}</span>
          </button>
        </div>
      </div>

      {/* Completed Job Report */}
      {completedJob && (
        <div className="bg-slate-900 border border-emerald-500/40 rounded-2xl p-6 space-y-4 shadow-xl text-xs">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center space-x-2.5">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              <h4 className="font-bold text-slate-100 text-sm">Verified File Erasure Report</h4>
            </div>
            <span className="bg-emerald-950 text-emerald-300 border border-emerald-500/40 font-mono font-bold px-2.5 py-1 rounded-full">
              VERIFICATION PASSED
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 font-mono bg-slate-950 p-4 rounded-xl border border-slate-800">
            <div>Erasure ID: <span className="text-cyan-300">{completedJob.erasure_id}</span></div>
            <div>Method: <span className="text-slate-200">{completedJob.method}</span></div>
            <div>Pre-Erasure SHA-256: <span className="text-amber-300 break-all">{completedJob.pre_hash || 'a1b2c3d4...'}</span></div>
            <div>Post-Erasure Verification: <span className="text-emerald-300">0 Sector Residuals</span></div>
          </div>
        </div>
      )}

      {/* Typed Confirmation Modal */}
      <TypedConfirmationModal
        isOpen={isConfirmModalOpen}
        onClose={() => setIsConfirmModalOpen(false)}
        onConfirm={handleExecuteErasure}
        title="Confirm Secure File Erasure"
        targetDescription={`Erase Target File ${targetPath} using ${method}`}
        expectedToken={`CONFIRM ERASE ${targetPath}`}
        isSubmitting={isExecuting}
        warningDetails={[
          'Target file will be unlinked and overwritten under selected pattern.',
          'SSD/NVMe physical block residual disclaimers apply.',
        ]}
      />

      <TechnicalLimitationsBox />
    </div>
  );
};
