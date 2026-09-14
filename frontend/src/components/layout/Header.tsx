import React from 'react';
import { Briefcase, User as UserIcon, LogOut, ShieldAlert, CheckCircle2, ChevronDown, Menu } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useCase } from '../../context/CaseContext';

interface HeaderProps {
  onLoginClick?: () => void;
  onToggleMobileSidebar?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onLoginClick, onToggleMobileSidebar }) => {
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
    <header className="h-14 bg-[#080B14]/90 backdrop-blur-md border-b border-[#253044] px-4 md:px-6 flex items-center justify-between sticky top-0 z-30">
      {/* Left: Mobile Sidebar Trigger + Case Selector */}
      <div className="flex items-center space-x-3">
        {onToggleMobileSidebar && (
          <button
            type="button"
            onClick={onToggleMobileSidebar}
            className="md:hidden text-[#94A3B8] hover:text-[#F8FAFC] p-1.5 rounded-lg hover:bg-[#162032] transition-colors"
            aria-label="Toggle navigation menu"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}

        <div className="hidden sm:flex items-center space-x-2 text-xs text-[#94A3B8]">
          <Briefcase className="w-3.5 h-3.5 text-[#22D3EE]" />
          <span className="font-medium">Active Case:</span>
        </div>

        {cases.length > 0 ? (
          <div className="relative">
            <select
              value={activeCase?.id || ''}
              onChange={e => setActiveCaseId(Number(e.target.value))}
              className="bg-[#0B0F19] hover:bg-[#111827] border border-[#253044] hover:border-[#22D3EE]/50 text-xs font-mono text-[#22D3EE] rounded-lg pl-2.5 pr-7 py-1.5 appearance-none focus:outline-none focus:border-[#22D3EE] transition-all cursor-pointer shadow-subtle"
            >
              {cases.map(c => (
                <option key={c.id} value={c.id} className="bg-[#111827] text-[#F8FAFC]">
                  #{c.case_number} — {c.title}
                </option>
              ))}
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-[#64748B] absolute right-2 top-2 pointer-events-none" />
          </div>
        ) : (
          <span className="text-[11px] font-mono text-[#64748B] bg-[#0B0F19] border border-[#253044] px-2.5 py-1 rounded-md">
            No Case Bound
          </span>
        )}
      </div>

      {/* Right: Security Status Pill & User Identity */}
      <div className="flex items-center space-x-3 text-xs">
        {/* System Safe Mode Indicator */}
        {isSafeMode ? (
          <div className="hidden sm:flex items-center space-x-1.5 bg-[#34D399]/10 border border-[#34D399]/30 text-[#34D399] px-2.5 py-1 rounded-full font-mono text-[11px] font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-[#34D399] animate-pulse shrink-0" />
            <CheckCircle2 className="w-3.5 h-3.5 text-[#34D399]" />
            <span>Safe Mode</span>
          </div>
        ) : (
          <div className="flex items-center space-x-1.5 bg-[#FB7185]/15 border border-[#FB7185]/40 text-[#FB7185] px-2.5 py-1 rounded-full font-mono text-[11px] font-bold animate-pulse">
            <ShieldAlert className="w-3.5 h-3.5 text-[#FB7185]" />
            <span>REAL HARDWARE OPS</span>
          </div>
        )}

        {/* User Profile or Sign In */}
        {isAuthenticated && user ? (
          <div className="flex items-center space-x-2.5 bg-[#111827] border border-[#253044] pl-2 pr-1.5 py-1 rounded-xl shadow-subtle">
            <div className="w-6 h-6 bg-[#22D3EE]/15 text-[#22D3EE] border border-[#22D3EE]/30 rounded-lg flex items-center justify-center font-bold font-mono text-[11px]">
              {user.username.substring(0, 2).toUpperCase()}
            </div>
            <div className="hidden sm:block leading-tight">
              <p className="text-[10px] text-[#FBBF24] font-mono">
                {typeof user.role === 'object' && user.role !== null ? user.role.name : (user.role || 'Operator')}
              </p>
            </div>
            <button
              onClick={logout}
              title="Sign Out"
              className="text-[#94A3B8] hover:text-[#FB7185] p-1 rounded-lg hover:bg-[#162032] transition-colors ml-1 cursor-pointer"
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        ) : (
          <button
            onClick={onLoginClick}
            className="flex items-center space-x-1.5 bg-[#22D3EE] hover:bg-[#67E8F9] text-[#080B14] font-semibold text-xs px-3 py-1.5 rounded-lg shadow-subtle transition-all cursor-pointer"
          >
            <UserIcon className="w-3.5 h-3.5" />
            <span>Sign In</span>
          </button>
        )}
      </div>
    </header>
  );
};
