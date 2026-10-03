import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { AuditLogItem } from '../types';
import { ListFilter, Search, Shield, Filter, Download, CheckCircle2, AlertCircle } from 'lucide-react';

export const AuditPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [roleFilter, setRoleFilter] = useState('');
  const [actionFilter, setActionFilter] = useState('');
  const [decisionFilter, setDecisionFilter] = useState('');

  useEffect(() => {
    loadAuditLogs();
  }, [roleFilter, actionFilter, decisionFilter]);

  const loadAuditLogs = async () => {
    setLoading(true);
    try {
      const res = await api.getAuditLogs({
        role: roleFilter || undefined,
        action: actionFilter || undefined,
        decision: decisionFilter || undefined,
        limit: 100,
      });
      setLogs(res.logs);
      setTotal(res.total);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Security & Compliance Audit Trail</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Immutable log of all user authentication events, ACL queries, prompt injection attempts, and document modifications.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-600 bg-white border border-slate-200 px-3 py-1.5 rounded-lg shadow-2xs">
            Total Records: {total}
          </span>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 flex flex-wrap gap-3 shadow-2xs">
        <div className="flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-xs font-medium text-slate-600">Filters:</span>
        </div>

        <select
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          className="px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700"
        >
          <option value="">All Roles</option>
          <option value="EMPLOYEE">EMPLOYEE</option>
          <option value="HR">HR</option>
          <option value="FINANCE">FINANCE</option>
          <option value="ADMIN">ADMIN</option>
          <option value="SECURITY">SECURITY</option>
        </select>

        <select
          value={actionFilter}
          onChange={(e) => setActionFilter(e.target.value)}
          className="px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700"
        >
          <option value="">All Actions</option>
          <option value="QUERY_SEARCH">QUERY_SEARCH</option>
          <option value="LOGIN_SUCCESS">LOGIN_SUCCESS</option>
          <option value="LOGIN_FAILED">LOGIN_FAILED</option>
          <option value="PROMPT_INJECTION_DETECTED">PROMPT_INJECTION_DETECTED</option>
          <option value="DOCUMENT_UPLOAD">DOCUMENT_UPLOAD</option>
        </select>

        <select
          value={decisionFilter}
          onChange={(e) => setDecisionFilter(e.target.value)}
          className="px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700"
        >
          <option value="">All Decisions</option>
          <option value="ALLOWED">ALLOWED</option>
          <option value="DENIED">DENIED</option>
        </select>
      </div>

      {/* Logs Table */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-2xs overflow-hidden">
        {loading ? (
          <div className="py-12 text-center text-xs text-slate-400">Loading audit records...</div>
        ) : logs.length === 0 ? (
          <div className="py-12 text-center text-xs text-slate-400">No audit records found matching criteria</div>
        ) : (
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase font-semibold text-[10px]">
              <tr>
                <th className="px-4 py-3">Timestamp</th>
                <th className="px-4 py-3">User / Role</th>
                <th className="px-4 py-3">Action</th>
                <th className="px-4 py-3">Query / Resource</th>
                <th className="px-4 py-3">ACL Decision</th>
                <th className="px-4 py-3">Trace / Req ID</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-50/70 transition-colors">
                  <td className="px-4 py-3 text-slate-500 font-mono text-[10px] whitespace-nowrap">
                    {new Date(log.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3">
                    <div className="font-semibold text-slate-800">{log.user_email}</div>
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-100 text-slate-700 font-medium">
                      {log.role}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="font-mono text-[11px] font-semibold text-slate-700">
                      {log.action}
                    </span>
                  </td>
                  <td className="px-4 py-3 max-w-xs">
                    <div className="truncate text-slate-800 font-medium" title={log.query || log.resource}>
                      {log.query || log.resource || '-'}
                    </div>
                    {log.reason && <div className="text-[10px] text-slate-400 truncate">{log.reason}</div>}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                        log.acl_decision === 'ALLOWED'
                          ? 'bg-emerald-50 text-emerald-700'
                          : 'bg-red-50 text-red-700'
                      }`}
                    >
                      {log.acl_decision}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono text-[10px] text-slate-400">
                    <div>{log.trace_id}</div>
                    <div className="text-[9px] text-slate-300">{log.request_id}</div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
