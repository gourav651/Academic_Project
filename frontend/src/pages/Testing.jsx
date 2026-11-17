import React, { useState } from 'react';
import CodeMirror from '@uiw/react-codemirror';
import { python } from '@codemirror/lang-python';
import { oneDark } from '@codemirror/theme-one-dark';
import { testCode } from '../api';
import { useApp } from '../context/AppContext';
import {
  CheckCircle2,
  XCircle,
  Play,
  FileCode,
  Terminal,
  ShieldCheck,
  ListOrdered
} from 'lucide-react';

const defaultTestCode = `def fibonacci(n):
    if not isinstance(n, int) or n < 0:
        raise ValueError("n must be a non-negative integer")
    if n in (0, 1):
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b`;

export default function Testing() {
  const { activeModel } = useApp();
  const [sourceCode, setSourceCode] = useState(defaultTestCode);
  const [testResult, setTestResult] = useState(null);
  const [isRunning, setIsRunning] = useState(false);

  const handleRunTests = async () => {
    setIsRunning(true);
    try {
      const res = await testCode({ code: sourceCode, model: activeModel });
      setTestResult(res.data);
    } catch (err) {
      alert('Test generation failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsRunning(false);
    }
  };

  const runResult = testResult?.run_result;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <CheckCircle2 className="w-6 h-6 text-emerald-400" />
          <span>Automated Unit Testing & Pytest Suite</span>
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Synthesize unit tests covering normal inputs, edge conditions, invalid parameters, and exception handling using Pytest.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Source Code */}
        <div className="space-y-4">
          <div className="bg-[#161b22] rounded-xl border border-[#30363d] overflow-hidden">
            <div className="flex justify-between items-center px-4 py-2 bg-[#21262d] border-b border-[#30363d] text-xs">
              <span className="font-mono text-gray-300">Target Python Code for Testing</span>
              <button
                onClick={handleRunTests}
                disabled={isRunning}
                className="flex items-center gap-1.5 px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded font-medium transition"
              >
                <Play className="w-3 h-3 fill-white" />
                <span>{isRunning ? 'Generating & Running...' : 'Generate & Run Tests'}</span>
              </button>
            </div>
            <CodeMirror
              value={sourceCode}
              height="340px"
              theme={oneDark}
              extensions={[python()]}
              onChange={(val) => setSourceCode(val)}
            />
          </div>

          {/* Test Strategy Info */}
          {testResult?.test_strategy && (
            <div className="p-4 bg-[#161b22] border border-[#30363d] rounded-xl text-xs space-y-1">
              <span className="font-semibold text-gray-300 block">Synthesized Test Strategy:</span>
              <p className="text-gray-400">{testResult.test_strategy}</p>
            </div>
          )}
        </div>

        {/* Generated Tests & Output */}
        <div className="space-y-4">
          {/* Test Metrics KPI */}
          {runResult && (
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-[#161b22] p-4 rounded-xl border border-[#30363d] text-center">
                <span className="text-xs text-gray-400 block">Total Tests</span>
                <span className="text-2xl font-bold text-gray-200">{runResult.total_tests}</span>
              </div>
              <div className="bg-[#161b22] p-4 rounded-xl border border-[#30363d] text-center">
                <span className="text-xs text-gray-400 block">Passed</span>
                <span className="text-2xl font-bold text-emerald-400">{runResult.passed_tests}</span>
              </div>
              <div className="bg-[#161b22] p-4 rounded-xl border border-[#30363d] text-center">
                <span className="text-xs text-gray-400 block">Failed</span>
                <span className="text-2xl font-bold text-red-400">{runResult.failed_tests}</span>
              </div>
            </div>
          )}

          {/* Generated Pytest Code */}
          <div className="bg-[#161b22] rounded-xl border border-[#30363d] overflow-hidden">
            <div className="px-4 py-2 bg-[#21262d] border-b border-[#30363d] text-xs font-mono text-gray-300">
              test_solution.py
            </div>
            <CodeMirror
              value={testResult?.test_code || '# Click "Generate & Run Tests" to synthesize tests'}
              height="240px"
              theme={oneDark}
              extensions={[python()]}
              editable={false}
            />
          </div>

          {/* Pytest Terminal Output */}
          <div className="bg-[#0d1117] rounded-xl border border-[#30363d] overflow-hidden">
            <div className="px-4 py-2 bg-[#161b22] border-b border-[#30363d] text-xs font-mono text-gray-400 flex items-center gap-2">
              <Terminal className="w-3.5 h-3.5 text-emerald-400" />
              <span>Pytest Runner Console Output</span>
            </div>
            <div className="p-4 font-mono text-xs text-gray-300 whitespace-pre-wrap max-h-48 overflow-y-auto">
              {runResult?.test_output || 'Awaiting test execution...'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
