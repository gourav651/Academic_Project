import React, { useEffect, useState } from 'react';
import { getGovernance, getStats, getHistory, submitApproval } from '../api';
import { useApp } from '../context/AppContext';
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Clock,
  UserCheck,
  FileText,
  ThumbsUp,
  ThumbsDown,
  Layers,
  ArrowRight
} from 'lucide-react';

export default function Governance() {
  const { currentTaskId } = useApp();
  const [history, setHistory] = useState([]);
  const [selectedTaskId, setSelectedTaskId] = useState(currentTaskId || '');
  const [auditData, setAuditData] = useState(null);
  const [stats, setStats] = useState(null);
  const [approvalReason, setApprovalReason] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function init() {
      try {
        const [histRes, statsRes] = await Promise.all([getHistory(), getStats()]);
        setHistory(histRes.data);
        setStats(statsRes.data);
        if (histRes.data.length > 0 && !selectedTaskId) {
          setSelectedTaskId(histRes.data[0].task_id);
        }
      } catch (err) {
        console.error('Failed to load governance records:', err);
      }
    }
    init();
  }, []);

  useEffect(() => {
    if (!selectedTaskId) return;
    async function loadAudit() {
      setLoading(true);
      try {
        const res = await getGovernance(selectedTaskId);
        setAuditData(res.data);
      } catch (err) {
        console.error('Audit fetch failed:', err);
      } finally {
        setLoading(false);
      }
    }
    loadAudit();
  }, [selectedTaskId]);

  const handleDecision = async (approved) => {
    if (!selectedTaskId) return;
    try {
      await submitApproval(selectedTaskId, approved, approvalReason);
      setApprovalReason('');
      const res = await getGovernance(selectedTaskId);
      setAuditData(res.data);
      const statsRes = await getStats();
      setStats(statsRes.data);
    } catch (err) {
      alert('Decision record failed: ' + err.message);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <ShieldCheck className="w-6 h-6 text-indigo-400" />
          <span>Governance, Accountability & Audit Logs</span>
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Full decision traceability, immutable audit trail, agent execution records, and human-in-the-loop oversight checkpoints.
        </p>
      </div>

      {/* KPI Cards for Governance & Oversight */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-[#161b22] p-5 rounded-xl border border-[#30363d] space-y-1">
          <span className="text-xs text-gray-400 font-medium uppercase tracking-wider">
            Total Audit Records
          </span>
          <div className="text-2xl font-bold text-white">
            {stats ? stats.governance.recorded_audit_logs : 0}
          </div>
          <p className="text-xs text-gray-500">Every agent transition recorded in SQLite</p>
        </div>

        <div className="bg-[#161b22] p-5 rounded-xl border border-[#30363d] space-y-1">
          <span className="text-xs text-gray-400 font-medium uppercase tracking-wider">
            Approved Code Modifications
          </span>
          <div className="text-2xl font-bold text-emerald-400">
            {stats ? stats.governance.approved_modifications : 0}
          </div>
          <p className="text-xs text-gray-500">Verified by human operator</p>
        </div>

        <div className="bg-[#161b22] p-5 rounded-xl border border-[#30363d] space-y-1">
          <span className="text-xs text-gray-400 font-medium uppercase tracking-wider">
            Rejected Modifications
          </span>
          <div className="text-2xl font-bold text-red-400">
            {stats ? stats.governance.rejected_modifications : 0}
          </div>
          <p className="text-xs text-gray-500">Operator overrides preventing incorrect merges</p>
        </div>
      </div>

      {/* Task Selector Dropdown */}
      <div className="bg-[#161b22] p-4 rounded-xl border border-[#30363d] flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-300 font-medium">Select Workflow Task:</span>
          <select
            value={selectedTaskId}
            onChange={(e) => setSelectedTaskId(e.target.value)}
            className="bg-[#21262d] border border-[#30363d] text-xs text-gray-200 rounded-lg px-3 py-1.5 font-mono outline-none cursor-pointer"
          >
            {history.map((h) => (
              <option key={h.task_id} value={h.task_id}>
                {h.task_id.slice(0, 10)}... - {h.requirement.slice(0, 45)}... ({h.workflow_status})
              </option>
            ))}
          </select>
        </div>
        <span className="text-xs text-gray-400 font-mono">
          Status: {auditData?.workflow_status || '--'}
        </span>
      </div>

      {/* Human Decision Action Checkpoint Card */}
      <div className="bg-[#161b22] p-5 rounded-xl border border-[#30363d] space-y-3">
        <div className="flex items-center gap-2 text-sm font-semibold text-white">
          <UserCheck className="w-4 h-4 text-indigo-400" />
          <span>Human-in-the-Loop Governance Checkpoint</span>
        </div>
        <p className="text-xs text-gray-400">
          Ensure developer oversight before accepting or rolling back autonomous changes. Record approval decisions with audit justification.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 pt-2">
          <input
            type="text"
            value={approvalReason}
            onChange={(e) => setApprovalReason(e.target.value)}
            placeholder="Decision rationale / review comment (optional)..."
            className="flex-1 bg-[#0d1117] border border-[#30363d] rounded-lg px-3 py-2 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition"
          />
          <div className="flex gap-2">
            <button
              onClick={() => handleDecision(true)}
              className="flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold transition"
            >
              <ThumbsUp className="w-3.5 h-3.5" />
              <span>Approve Changes</span>
            </button>
            <button
              onClick={() => handleDecision(false)}
              className="flex items-center gap-1.5 px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg text-xs font-semibold transition"
            >
              <ThumbsDown className="w-3.5 h-3.5" />
              <span>Reject Changes</span>
            </button>
          </div>
        </div>
      </div>

      {/* Audit Logs Table */}
      <div className="bg-[#161b22] rounded-xl border border-[#30363d] overflow-hidden space-y-0">
        <div className="p-4 border-b border-[#30363d] flex justify-between items-center">
          <h3 className="text-sm font-semibold text-gray-200 flex items-center gap-2">
            <FileText className="w-4 h-4 text-indigo-400" />
            <span>Traceable Audit Log Records</span>
          </h3>
          <span className="text-xs text-gray-500 font-mono">
            {auditData?.audit_logs?.length || 0} entries
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#21262d] text-gray-400 border-b border-[#30363d] uppercase tracking-wider font-mono text-[11px]">
              <tr>
                <th className="px-4 py-3">Agent</th>
                <th className="px-4 py-3">Action</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Duration</th>
                <th className="px-4 py-3">Summary</th>
                <th className="px-4 py-3">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#30363d] font-sans">
              {auditData?.audit_logs?.length > 0 ? (
                auditData.audit_logs.map((log, i) => (
                  <tr key={i} className="hover:bg-[#21262d]/50 transition">
                    <td className="px-4 py-3 font-semibold text-indigo-400 font-mono">
                      {log.agent_name}
                    </td>
                    <td className="px-4 py-3 text-gray-300">{log.action}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-medium uppercase ${
                          log.status === 'completed'
                            ? 'bg-emerald-500/10 text-emerald-400'
                            : log.status === 'failed'
                            ? 'bg-red-500/10 text-red-400'
                            : 'bg-indigo-500/10 text-indigo-400'
                        }`}
                      >
                        {log.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono text-gray-400">
                      {log.duration ? `${log.duration}s` : '--'}
                    </td>
                    <td className="px-4 py-3 text-gray-300 max-w-md truncate" title={log.output_summary}>
                      {log.output_summary || log.error_info || '--'}
                    </td>
                    <td className="px-4 py-3 font-mono text-gray-500 text-[11px]">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                    No audit records recorded for this task yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
