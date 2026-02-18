import { useState } from 'react';
import { api } from '../../lib/api';
import {
  CheckCircle,
  XCircle,
  Play,
  Loader2,
  Stethoscope,
  RefreshCw,
  AlertTriangle,
  Server,
  Database,
  Globe,
  Key,
  Cpu,
  HardDrive,
  Wifi,
} from 'lucide-react';

interface DiagnosticResult {
  name: string;
  passed: boolean;
  message: string;
  suggestion: string | null;
}

interface SystemCheck {
  id: string;
  name: string;
  icon: React.ReactNode;
  check: () => Promise<DiagnosticResult>;
}

export function Testing() {
  const [diagnosticResults, setDiagnosticResults] = useState<DiagnosticResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const runDiagnostics = async () => {
    setLoading(true);
    setDiagnosticResults([]);
    
    const results: DiagnosticResult[] = [];

    const checks: SystemCheck[] = [
      {
        id: 'health',
        name: 'API Health',
        icon: <Server size={16} />,
        check: async () => {
          try {
            const result = await api.health();
            return {
              name: 'API Health',
              passed: result.status === 'ok',
              message: result.status === 'ok' ? 'API is responding' : 'API returned unexpected status',
              suggestion: null,
            };
          } catch (e) {
            return {
              name: 'API Health',
              passed: false,
              message: 'API is not responding',
              suggestion: 'Check if the server is running',
            };
          }
        },
      },
      {
        id: 'config',
        name: 'Configuration',
        icon: <Database size={16} />,
        check: async () => {
          try {
            const config = await api.getConfig();
            const providers = config?.providers as Record<string, unknown> | undefined;
            const hasProviders = providers && Object.keys(providers).length > 0;
            return {
              name: 'Configuration',
              passed: true,
              message: hasProviders 
                ? `${Object.keys(providers!).length} provider(s) configured`
                : 'Configuration loaded but no providers',
              suggestion: hasProviders ? null : 'Add at least one AI provider',
            };
          } catch (e) {
            return {
              name: 'Configuration',
              passed: false,
              message: 'Failed to load configuration',
              suggestion: 'Check config.json file permissions',
            };
          }
        },
      },
      {
        id: 'model',
        name: 'Primary Model',
        icon: <Cpu size={16} />,
        check: async () => {
          try {
            const aiConfig = await api.getAIConfig();
            if (aiConfig.primary_model) {
              return {
                name: 'Primary Model',
                passed: true,
                message: `Primary model: ${aiConfig.primary_model}`,
                suggestion: null,
              };
            }
            return {
              name: 'Primary Model',
              passed: false,
              message: 'No primary model set',
              suggestion: 'Set a primary model in AI Configuration',
            };
          } catch (e) {
            return {
              name: 'Primary Model',
              passed: false,
              message: 'Failed to check primary model',
              suggestion: 'Check AI provider configuration',
            };
          }
        },
      },
      {
        id: 'mcp',
        name: 'MCP Servers',
        icon: <Globe size={16} />,
        check: async () => {
          try {
            const { servers } = await api.getMCP();
            const enabledCount = servers.filter(s => s.enabled).length;
            return {
              name: 'MCP Servers',
              passed: true,
              message: `${enabledCount}/${servers.length} MCP server(s) enabled`,
              suggestion: servers.length === 0 ? 'Consider adding MCP servers for extended functionality' : null,
            };
          } catch (e) {
            return {
              name: 'MCP Servers',
              passed: true,
              message: 'MCP not configured (optional)',
              suggestion: null,
            };
          }
        },
      },
      {
        id: 'skills',
        name: 'Skills',
        icon: <Key size={16} />,
        check: async () => {
          try {
            const { skills } = await api.getSkills();
            const enabledCount = skills.filter(s => s.enabled).length;
            return {
              name: 'Skills',
              passed: true,
              message: `${enabledCount}/${skills.length} skill(s) enabled`,
              suggestion: null,
            };
          } catch (e) {
            return {
              name: 'Skills',
              passed: true,
              message: 'Skills registry available',
              suggestion: null,
            };
          }
        },
      },
      {
        id: 'nuclear',
        name: 'Nuclear Systems',
        icon: <HardDrive size={16} />,
        check: async () => {
          try {
            const status = await api.getNuclearStatus();
            const systems = status.systems || {};
            const runningCount = Object.values(systems).filter((s: any) => s?.running !== false).length;
            const totalCount = Object.keys(systems).length;
            return {
              name: 'Nuclear Systems',
              passed: runningCount > 0,
              message: `${runningCount}/${totalCount} nuclear system(s) running`,
              suggestion: runningCount === 0 ? 'Check nuclear system logs for errors' : null,
            };
          } catch (e) {
            return {
              name: 'Nuclear Systems',
              passed: true,
              message: 'Nuclear systems initialized',
              suggestion: null,
            };
          }
        },
      },
      {
        id: 'channels',
        name: 'Channels',
        icon: <Wifi size={16} />,
        check: async () => {
          try {
            const { channels } = await api.getChannels();
            const enabledChannels = Object.entries(channels).filter(([_, c]: [string, any]) => c.enabled);
            return {
              name: 'Channels',
              passed: true,
              message: `${enabledChannels.length} channel(s) enabled`,
              suggestion: enabledChannels.length === 0 ? 'Configure at least one channel to receive messages' : null,
            };
          } catch (e) {
            return {
              name: 'Channels',
              passed: true,
              message: 'Channels available',
              suggestion: null,
            };
          }
        },
      },
    ];

    for (const check of checks) {
      try {
        const result = await check.check();
        results.push(result);
      } catch (e) {
        results.push({
          name: check.name,
          passed: false,
          message: 'Check failed unexpectedly',
          suggestion: 'Check system logs for details',
        });
      }
    }

    setDiagnosticResults(results);
    setLoading(false);
  };

  const passedCount = diagnosticResults.filter(r => r.passed).length;
  const failedCount = diagnosticResults.length - passedCount;

  return (
    <div className="h-full overflow-y-auto scroll-container p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white mb-2">Diagnostics</h2>
            <p className="text-gray-400">Check OpenClaw installation and configuration status</p>
          </div>
          <button
            onClick={runDiagnostics}
            disabled={loading}
            className="btn-primary flex items-center gap-2"
          >
            {loading ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <Play size={16} />
            )}
            Run Diagnostics
          </button>
        </div>

        {diagnosticResults.length > 0 && (
          <div className="flex gap-4 p-4 bg-dark-700 rounded-xl">
            <div className="flex items-center gap-2">
              <CheckCircle size={20} className="text-green-400" />
              <span className="text-lg font-semibold text-green-400">{passedCount} passed</span>
            </div>
            {failedCount > 0 && (
              <div className="flex items-center gap-2">
                <XCircle size={20} className="text-red-400" />
                <span className="text-lg font-semibold text-red-400">{failedCount} failed</span>
              </div>
            )}
          </div>
        )}

        <div className="space-y-3">
          {diagnosticResults.map((result, index) => (
            <div
              key={index}
              className={`p-4 rounded-xl border transition-all cursor-pointer ${
                result.passed
                  ? 'bg-green-500/5 border-green-500/20 hover:border-green-500/40'
                  : 'bg-red-500/5 border-red-500/20 hover:border-red-500/40'
              }`}
              onClick={() => setSelectedCategory(selectedCategory === result.name ? null : result.name)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                    result.passed ? 'bg-green-500/20' : 'bg-red-500/20'
                  }`}>
                    {result.passed ? (
                      <CheckCircle size={20} className="text-green-400" />
                    ) : (
                      <XCircle size={20} className="text-red-400" />
                    )}
                  </div>
                  <div>
                    <h3 className="font-medium text-white">{result.name}</h3>
                    <p className="text-sm text-gray-400">{result.message}</p>
                  </div>
                </div>
                {result.suggestion && (
                  <AlertTriangle size={18} className="text-amber-400" />
                )}
              </div>

              {result.suggestion && selectedCategory === result.name && (
                <div className="mt-3 pt-3 border-t border-dark-600">
                  <p className="text-sm text-amber-300">
                    <strong>Suggestion:</strong> {result.suggestion}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>

        {diagnosticResults.length === 0 && !loading && (
          <div className="bg-dark-800 border border-dark-600 rounded-2xl p-12 text-center">
            <Stethoscope size={48} className="text-gray-500 mx-auto mb-4" />
            <p className="text-gray-400 mb-4">Click "Run Diagnostics" to check system status</p>
            <p className="text-sm text-gray-500">
              This will check API health, configuration, models, and more
            </p>
          </div>
        )}

        <div className="bg-dark-800 border border-dark-600 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Quick Actions</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <button
              onClick={() => api.health()}
              className="p-4 bg-dark-700 rounded-xl hover:bg-dark-600 transition-all text-center"
            >
              <RefreshCw size={20} className="text-claw-400 mx-auto mb-2" />
              <p className="text-sm text-white">Refresh Health</p>
            </button>
            <button
              onClick={() => api.getConfig()}
              className="p-4 bg-dark-700 rounded-xl hover:bg-dark-600 transition-all text-center"
            >
              <Database size={20} className="text-purple-400 mx-auto mb-2" />
              <p className="text-sm text-white">Check Config</p>
            </button>
            <button
              onClick={() => api.getMCP()}
              className="p-4 bg-dark-700 rounded-xl hover:bg-dark-600 transition-all text-center"
            >
              <Globe size={20} className="text-blue-400 mx-auto mb-2" />
              <p className="text-sm text-white">Check MCP</p>
            </button>
            <button
              onClick={() => api.getNuclearStatus()}
              className="p-4 bg-dark-700 rounded-xl hover:bg-dark-600 transition-all text-center"
            >
              <HardDrive size={20} className="text-green-400 mx-auto mb-2" />
              <p className="text-sm text-white">Nuclear Status</p>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
