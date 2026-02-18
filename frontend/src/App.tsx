import { useEffect } from 'react';
import { useAppStore } from './stores/appStore';
import { Sidebar } from './components/Layout/Sidebar';
import { Dashboard } from './components/Dashboard';
import { AIConfig } from './components/AIConfig';
import { MCP } from './components/MCP';
import { Skills } from './components/Skills';
import { Channels } from './components/Channels';
import { Agents } from './components/Agents';
import { Logs } from './components/Logs';
import { Settings } from './components/Settings';

const pages = {
  dashboard: Dashboard,
  'ai-config': AIConfig,
  mcp: MCP,
  skills: Skills,
  channels: Channels,
  agents: Agents,
  logs: Logs,
  settings: Settings,
};

function App() {
  const { currentPage, loadAll, loading, error } = useAppStore();

  useEffect(() => {
    loadAll();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-dark-950">
        <div className="text-center">
          <div className="text-6xl mb-4">🦞</div>
          <p className="text-gray-400">Loading OpenClaw Fortress...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-dark-950">
        <div className="text-center">
          <div className="text-6xl mb-4">⚠️</div>
          <p className="text-red-400">{error}</p>
          <button onClick={loadAll} className="btn-primary mt-4">Retry</button>
        </div>
      </div>
    );
  }

  const Page = pages[currentPage];

  return (
    <div className="min-h-screen flex bg-dark-950">
      <Sidebar />
      <main className="flex-1 overflow-hidden">
        <Page />
      </main>
    </div>
  );
}

export default App;
