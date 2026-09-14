import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { CaseProvider } from './context/CaseContext';
import { NotificationProvider } from './context/NotificationContext';

import { MainLayout } from './components/layout/MainLayout';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { CasesPage } from './pages/CasesPage';
import { DevicesPage } from './pages/DevicesPage';
import { DriveSanitizationPage } from './pages/DriveSanitizationPage';
import { FileErasurePage } from './pages/FileErasurePage';
import { EvidenceIntakePage } from './pages/EvidenceIntakePage';
import { RecoveryWorkspacePage } from './pages/RecoveryWorkspacePage';
import { JobDetailsPage } from './pages/JobDetailsPage';
import { AuditChainPage } from './pages/AuditChainPage';
import { ReportsPage } from './pages/ReportsPage';
import { SettingsPage } from './pages/SettingsPage';

const AppContent: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedDeviceForSanitization, setSelectedDeviceForSanitization] = useState('');
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);

  React.useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      setIsLoginModalOpen(true);
    }
  }, [isLoading, isAuthenticated]);

  const handleNavigateToSanitization = (devicePath: string) => {
    setSelectedDeviceForSanitization(devicePath);
    setActiveTab('sanitization');
  };

  const handleLoginSuccess = () => {
    setIsLoginModalOpen(false);
    setActiveTab('dashboard');
  };

  const renderActivePage = () => {
    switch (activeTab) {
      case 'dashboard':
        return <DashboardPage onNavigate={setActiveTab} />;
      case 'cases':
        return <CasesPage />;
      case 'devices':
        return <DevicesPage onNavigateToSanitization={handleNavigateToSanitization} />;
      case 'sanitization':
        return <DriveSanitizationPage selectedDevicePath={selectedDeviceForSanitization} />;
      case 'erasure':
        return <FileErasurePage />;
      case 'evidence':
        return <EvidenceIntakePage />;
      case 'recovery':
        return <RecoveryWorkspacePage />;
      case 'jobs':
        return <JobDetailsPage />;
      case 'audit':
        return <AuditChainPage />;
      case 'reports':
        return <ReportsPage />;
      case 'settings':
        return <SettingsPage />;
      default:
        return <DashboardPage onNavigate={setActiveTab} />;
    }
  };

  return (
    <MainLayout
      activeTab={activeTab}
      onTabChange={setActiveTab}
      onLoginClick={() => setIsLoginModalOpen(true)}
    >
      {renderActivePage()}

      {/* Login Modal */}
      {isLoginModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#080B14]/85 backdrop-blur-md animate-fade-in">
          <div className="relative max-w-md w-full">
            <button
              onClick={() => setIsLoginModalOpen(false)}
              className="absolute right-4 top-4 text-[#94A3B8] hover:text-[#F8FAFC] p-1.5 rounded-lg hover:bg-[#162032] transition-colors z-10 cursor-pointer"
              aria-label="Close modal"
            >
              ✕
            </button>
            <LoginPage onSuccess={handleLoginSuccess} />
          </div>
        </div>
      )}
    </MainLayout>
  );
};

export function App() {
  return (
    <NotificationProvider>
      <AuthProvider>
        <CaseProvider>
          <AppContent />
        </CaseProvider>
      </AuthProvider>
    </NotificationProvider>
  );
}

export default App;
