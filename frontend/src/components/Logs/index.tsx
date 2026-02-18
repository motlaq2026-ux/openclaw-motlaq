import { useAppStore } from '../../stores/appStore';
import { useEffect } from 'react';
import { Loader2, RefreshCw, Trash2, Wifi, WifiOff } from 'lucide-react';
import { api } from '../../lib/api';
import { useWebSocket } from '../../lib/useWebSocket';

export function Logs() {
  const { loadLogs, loading } = useAppStore();
  const { connected, logs, refreshLogs } = useWebSocket();

  useEffect(() => {
    loadLogs();
  }, []);

  const handleClear = async () => {
    if (confirm('Clear all logs?')) {
      await api.clearLogs();
      refreshLogs();
    }
  };

  const levelColors: Record<string, string> = {
    DEBUG: 'text-gray-400',
    INFO: 'text-green-400',
    WARNING: 'text-yellow-400',
    ERROR: 'text-red-400',
    CRITICAL: 'text-red-500 bg-red-500/10',
  };

  if (loading && logs.length === 0) {
    return <div className="flex items-center justify-center h-64"><Loader2 className="w-8 h-8 animate-spin text-claw-500" /></div>;
  }

  return (
    <div className="h-full overflow-y-auto scroll-container p-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Logs</h2>
          <p className="text-gray-400">System logs and events</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-sm">
            {connected ? (
              <>
                <Wifi className="text-green-500" size={16} />
                <span className="text-green-400">Live</span>
              </>
            ) : (
              <>
                <WifiOff className="text-gray-500" size={16} />
                <span className="text-gray-400">Disconnected</span>
              </>
            )}
          </div>
          <button onClick={refreshLogs} className="btn-secondary flex items-center gap-2">
            <RefreshCw size={16} /> Refresh
          </button>
          <button onClick={handleClear} className="btn-secondary text-red-400 flex items-center gap-2">
            <Trash2 size={16} /> Clear
          </button>
        </div>
      </div>

      <div className="bg-dark-800 border border-dark-600 rounded-2xl overflow-hidden">
        <div className="max-h-[60vh] overflow-y-auto">
          {logs.map((log, i) => (
            <div key={i} className={`px-4 py-2 border-b border-dark-600 font-mono text-sm ${levelColors[log.level] || 'text-gray-300'}`}>
              <span className="text-gray-500 mr-2">{log.timestamp}</span>
              <span className="mr-2">[{log.level}]</span>
              {log.source && <span className="text-gray-400 mr-2">({log.source})</span>}
              <span>{log.message}</span>
            </div>
          ))}
          {logs.length === 0 && (
            <div className="p-8 text-center text-gray-400">No logs</div>
          )}
        </div>
      </div>
    </div>
  );
}
