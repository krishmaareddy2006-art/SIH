import React, { useState, useEffect } from 'react';
import { HardDrive, RefreshCw, AlertTriangle, ShieldCheck, Cpu, Database, Lock } from 'lucide-react';
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
      <div className="flex flex-wrap items-center justify-between gap-4 bg-slate-900 p-6 rounded-2xl border border-slate-800 shadow-xl">
        <div>
          <h2 className="text-xl font-extrabold text-slate-100 flex items-center">
            <HardDrive className="w-6 h-6 text-cyan-400 mr-2.5" />
            Storage Device Discovery & Safety Classification
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Hardware bus classification, system disk exclusions, and test-lab allowlist checks
          </p>
        </div>

        <button
          onClick={loadDevices}
          className="flex items-center space-x-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold px-4 py-2.5 rounded-xl border border-slate-700 transition-all"
        >
          <RefreshCw className="w-3.5 h-3.5" />
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
            className={`p-5 rounded-2xl border transition-all space-y-4 ${
              dev.is_system_disk
                ? 'bg-red-950/20 border-red-500/40 shadow-lg shadow-red-950/20'
                : 'bg-slate-900 border-slate-800 hover:border-slate-700'
            }`}
          >
            {/* Top Device Bar */}
            <div className="flex items-start justify-between">
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <HardDrive className={`w-5 h-5 ${dev.is_system_disk ? 'text-red-400' : 'text-cyan-400'}`} />
                  <span className="font-mono font-extrabold text-sm text-slate-100">{dev.device_path}</span>
                  <span className="bg-slate-800 text-cyan-300 font-mono text-[10px] px-2 py-0.5 rounded-full border border-slate-700">
                    {dev.device_type}
                  </span>
                </div>
                <p className="text-xs text-slate-400 font-mono">
                  {dev.vendor} {dev.model} (S/N: {dev.serial_number})
                </p>
              </div>

              {dev.is_system_disk ? (
                <span className="bg-red-950 text-red-300 border border-red-500/50 text-[10px] font-mono font-bold px-2.5 py-1 rounded-lg flex items-center">
                  <AlertTriangle className="w-3.5 h-3.5 mr-1 text-red-400" /> SYSTEM DISK EXCLUDED
                </span>
              ) : (
                <span className="bg-emerald-950 text-emerald-300 border border-emerald-500/40 text-[10px] font-mono font-bold px-2.5 py-1 rounded-lg flex items-center">
                  <ShieldCheck className="w-3.5 h-3.5 mr-1 text-emerald-400" /> SAFE TARGET
                </span>
              )}
            </div>

            {/* Specification Grid */}
            <div className="grid grid-cols-2 gap-2 text-xs font-mono bg-slate-950 p-3 rounded-xl border border-slate-800">
              <div>
                <span className="text-slate-500 block">Capacity:</span>
                <span className="text-slate-200 font-semibold">{(dev.size_bytes / (1024 * 1024 * 1024)).toFixed(2)} GB</span>
              </div>
              <div>
                <span className="text-slate-500 block">Bus Type:</span>
                <span className="text-slate-200">{dev.bus_type}</span>
              </div>
              <div>
                <span className="text-slate-500 block">Mounted Status:</span>
                <span className={dev.is_mounted ? 'text-amber-400 font-semibold' : 'text-emerald-400'}>
                  {dev.is_mounted ? 'MOUNTED' : 'UNMOUNTED'}
                </span>
              </div>
              <div>
                <span className="text-slate-500 block">Lab Allowlist:</span>
                <span className={dev.in_allowlist ? 'text-emerald-400' : 'text-slate-400'}>
                  {dev.in_allowlist ? 'ALLOWLISTED' : 'NOT IN ALLOWLIST'}
                </span>
              </div>
            </div>

            {/* Recommended Method & Action */}
            <div className="flex items-center justify-between border-t border-slate-800 pt-3">
              <div className="text-xs">
                <span className="text-slate-400 block text-[11px]">Recommended Method:</span>
                <span className="font-mono text-cyan-300 font-semibold">{dev.recommended_method}</span>
              </div>

              {!dev.is_system_disk ? (
                <button
                  onClick={() => onNavigateToSanitization(dev.device_path)}
                  className="bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs px-3.5 py-2 rounded-xl transition-all shadow-md shadow-cyan-950 cursor-pointer"
                >
                  Configure Sanitization →
                </button>
              ) : (
                <span className="text-xs text-red-400 font-semibold font-mono bg-red-950/40 px-3 py-1.5 rounded-xl border border-red-900">
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
