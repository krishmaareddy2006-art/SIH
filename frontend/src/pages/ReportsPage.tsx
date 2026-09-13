import React, { useState, useEffect } from 'react';
import { FileSpreadsheet, Download, Eye, CheckCircle2, ShieldCheck, AlertCircle, RefreshCw } from 'lucide-react';
import { api } from '../services/api';
import { ForensicReportResponse, ReportPreviewResponse } from '../types';
import { useCase } from '../context/CaseContext';
import { useNotification } from '../context/NotificationContext';
import { LoadingSpinner, ErrorState } from '../components/common/StateViews';
import { StatusBadge } from '../components/common/StatusBadge';
import { TechnicalLimitationsBox } from '../components/common/TechnicalLimitationsBox';

export const ReportsPage: React.FC = () => {
  const { activeCase } = useCase();
  const { addToast } = useNotification();

  const [previewData, setPreviewData] = useState<ReportPreviewResponse | null>(null);
  const [generatedReport, setGeneratedReport] = useState<ForensicReportResponse | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState('');

  const loadPreview = async () => {
    if (!activeCase) {
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    setError('');
    const res = await api.previewReport(activeCase.id);
    if (res.data) {
      setPreviewData(res.data);
    } else if (res.error) {
      setError(res.error.error.message);
    }
    setIsLoading(false);
  };

  useEffect(() => {
    loadPreview();
  }, [activeCase?.id]);

  const handleGenerateReport = async () => {
    if (!activeCase) return;
    setIsGenerating(true);
    const res = await api.generateReport(activeCase.id, { format: 'both' });
    setIsGenerating(false);

    if (res.data) {
      setGeneratedReport(res.data);
      addToast('success', 'Report Generated & Audited', `Court report ${res.data.report_id} generated cleanly.`);
    } else if (res.error) {
      addToast('error', 'Report Generation Failed', res.error.error.message);
    }
  };

  if (!activeCase) return <ErrorState code="NO_ACTIVE_CASE" message="Please select an active forensic case in the header to access report generation." />;
  if (isLoading && !previewData) return <LoadingSpinner message="Generating report preview matrix & summary statistics..." />;
  if (error) return <ErrorState code="REPORT_PREVIEW_ERROR" message={error} onRetry={loadPreview} />;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800 shadow-xl flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-extrabold text-slate-100 flex items-center">
            <FileSpreadsheet className="w-6 h-6 text-cyan-400 mr-2.5" />
            Court-Compliant Forensic Reporting & Compliance Hub
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Automated PDF & JSON report generation, ReportLab engine, compliance language policy, and report SHA-256 audit chaining
          </p>
        </div>

        <button
          onClick={handleGenerateReport}
          disabled={isGenerating}
          className="flex items-center space-x-2 bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs px-5 py-2.5 rounded-xl shadow-lg shadow-cyan-950 transition-all cursor-pointer"
        >
          <ShieldCheck className="w-4 h-4" />
          <span>{isGenerating ? 'Building Report...' : 'Generate PDF & JSON Manifest'}</span>
        </button>
      </div>

      {/* 5-Point Classification Breakdown Matrix */}
      {previewData && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-xl text-xs">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
              5-Point Status Classification Matrix (Case #{previewData.case_number})
            </h3>
            <span className="font-mono text-cyan-300">ISO/IEC 27037 Compliant</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-center">
            <div className="bg-slate-950 p-4 rounded-xl border border-emerald-500/30">
              <span className="text-emerald-400 font-bold block">Verified</span>
              <span className="text-2xl font-extrabold text-slate-100 mt-1 block">{previewData.classifications.verified}</span>
            </div>
            <div className="bg-slate-950 p-4 rounded-xl border border-amber-500/30">
              <span className="text-amber-400 font-bold block">Inconclusive</span>
              <span className="text-2xl font-extrabold text-slate-100 mt-1 block">{previewData.classifications.inconclusive}</span>
            </div>
            <div className="bg-slate-950 p-4 rounded-xl border border-red-500/30">
              <span className="text-red-400 font-bold block">Failed</span>
              <span className="text-2xl font-extrabold text-slate-100 mt-1 block">{previewData.classifications.failed}</span>
            </div>
            <div className="bg-slate-950 p-4 rounded-xl border border-purple-500/30">
              <span className="text-purple-400 font-bold block">Unsupported</span>
              <span className="text-2xl font-extrabold text-slate-100 mt-1 block">{previewData.classifications.unsupported}</span>
            </div>
            <div className="bg-slate-950 p-4 rounded-xl border border-blue-500/30">
              <span className="text-blue-400 font-bold block">Manual Review</span>
              <span className="text-2xl font-extrabold text-slate-100 mt-1 block">{previewData.classifications.manual_review}</span>
            </div>
          </div>
        </div>
      )}

      {/* Generated Report Card */}
      {generatedReport && (
        <div className="bg-slate-900 border border-emerald-500/40 rounded-2xl p-6 space-y-4 shadow-xl text-xs">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-xl">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <div>
                <h4 className="font-bold text-slate-100 text-sm">Generated Forensic Report & Manifest</h4>
                <p className="font-mono text-xs text-cyan-300">Report ID: {generatedReport.report_id}</p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 font-mono bg-slate-950 p-4 rounded-xl border border-slate-800">
            <div>
              <span className="text-slate-400 block text-[11px]">PDF SHA-256 Digest:</span>
              <span className="text-amber-300 text-[11px] break-all">{generatedReport.pdf_sha256}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[11px]">JSON Manifest SHA-256 Digest:</span>
              <span className="text-amber-300 text-[11px] break-all">{generatedReport.json_sha256}</span>
            </div>
          </div>

          <div className="flex items-center justify-end space-x-3 pt-2">
            <a
              href={`/api/v1/cases/${activeCase.id}/reports/${generatedReport.report_id}/download/pdf`}
              target="_blank"
              rel="noreferrer"
              className="flex items-center space-x-2 bg-cyan-600 hover:bg-cyan-500 text-white font-bold px-4 py-2 rounded-xl transition-all shadow-md shadow-cyan-950"
            >
              <Download className="w-4 h-4" />
              <span>Download PDF Report</span>
            </a>

            <a
              href={`/api/v1/cases/${activeCase.id}/reports/${generatedReport.report_id}/download/json`}
              target="_blank"
              rel="noreferrer"
              className="flex items-center space-x-2 bg-slate-800 hover:bg-slate-700 text-cyan-300 font-bold px-4 py-2 rounded-xl border border-slate-700 transition-all"
            >
              <Download className="w-4 h-4" />
              <span>Download JSON Manifest</span>
            </a>
          </div>
        </div>
      )}

      {/* Disclaimers */}
      <TechnicalLimitationsBox defaultExpanded={true} />
    </div>
  );
};
