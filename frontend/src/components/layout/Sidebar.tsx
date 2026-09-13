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
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onTabChange }) => {
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
    { key: 'core', label: 'Core Platform' },
    { key: 'operations', label: 'Forensic Operations' },
    { key: 'compliance', label: 'Audit & Compliance' },
  ];

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between shrink-0 h-screen sticky top-0 select-none">
      {/* Brand Header */}
      <div>
        <div className="p-4 border-b border-slate-800 flex items-center space-x-3">
          <div className="p-2 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-xl text-slate-950 shadow-md shadow-cyan-950">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <h1 className="font-extrabold text-sm tracking-wider text-slate-100 uppercase">
              FORENSIC<span className="text-cyan-400">SHIELD</span>
            </h1>
            <p className="text-[10px] font-mono text-slate-400">v1.0.0 Enterprise DFIR</p>
          </div>
        </div>

        {/* Navigation Categories */}
        <nav className="p-3 space-y-4 overflow-y-auto max-h-[calc(100vh-140px)]">
          {categories.map(cat => (
            <div key={cat.key} className="space-y-1">
              <span className="px-3 text-[10px] font-bold tracking-wider text-slate-500 uppercase">
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
                        onClick={() => onTabChange(item.id)}
                        className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium transition-all ${
                          isActive
                            ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 shadow-sm font-semibold'
                            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                        }`}
                        aria-current={isActive ? 'page' : undefined}
                      >
                        <div className="flex items-center space-x-2.5">
                          <span className={isActive ? 'text-cyan-400' : 'text-slate-400'}>{item.icon}</span>
                          <span>{item.label}</span>
                        </div>
                        {isActive && <ChevronRight className="w-3.5 h-3.5 text-cyan-400" />}
                      </button>
                    );
                  })}
              </div>
            </div>
          ))}
        </nav>
      </div>

      {/* Footer System Status Badge */}
      <div className="p-3 border-t border-slate-800 bg-slate-950/60 text-[11px] text-slate-400 flex items-center justify-between">
        <span className="flex items-center space-x-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="font-mono">SAFE_MODE: ON</span>
        </span>
        <span className="font-mono text-slate-500">ISO/IEC 27037</span>
      </div>
    </aside>
  );
};
