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

    try {
      const res = await api.login(username, password);
      setIsSubmitting(false);

      if (res.data) {
        const usernameStr = res.data.user?.username || res.data.username || username;
        const userObj = res.data.user || {
          id: (res.data as any).id || 1,
          username: usernameStr,
          email: (res.data as any).email || `${usernameStr}@forensicshield.local`,
          role: res.data.role || 'Operator',
          permissions: res.data.permissions || [],
          is_active: true,
        };

        login(res.data.access_token, userObj);
        addToast('success', 'Authentication Successful', `Welcome back, ${usernameStr}`);
        if (onSuccess) {
          onSuccess();
        }
      } else if (res.error) {
        setError(res.error.error?.message || 'Invalid username or password.');
      }
    } catch (err: any) {
      setIsSubmitting(false);
      setError(err?.message || 'Authentication error. Please check credentials.');
    }
  };

  const quickLoginAs = (user: string, pass: string) => {
    setUsername(user);
    setPassword(pass);
  };

  return (
    <div className="max-w-md w-full mx-auto my-8 p-6 bg-[#111827] border border-[#253044] rounded-2xl shadow-elevated space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <div className="inline-flex p-3 bg-[#22D3EE]/10 border border-[#22D3EE]/30 rounded-2xl text-[#22D3EE] shadow-subtle">
          <Shield className="w-7 h-7" />
        </div>
        <h2 className="text-lg font-extrabold tracking-wider text-[#F8FAFC] uppercase font-sans">
          FORENSIC<span className="text-[#22D3EE]">SHIELD</span>
        </h2>
        <p className="text-xs text-[#94A3B8] font-mono">Operator Authentication & Role Verification</p>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="bg-[#1A0E13] border border-[#FB7185]/40 p-3 rounded-xl text-xs text-[#FB7185] flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 text-[#FB7185] shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-4 text-xs">
        <div>
          <label className="block text-[#94A3B8] font-medium mb-1.5">Operator Username</label>
          <div className="relative">
            <User className="w-4 h-4 text-[#64748B] absolute left-3.5 top-3" />
            <input
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              placeholder="e.g. admin, investigator1, operator1"
              required
              className="w-full bg-[#0B0F19] border border-[#253044] focus:border-[#22D3EE] focus:ring-1 focus:ring-[#22D3EE] rounded-xl pl-10 pr-3.5 py-2.5 text-[#F8FAFC] placeholder-[#64748B] font-mono outline-none transition-all"
            />
          </div>
        </div>

        <div>
          <label className="block text-[#94A3B8] font-medium mb-1.5">Authentication Password</label>
          <div className="relative">
            <Lock className="w-4 h-4 text-[#64748B] absolute left-3.5 top-3" />
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="••••••••••••"
              required
              className="w-full bg-[#0B0F19] border border-[#253044] focus:border-[#22D3EE] focus:ring-1 focus:ring-[#22D3EE] rounded-xl pl-10 pr-3.5 py-2.5 text-[#F8FAFC] placeholder-[#64748B] font-mono outline-none transition-all"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full flex items-center justify-center space-x-2 bg-[#22D3EE] hover:bg-[#67E8F9] text-[#080B14] font-bold py-2.5 rounded-xl transition-all shadow-subtle cursor-pointer disabled:opacity-50"
        >
          <span>{isSubmitting ? 'Authenticating...' : 'Sign In to Workspace'}</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </form>

      {/* Quick Test Lab Credentials */}
      <div className="border-t border-[#253044] pt-4 space-y-2 text-[11px]">
        <span className="text-[#64748B] font-mono block text-center uppercase tracking-wider text-[10px]">
          Test Lab Quick Login:
        </span>
        <div className="grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={() => quickLoginAs('admin', 'AdminPass123!')}
            className="p-2.5 bg-[#0B0F19] hover:bg-[#162032] border border-[#253044] rounded-xl text-[#94A3B8] hover:text-[#F8FAFC] font-mono text-left transition-all cursor-pointer"
          >
            <span className="text-[#22D3EE] font-semibold block text-xs">Administrator</span>
            <span className="text-[10px] text-[#64748B]">admin</span>
          </button>
          <button
            type="button"
            onClick={() => quickLoginAs('investigator1', 'InvestigatorPass123!')}
            className="p-2.5 bg-[#0B0F19] hover:bg-[#162032] border border-[#253044] rounded-xl text-[#94A3B8] hover:text-[#F8FAFC] font-mono text-left transition-all cursor-pointer"
          >
            <span className="text-[#FBBF24] font-semibold block text-xs">Investigator</span>
            <span className="text-[10px] text-[#64748B]">investigator1</span>
          </button>
        </div>
      </div>
    </div>
  );
};
