import React, { useState } from 'react';
import { Settings, Lock, Server, Key } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useNotification } from '../context/NotificationContext';
import { TechnicalLimitationsBox } from '../components/common/TechnicalLimitationsBox';

export const SettingsPage: React.FC = () => {
  const { hasRole } = useAuth();
  const { addToast } = useNotification();

  const [blockchainEnabled, setBlockchainEnabled] = useState(true);
  const [network, setNetwork] = useState('Ethereum Sepolia (Testnet)');

  const isAdmin = hasRole(['Administrator']);

  const handleSaveSettings = () => {
    addToast('success', 'Policy Updated', 'ForensicShield system configuration updated cleanly.');
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="bg-[#111827] p-5 sm:p-6 rounded-2xl border border-[#253044] shadow-card flex items-center justify-between">
        <div>
          <h2 className="text-lg sm:text-xl font-bold text-[#F8FAFC] flex items-center">
            <Settings className="w-5 h-5 text-[#22D3EE] mr-2.5" />
            Security Policy & System Settings
          </h2>
          <p className="text-xs text-[#94A3B8] mt-1">
            Global system flags, safety-gate controls, blockchain notarization network, and RBAC matrix
          </p>
        </div>
      </div>

      {/* Safety Policy Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
        {/* System Flags */}
        <div className="bg-[#111827] border border-[#253044] rounded-2xl p-5 space-y-4 shadow-card">
          <div className="flex items-center space-x-2 border-b border-[#253044] pb-3">
            <Lock className="w-4 h-4 text-[#34D399]" />
            <h3 className="font-semibold text-[#F8FAFC] text-sm">Hardware & Execution Safety Flags</h3>
          </div>

          <div className="space-y-3 font-mono">
            <div className="p-3.5 bg-[#0B0F19] rounded-xl border border-[#253044] flex items-center justify-between">
              <div>
                <span className="text-[#F8FAFC] font-bold block">SAFE_MODE</span>
                <span className="text-[#94A3B8] text-[11px] font-sans">Forces simulation behavior first for all operations</span>
              </div>
              <span className="bg-[#34D399]/10 text-[#34D399] border border-[#34D399]/40 text-[10px] font-bold px-2.5 py-1 rounded-full">
                ENABLED
              </span>
            </div>

            <div className="p-3.5 bg-[#0B0F19] rounded-xl border border-[#253044] flex items-center justify-between">
              <div>
                <span className="text-[#F8FAFC] font-bold block">REAL_DEVICE_OPERATIONS</span>
                <span className="text-[#94A3B8] text-[11px] font-sans">Master override switch for physical hardware access</span>
              </div>
              <span className="bg-[#111827] text-[#64748B] border border-[#253044] text-[10px] font-bold px-2.5 py-1 rounded-full">
                BLOCKED (Default)
              </span>
            </div>
          </div>
        </div>

        {/* Blockchain Notarization Settings */}
        <div className="bg-[#111827] border border-[#253044] rounded-2xl p-5 space-y-4 shadow-card">
          <div className="flex items-center space-x-2 border-b border-[#253044] pb-3">
            <Server className="w-4 h-4 text-[#22D3EE]" />
            <h3 className="font-semibold text-[#F8FAFC] text-sm">Blockchain Notarization Integrity Adapter</h3>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label htmlFor="bcToggle" className="text-[#94A3B8] font-medium cursor-pointer text-xs select-none">
                Enable Audit Digest Blockchain Notarization
              </label>
              <input
                type="checkbox"
                id="bcToggle"
                checked={blockchainEnabled}
                onChange={e => setBlockchainEnabled(e.target.checked)}
                className="rounded border-[#253044] text-[#22D3EE] focus:ring-[#22D3EE] bg-[#0B0F19]"
              />
            </div>

            <div>
              <label className="block text-[#94A3B8] mb-1 font-mono text-[11px]">Permissioned Ledger Network</label>
              <select
                value={network}
                onChange={e => setNetwork(e.target.value)}
                disabled={!blockchainEnabled}
                className="w-full bg-[#0B0F19] border border-[#253044] font-mono text-[#22D3EE] rounded-xl px-3 py-2 outline-none focus:border-[#22D3EE] transition-all disabled:opacity-40"
              >
                <option value="Ethereum Sepolia (Testnet)" className="bg-[#111827]">Ethereum Sepolia (Testnet)</option>
                <option value="Hyperledger Fabric DFIR Network" className="bg-[#111827]">Hyperledger Fabric DFIR Network</option>
                <option value="Local Mock Ledger (Offline Safe)" className="bg-[#111827]">Local Mock Ledger (Offline Safe)</option>
              </select>
            </div>

            <div className="flex items-center justify-end pt-2">
              <button
                onClick={handleSaveSettings}
                className="px-4 py-2 bg-[#22D3EE] hover:bg-[#67E8F9] text-[#080B14] font-bold text-xs rounded-xl shadow-subtle transition-all cursor-pointer"
              >
                Save Security Settings
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Role Permission Matrix */}
      <div className="bg-[#111827] border border-[#253044] rounded-2xl p-5 sm:p-6 space-y-4 shadow-card text-xs">
        <div className="flex items-center space-x-2 border-b border-[#253044] pb-3">
          <Key className="w-4 h-4 text-[#FBBF24]" />
          <h3 className="font-semibold text-[#F8FAFC] text-sm">Role-Based Access Control (RBAC) Permission Matrix</h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono">
            <thead className="bg-[#0B0F19] text-[#64748B] border-b border-[#253044]">
              <tr>
                <th className="p-3 font-sans">Permission Scope</th>
                <th className="p-3 text-center">Administrator</th>
                <th className="p-3 text-center">Investigator</th>
                <th className="p-3 text-center">Operator</th>
                <th className="p-3 text-center">Viewer</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#253044]">
              <tr className="hover:bg-[#162032]/40 transition-colors">
                <td className="p-3 font-medium text-[#F8FAFC] font-sans">Drive Sanitization & Block Overwrite</td>
                <td className="p-3 text-center text-[#34D399] font-bold">✓ YES</td>
                <td className="p-3 text-center text-[#34D399] font-bold">✓ YES</td>
                <td className="p-3 text-center text-[#34D399] font-bold">✓ YES</td>
                <td className="p-3 text-center text-[#FB7185] font-bold">✗ DENIED</td>
              </tr>
              <tr className="hover:bg-[#162032]/40 transition-colors">
                <td className="p-3 font-medium text-[#F8FAFC] font-sans">Evidence Image Ingestion & Manifest Export</td>
                <td className="p-3 text-center text-[#34D399] font-bold">✓ YES</td>
                <td className="p-3 text-center text-[#34D399] font-bold">✓ YES</td>
                <td className="p-3 text-center text-[#34D399] font-bold">✓ YES</td>
                <td className="p-3 text-center text-[#34D399] font-bold">✓ YES</td>
              </tr>
              <tr className="hover:bg-[#162032]/40 transition-colors">
                <td className="p-3 font-medium text-[#F8FAFC] font-sans">System Safety Policy & Allowlist Management</td>
                <td className="p-3 text-center text-[#34D399] font-bold">✓ YES</td>
                <td className="p-3 text-center text-[#FB7185] font-bold">✗ DENIED</td>
                <td className="p-3 text-center text-[#FB7185] font-bold">✗ DENIED</td>
                <td className="p-3 text-center text-[#FB7185] font-bold">✗ DENIED</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <TechnicalLimitationsBox />
    </div>
  );
};
