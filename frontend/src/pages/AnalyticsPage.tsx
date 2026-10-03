import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { AnalyticsData } from '../types';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { BarChart3, Activity, ShieldAlert, Cpu, Clock, Layers } from 'lucide-react';

const COLORS = ['#2563eb', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444'];

export const AnalyticsPage: React.FC = () => {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(7);

  useEffect(() => {
    loadAnalytics();
  }, [days]);

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      const res = await api.getAnalytics(days);
      setData(res);
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
          <h1 className="text-xl font-bold text-slate-900">Observability & Operational Analytics</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Real-time telemetry, token consumption, security decisions, and retrieval latency metrics.
          </p>
        </div>

        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="px-3 py-1.5 rounded-lg bg-white border border-slate-200 text-xs text-slate-700 font-medium shadow-2xs focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value={1}>Last 24 Hours</option>
          <option value={7}>Last 7 Days</option>
          <option value={30}>Last 30 Days</option>
        </select>
      </div>

      {loading ? (
        <div className="py-12 text-center text-xs text-slate-400">Loading analytics telemetry...</div>
      ) : (
        <div className="space-y-6">
          {/* Summary KPIs */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs space-y-2">
              <div className="flex items-center justify-between text-slate-400 text-xs">
                <span>Total Queries</span>
                <Activity className="w-4 h-4 text-blue-600" />
              </div>
              <div className="text-xl font-bold text-slate-900">{data?.summary.total_queries || 0}</div>
              <p className="text-[10px] text-slate-400">Processed across all active roles</p>
            </div>

            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs space-y-2">
              <div className="flex items-center justify-between text-slate-400 text-xs">
                <span>ACL Denials Enforced</span>
                <ShieldAlert className="w-4 h-4 text-amber-600" />
              </div>
              <div className="text-xl font-bold text-amber-600">{data?.summary.acl_denials || 0}</div>
              <p className="text-[10px] text-slate-400">Unauthorized accesses blocked at boundary</p>
            </div>

            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs space-y-2">
              <div className="flex items-center justify-between text-slate-400 text-xs">
                <span>Prompt Injections Blocked</span>
                <ShieldAlert className="w-4 h-4 text-red-600" />
              </div>
              <div className="text-xl font-bold text-emerald-600">{data?.summary.prompt_injections || 0}</div>
              <p className="text-[10px] text-slate-400">Adversarial attempts neutralized</p>
            </div>

            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs space-y-2">
              <div className="flex items-center justify-between text-slate-400 text-xs">
                <span>Average Pipeline Latency</span>
                <Clock className="w-4 h-4 text-indigo-600" />
              </div>
              <div className="text-xl font-bold text-slate-900">
                {data?.summary.average_latency_ms || 0} ms
              </div>
              <p className="text-[10px] text-slate-400">Dense + Sparse + Rerank + LLM</p>
            </div>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Queries by Role */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-2xs space-y-4">
              <h3 className="text-xs font-bold text-slate-900">Query Volume by User Role</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={data?.role_distribution || []}
                      dataKey="count"
                      nameKey="role"
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      label={(entry: any) => `${entry.role || entry.name}: ${entry.count || entry.value}`}
                    >
                      {(data?.role_distribution || []).map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Decision Breakdown */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-2xs space-y-4">
              <h3 className="text-xs font-bold text-slate-900">ACL Decision Distribution (Allowed vs Denied)</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data?.decision_distribution || []}>
                    <XAxis dataKey="decision" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#2563eb" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Recent Telemetry Table */}
          <div className="bg-white border border-slate-200 rounded-xl shadow-2xs overflow-hidden">
            <div className="p-4 border-b border-slate-100 font-bold text-xs text-slate-900">
              Live Observability Request Log
            </div>
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase font-semibold text-[10px]">
                <tr>
                  <th className="px-4 py-3">Timestamp</th>
                  <th className="px-4 py-3">User</th>
                  <th className="px-4 py-3">Role</th>
                  <th className="px-4 py-3">Action</th>
                  <th className="px-4 py-3">ACL Decision</th>
                  <th className="px-4 py-3 text-right">Latency</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {(data?.recent_activity || []).map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="px-4 py-2.5 text-slate-500 font-mono text-[10px]">
                      {new Date(item.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="px-4 py-2.5 text-slate-800 font-medium">{item.user}</td>
                    <td className="px-4 py-2.5">
                      <span className="px-1.5 py-0.2 rounded bg-slate-100 text-slate-700 text-[10px] font-semibold">
                        {item.role}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-slate-600 font-mono text-[11px]">{item.action}</td>
                    <td className="px-4 py-2.5">
                      <span
                        className={`px-1.5 py-0.2 rounded text-[10px] font-semibold ${
                          item.decision === 'ALLOWED'
                            ? 'bg-emerald-50 text-emerald-700'
                            : 'bg-red-50 text-red-700'
                        }`}
                      >
                        {item.decision}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-right font-mono text-slate-600">
                      {item.latency_ms.toFixed(0)} ms
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
