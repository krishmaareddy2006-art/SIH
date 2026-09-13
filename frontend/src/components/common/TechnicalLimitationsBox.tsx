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
    <div className="bg-amber-950/20 border border-amber-500/30 rounded-xl overflow-hidden text-xs my-4">
      {/* Header Bar */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full bg-amber-950/40 hover:bg-amber-950/60 px-4 py-3 flex items-center justify-between text-amber-200 transition-colors"
      >
        <div className="flex items-center space-x-2 font-semibold text-amber-300">
          <ShieldAlert className="w-4 h-4 text-amber-400" />
          <span>{title}</span>
        </div>
        <div className="flex items-center space-x-1 text-amber-400 font-mono text-[11px]">
          <span>{isExpanded ? 'Hide Details' : 'Show Details'}</span>
          {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {/* Collapsible Content */}
      {isExpanded && (
        <div className="p-4 space-y-3 bg-slate-950/60 border-t border-amber-500/20 text-slate-300 leading-relaxed">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800 space-y-1">
              <div className="flex items-center text-amber-300 font-semibold mb-1">
                <HardDrive className="w-3.5 h-3.5 mr-1.5 text-amber-400" />
                HDD vs. SSD/Flash Media (FTL & Wear Leveling)
              </div>
              <p className="text-slate-400 text-[11px]">
                Magnetic HDDs support direct physical sector block overwriting. SSD, NVMe, and USB flash devices employ Flash Translation Layers (FTL), garbage collection, and wear leveling algorithms. Logical sector overwriting does not guarantee sanitization of unmapped over-provisioned physical NAND flash blocks.
              </p>
            </div>

            <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800 space-y-1">
              <div className="flex items-center text-cyan-300 font-semibold mb-1">
                <FileSpreadsheet className="w-3.5 h-3.5 mr-1.5 text-cyan-400" />
                Filesystem Support & Metadata Limits
              </div>
              <p className="text-slate-400 text-[11px]">
                Automated filesystem analysis is scoped to FAT32, NTFS, and Ext4 structures. Heavily damaged, encrypted, or unknown volume metadata entries are flagged for <span className="text-purple-300 font-medium">Unsupported / Manual Review</span> rather than unverified guessing.
              </p>
            </div>

            <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800 space-y-1">
              <div className="flex items-center text-emerald-300 font-semibold mb-1">
                <Binary className="w-3.5 h-3.5 mr-1.5 text-emerald-400" />
                Non-Contiguous File Fragmentation
              </div>
              <p className="text-slate-400 text-[11px]">
                Signature-based carving assumes contiguous block allocation between header and footer boundaries. Carving highly fragmented files without allocation extents produces corrupted byte streams and yields lower confidence levels.
              </p>
            </div>

            <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800 space-y-1">
              <div className="flex items-center text-indigo-300 font-semibold mb-1">
                <Cpu className="w-3.5 h-3.5 mr-1.5 text-indigo-400" />
                Validation Scoring & Compliance Phrasing
              </div>
              <p className="text-slate-400 text-[11px]">
                Validation scores (0-100) represent an empirical structural integrity index and are NOT statistical probabilities of truth. Under ForensicShield compliance policy, absolute claims ("100% unrecoverable") are strictly excluded.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
