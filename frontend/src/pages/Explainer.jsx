import React, { useState } from 'react';
import CodeMirror from '@uiw/react-codemirror';
import { python } from '@codemirror/lang-python';
import { oneDark } from '@codemirror/theme-one-dark';
import api from '../api';
import { useApp } from '../context/AppContext';
import {
  BookOpen,
  Play,
  Lightbulb,
  Cpu,
  Layers,
  ArrowRight,
  TrendingUp
} from 'lucide-react';

const sampleExplainCode = `def merge_sort(arr):
    """Sorts a list in ascending order using divide-and-conquer."""
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return _merge(left, right)

def _merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result`;

const cleanDisplayText = (val) => {
  if (!val) return '';
  if (typeof val !== 'string') return String(val);
  let cleaned = val.trim();
  if (cleaned.startsWith('```')) {
    cleaned = cleaned.replace(/^```[a-zA-Z]*\n?/, '').replace(/\n?```$/, '').trim();
  }
  if (cleaned.startsWith('{') && cleaned.endsWith('}')) {
    try {
      const obj = JSON.parse(cleaned);
      if (obj.overview) return obj.overview;
      if (obj.explanation) return obj.explanation;
      if (obj.purpose) return obj.purpose;
    } catch {}
  }
  cleaned = cleaned.replace(/^[{\s]*"(?:overview|explanation|purpose)"\s*:\s*"/i, '');
  cleaned = cleaned.replace(/",\s*"[a-zA-Z0-9_]+"\s*:[\s\S]*$/, '');
  cleaned = cleaned.replace(/["}\]]+$/, '').trim();
  return cleaned;
};

export default function Explainer() {
  const { activeModel } = useApp();
  const [code, setCode] = useState(sampleExplainCode);
  const [explanation, setExplanation] = useState(null);
  const [isExplaining, setIsExplaining] = useState(false);

  const handleExplain = async () => {
    setIsExplaining(true);
    try {
      const res = await api.post('/explain', { code, model: activeModel });
      setExplanation(res.data?.result);
    } catch (err) {
      alert('Explanation failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsExplaining(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <BookOpen className="w-6 h-6 text-indigo-400" />
          <span>Code Explainability & Algorithmic Transparency</span>
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Provides evidence-based explanations of program architecture, execution flow, function complexities, and key concepts.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Code Input */}
        <div className="space-y-4">
          <div className="bg-[#161b22] rounded-xl border border-[#30363d] overflow-hidden">
            <div className="flex justify-between items-center px-4 py-2 bg-[#21262d] border-b border-[#30363d] text-xs">
              <span className="font-mono text-gray-300">Target Python Code</span>
              <button
                onClick={handleExplain}
                disabled={isExplaining}
                className="flex items-center gap-1.5 px-3 py-1 bg-indigo-600 hover:bg-indigo-500 text-white rounded font-medium transition"
              >
                <Play className="w-3 h-3 fill-white" />
                <span>{isExplaining ? 'Formulating Explanation...' : 'Explain Code'}</span>
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

        {/* Right: Explanation Cards */}
        <div className="space-y-4">
          {explanation ? (
            <div className="space-y-4">
              {/* Overview */}
              <div className="p-5 bg-[#161b22] border border-[#30363d] rounded-xl space-y-2">
                <div className="flex items-center gap-2 text-indigo-400 text-xs font-semibold uppercase tracking-wider">
                  <Lightbulb className="w-4 h-4" />
                  <span>Program Overview</span>
                </div>
                <p className="text-xs text-gray-300 leading-relaxed">{cleanDisplayText(explanation.overview)}</p>
              </div>

              {/* Execution Flow */}
              {explanation.execution_flow && (
                <div className="p-5 bg-[#161b22] border border-[#30363d] rounded-xl space-y-2">
                  <div className="flex items-center gap-2 text-emerald-400 text-xs font-semibold uppercase tracking-wider">
                    <TrendingUp className="w-4 h-4" />
                    <span>Execution Flow</span>
                  </div>
                  <p className="text-xs text-gray-300 leading-relaxed font-sans">{cleanDisplayText(explanation.execution_flow)}</p>
                </div>
              )}

              {/* Functions Breakdown */}
              {explanation.functions?.length > 0 && (
                <div className="space-y-3">
                  <span className="text-xs font-semibold text-gray-300 uppercase tracking-wider block">
                    Functions Breakdown
                  </span>
                  {explanation.functions.map((fn, idx) => {
                    const name = cleanDisplayText(fn.name);
                    const displayName = /^[a-zA-Z_][a-zA-Z0-9_]*$/.test(name) ? `${name}()` : name;
                    return (
                      <div key={idx} className="p-4 bg-[#161b22] border border-[#30363d] rounded-xl space-y-2">
                        <div className="flex justify-between items-center border-b border-[#30363d] pb-2">
                          <span className="font-mono text-sm font-semibold text-indigo-400">{displayName}</span>
                          {fn.complexity && (
                            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-[#21262d] text-gray-300 border border-[#30363d]">
                              {cleanDisplayText(fn.complexity)}
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-gray-300">{cleanDisplayText(fn.explanation || fn.purpose)}</p>
                        {fn.parameters && (
                          <div className="text-[11px] text-gray-400">
                            <span className="text-gray-500">Parameters:</span> {cleanDisplayText(fn.parameters)}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          ) : (
            <div className="bg-[#161b22] p-10 rounded-xl border border-[#30363d] text-center space-y-3">
              <BookOpen className="w-10 h-10 text-gray-500 mx-auto" />
              <h3 className="text-sm font-medium text-gray-300">Ready to Explain</h3>
              <p className="text-xs text-gray-500 max-w-sm mx-auto">
                Click 'Explain Code' to generate a structured pedagogical breakdown of the algorithm.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
