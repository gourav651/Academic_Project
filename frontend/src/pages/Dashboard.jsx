import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getStats, getHistory, getProjects } from '../api';
import {
  Activity,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Sparkles,
  ShieldAlert,
  ArrowRight,
  TrendingUp,
  Cpu
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';

export default function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [history, setHistory] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [statsRes, historyRes, projectsRes] = await Promise.all([
          getStats(),
          getHistory(),
          getProjects()
        ]);
        setStats(statsRes.data);
        setHistory(historyRes.data);
        setProjects(projectsRes.data);
      } catch (err) {
        console.error('Failed to load dashboard metrics:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const pieData = stats
    ? [
        { name: 'Completed', value: stats.efficiency.total_workflow_runs - stats.resilience.failed_workflows, color: '#10b981' },
        { name: 'Failed', value: stats.resilience.failed_workflows, color: '#ef4444' }
      ]
    : [];

  const accuracyData = stats
    ? [
        { name: 'Passed', count: stats.accuracy.passed_tests, fill: '#3b82f6' },
        { name: 'Failed', count: stats.accuracy.total_tests_executed - stats.accuracy.passed_tests, fill: '#f59e0b' }
      ]
    : [];

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header Banner */}
      <div className="flex justify-between items-center bg-gradient-to-r from-indigo-950/40 via-[#161b22] to-[#161b22] p-6 rounded-xl border border-indigo-500/20">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Autonomous Software Engineering Dashboard
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Empirical metrics across the 5 core research dimensions: Efficiency, Accuracy, Resilience, Governance & Scalability.
          </p>
        </div>
        <button
          onClick={() => navigate('/generate')}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition shadow-lg shadow-indigo-600/20"
        >
          <Sparkles className="w-4 h-4" />
          <span>New AI Generation</span>
        </button>
      </div>

      {/* KPI Cards across the 5 Dimensions */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Dimension 1: Efficiency */}
        <div className="bg-[#161b22] p-5 rounded-xl border border-[#30363d] space-y-2">
          <div className="flex items-center justify-between text-gray-400">
            <span className="text-xs font-medium uppercase tracking-wider">Dimension A: Efficiency</span>
            <Activity className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {stats ? stats.efficiency.total_workflow_runs : 0}
          </div>
          <div className="text-xs text-gray-400 flex items-center gap-1">
            <span>Total Workflows run | Avg.</span>
            <span className="text-indigo-400 font-mono">
              {stats ? `${stats.efficiency.average_agent_duration_seconds}s` : '0s'}
            </span>
          </div>
        </div>

        {/* Dimension 2: Accuracy */}
        <div className="bg-[#161b22] p-5 rounded-xl border border-[#30363d] space-y-2">
          <div className="flex items-center justify-between text-gray-400">
            <span className="text-xs font-medium uppercase tracking-wider">Dimension B: Accuracy</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400">
            {stats ? `${stats.accuracy.test_pass_rate_percent}%` : '0%'}
          </div>
          <div className="text-xs text-gray-400 flex items-center gap-1">
            <span>Automated Pytest pass rate (</span>
            <span className="text-emerald-400 font-mono">
              {stats ? `${stats.accuracy.passed_tests}/${stats.accuracy.total_tests_executed}` : '0/0'}
            </span>
            <span>)</span>
          </div>
        </div>

        {/* Dimension 3: Resilience */}
        <div className="bg-[#161b22] p-5 rounded-xl border border-[#30363d] space-y-2">
          <div className="flex items-center justify-between text-gray-400">
            <span className="text-xs font-medium uppercase tracking-wider">Dimension C: Resilience</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-400">
            {stats ? stats.resilience.total_debugging_attempts : 0}
          </div>
          <div className="text-xs text-gray-400 flex items-center gap-1">
            <span>Self-Debug attempts (</span>
            <span className="text-emerald-400 font-mono">
              {stats ? stats.resilience.successful_debug_recoveries : 0} recovered
            </span>
            <span>)</span>
          </div>
        </div>

        {/* Dimension 4: Governance */}
        <div className="bg-[#161b22] p-5 rounded-xl border border-[#30363d] space-y-2">
          <div className="flex items-center justify-between text-gray-400">
            <span className="text-xs font-medium uppercase tracking-wider">Dimension D: Governance</span>
            <ShieldAlert className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-blue-400">
            {stats ? stats.governance.recorded_audit_logs : 0}
          </div>
          <div className="text-xs text-gray-400 flex items-center gap-1">
            <span>Audit logs |</span>
            <span className="text-emerald-400">{stats ? stats.governance.approved_modifications : 0} approved</span>
          </div>
        </div>
      </div>

      {/* Analytics Visualizations */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chart 1: Workflow Success vs Failure */}
        <div className="bg-[#161b22] p-5 rounded-xl border border-[#30363d] space-y-4">
          <h3 className="text-sm font-semibold text-gray-200">Workflow Execution Outcomes</h3>
          <div className="h-48 flex items-center justify-center">
            {stats && stats.efficiency.total_workflow_runs > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={60} label>
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-xs text-gray-500">No workflow runs recorded yet</p>
            )}
          </div>
        </div>

        {/* Chart 2: Test Case Results */}
        <div className="bg-[#161b22] p-5 rounded-xl border border-[#30363d] space-y-4">
          <h3 className="text-sm font-semibold text-gray-200">Pytest Verification Suite</h3>
          <div className="h-48 flex items-center justify-center">
            {stats && stats.accuracy.total_tests_executed > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={accuracyData}>
                  <XAxis dataKey="name" stroke="#8b949e" fontSize={12} />
                  <YAxis stroke="#8b949e" fontSize={12} />
                  <Tooltip />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-xs text-gray-500">No unit tests run yet</p>
            )}
          </div>
        </div>

        {/* Scalability: 6 Specialized Agents Architecture */}
        <div className="bg-[#161b22] p-5 rounded-xl border border-[#30363d] space-y-3">
          <h3 className="text-sm font-semibold text-gray-200 flex items-center gap-2">
            <Cpu className="w-4 h-4 text-indigo-400" />
            <span>Dimension E: Agent Collaboration</span>
          </h3>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between items-center p-2 rounded bg-[#21262d] border border-[#30363d]/50">
              <span className="text-gray-300 font-medium">1. Planner Agent</span>
              <span className="text-indigo-400 text-[11px]">Decomposition</span>
            </div>
            <div className="flex justify-between items-center p-2 rounded bg-[#21262d] border border-[#30363d]/50">
              <span className="text-gray-300 font-medium">2. Code Generator</span>
              <span className="text-indigo-400 text-[11px]">Python Synthesis</span>
            </div>
            <div className="flex justify-between items-center p-2 rounded bg-[#21262d] border border-[#30363d]/50">
              <span className="text-gray-300 font-medium">3. Code Reviewer</span>
              <span className="text-indigo-400 text-[11px]">AST + Ruff + AI</span>
            </div>
            <div className="flex justify-between items-center p-2 rounded bg-[#21262d] border border-[#30363d]/50">
              <span className="text-gray-300 font-medium">4. Debugger Agent</span>
              <span className="text-indigo-400 text-[11px]">Root-Cause Fix</span>
            </div>
            <div className="flex justify-between items-center p-2 rounded bg-[#21262d] border border-[#30363d]/50">
              <span className="text-gray-300 font-medium">5. Test Generator</span>
              <span className="text-indigo-400 text-[11px]">Pytest Runner</span>
            </div>
            <div className="flex justify-between items-center p-2 rounded bg-[#21262d] border border-[#30363d]/50">
              <span className="text-gray-300 font-medium">6. Code Explainer</span>
              <span className="text-indigo-400 text-[11px]">Pedagogical Trace</span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Workflow Runs */}
      <div className="bg-[#161b22] rounded-xl border border-[#30363d] overflow-hidden">
        <div className="p-5 border-b border-[#30363d] flex justify-between items-center">
          <h3 className="font-semibold text-sm text-gray-200">Recent Autonomous Engineering Runs</h3>
          <span className="text-xs text-gray-400">{history.length} records in SQLite</span>
        </div>
        <div className="divide-y divide-[#30363d]">
          {history.length > 0 ? (
            history.slice(0, 6).map((run) => (
              <div
                key={run.task_id}
                className="p-4 flex items-center justify-between hover:bg-[#21262d] transition"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={`w-2 h-2 rounded-full ${
                        run.workflow_status === 'completed'
                          ? 'bg-emerald-400'
                          : run.workflow_status === 'running'
                          ? 'bg-blue-400 animate-pulse'
                          : 'bg-red-400'
                      }`}
                    />
                    <span className="text-sm font-medium text-gray-200 truncate max-w-xl">
                      {run.requirement}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500 font-mono flex items-center gap-3">
                    <span>Task: {run.task_id.slice(0, 8)}...</span>
                    <span>Started: {new Date(run.started_at).toLocaleString()}</span>
                  </div>
                </div>

                <button
                  onClick={() => navigate('/workflow', { state: { taskId: run.task_id } })}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-[#21262d] hover:bg-[#30363d] text-indigo-400 rounded-lg text-xs font-medium border border-[#30363d] transition"
                >
                  <span>Inspect Workflow</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            ))
          ) : (
            <div className="p-8 text-center text-sm text-gray-500">
              No autonomous engineering workflows run yet. Click 'New AI Generation' to start.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
