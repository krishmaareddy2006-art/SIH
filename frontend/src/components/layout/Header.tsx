import React from 'react';
import { Briefcase, User as UserIcon, LogOut, ShieldAlert, CheckCircle2, ChevronDown } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useCase } from '../../context/CaseContext';

interface HeaderProps {
  onLoginClick?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onLoginClick }) => {
  const { user, isAuthenticated, logout } = useAuth();
  const { cases, activeCase, setActiveCaseId } = useCase();
  const [isSafeMode, setIsSafeMode] = React.useState<boolean>(true);

  React.useEffect(() => {
    import('../../services/api').then(({ api }) => {
      api.getSystemHealth().then(res => {
        if (res.data) {
          setIsSafeMode(res.data.safe_mode);
        }
      });
    });
  }, []);

  return (
    <header className="h-16 bg-slate-900 border-b border-slate-800 px-6 flex items-center justify-between sticky top-0 z-30 shadow-sm">
      {/* Active Forensic Case Switcher */}
      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-2 text-xs font-semibold text-slate-300">
          <Briefcase className="w-4 h-4 text-cyan-400" />
          <span>Active Case:</span>
        </div>

        {cases.length > 0 ? (
          <div className="relative">
            <select
              value={activeCase?.id || ''}
              onChange={e => setActiveCaseId(Number(e.target.value))}
              className="bg-slate-950 border border-slate-700 text-xs font-mono text-cyan-300 rounded-xl px-3 py-1.5 pr-8 appearance-none focus:outline-none focus:border-cyan-500 transition-colors cursor-pointer"
            >
              {cases.map(c => (
                <option key={c.id} value={c.id}>
                  #{c.case_number} - {c.title}
                </option>
              ))}
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2.5 top-2.5 pointer-events-none" />
          </div>
        ) : (
          <span className="text-xs font-mono text-slate-500 bg-slate-950 px-2.5 py-1 rounded-lg">
            No Active Case Selected
          </span>
        )}
      </div>

      {/* Right Controls & User Profile */}
      <div className="flex items-center space-x-4 text-xs">
        {/* System Safe Mode Indicator */}
        {isSafeMode ? (
          <div className="flex items-center space-x-1.5 bg-emerald-950/60 border border-emerald-500/30 text-emerald-300 px-3 py-1 rounded-full font-mono font-medium">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Simulation Active</span>
          </div>
        ) : (
          <div className="flex items-center space-x-1.5 bg-red-950/60 border border-red-500/40 text-red-300 px-3 py-1 rounded-full font-mono font-bold animate-pulse">
            <ShieldAlert className="w-3.5 h-3.5 text-red-400" />
            <span>REAL MODE (Live Ops)</span>
          </div>
        )}

        {/* User Identity or Login Trigger */}
        {isAuthenticated && user ? (
          <div className="flex items-center space-x-3 bg-slate-950 border border-slate-800 px-3 py-1.5 rounded-xl">
            <div className="w-7 h-7 bg-cyan-600/20 text-cyan-400 border border-cyan-500/40 rounded-lg flex items-center justify-center font-bold font-mono text-xs">
              {user.username.substring(0, 2).toUpperCase()}
            </div>
            <div>
              <p className="font-semibold text-slate-200">{user.username}</p>
              <p className="text-[10px] text-amber-400 font-mono">{user.role?.name || 'Operator'}</p>
            </div>
            <button
              onClick={logout}
              title="Logout"
              className="text-slate-400 hover:text-red-400 p-1 rounded-lg hover:bg-slate-800 transition-colors ml-1"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <button
            onClick={onLoginClick}
            className="flex items-center space-x-2 bg-cyan-600 hover:bg-cyan-500 text-white font-semibold px-4 py-1.5 rounded-xl shadow-md shadow-cyan-950 transition-all"
          >
            <UserIcon className="w-3.5 h-3.5" />
            <span>Sign In</span>
          </button>
        )}
      </div>
    </header>
  );
};
