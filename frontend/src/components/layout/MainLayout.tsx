import React from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { OfflineBanner } from '../common/StateViews';
import { useNotification } from '../../context/NotificationContext';
import { X, CheckCircle, AlertTriangle, Info, AlertOctagon } from 'lucide-react';

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

  const getToastIcon = (type: string) => {
    switch (type) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-emerald-400 shrink-0" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />;
      case 'error':
        return <AlertOctagon className="w-5 h-5 text-red-400 shrink-0" />;
      default:
        return <Info className="w-5 h-5 text-cyan-400 shrink-0" />;
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans antialiased selection:bg-cyan-500 selection:text-slate-950">
      {/* Network Offline Status Banner */}
      {!isOnline && <OfflineBanner />}

      <div className="flex flex-1">
        {/* Navigation Sidebar */}
        <Sidebar activeTab={activeTab} onTabChange={onTabChange} />

        {/* Main Application Area */}
        <div className="flex-1 flex flex-col min-w-0">
          <Header onLoginClick={onLoginClick} />

          <main className="flex-1 p-6 md:p-8 overflow-y-auto max-w-7xl w-full mx-auto space-y-6">
            {children}
          </main>
        </div>
      </div>

      {/* Floating Toast Notification Container */}
      <div className="fixed bottom-5 right-5 z-50 space-y-2.5 max-w-sm w-full pointer-events-none">
        {toasts.map(toast => (
          <div
            key={toast.id}
            className="pointer-events-auto bg-slate-900 border border-slate-700 p-4 rounded-xl shadow-2xl flex items-start justify-between space-x-3 animate-fade-in"
          >
            <div className="flex items-start space-x-3">
              {getToastIcon(toast.type)}
              <div>
                <h5 className="text-xs font-bold text-slate-100">{toast.title}</h5>
                <p className="text-[11px] text-slate-300 mt-0.5 leading-tight">{toast.message}</p>
              </div>
            </div>
            <button
              onClick={() => removeToast(toast.id)}
              className="text-slate-400 hover:text-slate-200 p-0.5 rounded-lg hover:bg-slate-800"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};
