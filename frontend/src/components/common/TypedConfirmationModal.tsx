import React, { useState, useEffect } from 'react';
import { AlertTriangle, X, ShieldCheck, Copy, Check } from 'lucide-react';

interface TypedConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  targetDescription: string;
  expectedToken: string;
  isSubmitting?: boolean;
  warningDetails?: string[];
}

export const TypedConfirmationModal: React.FC<TypedConfirmationModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  targetDescription,
  expectedToken,
  isSubmitting = false,
  warningDetails = [],
}) => {
  const [typedInput, setTypedInput] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setTypedInput('');
      setCopied(false);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const isMatched = typedInput.trim() === expectedToken;

  const handleCopyToken = () => {
    navigator.clipboard.writeText(expectedToken);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isMatched && !isSubmitting) {
      onConfirm();
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#080B14]/85 backdrop-blur-md animate-fade-in"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div className="bg-[#111827] border border-[#253044] rounded-2xl max-w-lg w-full p-6 shadow-elevated space-y-5">
        {/* Modal Header */}
        <div className="flex items-start justify-between border-b border-[#253044] pb-4">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-[#FB7185]/10 border border-[#FB7185]/30 rounded-xl text-[#FB7185]">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <h3 id="modal-title" className="text-base font-bold text-[#F8FAFC]">
                {title}
              </h3>
              <p className="text-[11px] text-[#FB7185] font-mono font-medium tracking-wide">
                MANDATORY SECURITY CONFIRMATION
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-[#94A3B8] hover:text-[#F8FAFC] p-1.5 rounded-lg hover:bg-[#162032] transition-colors"
            aria-label="Close modal"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Target Details */}
        <div className="space-y-3 text-xs">
          <p className="text-[#94A3B8]">
            You are about to execute a destructive forensic operation on:
          </p>
          <div className="bg-[#0B0F19] border border-[#253044] rounded-xl p-3 font-mono text-[#22D3EE] break-all select-all">
            {targetDescription}
          </div>

          {warningDetails.length > 0 && (
            <div className="bg-[#1C1014] border border-[#FB7185]/30 rounded-xl p-3 text-[11px] text-[#FB7185] space-y-1">
              <p className="font-semibold uppercase tracking-wider text-[10px]">Safety Notices:</p>
              <ul className="list-disc list-inside space-y-0.5 text-[#FDA4AF] pl-0.5">
                {warningDetails.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Form Input */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="block text-xs font-medium text-[#94A3B8]">
                Type the verification token below:
              </label>
              <button
                type="button"
                onClick={handleCopyToken}
                className="flex items-center space-x-1 text-[11px] text-[#22D3EE] hover:text-[#67E8F9] font-mono cursor-pointer"
              >
                {copied ? <Check className="w-3 h-3 text-[#34D399]" /> : <Copy className="w-3 h-3" />}
                <span>{copied ? 'Copied' : 'Copy token'}</span>
              </button>
            </div>
            <div className="p-2 bg-[#0B0F19] border border-[#253044] rounded-lg font-mono text-[11px] text-[#FBBF24] mb-2 select-all break-all">
              {expectedToken}
            </div>
            <input
              type="text"
              value={typedInput}
              onChange={e => setTypedInput(e.target.value)}
              placeholder={expectedToken}
              autoFocus
              className="w-full bg-[#0B0F19] border border-[#253044] focus:border-[#FB7185] focus:ring-1 focus:ring-[#FB7185] rounded-xl px-3.5 py-2.5 text-xs font-mono text-[#F8FAFC] placeholder-[#64748B] outline-none transition-all"
            />
          </div>

          {/* Action Controls */}
          <div className="flex items-center justify-end space-x-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-[#94A3B8] hover:text-[#F8FAFC] bg-[#0B0F19] hover:bg-[#162032] border border-[#253044] rounded-xl transition-all cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!isMatched || isSubmitting}
              className={`flex items-center space-x-2 px-5 py-2 text-xs font-semibold rounded-xl transition-all shadow-subtle ${
                isMatched && !isSubmitting
                  ? 'bg-[#FB7185] hover:bg-[#E11D48] text-white cursor-pointer font-bold'
                  : 'bg-[#162032] text-[#64748B] border border-[#253044] cursor-not-allowed'
              }`}
            >
              <ShieldCheck className="w-4 h-4" />
              <span>{isSubmitting ? 'Executing Operation...' : 'Confirm Execution'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
