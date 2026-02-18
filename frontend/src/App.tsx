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
import { Testing } from './components/Testing';
import { ErrorBoundary } from './components/ui/ErrorBoundary';
import { AnimatePresence, motion } from 'framer-motion';

const pages = {
  dashboard: Dashboard,
  'ai-config': AIConfig,
  mcp: MCP,
  skills: Skills,
  channels: Channels,
  agents: Agents,
  logs: Logs,
  testing: Testing,
  settings: Settings,
};

const pageKeys = Object.keys(pages);

const pageVariants = {
  initial: { opacity: 0, x: 20 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: -20 },
};

function App() {
  const { currentPage, setCurrentPage, loadAll, loading, error } = useAppStore();

  useEffect(() => {
    loadAll();
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }

      if (e.key === '?') {
        alert(`Keyboard Shortcuts:
        
1-9: Navigate pages
R: Refresh data
H: Go to Dashboard
/: Focus search (when available)
Esc: Close dialogs

Press any key to close this help.`);
        return;
      }

      const num = parseInt(e.key);
      if (num >= 1 && num <= pageKeys.length) {
        setCurrentPage(pageKeys[num - 1] as typeof currentPage);
        return;
      }

      if (e.key === 'r' || e.key === 'R') {
        loadAll();
        return;
      }

      if (e.key === 'h' || e.key === 'H') {
        setCurrentPage('dashboard');
        return;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [setCurrentPage, loadAll]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-dark-950">
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <motion.div 
            className="text-6xl mb-4"
            animate={{ y: [0, -10, 0] }}
            transition={{ repeat: Infinity, duration: 1 }}
          >
            🦞
          </motion.div>
          <p className="text-gray-400">Loading OpenClaw Fortress...</p>
          <div className="mt-4 flex justify-center gap-1">
            {[0, 1, 2].map((i) => (
              <motion.div
                key={i}
                className="w-2 h-2 bg-claw-500 rounded-full"
                animate={{ opacity: [0.3, 1, 0.3] }}
                transition={{ repeat: Infinity, duration: 1, delay: i * 0.15 }}
              />
            ))}
          </div>
        </motion.div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-dark-950">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center max-w-md"
        >
          <div className="text-6xl mb-4">⚠️</div>
          <h1 className="text-xl font-bold text-white mb-2">Something went wrong</h1>
          <p className="text-gray-400 mb-4">{error}</p>
          <button onClick={loadAll} className="btn-primary">Try Again</button>
        </motion.div>
      </div>
    );
  }

  const Page = pages[currentPage];

  return (
    <ErrorBoundary>
      <div className="min-h-screen flex bg-dark-950">
        <Sidebar />
        <main className="flex-1 overflow-hidden">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentPage}
              variants={pageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              transition={{ duration: 0.2 }}
              className="h-full"
            >
              <Page />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </ErrorBoundary>
  );
}

export default App;
