import React, { createContext, useContext, useState, useEffect } from 'react';
import { getHealth, getModels, selectModel as apiSelectModel } from '../api';

const AppContext = createContext();

export const AppProvider = ({ children }) => {
  const [health, setHealth] = useState({
    status: 'checking',
    ollama_connected: false,
    docker_available: false,
    model: 'qwen2.5-coder:1.5b'
  });
  const [models, setModels] = useState([]);
  const [activeModel, setActiveModel] = useState('qwen2.5-coder:1.5b');
  const [activeProject, setActiveProject] = useState(null);
  const [currentTaskId, setCurrentTaskId] = useState(null);
  const [workflowState, setWorkflowState] = useState(null);

  const fetchHealth = async () => {
    try {
      const res = await getHealth();
      setHealth(res.data);
      if (res.data.model) {
        setActiveModel(res.data.model);
      }
    } catch (err) {
      setHealth({
        status: 'error',
        ollama_connected: false,
        docker_available: false,
        ollama_error: 'Backend API unreachable'
      });
    }
  };

  const fetchModels = async () => {
    try {
      const res = await getModels();
      if (res.data.models) {
        setModels(res.data.models);
      }
      if (res.data.current_model) {
        setActiveModel(res.data.current_model);
      }
    } catch (err) {
      console.warn('Could not fetch models:', err);
    }
  };

  const changeModel = async (newModel) => {
    try {
      await apiSelectModel(newModel);
      setActiveModel(newModel);
    } catch (err) {
      console.error('Failed to change model:', err);
    }
  };

  useEffect(() => {
    fetchHealth();
    fetchModels();
    const interval = setInterval(fetchHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <AppContext.Provider
      value={{
        health,
        models,
        activeModel,
        changeModel,
        activeProject,
        setActiveProject,
        currentTaskId,
        setCurrentTaskId,
        workflowState,
        setWorkflowState,
        refreshHealth: fetchHealth
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => useContext(AppContext);
