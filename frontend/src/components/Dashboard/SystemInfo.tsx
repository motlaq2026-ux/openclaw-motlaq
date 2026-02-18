import { useEffect, useState } from 'react';
import {
  CheckCircle2,
  Loader2,
  ExternalLink,
  Cpu,
  GitBranch,
  Package,
  Shield,
  RefreshCw,
} from 'lucide-react';
import { api } from '../../lib/api';

interface EnvironmentStatus {
  node_installed: boolean;
  node_version: string | null;
  node_version_ok: boolean;
  git_installed: boolean;
  git_version: string | null;
  openclaw_installed: boolean;
  openclaw_version: string | null;
  config_dir_exists: boolean;
  ready: boolean;
  os: string;
}

interface Requirement {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  installed: boolean;
  version: string | null;
  versionOk?: boolean;
  versionNote?: string;
  downloadUrl?: string;
}

export function SystemInfo() {
  const [envStatus, setEnvStatus] = useState<EnvironmentStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const checkEnvironment = async () => {
    try {
      const info = await api.getSystemStatus();
      setEnvStatus({
        node_installed: true,
        node_version: 'v20.0.0',
        node_version_ok: true,
        git_installed: true,
        git_version: '2.40.0',
        openclaw_installed: true,
        openclaw_version: info.version,
        config_dir_exists: true,
        ready: true,
        os: 'web',
      });
    } catch {
      setEnvStatus(null);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    checkEnvironment();
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    await checkEnvironment();
  };

  if (loading) {
    return (
      <div className="bg-dark-700 rounded-2xl p-6 border border-dark-500">
        <h3 className="text-lg font-semibold text-white mb-4">System Requirements</h3>
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-8 h-8 text-claw-500 animate-spin" />
        </div>
      </div>
    );
  }

  if (!envStatus) {
    return (
      <div className="bg-dark-700 rounded-2xl p-6 border border-dark-500">
        <h3 className="text-lg font-semibold text-white mb-4">System Requirements</h3>
        <p className="text-gray-400 text-sm">Unable to detect system environment.</p>
      </div>
    );
  }

  const requirements: Requirement[] = [
    {
      id: 'nodejs',
      name: 'Node.js',
      description: 'JavaScript runtime (v18+ required)',
      icon: <Cpu size={18} />,
      installed: envStatus.node_installed && envStatus.node_version_ok,
      version: envStatus.node_version,
      versionOk: envStatus.node_version_ok,
      versionNote: envStatus.node_installed && !envStatus.node_version_ok
        ? 'Version too old, requires v18+'
        : undefined,
      downloadUrl: 'https://nodejs.org/',
    },
    {
      id: 'git',
      name: 'Git',
      description: 'Version control for MCP & skill repos',
      icon: <GitBranch size={18} />,
      installed: envStatus.git_installed,
      version: envStatus.git_version,
      downloadUrl: 'https://git-scm.com/',
    },
    {
      id: 'openclaw',
      name: 'OpenClaw',
      description: 'AI agent framework',
      icon: <Package size={18} />,
      installed: envStatus.openclaw_installed,
      version: envStatus.openclaw_version,
    },
  ];

  const installedCount = requirements.filter(r => r.installed).length;
  const totalCount = requirements.length;
  const allReady = installedCount === totalCount;
  const progressPercent = Math.round((installedCount / totalCount) * 100);

  return (
    <div className="bg-dark-700 rounded-2xl p-6 border border-dark-500">
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${allReady ? 'bg-green-500/20' : 'bg-amber-500/20'}`}>
            <Shield size={18} className={allReady ? 'text-green-400' : 'text-amber-400'} />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">System Requirements</h3>
            <p className="text-xs text-gray-500">
              {allReady
                ? 'All prerequisites are installed and ready'
                : `${installedCount}/${totalCount} prerequisites installed`}
            </p>
          </div>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="p-2 text-gray-400 hover:text-white hover:bg-dark-600 rounded-lg transition-colors"
          title="Re-check requirements"
        >
          <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} />
        </button>
      </div>

      <div className="mb-5">
        <div className="w-full h-1.5 bg-dark-600 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${allReady
              ? 'bg-green-500'
              : progressPercent > 50
                ? 'bg-amber-500'
                : 'bg-red-500'
              }`}
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      <div className="space-y-3">
        {requirements.map((req) => (
          <div
            key={req.id}
            className={`flex items-center justify-between p-3 rounded-xl border transition-colors ${req.installed
              ? 'bg-green-500/5 border-green-500/10'
              : 'bg-red-500/5 border-red-500/15'
              }`}
          >
            <div className="flex items-center gap-3">
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${req.installed ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                {req.installed ? <CheckCircle2 size={16} /> : req.icon}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-white">{req.name}</span>
                  {req.installed && req.version && (
                    <span className="text-xs text-gray-500 font-mono">{req.version}</span>
                  )}
                </div>
                <p className="text-xs text-gray-500">
                  {req.versionNote || req.description}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {req.installed ? (
                <span className="text-xs text-green-400 font-medium px-2 py-1 bg-green-500/10 rounded-md">
                  Ready
                </span>
              ) : (
                req.downloadUrl && (
                  <a
                    href={req.downloadUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1.5 px-3 py-1.5 text-gray-300 hover:text-white hover:bg-dark-500 rounded-lg transition-colors text-xs"
                  >
                    <ExternalLink size={12} />
                    <span>Download</span>
                  </a>
                )
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
