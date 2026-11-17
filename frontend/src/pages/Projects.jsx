import React, { useState, useEffect } from 'react';
import { getProjects, createProject, deleteProject, getVersions, rollbackVersion } from '../api';
import { useApp } from '../context/AppContext';
import {
  FolderGit2,
  Plus,
  Trash2,
  CheckCircle2,
  Clock,
  RotateCcw,
  FileCode,
  ArrowRight
} from 'lucide-react';

export default function Projects() {
  const { activeProject, setActiveProject } = useApp();
  const [projects, setProjects] = useState([]);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDesc, setNewProjectDesc] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchProjects = async () => {
    try {
      const res = await getProjects();
      setProjects(res.data);
      if (res.data.length > 0 && !activeProject) {
        setActiveProject(res.data[0]);
      }
    } catch (err) {
      console.error('Failed to load projects:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchProjectVersions = async (projectId) => {
    try {
      const res = await getVersions(projectId);
      setVersions(res.data);
    } catch (err) {
      console.error('Failed to load versions:', err);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  useEffect(() => {
    if (activeProject?.id) {
      fetchProjectVersions(activeProject.id);
    } else {
      setVersions([]);
    }
  }, [activeProject]);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;
    try {
      const res = await createProject({
        name: newProjectName.trim(),
        description: newProjectDesc.trim()
      });
      setNewProjectName('');
      setNewProjectDesc('');
      setShowCreateModal(false);
      await fetchProjects();
      setActiveProject(res.data);
    } catch (err) {
      alert('Failed to create project: ' + err.message);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to delete this project and all its runs?')) return;
    try {
      await deleteProject(id);
      if (activeProject?.id === id) {
        setActiveProject(null);
      }
      await fetchProjects();
    } catch (err) {
      alert('Delete failed: ' + err.message);
    }
  };

  const handleRollback = async (versionNum) => {
    if (!confirm(`Rollback to version ${versionNum}? This will restore its code.`)) return;
    try {
      const res = await rollbackVersion(activeProject.id, versionNum);
      alert(`Restored version ${versionNum}! Created new head version ${res.data.new_version}`);
      await fetchProjectVersions(activeProject.id);
    } catch (err) {
      alert('Rollback failed: ' + err.message);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <FolderGit2 className="w-6 h-6 text-indigo-400" />
            <span>Projects & Version History</span>
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Manage software projects, track immutable code versions, and perform one-click rollbacks.
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold transition"
        >
          <Plus className="w-4 h-4" />
          <span>New Project</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Projects List Column */}
        <div className="lg:col-span-1 space-y-3">
          <span className="text-xs font-semibold text-gray-300 uppercase tracking-wider block">
            Workspaces ({projects.length})
          </span>
          <div className="space-y-2">
            {projects.map((p) => {
              const isSelected = activeProject?.id === p.id;
              return (
                <div
                  key={p.id}
                  onClick={() => setActiveProject(p)}
                  className={`p-4 rounded-xl border cursor-pointer transition ${
                    isSelected
                      ? 'bg-indigo-950/20 border-indigo-500/60 shadow-md shadow-indigo-500/10'
                      : 'bg-[#161b22] border-[#30363d] hover:bg-[#21262d]'
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <h3 className="text-sm font-semibold text-gray-200">{p.name}</h3>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(p.id);
                      }}
                      className="text-gray-500 hover:text-red-400 p-1"
                      title="Delete project"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                  {p.description && (
                    <p className="text-xs text-gray-400 mt-1 line-clamp-2">{p.description}</p>
                  )}
                  <div className="text-[11px] text-gray-500 mt-3 font-mono">
                    Created: {new Date(p.created_at).toLocaleDateString()}
                  </div>
                </div>
              );
            })}

            {projects.length === 0 && (
              <div className="p-8 text-center text-xs text-gray-500 bg-[#161b22] rounded-xl border border-[#30363d]">
                No projects created yet.
              </div>
            )}
          </div>
        </div>

        {/* Project Details & Code Version History */}
        <div className="lg:col-span-2 space-y-4">
          <span className="text-xs font-semibold text-gray-300 uppercase tracking-wider block">
            {activeProject ? `Code Versions for "${activeProject.name}"` : 'Select a Project'}
          </span>

          {activeProject ? (
            <div className="space-y-3">
              {versions.length > 0 ? (
                versions.map((ver) => (
                  <div
                    key={ver.id}
                    className="p-4 bg-[#161b22] border border-[#30363d] rounded-xl flex items-center justify-between hover:bg-[#21262d] transition"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-400 font-mono font-bold text-xs">
                          v{ver.version_number}
                        </span>
                        <span className="text-sm font-medium text-gray-200">
                          {ver.change_summary || 'Generated Code Snapshot'}
                        </span>
                      </div>
                      <span className="text-xs text-gray-500 font-mono block">
                        Saved: {new Date(ver.created_at).toLocaleString()}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleRollback(ver.version_number)}
                        className="flex items-center gap-1 px-3 py-1.5 bg-[#21262d] hover:bg-[#30363d] text-amber-400 border border-[#30363d] rounded-lg text-xs font-medium transition"
                      >
                        <RotateCcw className="w-3 h-3" />
                        <span>Rollback</span>
                      </button>
                    </div>
                  </div>
                ))
              ) : (
                <div className="p-8 text-center text-xs text-gray-500 bg-[#161b22] rounded-xl border border-[#30363d]">
                  No code versions committed for this project yet. Complete an AI generation workflow to create a version snapshot.
                </div>
              )}
            </div>
          ) : (
            <div className="p-12 text-center text-gray-500 bg-[#161b22] rounded-xl border border-[#30363d]">
              Pick or create a project on the left.
            </div>
          )}
        </div>
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50">
          <div className="bg-[#161b22] border border-[#30363d] rounded-xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-base font-semibold text-white">Create New Software Project</h3>
            <form onSubmit={handleCreate} className="space-y-3">
              <div>
                <label className="text-xs text-gray-300 block mb-1">Project Name</label>
                <input
                  type="text"
                  required
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  placeholder="E.g., Token Bucket Rate Limiter"
                  className="w-full bg-[#0d1117] border border-[#30363d] rounded-lg p-2.5 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="text-xs text-gray-300 block mb-1">Description (Optional)</label>
                <textarea
                  rows={3}
                  value={newProjectDesc}
                  onChange={(e) => setNewProjectDesc(e.target.value)}
                  placeholder="Brief description of the software objectives..."
                  className="w-full bg-[#0d1117] border border-[#30363d] rounded-lg p-2.5 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-3 py-1.5 bg-[#21262d] text-gray-300 rounded-lg text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-indigo-600 text-white rounded-lg text-xs font-semibold"
                >
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
