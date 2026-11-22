import React from 'react';
import { useApp } from '../context/AppContext';
import { Cpu, Server, Box, AlertCircle, CheckCircle2 } from 'lucide-react';

export default function Navbar() {
  const { health, activeModel, changeModel, models, activeProject } = useApp();

  return (
    <header className="h-14 bg-[#161b22] border-b border-[#30363d] px-6 flex items-center justify-between sticky top-0 z-10">
      {/* Left: Active Project indicator */}
      <div className="flex items-center gap-3">
        <span className="text-xs text-gray-400">Project:</span>
        <span className="text-xs font-medium px-2 py-1 rounded bg-[#21262d] text-gray-200 border border-[#30363d]">
          {activeProject ? activeProject.name : 'Default Workspace'}
        </span>
      </div>

      {/* Right: Status and Model selection */}
      <div className="flex items-center gap-4 text-xs">
        {/* Model dropdown */}
        <div className="flex items-center gap-2 bg-[#21262d] px-2.5 py-1.5 rounded-lg border border-[#30363d]">
          <Cpu className="w-3.5 h-3.5 text-indigo-400" />
          <select
            value={activeModel}
            onChange={(e) => changeModel(e.target.value)}
            className="bg-transparent text-gray-200 outline-none cursor-pointer text-xs font-mono"
          >
            {models.length > 0 ? (
              models.map((m) => (
                <option key={m.name} value={m.name} className="bg-[#161b22] text-gray-200">
                  {m.name}
                </option>
              ))
            ) : (
              <option value="qwen2.5-coder:1.5b" className="bg-[#161b22]">
                qwen2.5-coder:1.5b
              </option>
            )}
          </select>
        </div>

        {/* Ollama status badge */}
        {/* <div
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border ${
            health.ollama_connected
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
              : 'bg-amber-500/10 border-amber-500/30 text-amber-400'
          }`}
          title={health.ollama_connected ? 'Ollama inference ready' : health.ollama_error || 'Ollama offline'}
        >
          <Server className="w-3 h-3" />
          <span>{health.ollama_connected ? 'Ollama Online' : 'Ollama Offline'}</span>
        </div> */}

        {/* Docker sandbox badge */}
        <div
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border ${
            health.docker_available
              ? 'bg-blue-500/10 border-blue-500/30 text-blue-400'
              : 'bg-gray-500/10 border-gray-500/30 text-gray-400'
          }`}
          title={health.docker_available ? 'Isolated Docker runtime enabled' : 'Docker daemon not running'}
        >
          <Box className="w-3 h-3" />
          <span>{health.docker_available ? 'Docker Sandbox' : 'No Docker'}</span>
        </div>
      </div>
    </header>
  );
}
