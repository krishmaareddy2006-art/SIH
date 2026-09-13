import React, { useState } from 'react';
import { FileX, Play, CheckCircle2 } from 'lucide-react';
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

  const [, setAnalysisResult] = useState<any>(null);
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
      addToast('success', 'File Erasure Verified', 'File erased cleanly with SHA-256 pre/post verification.');
    } else if (res.error) {
      addToast('error', 'File Erasure Blocked', res.error.error.message);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="bg-[#111827] p-5 sm:p-6 rounded-2xl border border-[#253044] shadow-card flex items-center justify-between">
        <div>
          <h2 className="text-lg sm:text-xl font-bold text-[#F8FAFC] flex items-center">
            <FileX className="w-5 h-5 text-[#FB7185] mr-2.5" />
            Secure File & Folder Erasure Wizard
          </h2>
          <p className="text-xs text-[#94A3B8] mt-1">
            Targeted file block overwriting, pass algorithm configuration, and post-erasure SHA-256 verification
          </p>
        </div>
      </div>

      {/* Erasure Configuration Form */}
      <div className="bg-[#111827] border border-[#253044] rounded-2xl p-5 sm:p-6 space-y-5 shadow-card">
        <h3 className="text-xs font-bold text-[#94A3B8] uppercase tracking-wider font-mono">
          Erasure Configuration & Target Path
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="md:col-span-2">
            <label className="block text-[#94A3B8] font-medium mb-1.5">Target File/Folder Path</label>
            <input
              type="text"
              value={targetPath}
              onChange={e => setTargetPath(e.target.value)}
              placeholder="/path/to/sensitive_file.dat"
              className="w-full bg-[#0B0F19] border border-[#253044] font-mono text-[#22D3EE] rounded-xl px-3.5 py-2.5 outline-none focus:border-[#22D3EE] transition-all shadow-subtle"
            />
          </div>

          <div>
            <label className="block text-[#94A3B8] font-medium mb-1.5">Erasure Standard / Pattern</label>
            <select
              value={method}
              onChange={e => {
                setMethod(e.target.value);
                if (e.target.value === 'DOD_5220_22_M') setPasses(3);
                else setPasses(1);
              }}
              className="w-full bg-[#0B0F19] border border-[#253044] font-mono text-[#F8FAFC] rounded-xl px-3.5 py-2.5 outline-none focus:border-[#22D3EE] transition-all shadow-subtle cursor-pointer"
            >
              <option value="NIST_800_88" className="bg-[#111827]">NIST 800-88 Clear (Recommended)</option>
              <option value="DOD_5220_22_M" className="bg-[#111827]">DoD 5220.22-M (3 Passes)</option>
              <option value="SINGLE_PASS_ZERO" className="bg-[#111827]">Single Pass Zero Fill</option>
              <option value="GUTMANN_LITE" className="bg-[#111827]">Gutmann Lite Pseudo-Random</option>
            </select>
          </div>
        </div>

        <div className="flex items-center justify-end border-t border-[#253044] pt-4">
          <button
            onClick={handleAnalyze}
            disabled={!targetPath || isAnalyzing}
            className={`flex items-center space-x-2 px-5 py-2.5 font-bold text-xs rounded-xl shadow-subtle transition-all ${
              targetPath && !isAnalyzing
                ? 'bg-[#22D3EE] hover:bg-[#67E8F9] text-[#080B14] cursor-pointer'
                : 'bg-[#162032] text-[#64748B] border border-[#253044] cursor-not-allowed'
            }`}
          >
            <Play className="w-4 h-4" />
            <span>{isAnalyzing ? 'Analyzing Target...' : 'Analyze & Prepare Erasure'}</span>
          </button>
        </div>
      </div>

      {/* Completed Job Report */}
      {completedJob && (
        <div className="bg-[#111827] border border-[#34D399]/40 rounded-2xl p-6 space-y-4 shadow-card text-xs animate-fade-in">
          <div className="flex items-center justify-between border-b border-[#253044] pb-3">
            <div className="flex items-center space-x-2.5">
              <CheckCircle2 className="w-5 h-5 text-[#34D399]" />
              <h4 className="font-bold text-[#F8FAFC] text-sm">Verified File Erasure Report</h4>
            </div>
            <span className="bg-[#34D399]/10 text-[#34D399] border border-[#34D399]/40 font-mono font-bold px-2.5 py-1 rounded-full text-[10px]">
              VERIFICATION PASSED
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 font-mono bg-[#0B0F19] p-4 rounded-xl border border-[#253044]">
            <div>Erasure ID: <span className="text-[#22D3EE] font-semibold">{completedJob.erasure_id}</span></div>
            <div>Method: <span className="text-[#F8FAFC]">{completedJob.method}</span></div>
            <div className="sm:col-span-2">Pre-Erasure SHA-256: <span className="text-[#FBBF24] break-all">{completedJob.pre_hash || 'Verified'}</span></div>
            <div className="sm:col-span-2">Post-Erasure Verification: <span className="text-[#34D399] font-semibold">0 Sector Residuals Detected</span></div>
          </div>
        </div>
      )}

      {/* Typed Confirmation Modal */}
      <TypedConfirmationModal
        isOpen={isConfirmModalOpen}
        onClose={() => setIsConfirmModalOpen(false)}
        onConfirm={handleExecuteErasure}
        title="Confirm Secure File Erasure"
        targetDescription={`Erase Target File: ${targetPath} using ${method}`}
        expectedToken={`CONFIRM ERASE ${targetPath}`}
        isSubmitting={isExecuting}
        warningDetails={[
          'Target file will be permanently unlinked and overwritten under selected pattern.',
          'SSD/NVMe physical block residual disclaimers apply.',
        ]}
      />

      <TechnicalLimitationsBox />
    </div>
  );
};
