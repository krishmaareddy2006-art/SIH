import React, { useState, useEffect } from 'react';
import { AlertTriangle, X, ShieldCheck } from 'lucide-react';

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

  useEffect(() => {
    if (isOpen) {
      setTypedInput('');
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const isMatched = typedInput.trim() === expectedToken;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isMatched && !isSubmitting) {
      onConfirm();
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div className="bg-slate-900 border border-red-500/40 rounded-2xl max-w-lg w-full p-6 shadow-2xl shadow-red-950/40 space-y-5">
        {/* Modal Header */}
        <div className="flex items-start justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div>
              <h3 id="modal-title" className="text-lg font-bold text-slate-100">
                {title}
              </h3>
              <p className="text-xs text-red-400 font-medium">MANDATORY DESTRUCTIVE ACTION CONFIRMATION</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 p-1 rounded-lg hover:bg-slate-800 transition-colors"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Warning Details */}
        <div className="space-y-3">
          <p className="text-sm text-slate-300">
            You are about to execute a destructive operation on:
          </p>
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs font-mono text-cyan-300 break-all">
            {targetDescription}
          </div>

          {warningDetails.length > 0 && (
            <div className="bg-red-950/50 border border-red-900/60 rounded-xl p-3 text-xs text-red-200 space-y-1">
              <p className="font-semibold text-red-300">Warning Notices:</p>
              <ul className="list-disc list-inside space-y-0.5">
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
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              To confirm, type <span className="font-mono bg-slate-800 px-1.5 py-0.5 rounded text-amber-300 select-all">{expectedToken}</span> below:
            </label>
            <input
              type="text"
              value={typedInput}
              onChange={e => setTypedInput(e.target.value)}
              placeholder={expectedToken}
              autoFocus
              className="w-full bg-slate-950 border border-slate-700 focus:border-red-500 focus:ring-1 focus:ring-red-500 rounded-xl px-3.5 py-2.5 text-sm font-mono text-slate-100 placeholder-slate-600 outline-none transition-all"
            />
          </div>

          {/* Action Controls */}
          <div className="flex items-center justify-end space-x-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-slate-300 hover:text-slate-100 bg-slate-800 hover:bg-slate-700 rounded-xl transition-all"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!isMatched || isSubmitting}
              className={`flex items-center space-x-2 px-5 py-2 text-xs font-bold rounded-xl transition-all shadow-lg ${
                isMatched && !isSubmitting
                  ? 'bg-red-600 hover:bg-red-500 text-white shadow-red-900/50 cursor-pointer'
                  : 'bg-slate-800 text-slate-500 border border-slate-700 cursor-not-allowed'
              }`}
            >
              <ShieldCheck className="w-4 h-4" />
              <span>{isSubmitting ? 'Executing...' : 'Confirm Execution'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
