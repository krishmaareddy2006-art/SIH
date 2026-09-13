import React, { useState, useEffect } from 'react';
import { HardDrive, RefreshCw, AlertTriangle, ShieldCheck } from 'lucide-react';
import { api } from '../services/api';
import { DeviceInfo } from '../types';
import { LoadingSpinner, ErrorState } from '../components/common/StateViews';
import { SafetyGateBanner } from '../components/common/SafetyGateBanner';
import { TechnicalLimitationsBox } from '../components/common/TechnicalLimitationsBox';

export const DevicesPage: React.FC<{ onNavigateToSanitization: (devicePath: string) => void }> = ({
  onNavigateToSanitization,
}) => {
  const [devices, setDevices] = useState<DeviceInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const loadDevices = async () => {
    setIsLoading(true);
    setError('');
    const res = await api.listDevices();
    if (res.data) {
      setDevices(res.data);
    } else if (res.error) {
      setError(res.error.error.message);
    }
    setIsLoading(false);
  };

  useEffect(() => {
    loadDevices();
  }, []);

  if (isLoading) return <LoadingSpinner message="Scanning physical & virtual storage buses..." />;
  if (error) return <ErrorState code="DEVICE_SCAN_ERROR" message={error} onRetry={loadDevices} />;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-[#111827] p-5 sm:p-6 rounded-2xl border border-[#253044] shadow-card">
        <div>
          <h2 className="text-lg sm:text-xl font-bold text-[#F8FAFC] flex items-center">
            <HardDrive className="w-5 h-5 text-[#22D3EE] mr-2.5" />
            Storage Device Discovery & Safety Classification
          </h2>
          <p className="text-xs text-[#94A3B8] mt-1">
            Hardware bus classification, system disk exclusions, and test-lab allowlist checks
          </p>
        </div>

        <button
          onClick={loadDevices}
          className="flex items-center space-x-2 bg-[#0B0F19] hover:bg-[#162032] text-[#F8FAFC] text-xs font-semibold px-4 py-2 rounded-xl border border-[#253044] transition-all cursor-pointer shadow-subtle"
        >
          <RefreshCw className="w-3.5 h-3.5 text-[#22D3EE]" />
          <span>Rescan Hardware Bus</span>
        </button>
      </div>

      {/* Safety Gate Banner */}
      <SafetyGateBanner safeMode={true} realDeviceOps={false} />

      {/* Device List Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {devices.map((dev, idx) => (
          <div
            key={idx}
            className={`p-5 rounded-2xl border transition-all space-y-4 shadow-card ${
              dev.is_system_disk
                ? 'bg-[#1A0E13] border-[#FB7185]/40'
                : 'bg-[#111827] border-[#253044] hover:border-[#22D3EE]/30'
            }`}
          >
            {/* Top Device Bar */}
            <div className="flex items-start justify-between">
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <HardDrive className={`w-4 h-4 ${dev.is_system_disk ? 'text-[#FB7185]' : 'text-[#22D3EE]'}`} />
                  <span className="font-mono font-bold text-sm text-[#F8FAFC]">{dev.device_path}</span>
                  <span className="bg-[#0B0F19] text-[#22D3EE] font-mono text-[10px] px-2 py-0.5 rounded-md border border-[#253044]">
                    {dev.device_type}
                  </span>
                </div>
                <p className="text-xs text-[#94A3B8] font-mono">
                  {dev.vendor} {dev.model} (S/N: {dev.serial_number})
                </p>
              </div>

              {dev.is_system_disk ? (
                <span className="bg-[#FB7185]/10 text-[#FB7185] border border-[#FB7185]/40 text-[10px] font-mono font-bold px-2 py-0.5 rounded-full flex items-center">
                  <AlertTriangle className="w-3 h-3 mr-1 text-[#FB7185]" /> EXCLUDED
                </span>
              ) : (
                <span className="bg-[#34D399]/10 text-[#34D399] border border-[#34D399]/40 text-[10px] font-mono font-bold px-2 py-0.5 rounded-full flex items-center">
                  <ShieldCheck className="w-3 h-3 mr-1 text-[#34D399]" /> SAFE TARGET
                </span>
              )}
            </div>

            {/* Specification Grid */}
            <div className="grid grid-cols-2 gap-2 text-xs font-mono bg-[#0B0F19] p-3 rounded-xl border border-[#253044]">
              <div>
                <span className="text-[#64748B] block text-[10px]">Capacity:</span>
                <span className="text-[#F8FAFC] font-semibold">{(dev.size_bytes / (1024 * 1024 * 1024)).toFixed(2)} GB</span>
              </div>
              <div>
                <span className="text-[#64748B] block text-[10px]">Bus Type:</span>
                <span className="text-[#F8FAFC]">{dev.bus_type}</span>
              </div>
              <div>
                <span className="text-[#64748B] block text-[10px]">Mounted Status:</span>
                <span className={dev.is_mounted ? 'text-[#FBBF24] font-semibold' : 'text-[#34D399]'}>
                  {dev.is_mounted ? 'MOUNTED' : 'UNMOUNTED'}
                </span>
              </div>
              <div>
                <span className="text-[#64748B] block text-[10px]">Lab Allowlist:</span>
                <span className={dev.in_allowlist ? 'text-[#34D399]' : 'text-[#64748B]'}>
                  {dev.in_allowlist ? 'ALLOWLISTED' : 'NOT IN ALLOWLIST'}
                </span>
              </div>
            </div>

            {/* Recommended Method & Action */}
            <div className="flex items-center justify-between border-t border-[#253044] pt-3">
              <div className="text-xs">
                <span className="text-[#64748B] block text-[10px] font-mono">Recommended:</span>
                <span className="font-mono text-[#22D3EE] font-semibold">{dev.recommended_method}</span>
              </div>

              {!dev.is_system_disk ? (
                <button
                  onClick={() => onNavigateToSanitization(dev.device_path)}
                  className="bg-[#22D3EE] hover:bg-[#67E8F9] text-[#080B14] font-semibold text-xs px-3.5 py-1.5 rounded-xl transition-all shadow-subtle cursor-pointer"
                >
                  Configure Sanitization →
                </button>
              ) : (
                <span className="text-[11px] text-[#FB7185] font-mono bg-[#2A151C] px-2.5 py-1 rounded-lg border border-[#FB7185]/30">
                  Wipe Disabled (System Volume)
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Technical Disclaimers */}
      <TechnicalLimitationsBox />
    </div>
  );
};
