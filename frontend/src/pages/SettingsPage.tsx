import React, { useState } from 'react';
import { Settings, Shield, Lock, Cpu, Server, Key, CheckCircle2, AlertTriangle, ShieldCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useNotification } from '../context/NotificationContext';
import { TechnicalLimitationsBox } from '../components/common/TechnicalLimitationsBox';

export const SettingsPage: React.FC = () => {
  const { user, hasRole } = useAuth();
  const { addToast } = useNotification();

  const [blockchainEnabled, setBlockchainEnabled] = useState(true);
  const [network, setNetwork] = useState('Ethereum Sepolia (Testnet)');
  const [autoVerifyAudit, setAutoVerifyAudit] = useState(true);

  const isAdmin = hasRole(['Administrator']);

  const handleSaveSettings = () => {
    addToast('success', 'Policy Updated', 'ForensicShield system configuration updated cleanly.');
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800 shadow-xl flex items-center justify-between">
        <div>
          <h2 className="text-xl font-extrabold text-slate-100 flex items-center">
            <Settings className="w-6 h-6 text-cyan-400 mr-2.5" />
            Security Policy & System Settings
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Global system flags, safety-gate controls, blockchain notarization network, and RBAC matrix
          </p>
        </div>
      </div>

      {/* Safety Policy Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
        {/* System Flags */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-xl">
          <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
            <Lock className="w-4 h-4 text-emerald-400" />
            <h3 className="font-bold text-slate-200 text-sm">Hardware & Execution Safety Flags</h3>
          </div>

          <div className="space-y-3 font-mono">
            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 flex items-center justify-between">
              <div>
                <span className="text-slate-200 font-bold block">SAFE_MODE</span>
                <span className="text-slate-400 text-[11px] font-sans">Forces simulation behavior first for all operations</span>
              </div>
              <span className="bg-emerald-950 text-emerald-300 border border-emerald-500/40 text-[10px] font-bold px-2.5 py-1 rounded-full">
                ENABLED
              </span>
            </div>

            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 flex items-center justify-between">
              <div>
                <span className="text-slate-200 font-bold block">REAL_DEVICE_OPERATIONS</span>
                <span className="text-slate-400 text-[11px] font-sans">Master override switch for physical hardware access</span>
              </div>
              <span className="bg-slate-800 text-slate-400 border border-slate-700 text-[10px] font-bold px-2.5 py-1 rounded-full">
                BLOCKED (Default)
              </span>
            </div>
          </div>
        </div>

        {/* Blockchain Notarization Settings */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-xl">
          <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
            <Server className="w-4 h-4 text-cyan-400" />
            <h3 className="font-bold text-slate-200 text-sm">Blockchain Notarization Integrity Adapter</h3>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label htmlFor="bcToggle" className="text-slate-300 font-semibold cursor-pointer">
                Enable Audit Digest Blockchain Notarization
              </label>
              <input
                type="checkbox"
                id="bcToggle"
                checked={blockchainEnabled}
                onChange={e => setBlockchainEnabled(e.target.checked)}
                className="rounded border-slate-700 text-cyan-600 focus:ring-cyan-500 bg-slate-950"
              />
            </div>

            <div>
              <label className="block text-slate-400 mb-1">Permissioned Ledger Network</label>
              <select
                value={network}
                onChange={e => setNetwork(e.target.value)}
                disabled={!blockchainEnabled}
                className="w-full bg-slate-950 border border-slate-700 font-mono text-cyan-300 rounded-xl px-3 py-2 outline-none"
              >
                <option value="Ethereum Sepolia (Testnet)">Ethereum Sepolia (Testnet)</option>
                <option value="Hyperledger Fabric DFIR Network">Hyperledger Fabric DFIR Network</option>
                <option value="Local Mock Ledger (Offline Safe)">Local Mock Ledger (Offline Safe)</option>
              </select>
            </div>

            <div className="flex items-center justify-end pt-2">
              <button
                onClick={handleSaveSettings}
                className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs rounded-xl shadow-md"
              >
                Save Security Settings
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Role Permission Matrix */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-xl text-xs">
        <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
          <Key className="w-4 h-4 text-amber-400" />
          <h3 className="font-bold text-slate-200 text-sm">Role-Based Access Control (RBAC) Permission Matrix</h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono">
            <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="p-3">Permission Scope</th>
                <th className="p-3 text-center">Administrator</th>
                <th className="p-3 text-center">Investigator</th>
                <th className="p-3 text-center">Operator</th>
                <th className="p-3 text-center">Viewer</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              <tr className="hover:bg-slate-800/40">
                <td className="p-3 font-bold text-slate-200">Drive Sanitization & Block Overwrite</td>
                <td className="p-3 text-center text-emerald-400 font-bold">✓ YES</td>
                <td className="p-3 text-center text-emerald-400 font-bold">✓ YES</td>
                <td className="p-3 text-center text-emerald-400 font-bold">✓ YES</td>
                <td className="p-3 text-center text-red-400 font-bold">✗ DENIED</td>
              </tr>
              <tr className="hover:bg-slate-800/40">
                <td className="p-3 font-bold text-slate-200">Evidence Image Ingestion & Manifest Export</td>
                <td className="p-3 text-center text-emerald-400 font-bold">✓ YES</td>
                <td className="p-3 text-center text-emerald-400 font-bold">✓ YES</td>
                <td className="p-3 text-center text-emerald-400 font-bold">✓ YES</td>
                <td className="p-3 text-center text-emerald-400 font-bold">✓ YES</td>
              </tr>
              <tr className="hover:bg-slate-800/40">
                <td className="p-3 font-bold text-slate-200">System Safety Policy & Allowlist Management</td>
                <td className="p-3 text-center text-emerald-400 font-bold">✓ YES</td>
                <td className="p-3 text-center text-red-400 font-bold">✗ DENIED</td>
                <td className="p-3 text-center text-red-400 font-bold">✗ DENIED</td>
                <td className="p-3 text-center text-red-400 font-bold">✗ DENIED</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <TechnicalLimitationsBox />
    </div>
  );
};
