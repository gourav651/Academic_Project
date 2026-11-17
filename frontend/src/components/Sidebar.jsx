import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Sparkles,
  Network,
  Bug,
  CheckCircle2,
  FileCode,
  BookOpen,
  ShieldCheck,
  FolderGit2,
  Settings,
  Bot
} from 'lucide-react';
import { useApp } from '../context/AppContext';

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/generate', label: 'AI Generator', icon: Sparkles },
  { path: '/workflow', label: 'Agent Workflow', icon: Network },
  { path: '/debugger', label: 'Code Debugger', icon: Bug },
  { path: '/testing', label: 'Automated Tests', icon: CheckCircle2 },
  { path: '/review', label: 'Code Review', icon: FileCode },
  { path: '/explanation', label: 'Explainability', icon: BookOpen },
  { path: '/governance', label: 'Governance & Audit', icon: ShieldCheck },
  { path: '/projects', label: 'Projects & History', icon: FolderGit2 },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export default function Sidebar() {
  const { currentTaskId, workflowState } = useApp();

  return (
    <aside className="w-64 bg-[#161b22] border-r border-[#30363d] flex flex-col h-screen sticky top-0 select-none">
      {/* Brand Header */}
      <div className="p-5 border-b border-[#30363d] flex items-center gap-3">
        <div className="p-2 bg-indigo-500/10 border border-indigo-500/30 rounded-lg text-indigo-400">
          <Bot className="w-6 h-6" />
        </div>
        <div>
          <h1 className="font-semibold text-sm tracking-wide text-white leading-tight">
            Agentic AI
          </h1>
          <p className="text-xs text-gray-400">Software Eng. Framework</p>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/40'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-[#21262d]'
                }`
              }
            >
              <Icon className="w-4 h-4" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Active Workflow Badge */}
      {currentTaskId && (
        <div className="p-3 mx-3 mb-4 rounded-lg bg-[#21262d] border border-[#30363d] text-xs">
          <div className="flex items-center justify-between text-gray-400 mb-1">
            <span>Active Task</span>
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          </div>
          <p className="font-mono text-[10px] text-gray-300 truncate">{currentTaskId}</p>
          <div className="mt-2 text-indigo-400 text-[11px] font-medium">
            Status: {workflowState?.workflow_status || 'running'}
          </div>
        </div>
      )}

      {/* Footer Info */}
      <div className="p-4 border-t border-[#30363d] text-[11px] text-gray-500 flex justify-between items-center">
        <span>B.Tech Final Year</span>
        <span className="px-1.5 py-0.5 rounded bg-[#21262d] text-gray-400 border border-[#30363d]">
          v1.0.0
        </span>
      </div>
    </aside>
  );
}
