import React, { useState } from 'react';
import { ShieldAlert, ChevronDown, ChevronUp, Cpu, HardDrive, FileSpreadsheet, Binary } from 'lucide-react';

interface TechnicalLimitationsBoxProps {
  title?: string;
  defaultExpanded?: boolean;
}

export const TechnicalLimitationsBox: React.FC<TechnicalLimitationsBoxProps> = ({
  title = 'Forensic Boundaries & Technical Disclaimers',
  defaultExpanded = false,
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  return (
    <div className="bg-[#111827] border border-[#253044] rounded-xl overflow-hidden text-xs my-4 shadow-subtle">
      {/* Header Bar */}
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full bg-[#111827] hover:bg-[#162032] px-4 py-3 flex items-center justify-between text-[#94A3B8] transition-colors cursor-pointer"
      >
        <div className="flex items-center space-x-2.5 font-medium text-[#F8FAFC]">
          <ShieldAlert className="w-4 h-4 text-[#FBBF24]" />
          <span className="text-xs">{title}</span>
        </div>
        <div className="flex items-center space-x-1.5 text-[#22D3EE] font-mono text-[11px]">
          <span>{isExpanded ? 'Hide Scope' : 'Review Boundaries'}</span>
          {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </div>
      </button>

      {/* Collapsible Content */}
      {isExpanded && (
        <div className="p-4 space-y-3 bg-[#0B0F19] border-t border-[#253044] text-[#94A3B8] leading-relaxed">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="bg-[#111827] p-3 rounded-xl border border-[#253044] space-y-1">
              <div className="flex items-center text-[#FBBF24] font-semibold text-[11px] mb-1">
                <HardDrive className="w-3.5 h-3.5 mr-1.5 text-[#FBBF24]" />
                HDD vs. SSD/Flash Media (FTL & Wear Leveling)
              </div>
              <p className="text-[#94A3B8] text-[11px]">
                Magnetic HDDs support direct physical sector block overwriting. SSD, NVMe, and USB flash devices employ Flash Translation Layers (FTL), garbage collection, and wear leveling algorithms. Logical sector overwriting does not guarantee sanitization of unmapped over-provisioned physical NAND flash blocks.
              </p>
            </div>

            <div className="bg-[#111827] p-3 rounded-xl border border-[#253044] space-y-1">
              <div className="flex items-center text-[#22D3EE] font-semibold text-[11px] mb-1">
                <FileSpreadsheet className="w-3.5 h-3.5 mr-1.5 text-[#22D3EE]" />
                Filesystem Support & Metadata Limits
              </div>
              <p className="text-[#94A3B8] text-[11px]">
                Automated filesystem analysis is scoped to FAT32, NTFS, and Ext4 structures. Heavily damaged, encrypted, or unknown volume metadata entries are flagged for <span className="text-[#A78BFA] font-mono">Unsupported / Manual Review</span> rather than unverified guessing.
              </p>
            </div>

            <div className="bg-[#111827] p-3 rounded-xl border border-[#253044] space-y-1">
              <div className="flex items-center text-[#34D399] font-semibold text-[11px] mb-1">
                <Binary className="w-3.5 h-3.5 mr-1.5 text-[#34D399]" />
                Non-Contiguous File Fragmentation
              </div>
              <p className="text-[#94A3B8] text-[11px]">
                Signature-based carving assumes contiguous block allocation between header and footer boundaries. Carving highly fragmented files without allocation extents produces corrupted byte streams and yields lower confidence levels.
              </p>
            </div>

            <div className="bg-[#111827] p-3 rounded-xl border border-[#253044] space-y-1">
              <div className="flex items-center text-[#67E8F9] font-semibold text-[11px] mb-1">
                <Cpu className="w-3.5 h-3.5 mr-1.5 text-[#67E8F9]" />
                Validation Scoring & Compliance Phrasing
              </div>
              <p className="text-[#94A3B8] text-[11px]">
                Validation scores (0-100) represent an empirical structural integrity index and are NOT statistical probabilities of truth. Under ForensicShield compliance policy, absolute claims (&quot;100% unrecoverable&quot;) are strictly excluded.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
