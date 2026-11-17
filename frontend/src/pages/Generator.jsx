import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import CodeMirror from '@uiw/react-codemirror';
import { python } from '@codemirror/lang-python';
import { oneDark } from '@codemirror/theme-one-dark';
import { startWorkflow } from '../api';
import { useApp } from '../context/AppContext';
import {
  Sparkles,
  Play,
  Copy,
  Download,
  Check,
  FileCode,
  ListOrdered,
  ShieldCheck,
  BookOpen,
  ArrowRight,
  AlertCircle
} from 'lucide-react';

const examplePrompts = [
  'Implement a thread-safe LRU Cache with capacity limit, get() and put() methods.',
  'Write a Python function to validate credit card numbers using the Luhn algorithm.',
  'Implement a Binary Search Tree with insert, search, delete, and in-order traversal.',
  'Create a rate-limiting token bucket algorithm with configurable refill rate.'
];

export default function Generator() {
  const navigate = useNavigate();
  const { activeModel, activeProject, setCurrentTaskId, setWorkflowState } = useApp();
  const [requirement, setRequirement] = useState('');
  const [isStarting, setIsStarting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [copied, setCopied] = useState(false);

  const handleStartWorkflow = async () => {
    if (!requirement.trim()) {
      setErrorMsg('Please enter a software requirement or choose an example.');
      return;
    }
    setErrorMsg('');
    setIsStarting(true);

    try {
      const res = await startWorkflow({
        requirement: requirement.trim(),
        project_id: activeProject?.id || null,
        model: activeModel
      });

      const taskId = res.data.task_id;
      setCurrentTaskId(taskId);
      navigate('/workflow', { state: { taskId } });
    } catch (err) {
      console.error('Workflow start failed:', err);
      setErrorMsg(
        err.response?.data?.detail || 'Failed to start workflow. Check backend status.'
      );
    } finally {
      setIsStarting(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
          <Sparkles className="w-6 h-6 text-indigo-400" />
          <span>Autonomous Code Generation</span>
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Decompose natural language requirements into implementation plans, executable Python code, unit tests, and review findings.
        </p>
      </div>

      {/* Input Form Card */}
      <div className="bg-[#161b22] p-6 rounded-xl border border-[#30363d] space-y-4">
        <label className="block text-sm font-medium text-gray-200">
          Software Specification / Natural Language Requirement
        </label>
        <textarea
          rows={4}
          value={requirement}
          onChange={(e) => setRequirement(e.target.value)}
          placeholder="E.g., Write a thread-safe LRU Cache in Python with get and put methods, handling capacity eviction..."
          className="w-full bg-[#0d1117] border border-[#30363d] rounded-lg p-3 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition font-sans"
        />

        {/* Quick Example Chips */}
        <div className="space-y-1.5">
          <span className="text-xs text-gray-400">Quick Examples:</span>
          <div className="flex flex-wrap gap-2">
            {examplePrompts.map((prompt, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setRequirement(prompt)}
                className="text-xs bg-[#21262d] hover:bg-[#30363d] text-gray-300 hover:text-white px-2.5 py-1 rounded-md border border-[#30363d] transition text-left"
              >
                {prompt.length > 55 ? `${prompt.slice(0, 55)}...` : prompt}
              </button>
            ))}
          </div>
        </div>

        {errorMsg && (
          <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-xs text-red-400">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        <div className="flex justify-between items-center pt-2">
          <div className="text-xs text-gray-400 font-mono">
            Model: <span className="text-indigo-400">{activeModel}</span>
          </div>

          <button
            onClick={handleStartWorkflow}
            disabled={isStarting}
            className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-sm font-semibold transition shadow-lg shadow-indigo-600/20"
          >
            {isStarting ? (
              <>
                <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                <span>Launching Multi-Agent Pipeline...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white" />
                <span>Start Autonomous Generation</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Info Card explaining what happens */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 bg-[#161b22] border border-[#30363d] rounded-xl space-y-1.5">
          <div className="flex items-center gap-2 text-indigo-400 text-sm font-medium">
            <ListOrdered className="w-4 h-4" />
            <span>1. Decomposition & Code Gen</span>
          </div>
          <p className="text-xs text-gray-400">
            Planner decomposes specifications into functional steps. Code Generator produces PEP-8 compliant Python code.
          </p>
        </div>

        <div className="p-4 bg-[#161b22] border border-[#30363d] rounded-xl space-y-1.5">
          <div className="flex items-center gap-2 text-emerald-400 text-sm font-medium">
            <ShieldCheck className="w-4 h-4" />
            <span>2. Static Analysis & Tests</span>
          </div>
          <p className="text-xs text-gray-400">
            Deterministic AST and Ruff linting check syntax and style. Test Generator creates Pytest suites executed in isolation.
          </p>
        </div>

        <div className="p-4 bg-[#161b22] border border-[#30363d] rounded-xl space-y-1.5">
          <div className="flex items-center gap-2 text-amber-400 text-sm font-medium">
            <BookOpen className="w-4 h-4" />
            <span>3. Self-Debug & Transparency</span>
          </div>
          <p className="text-xs text-gray-400">
            If errors occur, Debugger performs root-cause analysis and retry loops. Explainer provides step-by-step logic breakdown.
          </p>
        </div>
      </div>
    </div>
  );
}
