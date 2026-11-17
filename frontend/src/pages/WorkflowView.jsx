import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import CodeMirror from '@uiw/react-codemirror';
import { python } from '@codemirror/lang-python';
import { oneDark } from '@codemirror/theme-one-dark';
import { getWorkflow, submitApproval } from '../api';
import { useApp } from '../context/AppContext';
import {
  Network,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Terminal,
  FileCode,
  ShieldCheck,
  BookOpen,
  Cpu,
  RefreshCw,
  Copy,
  Download,
  Check,
  ThumbsUp,
  ThumbsDown
} from 'lucide-react';

const agentOrder = [
  { key: 'planner', name: 'Planner Agent', desc: 'Requirements analysis & decomposition' },
  { key: 'code_generator', name: 'Code Generator', desc: 'Python source code generation' },
  { key: 'code_reviewer', name: 'Code Reviewer', desc: 'AST & Ruff static analysis + AI review' },
  { key: 'test_generator', name: 'Test Generator', desc: 'Pytest unit test generation & execution' },
  { key: 'debugger', name: 'Debugger Agent', desc: 'Traceback root-cause analysis & correction' },
  { key: 'explainer', name: 'Code Explainer', desc: 'Algorithmic breakdown & explainability' }
];

export default function WorkflowView() {
  const location = useLocation();
  const { currentTaskId, setCurrentTaskId } = useApp();
  const taskId = location.state?.taskId || currentTaskId;

  const [workflow, setWorkflow] = useState(null);
  const [logs, setLogs] = useState([]);
  const [activeTab, setActiveTab] = useState('code');
  const [copied, setCopied] = useState(false);
  const [approvalSubmitting, setApprovalSubmitting] = useState(false);
  const [approvalRecorded, setApprovalRecorded] = useState(null);

  useEffect(() => {
    if (!taskId) return;
    setCurrentTaskId(taskId);

    // Initial fetch
    async function fetchStatus() {
      try {
        const res = await getWorkflow(taskId);
        setWorkflow(res.data);
        if (res.data.execution_logs) {
          setLogs(res.data.execution_logs);
        }
      } catch (err) {
        console.error('Fetch workflow error:', err);
      }
    }
    fetchStatus();

    // SSE EventSource for real-time progress
    const eventSource = new EventSource(`/api/workflow/${taskId}/events`);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'log') {
          setLogs((prev) => [...prev, data.message]);
        } else if (data.type === 'status') {
          setWorkflow((prev) => ({
            ...prev,
            workflow_status: data.workflow_status,
            agent_statuses: data.agent_statuses
          }));
        } else if (data.type === 'done') {
          // Re-fetch complete state
          fetchStatus();
          eventSource.close();
        }
      } catch (e) {
        console.error('SSE parse error:', e);
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
      // Fallback periodic poll if SSE connection drops
      const poll = setInterval(fetchStatus, 3000);
      return () => clearInterval(poll);
    };

    return () => {
      eventSource.close();
    };
  }, [taskId]);

  const handleCopyCode = () => {
    if (workflow?.generated_code) {
      navigator.clipboard.writeText(workflow.generated_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownloadCode = () => {
    if (workflow?.generated_code) {
      const blob = new Blob([workflow.generated_code], { type: 'text/x-python' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'solution.py';
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  const handleApproval = async (approved) => {
    setApprovalSubmitting(true);
    try {
      await submitApproval(taskId, approved, approved ? 'Approved by operator' : 'Rejected by operator');
      setApprovalRecorded(approved ? 'approved' : 'rejected');
    } catch (err) {
      console.error('Approval failed:', err);
    } finally {
      setApprovalSubmitting(false);
    }
  };

  if (!taskId) {
    return (
      <div className="p-8 max-w-4xl mx-auto text-center space-y-4">
        <Network className="w-12 h-12 text-gray-500 mx-auto" />
        <h2 className="text-lg font-semibold text-gray-300">No Active Workflow Selected</h2>
        <p className="text-xs text-gray-500">
          Start a new code generation task from the AI Generator page or pick one from History.
        </p>
      </div>
    );
  }

  const agentStatuses = workflow?.agent_statuses || {};

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Top Banner with Task Status */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center bg-[#161b22] p-5 rounded-xl border border-[#30363d] gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
              <Network className="w-5 h-5 text-indigo-400" />
              <span>Multi-Agent Orchestration Flow</span>
            </h1>
            <span
              className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
                workflow?.workflow_status === 'completed'
                  ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-400'
                  : workflow?.workflow_status === 'failed'
                  ? 'bg-red-500/10 border border-red-500/30 text-red-400'
                  : 'bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 animate-pulse'
              }`}
            >
              {workflow?.workflow_status || 'running'}
            </span>
          </div>
          <p className="text-xs text-gray-400 font-mono">Task ID: {taskId}</p>
        </div>

        {/* Human Governance Action Checkpoint */}
        {workflow?.workflow_status === 'completed' && !approvalRecorded && (
          <div className="flex items-center gap-2 bg-[#21262d] px-3 py-1.5 rounded-lg border border-[#30363d]">
            <span className="text-xs text-gray-300 font-medium">Human Approval:</span>
            <button
              onClick={() => handleApproval(true)}
              disabled={approvalSubmitting}
              className="flex items-center gap-1 px-2.5 py-1 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 rounded text-xs font-medium border border-emerald-500/30 transition"
            >
              <ThumbsUp className="w-3 h-3" />
              <span>Approve</span>
            </button>
            <button
              onClick={() => handleApproval(false)}
              disabled={approvalSubmitting}
              className="flex items-center gap-1 px-2.5 py-1 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded text-xs font-medium border border-red-500/30 transition"
            >
              <ThumbsDown className="w-3 h-3" />
              <span>Reject</span>
            </button>
          </div>
        )}

        {approvalRecorded && (
          <div
            className={`text-xs px-3 py-1.5 rounded-lg border font-medium ${
              approvalRecorded === 'approved'
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                : 'bg-red-500/10 border-red-500/30 text-red-400'
            }`}
          >
            Human Decision: {approvalRecorded.toUpperCase()}
          </div>
        )}
      </div>

      {/* Six Agent Grid Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {agentOrder.map((item, idx) => {
          const info = agentStatuses[item.key];
          const status = info?.status || 'pending';

          return (
            <div
              key={item.key}
              className={`p-4 rounded-xl border transition-all ${
                status === 'running'
                  ? 'bg-indigo-950/20 border-indigo-500/50 shadow-md shadow-indigo-500/10'
                  : status === 'completed'
                  ? 'bg-[#161b22] border-[#30363d]'
                  : status === 'failed'
                  ? 'bg-red-950/20 border-red-500/40'
                  : 'bg-[#161b22]/50 border-[#30363d]/40 opacity-70'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-gray-500">#{idx + 1}</span>
                  <h3 className="text-sm font-semibold text-gray-200">{item.name}</h3>
                </div>

                {/* Status Indicator */}
                {status === 'completed' && (
                  <span className="flex items-center gap-1 text-[11px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                    <CheckCircle2 className="w-3 h-3" />
                    <span>Done</span>
                  </span>
                )}
                {status === 'running' && (
                  <span className="flex items-center gap-1 text-[11px] text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded-full border border-indigo-500/30 animate-pulse">
                    <RefreshCw className="w-3 h-3 animate-spin" />
                    <span>Working...</span>
                  </span>
                )}
                {status === 'failed' && (
                  <span className="flex items-center gap-1 text-[11px] text-red-400 bg-red-500/10 px-2 py-0.5 rounded-full border border-red-500/20">
                    <AlertTriangle className="w-3 h-3" />
                    <span>Failed</span>
                  </span>
                )}
                {status === 'pending' && (
                  <span className="text-[11px] text-gray-500 bg-[#21262d] px-2 py-0.5 rounded-full border border-[#30363d]">
                    Pending
                  </span>
                )}
              </div>

              <p className="text-xs text-gray-400 mb-3">{item.desc}</p>

              {/* Execution duration & summary */}
              <div className="pt-2 border-t border-[#30363d]/50 text-[11px] space-y-1">
                <div className="flex justify-between text-gray-500">
                  <span>Duration:</span>
                  <span className="font-mono text-gray-300">
                    {info?.duration ? `${info.duration}s` : '--'}
                  </span>
                </div>
                {info?.output_summary && (
                  <p className="text-gray-300 font-sans truncate" title={info.output_summary}>
                    {info.output_summary}
                  </p>
                )}
                {info?.error && (
                  <p className="text-red-400 font-mono truncate" title={info.error}>
                    Err: {info.error}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Live SSE Execution Log Console */}
      <div className="bg-[#0d1117] rounded-xl border border-[#30363d] overflow-hidden">
        <div className="px-4 py-2.5 bg-[#161b22] border-b border-[#30363d] flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-mono text-gray-400">
            <Terminal className="w-3.5 h-3.5 text-indigo-400" />
            <span>Workflow Execution Tracing Console (Live SSE)</span>
          </div>
          <span className="text-[11px] text-gray-500 font-mono">{logs.length} events</span>
        </div>
        <div className="p-4 font-mono text-xs text-gray-300 max-h-48 overflow-y-auto space-y-1">
          {logs.length > 0 ? (
            logs.map((log, i) => (
              <div key={i} className="leading-relaxed">
                <span className="text-indigo-400 select-none">&gt; </span>
                {log}
              </div>
            ))
          ) : (
            <div className="text-gray-500 italic">Awaiting agent execution events...</div>
          )}
        </div>
      </div>

      {/* Results Tabs: Generated Code, Plan, Review, Tests, Explainability */}
      <div className="bg-[#161b22] rounded-xl border border-[#30363d] overflow-hidden">
        <div className="flex border-b border-[#30363d] bg-[#161b22] px-4 pt-2 gap-2 text-xs font-medium">
          <button
            onClick={() => setActiveTab('code')}
            className={`pb-2.5 px-3 border-b-2 transition flex items-center gap-1.5 ${
              activeTab === 'code'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >
            <FileCode className="w-3.5 h-3.5" />
            <span>Generated Python Code</span>
          </button>
          <button
            onClick={() => setActiveTab('plan')}
            className={`pb-2.5 px-3 border-b-2 transition flex items-center gap-1.5 ${
              activeTab === 'plan'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >
            <span>Implementation Plan</span>
          </button>
          <button
            onClick={() => setActiveTab('review')}
            className={`pb-2.5 px-3 border-b-2 transition flex items-center gap-1.5 ${
              activeTab === 'review'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Code Review</span>
          </button>
          <button
            onClick={() => setActiveTab('tests')}
            className={`pb-2.5 px-3 border-b-2 transition flex items-center gap-1.5 ${
              activeTab === 'tests'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Unit Tests</span>
          </button>
          <button
            onClick={() => setActiveTab('explainer')}
            className={`pb-2.5 px-3 border-b-2 transition flex items-center gap-1.5 ${
              activeTab === 'explainer'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>Explanation</span>
          </button>
        </div>

        {/* Tab 1: Code */}
        {activeTab === 'code' && (
          <div>
            <div className="flex justify-between items-center px-4 py-2 bg-[#21262d] border-b border-[#30363d] text-xs">
              <span className="font-mono text-gray-400">solution.py</span>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleCopyCode}
                  className="flex items-center gap-1 px-2.5 py-1 bg-[#161b22] hover:bg-[#30363d] text-gray-300 rounded border border-[#30363d] transition"
                >
                  {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  <span>{copied ? 'Copied' : 'Copy'}</span>
                </button>
                <button
                  onClick={handleDownloadCode}
                  className="flex items-center gap-1 px-2.5 py-1 bg-[#161b22] hover:bg-[#30363d] text-gray-300 rounded border border-[#30363d] transition"
                >
                  <Download className="w-3 h-3" />
                  <span>Download</span>
                </button>
              </div>
            </div>
            <CodeMirror
              value={workflow?.generated_code || '# Code generation in progress or pending...'}
              height="380px"
              theme={oneDark}
              extensions={[python()]}
              editable={false}
            />
          </div>
        )}

        {/* Tab 2: Implementation Plan */}
        {activeTab === 'plan' && (
          <div className="p-6 space-y-4 text-xs">
            {workflow?.implementation_plan ? (
              <>
                <div className="p-3 bg-[#21262d] rounded-lg border border-[#30363d]">
                  <span className="font-semibold text-gray-200 block mb-1">Problem Understanding:</span>
                  <p className="text-gray-400">
                    {workflow.implementation_plan.problem_understanding}
                  </p>
                </div>

                <div className="space-y-2">
                  <span className="font-semibold text-gray-200 block">Decomposed Steps:</span>
                  <div className="space-y-2">
                    {workflow.implementation_plan.implementation_plan?.map((s, idx) => (
                      <div key={idx} className="p-3 bg-[#0d1117] rounded-lg border border-[#30363d]">
                        <span className="text-indigo-400 font-mono font-medium">
                          Step {s.step}: {s.description}
                        </span>
                        <p className="text-gray-400 mt-1">{s.details}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <p className="text-gray-500">Plan not yet generated.</p>
            )}
          </div>
        )}

        {/* Tab 3: Code Review */}
        {activeTab === 'review' && (
          <div className="p-6 space-y-4 text-xs">
            {workflow?.review_results ? (
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 bg-[#21262d] rounded-lg border border-[#30363d]">
                  <span className="font-semibold text-gray-200">Overall Quality:</span>
                  <span className="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-400 font-medium capitalize">
                    {workflow.review_results.overall_quality}
                  </span>
                </div>
                <div className="space-y-2">
                  <span className="font-semibold text-gray-200 block">Findings & Recommendations:</span>
                  {workflow.review_results.findings?.map((f, idx) => (
                    <div key={idx} className="p-3 bg-[#0d1117] rounded-lg border border-[#30363d] space-y-1">
                      <div className="flex items-center gap-2">
                        <span
                          className={`px-1.5 py-0.5 rounded text-[10px] uppercase font-semibold ${
                            f.severity === 'critical' || f.severity === 'high'
                              ? 'bg-red-500/20 text-red-400'
                              : 'bg-amber-500/20 text-amber-400'
                          }`}
                        >
                          {f.severity || 'info'}
                        </span>
                        <span className="text-gray-400 text-[11px] font-mono">[{f.source || 'review'}]</span>
                        <span className="text-gray-200 font-medium">{f.description || f.message}</span>
                      </div>
                      {f.suggestion && <p className="text-gray-400 text-[11px] pl-2 border-l border-gray-700">{f.suggestion}</p>}
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-gray-500">Review not yet completed.</p>
            )}
          </div>
        )}

        {/* Tab 4: Tests */}
        {activeTab === 'tests' && (
          <div className="p-6 space-y-4 text-xs">
            {workflow?.test_results ? (
              <div className="space-y-3">
                <div className="flex gap-4 p-3 bg-[#21262d] rounded-lg border border-[#30363d]">
                  <div>
                    <span className="text-gray-500 block">Total Tests</span>
                    <span className="text-lg font-bold text-gray-200">{workflow.test_results.total_tests}</span>
                  </div>
                  <div>
                    <span className="text-gray-500 block">Passed</span>
                    <span className="text-lg font-bold text-emerald-400">{workflow.test_results.passed_tests}</span>
                  </div>
                  <div>
                    <span className="text-gray-500 block">Failed</span>
                    <span className="text-lg font-bold text-red-400">{workflow.test_results.failed_tests}</span>
                  </div>
                </div>

                <div className="bg-[#0d1117] p-3 rounded-lg border border-[#30363d] font-mono text-gray-300 whitespace-pre-wrap">
                  {workflow.test_results.test_output}
                </div>
              </div>
            ) : (
              <p className="text-gray-500">Unit tests not executed yet.</p>
            )}
          </div>
        )}

        {/* Tab 5: Explainer */}
        {activeTab === 'explainer' && (
          <div className="p-6 space-y-4 text-xs">
            {workflow?.explanation ? (
              <div className="space-y-4">
                <div className="p-3 bg-[#21262d] rounded-lg border border-[#30363d]">
                  <span className="font-semibold text-gray-200 block mb-1">Overview:</span>
                  <p className="text-gray-300 leading-relaxed">{workflow.explanation.overview}</p>
                </div>

                <div className="space-y-2">
                  <span className="font-semibold text-gray-200 block">Functions Breakdown:</span>
                  {workflow.explanation.functions?.map((fn, idx) => (
                    <div key={idx} className="p-3 bg-[#0d1117] rounded-lg border border-[#30363d] space-y-1">
                      <div className="flex justify-between items-center">
                        <span className="font-mono text-indigo-400 font-semibold">{fn.name}()</span>
                        {fn.complexity && <span className="text-gray-500 font-mono text-[11px]">{fn.complexity}</span>}
                      </div>
                      <p className="text-gray-400">{fn.explanation || fn.purpose}</p>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-gray-500">Explanation not yet formulated.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
