import React from 'react';
import { Shield, ShieldAlert, HardDrive, UserCheck, LogOut, Lock } from 'lucide-react';
import { SystemStatus, UserProfile } from '../services/api';

interface HeaderProps {
  status: SystemStatus | null;
  user: UserProfile | null;
  onLogout: () => void;
  onOpenLogin: () => void;
}

export const Header: React.FC<HeaderProps> = ({ status, user, onLogout, onOpenLogin }) => {
  return (
    <header className="border-b border-dark-600/60 bg-dark-900/90 backdrop-blur sticky top-0 z-50 py-4 px-6">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
        {/* Brand Logo & Name */}
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-tr from-cyan-500 to-teal-400 text-dark-900 shadow-lg shadow-teal-500/20">
            <Shield className="w-7 h-7 stroke-[2.5]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-white font-mono">
                FORENSIC<span className="text-cyber-teal">SHIELD</span>
              </h1>
              <span className="text-xs px-2 py-0.5 rounded-full bg-dark-700 text-slate-400 font-mono">
                v{status?.version || '0.1.0'}
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Enterprise Digital Forensics & Security Core
            </p>
          </div>
        </div>

        {/* Security Feature Badges & User Status */}
        <div className="flex items-center gap-3">
          {/* SAFE MODE Indicator */}
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border font-mono text-xs ${
            status?.safe_mode 
              ? 'bg-teal-500/10 border-teal-500/40 text-teal-300' 
              : 'bg-rose-500/10 border-rose-500/40 text-rose-300'
          }`}>
            <ShieldAlert className="w-4 h-4" />
            <span>SAFE_MODE: <strong>{status?.safe_mode ? 'ENABLED (PROTECTED)' : 'DISABLED'}</strong></span>
          </div>

          {/* REAL DEVICE OPERATIONS Indicator */}
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border font-mono text-xs ${
            !status?.real_device_operations 
              ? 'bg-amber-500/10 border-amber-500/40 text-amber-300' 
              : 'bg-rose-500/10 border-rose-500/40 text-rose-300'
          }`}>
            <HardDrive className="w-4 h-4" />
            <span>REAL_DEVICE_OPS: <strong>{status?.real_device_operations ? 'ENABLED' : 'DISABLED (SAFE)'}</strong></span>
          </div>

          {/* User Session Status & Controls */}
          {user ? (
            <div className="flex items-center gap-2 pl-2 border-l border-dark-700">
              <div className="flex flex-col text-right">
                <span className="text-xs font-semibold text-white font-mono flex items-center gap-1 justify-end">
                  <UserCheck className="w-3.5 h-3.5 text-cyber-teal" />
                  {user.username}
                </span>
                <span className="text-[10px] text-cyber-teal font-mono font-semibold">
                  [{typeof user.role === 'object' ? (user.role as any).name : user.role}]
                </span>
              </div>
              <button
                onClick={onLogout}
                className="p-2 rounded-lg bg-dark-800 hover:bg-rose-500/20 text-slate-400 hover:text-rose-300 border border-dark-600 transition-colors"
                title="Logout Session"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <button
              onClick={onOpenLogin}
              className="px-3.5 py-1.5 rounded-lg bg-cyber-teal hover:bg-teal-300 text-dark-900 font-semibold text-xs flex items-center gap-1.5 transition-colors shadow-md shadow-teal-500/20"
            >
              <Lock className="w-3.5 h-3.5" />
              Operator Login
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
