import React, { useState, useEffect } from 'react';
import { FileSpreadsheet, Download, CheckCircle2, ShieldCheck } from 'lucide-react';
import { api } from '../services/api';
import { ForensicReportResponse, ReportPreviewResponse } from '../types';
import { useCase } from '../context/CaseContext';
import { useNotification } from '../context/NotificationContext';
import { LoadingSpinner, ErrorState } from '../components/common/StateViews';
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
      <div className="bg-[#111827] p-5 sm:p-6 rounded-2xl border border-[#253044] shadow-card flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-lg sm:text-xl font-bold text-[#F8FAFC] flex items-center">
            <FileSpreadsheet className="w-5 h-5 text-[#22D3EE] mr-2.5" />
            Court-Compliant Forensic Reporting & Compliance Hub
          </h2>
          <p className="text-xs text-[#94A3B8] mt-1">
            Automated PDF & JSON report generation, ReportLab engine, compliance language policy, and report SHA-256 audit chaining
          </p>
        </div>

        <button
          onClick={handleGenerateReport}
          disabled={isGenerating}
          className="flex items-center space-x-2 bg-[#22D3EE] hover:bg-[#67E8F9] text-[#080B14] font-bold text-xs px-5 py-2.5 rounded-xl shadow-subtle transition-all cursor-pointer disabled:opacity-50"
        >
          <ShieldCheck className="w-4 h-4" />
          <span>{isGenerating ? 'Building Report...' : 'Generate PDF & JSON Manifest'}</span>
        </button>
      </div>

      {/* 5-Point Classification Breakdown Matrix */}
      {previewData && (
        <div className="bg-[#111827] border border-[#253044] rounded-2xl p-5 sm:p-6 space-y-4 shadow-card text-xs">
          <div className="flex items-center justify-between border-b border-[#253044] pb-3">
            <h3 className="text-xs font-bold text-[#94A3B8] uppercase tracking-wider font-mono">
              5-Point Status Classification Matrix (Case #{previewData.case_number})
            </h3>
            <span className="font-mono text-[#22D3EE] text-[11px]">ISO/IEC 27037 Compliant</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-center">
            <div className="bg-[#0B0F19] p-4 rounded-xl border border-[#34D399]/30">
              <span className="text-[#34D399] font-bold block text-xs">Verified</span>
              <span className="text-2xl font-bold font-mono text-[#F8FAFC] mt-1 block">{previewData.classifications.verified}</span>
            </div>
            <div className="bg-[#0B0F19] p-4 rounded-xl border border-[#FBBF24]/30">
              <span className="text-[#FBBF24] font-bold block text-xs">Inconclusive</span>
              <span className="text-2xl font-bold font-mono text-[#F8FAFC] mt-1 block">{previewData.classifications.inconclusive}</span>
            </div>
            <div className="bg-[#0B0F19] p-4 rounded-xl border border-[#FB7185]/30">
              <span className="text-[#FB7185] font-bold block text-xs">Failed</span>
              <span className="text-2xl font-bold font-mono text-[#F8FAFC] mt-1 block">{previewData.classifications.failed}</span>
            </div>
            <div className="bg-[#0B0F19] p-4 rounded-xl border border-[#A78BFA]/30">
              <span className="text-[#A78BFA] font-bold block text-xs">Unsupported</span>
              <span className="text-2xl font-bold font-mono text-[#F8FAFC] mt-1 block">{previewData.classifications.unsupported}</span>
            </div>
            <div className="bg-[#0B0F19] p-4 rounded-xl border border-[#22D3EE]/30">
              <span className="text-[#22D3EE] font-bold block text-xs">Manual Review</span>
              <span className="text-2xl font-bold font-mono text-[#F8FAFC] mt-1 block">{previewData.classifications.manual_review}</span>
            </div>
          </div>
        </div>
      )}

      {/* Generated Report Card */}
      {generatedReport && (
        <div className="bg-[#111827] border border-[#34D399]/40 rounded-2xl p-6 space-y-4 shadow-card text-xs animate-fade-in">
          <div className="flex items-center justify-between border-b border-[#253044] pb-3">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-[#34D399]/10 text-[#34D399] rounded-xl">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <div>
                <h4 className="font-bold text-[#F8FAFC] text-sm">Generated Forensic Report & Manifest</h4>
                <p className="font-mono text-xs text-[#22D3EE]">Report ID: {generatedReport.report_id}</p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 font-mono bg-[#0B0F19] p-4 rounded-xl border border-[#253044]">
            <div>
              <span className="text-[#64748B] block text-[10px]">PDF SHA-256 Digest:</span>
              <span className="text-[#FBBF24] text-[11px] break-all">{generatedReport.pdf_sha256}</span>
            </div>
            <div>
              <span className="text-[#64748B] block text-[10px]">JSON Manifest SHA-256 Digest:</span>
              <span className="text-[#FBBF24] text-[11px] break-all">{generatedReport.json_sha256}</span>
            </div>
          </div>

          <div className="flex items-center justify-end space-x-3 pt-2">
            <a
              href={`/api/v1/cases/${activeCase.id}/reports/${generatedReport.report_id}/download/pdf`}
              target="_blank"
              rel="noreferrer"
              className="flex items-center space-x-2 bg-[#22D3EE] hover:bg-[#67E8F9] text-[#080B14] font-bold px-4 py-2 rounded-xl transition-all shadow-subtle cursor-pointer"
            >
              <Download className="w-4 h-4" />
              <span>Download PDF Report</span>
            </a>

            <a
              href={`/api/v1/cases/${activeCase.id}/reports/${generatedReport.report_id}/download/json`}
              target="_blank"
              rel="noreferrer"
              className="flex items-center space-x-2 bg-[#0B0F19] hover:bg-[#162032] text-[#22D3EE] font-bold px-4 py-2 rounded-xl border border-[#253044] transition-all cursor-pointer shadow-subtle"
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
