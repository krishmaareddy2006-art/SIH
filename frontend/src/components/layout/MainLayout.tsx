import React, { useState } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { OfflineBanner } from '../common/StateViews';
import { useNotification } from '../../context/NotificationContext';
import { X, CheckCircle2, AlertTriangle, Info, AlertOctagon } from 'lucide-react';

interface MainLayoutProps {
  activeTab: string;
  onTabChange: (tabId: string) => void;
  children: React.ReactNode;
  onLoginClick?: () => void;
}

export const MainLayout: React.FC<MainLayoutProps> = ({
  activeTab,
  onTabChange,
  children,
  onLoginClick,
}) => {
  const { toasts, removeToast, isOnline } = useNotification();
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  const getToastIcon = (type: string) => {
    switch (type) {
      case 'success':
        return <CheckCircle2 className="w-4 h-4 text-[#20D69A] shrink-0" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-[#F5B642] shrink-0" />;
      case 'error':
        return <AlertOctagon className="w-4 h-4 text-[#FB7185] shrink-0" />;
      default:
        return <Info className="w-4 h-4 text-[#19D3E6] shrink-0" />;
    }
  };

  return (
    <div className="min-h-screen bg-[#070B14] text-[#F5F7FA] flex flex-col font-sans antialiased selection:bg-[#1683FF]/25 selection:text-[#19D3E6]">
      {/* Network Offline Status Banner */}
      {!isOnline && <OfflineBanner />}

      <div className="flex flex-1">
        {/* Desktop Sidebar */}
        <div className="hidden md:block shrink-0">
          <Sidebar activeTab={activeTab} onTabChange={onTabChange} />
        </div>

        {/* Mobile Sidebar Overlay Drawer */}
        {isMobileSidebarOpen && (
          <div className="fixed inset-0 z-50 md:hidden flex">
            <div
              className="fixed inset-0 bg-[#070B14]/80 backdrop-blur-sm"
              onClick={() => setIsMobileSidebarOpen(false)}
            />
            <div className="relative z-10 w-64 max-w-full">
              <Sidebar
                activeTab={activeTab}
                onTabChange={onTabChange}
                onCloseMobile={() => setIsMobileSidebarOpen(false)}
              />
            </div>
          </div>
        )}

        {/* Main Application Area */}
        <div className="flex-1 flex flex-col min-w-0">
          <Header
            onLoginClick={onLoginClick}
            onToggleMobileSidebar={() => setIsMobileSidebarOpen(prev => !prev)}
          />

          <main className="flex-1 p-4 md:p-6 lg:p-7 overflow-y-auto max-w-7xl w-full mx-auto space-y-6">
            {children}
          </main>
        </div>
      </div>

      {/* Floating Toast Notification Container */}
      <div className="fixed bottom-5 right-5 z-50 space-y-2.5 max-w-sm w-full pointer-events-none px-4 sm:px-0">
        {toasts.map(toast => (
          <div
            key={toast.id}
            className="pointer-events-auto bg-[#101827] border border-[#1E3048] p-3.5 rounded-xl shadow-elevated flex items-start justify-between space-x-3 animate-fade-in"
          >
            <div className="flex items-start space-x-2.5">
              <div className="mt-0.5">{getToastIcon(toast.type)}</div>
              <div>
                <h5 className="text-xs font-semibold text-[#F5F7FA]">{toast.title}</h5>
                <p className="text-[11px] text-[#91A0B5] mt-0.5 leading-snug">{toast.message}</p>
              </div>
            </div>
            <button
              onClick={() => removeToast(toast.id)}
              className="text-[#64748B] hover:text-[#F5F7FA] p-1 rounded-lg hover:bg-[#141F32] transition-colors cursor-pointer"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};
