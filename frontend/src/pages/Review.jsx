import React, { useState } from 'react';
import CodeMirror from '@uiw/react-codemirror';
import { python } from '@codemirror/lang-python';
import { oneDark } from '@codemirror/theme-one-dark';
import { reviewCode } from '../api';
import { useApp } from '../context/AppContext';
import {
  FileCode,
  ShieldCheck,
  AlertTriangle,
  Play,
  CheckCircle2,
  Cpu,
  Layers
} from 'lucide-react';

const sampleReviewCode = `def process_records(records):
    # Potential bare except & excessive parameters
    try:
        results = []
        for r in records:
            if r is "admin":
                results.append(r)
        return results
    except:
        pass`;

export default function Review() {
  const { activeModel } = useApp();
  const [code, setCode] = useState(sampleReviewCode);
  const [reviewResult, setReviewResult] = useState(null);
  const [isReviewing, setIsReviewing] = useState(false);

  const handleReview = async () => {
    setIsReviewing(true);
    try {
      const res = await reviewCode({ code, model: activeModel });
      setReviewResult(res.data?.review);
    } catch (err) {
      alert('Review failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsReviewing(false);
    }
  };

  const deterministicFindings = reviewResult?.findings?.filter((f) => f.source !== 'ai') || [];
  const aiFindings = reviewResult?.findings?.filter((f) => f.source === 'ai') || [];

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <FileCode className="w-6 h-6 text-indigo-400" />
          <span>Code Review & Deterministic Static Analysis</span>
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Combines deterministic Python AST inspections and Ruff linter findings with AI architectural review.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Code Input */}
        <div className="space-y-4">
          <div className="bg-[#161b22] rounded-xl border border-[#30363d] overflow-hidden">
            <div className="flex justify-between items-center px-4 py-2 bg-[#21262d] border-b border-[#30363d] text-xs">
              <span className="font-mono text-gray-300">Python Source Code for Review</span>
              <button
                onClick={handleReview}
                disabled={isReviewing}
                className="flex items-center gap-1.5 px-3 py-1 bg-indigo-600 hover:bg-indigo-500 text-white rounded font-medium transition"
              >
                <Play className="w-3 h-3 fill-white" />
                <span>{isReviewing ? 'Analyzing...' : 'Run Review'}</span>
              </button>
            </div>
            <CodeMirror
              value={code}
              height="380px"
              theme={oneDark}
              extensions={[python()]}
              onChange={(val) => setCode(val)}
            />
          </div>
        </div>

        {/* Review Results */}
        <div className="space-y-4">
          {reviewResult ? (
            <div className="space-y-4">
              {/* Quality & Scorecard Banner */}
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-[#161b22] p-4 rounded-xl border border-[#30363d] text-center">
                  <span className="text-xs text-gray-400 block">Overall Quality</span>
                  <span className="text-base font-bold text-indigo-400 capitalize">
                    {reviewResult.overall_quality}
                  </span>
                </div>
                <div className="bg-[#161b22] p-4 rounded-xl border border-[#30363d] text-center">
                  <span className="text-xs text-gray-400 block">Readability</span>
                  <span className="text-base font-bold text-gray-200">
                    {reviewResult.readability_score}/10
                  </span>
                </div>
                <div className="bg-[#161b22] p-4 rounded-xl border border-[#30363d] text-center">
                  <span className="text-xs text-gray-400 block">Maintainability</span>
                  <span className="text-base font-bold text-gray-200">
                    {reviewResult.maintainability_score}/10
                  </span>
                </div>
              </div>

              {/* Summary */}
              <div className="p-4 bg-[#161b22] border border-[#30363d] rounded-xl text-xs space-y-1">
                <span className="font-semibold text-gray-300 block">Review Summary:</span>
                <p className="text-gray-400 leading-relaxed">{reviewResult.review_summary}</p>
              </div>

              {/* Category 1: Deterministic Static Analysis Findings */}
              <div className="bg-[#161b22] p-4 rounded-xl border border-[#30363d] space-y-3">
                <div className="flex items-center gap-2">
                  <Layers className="w-4 h-4 text-emerald-400" />
                  <h3 className="text-xs font-semibold text-white uppercase tracking-wider">
                    Deterministic Findings ({deterministicFindings.length}) [AST & Ruff]
                  </h3>
                </div>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {deterministicFindings.length > 0 ? (
                    deterministicFindings.map((f, i) => (
                      <div key={i} className="p-2.5 bg-[#0d1117] rounded-lg border border-[#30363d] text-xs space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-mono text-gray-300">
                            Line {f.line || '--'}: {f.message}
                          </span>
                          <span className="px-1.5 py-0.2 rounded text-[10px] uppercase font-mono text-emerald-400 bg-emerald-500/10">
                            {f.source}
                          </span>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-gray-500">No static analysis issues detected.</p>
                  )}
                </div>
              </div>

              {/* Category 2: AI Observations */}
              <div className="bg-[#161b22] p-4 rounded-xl border border-[#30363d] space-y-3">
                <div className="flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-indigo-400" />
                  <h3 className="text-xs font-semibold text-white uppercase tracking-wider">
                    AI Review Observations ({aiFindings.length})
                  </h3>
                </div>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {aiFindings.length > 0 ? (
                    aiFindings.map((f, i) => (
                      <div key={i} className="p-2.5 bg-[#0d1117] rounded-lg border border-[#30363d] text-xs space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="text-gray-200 font-medium">{f.description}</span>
                          <span className="px-1.5 py-0.2 rounded text-[10px] uppercase text-indigo-400 bg-indigo-500/10">
                            {f.severity || 'info'}
                          </span>
                        </div>
                        {f.suggestion && (
                          <p className="text-gray-400 text-[11px] pl-2 border-l border-indigo-500/40">
                            {f.suggestion}
                          </p>
                        )}
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-gray-500">No AI-suggested anomalies.</p>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-[#161b22] p-10 rounded-xl border border-[#30363d] text-center space-y-3">
              <ShieldCheck className="w-10 h-10 text-gray-500 mx-auto" />
              <h3 className="text-sm font-medium text-gray-300">Ready to Review</h3>
              <p className="text-xs text-gray-500 max-w-sm mx-auto">
                Click 'Run Review' to analyze Python AST syntax, check PEP 8 style via Ruff, and generate AI insights.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
