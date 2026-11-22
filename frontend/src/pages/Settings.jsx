import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import {
  Settings as SettingsIcon,
  Server,
  Box,
  Cpu,
  Clock,
  Shield,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  HardDrive
} from 'lucide-react';

export default function Settings() {
  const { health, activeModel, changeModel, models, refreshHealth } = useApp();
  const [ollamaUrl, setOllamaUrl] = useState('http://localhost:11434');
  const [maxDebugAttempts, setMaxDebugAttempts] = useState(3);
  const [executionTimeout, setExecutionTimeout] = useState(30);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await refreshHealth();
    setTimeout(() => setIsRefreshing(false), 500);
  };

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <SettingsIcon className="w-6 h-6 text-indigo-400" />
          <span>System Configuration & Hardware Settings</span>
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Configure local Ollama inference, model selections, Docker execution sandbox parameters, and debugging limits.
        </p>
      </div>

      <div className="space-y-6">
        {/* Section 1: Local Ollama Configuration */}
        <div className="bg-[#161b22] p-6 rounded-xl border border-[#30363d] space-y-4">
          <div className="flex justify-between items-center border-b border-[#30363d] pb-3">
            <div className="flex items-center gap-2">
              <Server className="w-5 h-5 text-indigo-400" />
              <h2 className="text-sm font-semibold text-white">Local Ollama LLM Engine</h2>
            </div>
            <button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="flex items-center gap-1.5 px-3 py-1 bg-[#21262d] hover:bg-[#30363d] text-gray-300 rounded text-xs transition border border-[#30363d]"
            >
              <RefreshCw className={`w-3 h-3 ${isRefreshing ? 'animate-spin' : ''}`} />
              <span>Test Connection</span>
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-gray-400 block mb-1">Ollama Base URL</label>
              <input
                type="text"
                value={ollamaUrl}
                onChange={(e) => setOllamaUrl(e.target.value)}
                className="w-full bg-[#0d1117] border border-[#30363d] rounded-lg p-2.5 text-xs text-gray-200 font-mono focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="text-xs text-gray-400 block mb-1">Active Coding Model</label>
              <select
                value={activeModel}
                onChange={(e) => changeModel(e.target.value)}
                className="w-full bg-[#0d1117] border border-[#30363d] rounded-lg p-2.5 text-xs text-gray-200 font-mono focus:outline-none focus:border-indigo-500 cursor-pointer"
              >
                {models.length > 0 ? (
                  models.map((m) => (
                    <option key={m.name} value={m.name}>
                      {m.name} {m.size ? `(${(m.size / (1024 ** 3)).toFixed(1)} GB)` : ''}
                    </option>
                  ))
                ) : (
                  <option value="qwen2.5-coder:1.5b">qwen2.5-coder:1.5b (Recommended for 4GB VRAM)</option>
                )}
              </select>
            </div>
          </div>

          {/* Connection Status Box */}
          <div
            className={`p-3.5 rounded-lg border flex items-start gap-3 text-xs ${
              health.ollama_connected
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                : 'bg-amber-500/10 border-amber-500/30 text-amber-300'
            }`}
          >
            {health.ollama_connected ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
            )}
            <div>
              <span className="font-semibold block mb-0.5">
                {health.ollama_connected ? 'Ollama Service Reachable' : 'Ollama Offline / Not Reachable'}
              </span>
              <p className="text-[11px] opacity-80 leading-relaxed">
                {health.ollama_connected
                  ? `Inference ready. ${models.length} model(s) available on local endpoint.`
                  : health.ollama_error || 'Start Ollama using `ollama serve` or open the Ollama app.'}
              </p>
            </div>
          </div>

          {/* Hardware & Model Recommendations Guide */}
          {/* <div className="p-4 bg-[#0d1117] rounded-xl border border-[#30363d] space-y-2 text-xs">
            <span className="font-semibold text-gray-200 block flex items-center gap-1.5">
              <HardDrive className="w-4 h-4 text-indigo-400" />
              <span>Recommended Models for Your System (8GB RAM / 4GB GPU VRAM)</span>
            </span>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2 pt-1">
              <div className="p-2.5 rounded bg-[#161b22] border border-[#30363d] space-y-1">
                <span className="font-bold text-emerald-400 block">qwen2.5-coder:1.5b</span>
                <p className="text-[11px] text-gray-400">Download: ~1.0 GB | VRAM: ~1.8 GB</p>
                <p className="text-[10px] text-gray-500">Sub-second generation. Fits 100% inside 4GB GPU.</p>
              </div>
              <div className="p-2.5 rounded bg-[#161b22] border border-[#30363d] space-y-1">
                <span className="font-bold text-indigo-400 block">qwen2.5-coder:3b</span>
                <p className="text-[11px] text-gray-400">Download: ~2.0 GB | VRAM: ~3.2 GB</p>
                <p className="text-[10px] text-gray-500">Higher reasoning accuracy, comfortable in 4GB GPU.</p>
              </div>
              <div className="p-2.5 rounded bg-[#161b22] border border-[#30363d] space-y-1">
                <span className="font-bold text-purple-400 block">deepseek-r1:1.5b</span>
                <p className="text-[11px] text-gray-400">Download: ~1.1 GB | VRAM: ~1.9 GB</p>
                <p className="text-[10px] text-gray-500">Chain-of-thought code reasoning capability.</p>
              </div>
            </div>
          </div> */}
        </div>

        {/* Section 2: Safe Execution & Docker Isolation */}
        <div className="bg-[#161b22] p-6 rounded-xl border border-[#30363d] space-y-4">
          <div className="flex items-center gap-2 border-b border-[#30363d] pb-3">
            <Box className="w-5 h-5 text-blue-400" />
            <h2 className="text-sm font-semibold text-white">Docker-Based Isolated Execution Sandbox</h2>
          </div>

          <div
            className={`p-3.5 rounded-lg border flex items-start gap-3 text-xs ${
              health.docker_available
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                : 'bg-blue-500/10 border-blue-500/30 text-blue-300'
            }`}
          >
            {health.docker_available ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
            )}
            <div>
              <span className="font-semibold block mb-0.5">
                {health.docker_available ? 'Docker Container Sandbox Ready' : 'Docker Engine Daemon Inactive'}
              </span>
              <p className="text-[11px] opacity-80 leading-relaxed">
                {health.docker_available
                  ? 'Code is safely executed in temporary containers with network disabled and CPU/memory constraints.'
                  : 'Start Docker Desktop to enable containerized code execution. Unrestricted host execution is safely blocked.'}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
            <div>
              <label className="text-xs text-gray-400 block mb-1">Execution Timeout (Seconds)</label>
              <input
                type="number"
                min={5}
                max={120}
                value={executionTimeout}
                onChange={(e) => setExecutionTimeout(Number(e.target.value))}
                className="w-full bg-[#0d1117] border border-[#30363d] rounded-lg p-2.5 text-xs text-gray-200 font-mono focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="text-xs text-gray-400 block mb-1">Max Self-Debugging Iterations</label>
              <input
                type="number"
                min={1}
                max={5}
                value={maxDebugAttempts}
                onChange={(e) => setMaxDebugAttempts(Number(e.target.value))}
                className="w-full bg-[#0d1117] border border-[#30363d] rounded-lg p-2.5 text-xs text-gray-200 font-mono focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
