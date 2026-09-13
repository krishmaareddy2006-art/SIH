import React, { useState } from 'react';
import { Lock, LogIn, AlertCircle, KeyRound } from 'lucide-react';
import { api, setStoredToken, TokenResponse } from '../services/api';

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLoginSuccess: (tokenData: TokenResponse) => void;
}

export const LoginModal: React.FC<LoginModalProps> = ({ isOpen, onClose, onLoginSuccess }) => {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('AdminPass123!');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);

    const { data, error } = await api.login(username, password);
    setLoading(false);

    if (error) {
      setErrorMsg(error.error.message);
    } else if (data) {
      setStoredToken(data.access_token);
      onLoginSuccess(data);
      onClose();
    }
  };

  const handleQuickFill = (user: string, pass: string) => {
    setUsername(user);
    setPassword(pass);
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="glass-panel p-6 max-w-md w-full border border-dark-600">
        <div className="flex items-center gap-2 mb-4">
          <Lock className="w-5 h-5 text-cyber-teal" />
          <h3 className="text-lg font-bold text-white">ForensicShield Authentication</h3>
        </div>

        {errorMsg && (
          <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs font-mono mb-4 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-xs font-mono text-slate-400 mb-1">Username / Operator ID</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-dark-900 border border-dark-600 text-sm text-white font-mono focus:border-cyber-teal"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-mono text-slate-400 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-dark-900 border border-dark-600 text-sm text-white font-mono focus:border-cyber-teal"
              required
            />
          </div>

          <div className="pt-2 flex items-center justify-between">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg bg-dark-700 hover:bg-dark-600 text-slate-300 text-xs font-semibold"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 rounded-lg bg-cyber-teal hover:bg-teal-300 text-dark-900 text-xs font-bold flex items-center gap-1.5 shadow-md shadow-teal-500/20"
            >
              <LogIn className="w-4 h-4" />
              {loading ? 'Authenticating...' : 'Authenticate'}
            </button>
          </div>
        </form>

        {/* Quick Seed Accounts for Testing Roles */}
        <div className="mt-6 pt-4 border-t border-dark-700">
          <p className="text-[11px] font-mono text-slate-400 mb-2 flex items-center gap-1">
            <KeyRound className="w-3.5 h-3.5 text-cyber-teal" />
            Quick Switch RBAC Role Credentials:
          </p>
          <div className="grid grid-cols-2 gap-2 font-mono text-[11px]">
            <button
              onClick={() => handleQuickFill('admin', 'AdminPass123!')}
              className="p-1.5 rounded bg-dark-900 hover:bg-dark-700 text-slate-300 border border-dark-700 text-left"
            >
              <div className="font-semibold text-teal-400">admin</div>
              <div className="text-[10px] text-slate-400">Administrator</div>
            </button>

            <button
              onClick={() => handleQuickFill('investigator1', 'InvestigatorPass123!')}
              className="p-1.5 rounded bg-dark-900 hover:bg-dark-700 text-slate-300 border border-dark-700 text-left"
            >
              <div className="font-semibold text-cyan-400">investigator1</div>
              <div className="text-[10px] text-slate-400">Investigator</div>
            </button>

            <button
              onClick={() => handleQuickFill('operator1', 'OperatorPass123!')}
              className="p-1.5 rounded bg-dark-900 hover:bg-dark-700 text-slate-300 border border-dark-700 text-left"
            >
              <div className="font-semibold text-amber-400">operator1</div>
              <div className="text-[10px] text-slate-400">Operator</div>
            </button>

            <button
              onClick={() => handleQuickFill('viewer1', 'ViewerPass123!')}
              className="p-1.5 rounded bg-dark-900 hover:bg-dark-700 text-slate-300 border border-dark-700 text-left"
            >
              <div className="font-semibold text-slate-400">viewer1</div>
              <div className="text-[10px] text-slate-500">Viewer</div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
