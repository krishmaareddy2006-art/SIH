import React from 'react';
import { Briefcase, User as UserIcon, LogOut, ShieldAlert, CheckCircle2, ChevronDown, Menu, Search } from 'lucide-react';
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
  const [searchQuery, setSearchQuery] = React.useState<string>('');

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
    <header className="h-14 bg-[#080D17]/95 backdrop-blur-md border-b border-[#1B2B40] px-4 md:px-6 flex items-center justify-between sticky top-0 z-30">
      {/* Left: Mobile Sidebar Trigger + Case Selector + Search */}
      <div className="flex items-center space-x-3 min-w-0">
        {onToggleMobileSidebar && (
          <button
            type="button"
            onClick={onToggleMobileSidebar}
            className="md:hidden text-[#94A3B8] hover:text-[#F1F5F9] p-1.5 rounded-lg hover:bg-[#121E30] transition-colors shrink-0"
            aria-label="Toggle navigation menu"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}

        {/* Enterprise Command-Center Active Case Selector */}
        <div className="flex items-center space-x-2 bg-[#0E1726] border border-[#1B2B40] hover:border-[#1683FF]/40 rounded-lg px-2.5 py-1.5 transition-all shadow-subtle min-w-0 max-w-[220px] sm:max-w-[320px] md:max-w-[420px]">
          <div className="flex items-center space-x-1.5 text-xs shrink-0">
            <Briefcase className="w-3.5 h-3.5 text-[#1683FF]" />
            <span className="hidden sm:inline font-mono text-[10px] uppercase font-bold tracking-wider text-[#64748B]">Case:</span>
          </div>

          {cases.length > 0 ? (
            <div className="relative flex items-center min-w-0 w-full">
              <select
                value={activeCase?.id || ''}
                onChange={e => setActiveCaseId(Number(e.target.value))}
                className="bg-transparent text-xs font-mono text-[#F1F5F9] font-medium pl-1 pr-5 py-0 appearance-none focus:outline-none transition-all cursor-pointer truncate w-full"
              >
                {cases.map(c => (
                  <option key={c.id} value={c.id} className="bg-[#0E1726] text-[#F1F5F9]">
                    #{c.case_number} — {c.title}
                  </option>
                ))}
              </select>
              <ChevronDown className="w-3 h-3 text-[#94A3B8] absolute right-0 pointer-events-none shrink-0" />
            </div>
          ) : (
            <span className="text-[11px] font-mono text-[#64748B] truncate">No Case Bound</span>
          )}
        </div>

        {/* Compact Enterprise Search Input */}
        <div className="hidden xl:flex items-center space-x-2 bg-[#0E1726] border border-[#1B2B40] focus-within:border-[#1683FF]/40 rounded-lg px-2.5 py-1 text-xs transition-all shrink-0">
          <Search className="w-3.5 h-3.5 text-[#64748B]" />
          <input
            type="text"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder="Search artifacts, hashes, evidence..."
            className="bg-transparent border-none outline-none text-xs text-[#F1F5F9] placeholder-[#64748B] w-48 font-sans"
          />
          <kbd className="text-[9px] font-mono text-[#64748B] bg-[#070B14] px-1.5 py-0.5 rounded border border-[#1B2B40]">
            /
          </kbd>
        </div>
      </div>

      {/* Right: Security Status Pill & User Identity */}
      <div className="flex items-center space-x-3 text-xs shrink-0">
        {/* System Safe Mode Indicator */}
        {isSafeMode ? (
          <div className="hidden sm:flex items-center space-x-1.5 bg-[#20C997]/10 border border-[#20C997]/30 text-[#20C997] px-2.5 py-1 rounded-full font-mono text-[11px] font-medium whitespace-nowrap shrink-0">
            <span className="w-1.5 h-1.5 rounded-full bg-[#20C997] animate-pulse shrink-0" />
            <CheckCircle2 className="w-3.5 h-3.5 text-[#20C997] shrink-0" />
            <span>Safe Mode</span>
          </div>
        ) : (
          <div className="flex items-center space-x-1.5 bg-[#FB7185]/15 border border-[#FB7185]/40 text-[#FB7185] px-2.5 py-1 rounded-full font-mono text-[11px] font-bold whitespace-nowrap shrink-0">
            <ShieldAlert className="w-3.5 h-3.5 text-[#FB7185] shrink-0" />
            <span>REAL HARDWARE OPS</span>
          </div>
        )}

        {/* User Profile or Sign In */}
        {isAuthenticated && user ? (
          <div className="flex items-center space-x-2.5 bg-[#0E1726] border border-[#1B2B40] pl-2 pr-1.5 py-1 rounded-lg shadow-subtle shrink-0">
            <div className="w-6 h-6 bg-[#1683FF]/10 text-[#16C7D9] border border-[#1683FF]/25 rounded flex items-center justify-center font-bold font-mono text-[11px]">
              {user.username.substring(0, 2).toUpperCase()}
            </div>
            <div className="hidden sm:block leading-tight">
              <p className="text-[10px] text-[#F2B84B] font-mono font-medium">
                {typeof user.role === 'object' && user.role !== null ? user.role.name : (user.role || 'Operator')}
              </p>
            </div>
            <button
              onClick={logout}
              title="Sign Out"
              className="text-[#94A3B8] hover:text-[#FB7185] p-1 rounded hover:bg-[#121E30] transition-colors ml-1 cursor-pointer"
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        ) : (
          <button
            onClick={onLoginClick}
            className="flex items-center space-x-1.5 bg-[#1683FF] hover:bg-[#0E5BD1] text-white font-semibold text-xs px-3.5 py-1.5 rounded-lg shadow-subtle transition-all cursor-pointer"
          >
            <UserIcon className="w-3.5 h-3.5" />
            <span>Sign In</span>
          </button>
        )}
      </div>
    </header>
  );
};
