import React, { useState } from 'react';
import { Terminal, Filter } from 'lucide-react';

export interface AuditLogItem {
  timestamp: string;
  level: string;
  operation: string;
  status: string;
  request_id: string;
  case_id: string;
  user_id?: string;
  message: string;
}

interface AuditLogViewerProps {
  logs: AuditLogItem[];
}

export const AuditLogViewer: React.FC<AuditLogViewerProps> = ({ logs }) => {
  const [filter, setFilter] = useState('');
  const [selectedLog, setSelectedLog] = useState<AuditLogItem | null>(null);

  const filteredLogs = logs.filter((log) => {
    const search = filter.toLowerCase();
    return (
      log.request_id.toLowerCase().includes(search) ||
      log.case_id.toLowerCase().includes(search) ||
      log.operation.toLowerCase().includes(search) ||
      log.status.toLowerCase().includes(search)
    );
  });

  return (
    <div className="glass-panel p-6">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
        <div className="flex items-center gap-2">
          <Terminal className="w-5 h-5 text-cyber-teal" />
          <h2 className="text-lg font-semibold text-white">Structured JSON Audit Logs</h2>
          <span className="text-xs px-2 py-0.5 rounded bg-dark-700 font-mono text-slate-300">
            {logs.length} Frames
          </span>
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Filter by request_id, case_id, operation..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-dark-900 border border-dark-600 text-xs font-mono text-slate-200 w-64 focus:outline-none focus:border-cyber-teal"
          />
        </div>
      </div>

      <div className="border border-dark-700 rounded-lg overflow-hidden bg-dark-900/90 font-mono text-xs">
        <div className="grid grid-cols-12 gap-2 p-3 bg-dark-800 text-slate-400 border-b border-dark-700 font-semibold">
          <div className="col-span-3">Timestamp</div>
          <div className="col-span-2">Operation</div>
          <div className="col-span-2">Request ID</div>
          <div className="col-span-2">Case ID</div>
          <div className="col-span-1 text-center">Status</div>
          <div className="col-span-2 text-right">Details</div>
        </div>

        <div className="max-h-64 overflow-y-auto divide-y divide-dark-800">
          {filteredLogs.length === 0 ? (
            <div className="p-4 text-center text-slate-500">
              No audit log records match filter query.
            </div>
          ) : (
            filteredLogs.map((log, index) => {
              const isSelected = selectedLog === log;
              return (
                <div
                  key={index}
                  onClick={() => setSelectedLog(isSelected ? null : log)}
                  className={`grid grid-cols-12 gap-2 p-3 cursor-pointer transition-colors hover:bg-dark-800/60 ${
                    isSelected ? 'bg-teal-500/10' : ''
                  }`}
                >
                  <div className="col-span-3 text-slate-400 truncate">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </div>
                  <div className="col-span-2 text-cyber-teal font-semibold truncate">
                    {log.operation}
                  </div>
                  <div className="col-span-2 text-slate-300 truncate" title={log.request_id}>
                    {log.request_id}
                  </div>
                  <div className="col-span-2 text-slate-300 truncate">
                    {log.case_id}
                  </div>
                  <div className="col-span-1 text-center">
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] ${
                        log.status === 'SUCCESS'
                          ? 'bg-teal-500/20 text-teal-300'
                          : log.status === 'SIMULATED'
                          ? 'bg-cyan-500/20 text-cyan-300'
                          : 'bg-rose-500/20 text-rose-300'
                      }`}
                    >
                      {log.status}
                    </span>
                  </div>
                  <div className="col-span-2 text-right text-slate-400 truncate">
                    {log.message}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Selected JSON Frame Modal Inspector */}
      {selectedLog && (
        <div className="mt-4 p-4 rounded-lg bg-dark-900 border border-dark-600 font-mono text-xs">
          <div className="flex items-center justify-between text-slate-400 mb-2 border-b border-dark-700 pb-2">
            <span>JSON Log Frame Context</span>
            <button
              onClick={() => setSelectedLog(null)}
              className="text-slate-500 hover:text-white"
            >
              Close Inspector
            </button>
          </div>
          <pre className="text-teal-300 overflow-x-auto p-2 bg-dark-950 rounded">
            {JSON.stringify(selectedLog, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};
