import React, { useState } from 'react';
import CodeMirror from '@uiw/react-codemirror';
import { python } from '@codemirror/lang-python';
import { oneDark } from '@codemirror/theme-one-dark';
import { debugCode, executeCode } from '../api';
import { useApp } from '../context/AppContext';
import {
  Bug,
  Play,
  Wrench,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  RotateCcw,
  Sparkles,
  Terminal,
  ShieldCheck
} from 'lucide-react';

const sampleBuggyCode = `def calculate_average(numbers):
    # Bug: Division by zero when empty list passed
    total = sum(numbers)
    return total / len(numbers)

# Test run
print(calculate_average([]))`;

export default function Debugger() {
  const { activeModel, activeProject } = useApp();
  const [code, setCode] = useState(sampleBuggyCode);
  const [errorInput, setErrorInput] = useState('');
  const [executionOutput, setExecutionOutput] = useState(null);
  const [debugResult, setDebugResult] = useState(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [isDebugging, setIsDebugging] = useState(false);
  const [accepted, setAccepted] = useState(false);

  const handleExecute = async () => {
    setIsExecuting(true);
    setExecutionOutput(null);
    try {
      const res = await executeCode({ code });
      setExecutionOutput(res.data);
      if (!res.data.success && (res.data.stderr || res.data.traceback)) {
        setErrorInput(res.data.stderr || res.data.traceback);
      }
    } catch (err) {
      setExecutionOutput({
        success: false,
        error: 'Execution request failed',
        stderr: err.message
      });
    } finally {
      setIsExecuting(false);
    }
  };

  const handleDebug = async () => {
    if (!errorInput.trim()) {
      alert('Please run the code or provide an error traceback first.');
      return;
    }
    setIsDebugging(true);
    setAccepted(false);
    try {
      const res = await debugCode({
        code,
        error: errorInput,
        model: activeModel,
        project_id: activeProject?.id || null
      });
      setDebugResult(res.data);
    } catch (err) {
      alert('Debugging failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsDebugging(false);
    }
  };

  const handleAcceptCorrection = () => {
    if (debugResult?.corrected_code) {
      setCode(debugResult.corrected_code);
      setAccepted(true);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <Bug className="w-6 h-6 text-amber-400" />
          <span>Automated Code Debugger</span>
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Detect syntax and runtime errors, analyze Python tracebacks, diagnose root causes, and validate auto-generated fixes.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Code Editor & Execution Output */}
        <div className="space-y-4">
          <div className="bg-[#161b22] rounded-xl border border-[#30363d] overflow-hidden">
            <div className="flex justify-between items-center px-4 py-2 bg-[#21262d] border-b border-[#30363d] text-xs">
              <span className="font-mono text-gray-300">Target Python Code</span>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleExecute}
                  disabled={isExecuting}
                  className="flex items-center gap-1 px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded font-medium transition"
                >
                  <Play className="w-3 h-3 fill-white" />
                  <span>{isExecuting ? 'Running...' : 'Run in Sandbox'}</span>
                </button>
              </div>
            </div>
            <CodeMirror
              value={code}
              height="300px"
              theme={oneDark}
              extensions={[python()]}
              onChange={(val) => setCode(val)}
            />
          </div>

          {/* Execution Output Console */}
          <div className="bg-[#0d1117] rounded-xl border border-[#30363d] overflow-hidden">
            <div className="px-4 py-2 bg-[#161b22] border-b border-[#30363d] text-xs font-mono text-gray-400 flex items-center gap-2">
              <Terminal className="w-3.5 h-3.5 text-blue-400" />
              <span>Execution Output & Traceback</span>
            </div>
            <div className="p-4 font-mono text-xs max-h-40 overflow-y-auto">
              {executionOutput ? (
                <div>
                  {executionOutput.stdout && (
                    <div className="text-emerald-400 whitespace-pre-wrap">{executionOutput.stdout}</div>
                  )}
                  {(executionOutput.stderr || executionOutput.traceback) && (
                    <div className="text-red-400 whitespace-pre-wrap">
                      {executionOutput.stderr || executionOutput.traceback}
                    </div>
                  )}
                  {executionOutput.error && !executionOutput.stderr && (
                    <div className="text-amber-400">{executionOutput.error}</div>
                  )}
                </div>
              ) : (
                <div className="text-gray-500 italic">Click 'Run in Sandbox' to execute.</div>
              )}
            </div>
          </div>

          {/* Traceback Manual Input */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-gray-300 block">
              Error / Traceback Description
            </label>
            <textarea
              rows={3}
              value={errorInput}
              onChange={(e) => setErrorInput(e.target.value)}
              placeholder="Paste Python error traceback here or run code above to auto-populate..."
              className="w-full bg-[#161b22] border border-[#30363d] rounded-lg p-2.5 text-xs text-gray-200 font-mono placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition"
            />
            <button
              onClick={handleDebug}
              disabled={isDebugging}
              className="flex items-center gap-2 px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-xs font-semibold transition"
            >
              <Wrench className="w-3.5 h-3.5" />
              <span>{isDebugging ? 'Analyzing Error...' : 'Run Debugger Agent'}</span>
            </button>
          </div>
        </div>

        {/* Right Column: Diagnosis & Proposed Correction */}
        <div className="space-y-4">
          {debugResult ? (
            <div className="bg-[#161b22] p-5 rounded-xl border border-[#30363d] space-y-4">
              <div className="flex justify-between items-center border-b border-[#30363d] pb-3">
                <div>
                  <h3 className="text-sm font-semibold text-white">Root Cause Analysis</h3>
                  <span className="text-xs text-amber-400 font-mono">
                    Category: {debugResult.error_category || 'runtime'}
                  </span>
                </div>
                <span className="px-2 py-0.5 rounded text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  Confidence: {debugResult.confidence || 'high'}
                </span>
              </div>

              {/* Explanation of fix */}
              <div className="p-3 bg-[#0d1117] rounded-lg border border-[#30363d] text-xs text-gray-300 leading-relaxed">
                <span className="text-gray-400 font-semibold block mb-1">Diagnosis:</span>
                {debugResult.root_cause || debugResult.explanation}
              </div>

              {/* Corrected Code Editor */}
              <div className="space-y-1">
                <span className="text-xs font-semibold text-gray-300 block">Proposed Working Code:</span>
                <div className="rounded-lg overflow-hidden border border-[#30363d]">
                  <CodeMirror
                    value={debugResult.corrected_code || '# No corrected code'}
                    height="240px"
                    theme={oneDark}
                    extensions={[python()]}
                    editable={false}
                  />
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex justify-between items-center pt-2">
                <div className="text-xs text-gray-400 font-mono">
                  Syntax Validated: {debugResult.syntax_valid ? 'Yes (AST verified)' : 'Unverified'}
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleAcceptCorrection}
                    disabled={accepted}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold transition"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>{accepted ? 'Applied to Editor' : 'Accept Correction'}</span>
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-[#161b22] p-10 rounded-xl border border-[#30363d] text-center space-y-3">
              <Wrench className="w-10 h-10 text-gray-500 mx-auto" />
              <h3 className="text-sm font-medium text-gray-300">No Active Debug Analysis</h3>
              <p className="text-xs text-gray-500 max-w-sm mx-auto">
                Trigger an execution error on the left or paste a traceback, then run the Debugger Agent.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
