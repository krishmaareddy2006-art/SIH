import React, { useState } from 'react';
import { Shield, Lock, User, AlertCircle, ArrowRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { useNotification } from '../context/NotificationContext';

export const LoginPage: React.FC<{ onSuccess?: () => void }> = ({ onSuccess }) => {
  const { login } = useAuth();
  const { addToast } = useNotification();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);

    const res = await api.login(username, password);
    setIsSubmitting(false);

    if (res.data) {
      login(res.data.access_token, res.data.user);
      addToast('success', 'Authentication Successful', `Welcome back, ${res.data.user.username}`);
      if (onSuccess) onSuccess();
    } else if (res.error) {
      setError(res.error.error.message || 'Invalid credentials.');
    }
  };

  const quickLoginAs = (user: string, pass: string) => {
    setUsername(user);
    setPassword(pass);
  };

  return (
    <div className="max-w-md w-full mx-auto my-8 p-6 bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <div className="inline-flex p-3 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-2xl text-slate-950 shadow-lg shadow-cyan-950">
          <Shield className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-extrabold tracking-wider text-slate-100 uppercase">
          FORENSIC<span className="text-cyan-400">SHIELD</span>
        </h2>
        <p className="text-xs text-slate-400 font-mono">Operator Authentication & Role Verification</p>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="bg-red-950/80 border border-red-500/40 p-3 rounded-xl text-xs text-red-200 flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-4 text-xs">
        <div>
          <label className="block text-slate-300 font-semibold mb-1.5">Operator Username</label>
          <div className="relative">
            <User className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
            <input
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              placeholder="e.g. admin, investigator1, operator1"
              required
              className="w-full bg-slate-950 border border-slate-700 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 rounded-xl pl-10 pr-3.5 py-2.5 text-slate-100 placeholder-slate-600 font-mono outline-none transition-all"
            />
          </div>
        </div>

        <div>
          <label className="block text-slate-300 font-semibold mb-1.5">Authentication Password</label>
          <div className="relative">
            <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="••••••••••••"
              required
              className="w-full bg-slate-950 border border-slate-700 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 rounded-xl pl-10 pr-3.5 py-2.5 text-slate-100 placeholder-slate-600 font-mono outline-none transition-all"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full flex items-center justify-center space-x-2 bg-cyan-600 hover:bg-cyan-500 text-white font-bold py-2.5 rounded-xl transition-all shadow-lg shadow-cyan-950 cursor-pointer disabled:opacity-50"
        >
          <span>{isSubmitting ? 'Authenticating...' : 'Sign In to Workspace'}</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </form>

      {/* Quick Test Lab Credentials */}
      <div className="border-t border-slate-800 pt-4 space-y-2 text-[11px]">
        <span className="text-slate-500 font-mono block text-center uppercase tracking-wider">Test Lab Quick Login:</span>
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => quickLoginAs('admin', 'AdminPass123!')}
            className="p-2 bg-slate-950 hover:bg-slate-800 border border-slate-800 rounded-lg text-slate-300 font-mono text-left"
          >
            <span className="text-cyan-400 font-semibold block">Administrator</span>
            <span>admin</span>
          </button>
          <button
            onClick={() => quickLoginAs('investigator1', 'InvestigatorPass123!')}
            className="p-2 bg-slate-950 hover:bg-slate-800 border border-slate-800 rounded-lg text-slate-300 font-mono text-left"
          >
            <span className="text-amber-400 font-semibold block">Investigator</span>
            <span>investigator1</span>
          </button>
        </div>
      </div>
    </div>
  );
};
