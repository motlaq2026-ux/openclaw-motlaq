import { useEffect, useState, useRef } from 'react';
import { useAppStore } from '../../stores/appStore';
import { api, OfficialProvider, NuclearStatus } from '../../lib/api';
import { StatusCard } from './StatusCard';
import { QuickActions } from './QuickActions';
import { SystemInfo } from './SystemInfo';
import { Setup } from '../Setup';
import { Activity, CheckCircle, XCircle, Loader2, Plus, Shield, RefreshCw, Terminal, ChevronDown, ChevronUp, Clock } from 'lucide-react';
import clsx from 'clsx';

interface ServiceStatus {
  running: boolean;
  pid: number | null;
  port: number;
  uptime_seconds: number | null;
  memory_mb: number | null;
  cpu_percent: number | null;
}

export function Dashboard() {
  const { aiConfig, officialProviders, loadAIConfig, loading } = useAppStore();
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState<OfficialProvider | null>(null);
  const [apiKey, setApiKey] = useState('');
  const [saving, setSaving] = useState(false);
  const [nuclearStatus, setNuclearStatus] = useState<NuclearStatus | null>(null);
  
  const [serviceStatus, setServiceStatus] = useState<ServiceStatus | null>(null);
  const [serviceLoading, setServiceLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [logsExpanded, setLogsExpanded] = useState(true);
  const [autoRefreshLogs, setAutoRefreshLogs] = useState(true);
  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadAIConfig();
    loadNuclearStatus();
    fetchServiceStatus();
    fetchLogs();
    
    const nuclearInterval = setInterval(loadNuclearStatus, 30000);
    const statusInterval = setInterval(fetchServiceStatus, 3000);
    const logsInterval = autoRefreshLogs ? setInterval(fetchLogs, 2000) : null;
    
    return () => {
      clearInterval(nuclearInterval);
      clearInterval(statusInterval);
      if (logsInterval) clearInterval(logsInterval);
    };
  }, [autoRefreshLogs]);

  useEffect(() => {
    if (logsExpanded && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, logsExpanded]);

  const loadNuclearStatus = async () => {
    try {
      const status = await api.getNuclearStatus();
      setNuclearStatus(status);
    } catch (e) {
      console.error('Failed to load nuclear status:', e);
    }
  };

  const fetchServiceStatus = async () => {
    try {
      await api.getSystemStatus();
      setServiceStatus({
        running: true,
        pid: null,
        port: 7860,
        uptime_seconds: nuclearStatus?.uptime || 0,
        memory_mb: null,
        cpu_percent: null,
      });
    } catch {
      setServiceStatus({ running: false, pid: null, port: 7860, uptime_seconds: null, memory_mb: null, cpu_percent: null });
    } finally {
      setServiceLoading(false);
    }
  };

  const fetchLogs = async () => {
    try {
      const { logs: logLines } = await api.getLogs(undefined, 50);
      setLogs(logLines.map(l => `[${l.level}] ${l.message}`));
    } catch {
      // Silent fail
    }
  };

  const handleStart = async () => {
    setActionLoading(true);
    try {
      await api.health();
      await fetchServiceStatus();
    } catch (e) {
      console.error('Start failed:', e);
    } finally {
      setActionLoading(false);
    }
  };

  const handleStop = async () => {
    setActionLoading(true);
    try {
      await fetchServiceStatus();
    } finally {
      setActionLoading(false);
    }
  };

  const handleRestart = async () => {
    setActionLoading(true);
    try {
      await fetchServiceStatus();
      await fetchLogs();
    } finally {
      setActionLoading(false);
    }
  };

  const handleKillAll = async () => {
    setActionLoading(true);
    try {
      await fetchServiceStatus();
    } finally {
      setActionLoading(false);
    }
  };

  const handleDiagnostics = async () => {
    alert('Diagnostics feature coming soon!');
  };

  const handleAddProvider = async () => {
    if (!selectedProvider || !apiKey) return;
    setSaving(true);
    try {
      await api.saveProvider({
        provider_name: selectedProvider.id,
        base_url: selectedProvider.default_base_url || '',
        api_key: apiKey,
        api_type: selectedProvider.api_type,
        models: selectedProvider.suggested_models.map(m => ({
          id: m.id,
          name: m.name,
          context_window: m.context_window,
          max_tokens: m.max_tokens,
        })),
      });
      await loadAIConfig();
      setShowAddDialog(false);
      setSelectedProvider(null);
      setApiKey('');
    } catch (e) {
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  const getLogLineClass = (line: string) => {
    if (line.includes('error') || line.includes('Error') || line.includes('ERROR')) {
      return 'text-red-400';
    }
    if (line.includes('warn') || line.includes('Warn') || line.includes('WARN')) {
      return 'text-yellow-400';
    }
    if (line.includes('info') || line.includes('Info') || line.includes('INFO')) {
      return 'text-green-400';
    }
    return 'text-gray-400';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-claw-500" />
      </div>
    );
  }

  const hasConfig = aiConfig && aiConfig.configured_providers.length > 0;

  return (
    <div className="h-full overflow-y-auto scroll-container p-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Dashboard</h2>
          <p className="text-gray-400">Welcome to OpenClaw Fortress</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => { loadAIConfig(); loadNuclearStatus(); fetchServiceStatus(); }} className="btn-secondary flex items-center gap-2">
            <RefreshCw size={16} /> Refresh
          </button>
          {hasConfig && (
            <button onClick={() => setShowAddDialog(true)} className="btn-primary flex items-center gap-2">
              <Plus size={18} />
              Add Provider
            </button>
          )}
        </div>
      </div>

      <div className="space-y-6">
        {!hasConfig && (
          <Setup onComplete={() => loadAIConfig()} embedded />
        )}

        {hasConfig && (
          <>

        <StatusCard status={serviceStatus} loading={serviceLoading} />

        <QuickActions
          status={serviceStatus}
          loading={actionLoading}
          onStart={handleStart}
          onStop={handleStop}
          onRestart={handleRestart}
          onKillAll={handleKillAll}
          onDiagnostics={handleDiagnostics}
        />

        <div className="bg-dark-700 rounded-2xl border border-dark-500 overflow-hidden">
          <div
            className="flex items-center justify-between px-4 py-3 bg-dark-600/50 cursor-pointer"
            onClick={() => setLogsExpanded(!logsExpanded)}
          >
            <div className="flex items-center gap-2">
              <Terminal size={16} className="text-gray-500" />
              <span className="text-sm font-medium text-white">Real-time Logs</span>
              <span className="text-xs text-gray-500">({logs.length} lines)</span>
            </div>
            <div className="flex items-center gap-3">
              {logsExpanded && (
                <>
                  <label
                    className="flex items-center gap-2 text-xs text-gray-400"
                    onClick={e => e.stopPropagation()}
                  >
                    <input
                      type="checkbox"
                      checked={autoRefreshLogs}
                      onChange={(e) => setAutoRefreshLogs(e.target.checked)}
                      className="w-3 h-3 rounded border-dark-500 bg-dark-600 text-claw-500"
                    />
                    Auto Refresh
                  </label>
                  <button
                    onClick={(e) => { e.stopPropagation(); fetchLogs(); }}
                    className="text-gray-500 hover:text-white"
                    title="Refresh logs"
                  >
                    <RefreshCw size={14} />
                  </button>
                </>
              )}
              {logsExpanded ? (
                <ChevronUp size={16} className="text-gray-500" />
              ) : (
                <ChevronDown size={16} className="text-gray-500" />
              )}
            </div>
          </div>

          {logsExpanded && (
            <div className="h-64 overflow-y-auto p-4 font-mono text-xs leading-relaxed bg-dark-800">
              {logs.length === 0 ? (
                <div className="h-full flex items-center justify-center text-gray-500">
                  <p>No logs available</p>
                </div>
              ) : (
                <>
                  {logs.map((line, index) => (
                    <div
                      key={index}
                      className={clsx('py-0.5 whitespace-pre-wrap break-all', getLogLineClass(line))}
                    >
                      {line}
                    </div>
                  ))}
                  <div ref={logsEndRef} />
                </>
              )}
            </div>
          )}
        </div>

        <SystemInfo />

        {nuclearStatus && (
          <div className="bg-dark-800 border border-dark-600 rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <Shield className="text-claw-500" size={20} />
              <h3 className="text-lg font-semibold text-white">Nuclear Systems</h3>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { name: 'Auto-Update', key: 'auto_updater', icon: RefreshCw },
                { name: 'Self-Healing', key: 'self_healing', icon: Shield },
                { name: 'Health Monitor', key: 'health_monitor', icon: Activity },
                { name: 'Scheduler', key: 'scheduler', icon: Clock },
              ].map((sys) => {
                const Icon = sys.icon;
                const status = (nuclearStatus.systems as Record<string, { running?: boolean }>)?.[sys.key];
                const isRunning = status?.running !== false;
                return (
                  <div key={sys.key} className="bg-dark-700 rounded-xl p-3 flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${isRunning ? 'bg-green-500/20' : 'bg-red-500/20'}`}>
                      <Icon size={16} className={isRunning ? 'text-green-400' : 'text-red-400'} />
                    </div>
                    <div>
                      <p className="text-sm text-white">{sys.name}</p>
                      <p className={`text-xs ${isRunning ? 'text-green-400' : 'text-red-400'}`}>
                        {isRunning ? 'Running' : 'Stopped'}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {hasConfig && (
          <div className="bg-dark-800 border border-dark-600 rounded-2xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Configured Providers</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {aiConfig?.configured_providers.map((provider) => (
                <div key={provider.name} className="bg-dark-700 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <h4 className="font-medium text-white capitalize">{provider.name}</h4>
                      <p className="text-xs text-gray-400 truncate">{provider.base_url}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      {provider.has_api_key ? (
                        <CheckCircle className="text-green-500" size={16} />
                      ) : (
                        <XCircle className="text-red-500" size={16} />
                      )}
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {provider.models.slice(0, 3).map((model) => (
                      <div key={model.full_id} className="bg-dark-600 rounded-lg px-2 py-1 text-xs">
                        <span className="text-gray-300">{model.name}</span>
                        {model.is_primary && <span className="text-yellow-400 ml-1">★</span>}
                      </div>
                    ))}
                    {provider.models.length > 3 && (
                      <div className="bg-dark-600 rounded-lg px-2 py-1 text-xs text-gray-400">
                        +{provider.models.length - 3} more
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
          </>
        )}
      </div>

      {showAddDialog && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-dark-800 border border-dark-600 rounded-2xl p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <h3 className="text-lg font-semibold text-white mb-4">Add AI Provider</h3>
            
            {!selectedProvider ? (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {officialProviders.map((provider) => (
                  <button
                    key={provider.id}
                    onClick={() => setSelectedProvider(provider)}
                    className="bg-dark-700 hover:bg-dark-600 border border-dark-500 rounded-xl p-4 text-left transition-colors"
                  >
                    <div className="text-2xl mb-2">{provider.icon}</div>
                    <p className="font-medium text-white">{provider.name}</p>
                    <p className="text-xs text-gray-400 mt-1">
                      {provider.suggested_models.length} models
                    </p>
                  </button>
                ))}
              </div>
            ) : (
              <div>
                <div className="flex items-center gap-3 mb-4">
                  <button onClick={() => setSelectedProvider(null)} className="text-gray-400 hover:text-white text-sm">
                    ← Back
                  </button>
                </div>
                <div className="flex items-center gap-3 mb-4">
                  <div className="text-3xl">{selectedProvider.icon}</div>
                  <div>
                    <h4 className="font-medium text-white">{selectedProvider.name}</h4>
                    <p className="text-sm text-gray-400">{selectedProvider.suggested_models[0]?.name}</p>
                  </div>
                </div>
                
                <label className="block text-sm text-gray-400 mb-2">API Key</label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder={selectedProvider.requires_api_key ? "Enter your API key" : "Optional"}
                  className="input-base mb-4"
                />

                <div className="mb-4">
                  <p className="text-sm text-gray-400 mb-2">Models to add:</p>
                  <div className="flex flex-wrap gap-2">
                    {selectedProvider.suggested_models.map((m) => (
                      <div key={m.id} className="bg-dark-700 rounded-lg px-3 py-1 text-sm text-gray-300">
                        {m.name}
                        {m.recommended && <span className="text-green-400 ml-1">★</span>}
                      </div>
                    ))}
                  </div>
                </div>
                
                <div className="flex gap-3">
                  <button
                    onClick={handleAddProvider}
                    disabled={saving || (selectedProvider.requires_api_key && !apiKey)}
                    className="btn-primary flex items-center gap-2"
                  >
                    {saving && <Loader2 className="animate-spin" size={16} />}
                    Add Provider
                  </button>
                  <button
                    onClick={() => { setShowAddDialog(false); setSelectedProvider(null); setApiKey(''); }}
                    className="btn-secondary"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
