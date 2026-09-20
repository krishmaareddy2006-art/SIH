import React from 'react';
import {
  LayoutDashboard,
  Briefcase,
  HardDrive,
  Flame,
  FileX,
  UploadCloud,
  FileSearch,
  Activity,
  History,
  FileSpreadsheet,
  Settings,
  Shield,
  ChevronRight,
  X,
} from 'lucide-react';

export interface NavItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  path: string;
  category: 'core' | 'operations' | 'compliance';
}

interface SidebarProps {
  activeTab: string;
  onTabChange: (tabId: string) => void;
  onCloseMobile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onTabChange, onCloseMobile }) => {
  const navItems: NavItem[] = [
    { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard className="w-4 h-4" />, path: '/', category: 'core' },
    { id: 'cases', label: 'Cases Workspace', icon: <Briefcase className="w-4 h-4" />, path: '/cases', category: 'core' },
    { id: 'devices', label: 'Storage Devices', icon: <HardDrive className="w-4 h-4" />, path: '/devices', category: 'core' },

    { id: 'sanitization', label: 'Drive Sanitization', icon: <Flame className="w-4 h-4" />, path: '/sanitization', category: 'operations' },
    { id: 'erasure', label: 'Secure File Erasure', icon: <FileX className="w-4 h-4" />, path: '/erasure', category: 'operations' },
    { id: 'evidence', label: 'Evidence Intake', icon: <UploadCloud className="w-4 h-4" />, path: '/evidence', category: 'operations' },
    { id: 'recovery', label: 'Recovery & Carving', icon: <FileSearch className="w-4 h-4" />, path: '/recovery', category: 'operations' },

    { id: 'jobs', label: 'Background Jobs', icon: <Activity className="w-4 h-4" />, path: '/jobs', category: 'compliance' },
    { id: 'audit', label: 'Audit Chain Ledger', icon: <History className="w-4 h-4" />, path: '/audit', category: 'compliance' },
    { id: 'reports', label: 'Reports & Compliance', icon: <FileSpreadsheet className="w-4 h-4" />, path: '/reports', category: 'compliance' },
    { id: 'settings', label: 'Security & Policy', icon: <Settings className="w-4 h-4" />, path: '/settings', category: 'compliance' },
  ];

  const categories = [
    { key: 'core', label: 'Platform Core' },
    { key: 'operations', label: 'Forensic Operations' },
    { key: 'compliance', label: 'Governance & Audit' },
  ];

  const handleSelect = (tabId: string) => {
    onTabChange(tabId);
    if (onCloseMobile) onCloseMobile();
  };

  return (
    <aside className="w-60 bg-[#080D17] border-r border-[#1B2B40] flex flex-col justify-between shrink-0 h-screen sticky top-0 select-none z-40">
      {/* Brand Header */}
      <div>
        <div className="h-14 px-4 border-b border-[#1B2B40] flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="p-1.5 bg-[#1683FF]/10 border border-[#1683FF]/25 rounded-lg text-[#1683FF]">
              <Shield className="w-4 h-4 text-[#1683FF]" />
            </div>
            <div>
              <div className="flex items-center space-x-1.5">
                <span className="font-extrabold text-xs tracking-wider text-[#F1F5F9] uppercase font-sans">
                  FORENSIC<span className="text-[#16C7D9]">SHIELD</span>
                </span>
                <span className="w-1.5 h-1.5 rounded-full bg-[#16C7D9] animate-pulse" />
              </div>
              <p className="text-[10px] font-mono text-[#94A3B8]">Enterprise DFIR Platform</p>
            </div>
          </div>

          {onCloseMobile && (
            <button
              onClick={onCloseMobile}
              className="md:hidden text-[#94A3B8] hover:text-[#F1F5F9] p-1 rounded-lg hover:bg-[#121E30]"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Navigation Categories */}
        <nav className="p-3 space-y-4 overflow-y-auto max-h-[calc(100vh-125px)]">
          {categories.map(cat => (
            <div key={cat.key} className="space-y-1">
              <span className="px-2.5 text-[10px] font-bold tracking-wider text-[#64748B] uppercase font-mono">
                {cat.label}
              </span>
              <div className="space-y-0.5 mt-1">
                {navItems
                  .filter(item => item.category === cat.key)
                  .map(item => {
                    const isActive = activeTab === item.id;
                    return (
                      <button
                        key={item.id}
                        onClick={() => handleSelect(item.id)}
                        className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition-all cursor-pointer group ${
                          isActive
                            ? 'bg-[#1683FF]/10 text-[#F1F5F9] border border-[#1683FF]/30 font-medium'
                            : 'text-[#94A3B8] hover:text-[#F1F5F9] hover:bg-[#0E1726] border border-transparent font-medium'
                        }`}
                        aria-current={isActive ? 'page' : undefined}
                      >
                        <div className="flex items-center space-x-2.5">
                          <span
                            className={`transition-colors ${
                              isActive ? 'text-[#1683FF]' : 'text-[#64748B] group-hover:text-[#94A3B8]'
                            }`}
                          >
                            {item.icon}
                          </span>
                          <span>{item.label}</span>
                        </div>
                        {isActive && <ChevronRight className="w-3 h-3 text-[#1683FF]" />}
                      </button>
                    );
                  })}
              </div>
            </div>
          ))}
        </nav>
      </div>

      {/* Footer System Status Badge */}
      <div className="p-3 border-t border-[#1B2B40] bg-[#070B14] text-[11px] text-[#94A3B8] flex items-center justify-between font-mono">
        <span className="flex items-center space-x-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-[#20C997] animate-pulse" />
          <span className="text-[#20C997] text-[10px] font-semibold">SAFE_MODE: ON</span>
        </span>
        <span className="px-2 py-0.5 rounded bg-[#0E1726] border border-[#1B2B40] text-[#94A3B8] text-[10px]">
          ISO 27037
        </span>
      </div>
    </aside>
  );
};
