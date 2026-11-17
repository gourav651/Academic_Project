import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Generator from './pages/Generator';
import WorkflowView from './pages/WorkflowView';
import Debugger from './pages/Debugger';
import Testing from './pages/Testing';
import Review from './pages/Review';
import Explainer from './pages/Explainer';
import Governance from './pages/Governance';
import Projects from './pages/Projects';
import Settings from './pages/Settings';

export default function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <div className="flex min-h-screen bg-[#0d1117] text-[#e6edf3]">
          <Sidebar />
          <div className="flex-1 flex flex-col min-w-0">
            <Navbar />
            <main className="flex-1 overflow-y-auto">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/generate" element={<Generator />} />
                <Route path="/workflow" element={<WorkflowView />} />
                <Route path="/debugger" element={<Debugger />} />
                <Route path="/testing" element={<Testing />} />
                <Route path="/review" element={<Review />} />
                <Route path="/explanation" element={<Explainer />} />
                <Route path="/governance" element={<Governance />} />
                <Route path="/projects" element={<Projects />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </main>
          </div>
        </div>
      </BrowserRouter>
    </AppProvider>
  );
}
