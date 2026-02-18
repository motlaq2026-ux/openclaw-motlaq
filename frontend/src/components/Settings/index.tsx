import { useAppStore } from '../../stores/appStore';
import { api } from '../../lib/api';
import { useTheme, ThemePicker } from '../../lib/theme.tsx';
import { useState, useEffect } from 'react';
import { 
  Download, Upload, Save, Loader2, Key, Plus, Trash2, Eye, EyeOff, Cpu, HardDrive, MemoryStick,
  User, Shield, FileText, Zap, FolderOpen, Bell, Palette
} from 'lucide-react';
import clsx from 'clsx';

interface EnvVar {
  key: string;
  value: string;
  isSystem?: boolean;
}

interface SystemInfo {
  python_version: string;
  platform: string;
  cpu_count: number;
  memory_total: number;
  memory_available: number;
  disk_total: number;
  disk_free: number;
}

interface IdentityConfig {
  bot_name: string;
  user_name: string;
  timezone: string;
}

interface HeartbeatConfig {
  every: string;
  target: string;
}

interface CompactionConfig {
  enabled: boolean;
  threshold: number;
  context_pruning: boolean;
  max_context_messages: number;
}

interface WorkspaceConfig {
  workspace: string;
  timezone: string;
  time_format: string;
  skip_bootstrap: boolean;
  bootstrap_max_chars: number;
}

const PERSONALITY_FILES = ['AGENTS.md', 'SOUL.md', 'TOOLS.md'] as const;
type PersonalityFile = typeof PERSONALITY_FILES[number];

const TIMEZONES = [
  'UTC', 'America/New_York', 'America/Los_Angeles', 'America/Chicago',
  'Europe/London', 'Europe/Paris', 'Europe/Berlin', 'Asia/Shanghai',
  'Asia/Tokyo', 'Asia/Dubai', 'Asia/Kolkata', 'Australia/Sydney'
];

export function Settings() {
  const { loadAll } = useAppStore();
  const { theme, setTheme } = useTheme();
  const [saving, setSaving] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [envVars, setEnvVars] = useState<EnvVar[]>([]);
  const [systemEnv, setSystemEnv] = useState<Record<string, boolean>>({});
  const [showAddEnv, setShowAddEnv] = useState(false);
  const [newEnvKey, setNewEnvKey] = useState('');
  const [newEnvValue, setNewEnvValue] = useState('');
  const [visibleKeys, setVisibleKeys] = useState<Set<string>>(new Set());
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  
  const [activeTab, setActiveTab] = useState<'identity' | 'advanced' | 'personality' | 'env' | 'backup'>('identity');
  
  const [identity, setIdentity] = useState<IdentityConfig>({
    bot_name: 'Clawd',
    user_name: 'Master',
    timezone: 'UTC',
  });
  
  const [heartbeat, setHeartbeat] = useState<HeartbeatConfig>({
    every: '',
    target: '',
  });
  
  const [compaction, setCompaction] = useState<CompactionConfig>({
    enabled: false,
    threshold: 100,
    context_pruning: false,
    max_context_messages: 50,
  });
  
  const [workspace, setWorkspace] = useState<WorkspaceConfig>({
    workspace: '',
    timezone: 'UTC',
    time_format: '24h',
    skip_bootstrap: false,
    bootstrap_max_chars: 8000,
  });
  
  const [selectedFile, setSelectedFile] = useState<PersonalityFile>('AGENTS.md');
  const [fileContent, setFileContent] = useState('');
  const [fileLoading, setFileLoading] = useState(false);

  useEffect(() => {
    loadEnvVars();
    loadSystemInfo();
    loadConfig();
    loadPersonalityFile();
  }, []);

  useEffect(() => {
    loadPersonalityFile();
  }, [selectedFile]);

  const loadEnvVars = async () => {
    try {
      const { env_vars, system_env } = await fetch('/api/env').then(r => r.json());
      const vars = Object.entries(env_vars).map(([key, value]) => ({ key, value: String(value) }));
      setEnvVars(vars);
      setSystemEnv(system_env);
    } catch (e) {
      console.error('Failed to load env vars:', e);
    }
  };

  const loadSystemInfo = async () => {
    try {
      const info = await fetch('/api/system/info').then(r => r.json());
      setSystemInfo(info);
    } catch (e) {
      console.error('Failed to load system info:', e);
    }
  };

  const loadConfig = async () => {
    try {
      const config = await api.getConfig();
      if (config.identity) {
        const identity = config.identity as IdentityConfig;
        setIdentity({
          bot_name: identity.bot_name || 'Clawd',
          user_name: identity.user_name || 'Master',
          timezone: identity.timezone || 'UTC',
        });
      }
      if (config.heartbeat) {
        const heartbeat = config.heartbeat as HeartbeatConfig;
        setHeartbeat({
          every: heartbeat.every || '',
          target: heartbeat.target || '',
        });
      }
      if (config.compaction) {
        const compaction = config.compaction as CompactionConfig;
        setCompaction({
          enabled: compaction.enabled || false,
          threshold: compaction.threshold || 100,
          context_pruning: compaction.context_pruning || false,
          max_context_messages: compaction.max_context_messages || 50,
        });
      }
      if (config.workspace) {
        const workspace = config.workspace as WorkspaceConfig;
        setWorkspace({
          workspace: workspace.workspace || '',
          timezone: workspace.timezone || 'UTC',
          time_format: workspace.time_format || '24h',
          skip_bootstrap: workspace.skip_bootstrap || false,
          bootstrap_max_chars: workspace.bootstrap_max_chars || 8000,
        });
      }
    } catch (e) {
      console.error('Failed to load config:', e);
    }
  };

  const loadPersonalityFile = async () => {
    setFileLoading(true);
    try {
      const result = await fetch(`/api/prompt?template=${selectedFile}`).then(r => r.json());
      setFileContent(result.content || '');
    } catch {
      setFileContent('');
    } finally {
      setFileLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.saveConfig({
        identity,
        heartbeat,
        compaction,
        workspace,
      });
      
      if (fileContent) {
        await fetch('/api/prompt', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ template: selectedFile, content: fileContent }),
        });
      }
      
      alert('Settings saved!');
    } catch (e) {
      alert('Failed to save: ' + e);
    } finally {
      setSaving(false);
    }
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      const data = await api.getBackup();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `openclaw-backup-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
    }
  };

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const text = await file.text();
    const data = JSON.parse(text);
    setSaving(true);
    try {
      await api.restoreBackup(data);
      await loadAll();
      alert('Backup restored!');
    } catch (err) {
      alert('Failed to restore: ' + err);
    } finally {
      setSaving(false);
    }
  };

  const handleAddEnv = async () => {
    if (!newEnvKey || !newEnvValue) return;
    setSaving(true);
    try {
      await fetch('/api/env', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key: newEnvKey, value: newEnvValue }),
      });
      await loadEnvVars();
      setShowAddEnv(false);
      setNewEnvKey('');
      setNewEnvValue('');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteEnv = async (key: string) => {
    if (!confirm(`Delete ${key}?`)) return;
    await fetch(`/api/env/${key}`, { method: 'DELETE' });
    await loadEnvVars();
  };

  const formatBytes = (bytes: number) => {
    const gb = bytes / (1024 * 1024 * 1024);
    return `${gb.toFixed(1)} GB`;
  };

  const tabs = [
    { id: 'identity', label: 'Identity', icon: User },
    { id: 'advanced', label: 'Advanced', icon: Shield },
    { id: 'personality', label: 'Personality', icon: FileText },
    { id: 'env', label: 'Environment', icon: Key },
    { id: 'backup', label: 'Backup', icon: Download },
  ] as const;

  return (
    <div className="h-full overflow-y-auto scroll-container p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Settings</h2>
          <p className="text-gray-400">System configuration</p>
        </div>
        <button onClick={handleSave} disabled={saving} className="btn-primary flex items-center gap-2">
          {saving ? <Loader2 className="animate-spin" size={16} /> : <Save size={16} />}
          Save All
        </button>
      </div>

      <div className="flex gap-6 max-w-6xl">
        <div className="w-48 shrink-0 space-y-1">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={clsx(
                  'w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all text-left',
                  activeTab === tab.id
                    ? 'bg-claw-500/20 text-claw-400 border border-claw-500/30'
                    : 'text-gray-400 hover:text-white hover:bg-dark-700'
                )}
              >
                <Icon size={18} />
                <span className="font-medium">{tab.label}</span>
              </button>
            );
          })}
        </div>

        <div className="flex-1 min-w-0">
          {activeTab === 'identity' && (
            <div className="space-y-6">
              <div className="bg-dark-800 border border-dark-600 rounded-2xl p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Identity Settings</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Bot Name</label>
                    <input
                      value={identity.bot_name}
                      onChange={(e) => setIdentity({ ...identity, bot_name: e.target.value })}
                      className="input-base"
                      placeholder="Clawd"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Your Name</label>
                    <input
                      value={identity.user_name}
                      onChange={(e) => setIdentity({ ...identity, user_name: e.target.value })}
                      className="input-base"
                      placeholder="Master"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Timezone</label>
                    <select
                      value={identity.timezone}
                      onChange={(e) => setIdentity({ ...identity, timezone: e.target.value })}
                      className="input-base"
                    >
                      {TIMEZONES.map((tz) => (
                        <option key={tz} value={tz}>{tz}</option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              <div className="bg-dark-800 border border-dark-600 rounded-2xl p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Palette size={20} className="text-claw-400" />
                  <h3 className="text-lg font-semibold text-white">Theme</h3>
                </div>
                <p className="text-sm text-gray-400 mb-4">Choose your accent color</p>
                <ThemePicker currentTheme={theme} onThemeChange={setTheme} />
              </div>

              {systemInfo && (
                <div className="bg-dark-800 border border-dark-600 rounded-2xl p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">System Info</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-dark-700 rounded-xl p-3">
                      <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
                        <Cpu size={14} /> CPU Cores
                      </div>
                      <p className="text-xl font-bold text-white">{systemInfo.cpu_count}</p>
                    </div>
                    <div className="bg-dark-700 rounded-xl p-3">
                      <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
                        <MemoryStick size={14} /> Memory
                      </div>
                      <p className="text-xl font-bold text-white">{formatBytes(systemInfo.memory_available)}</p>
                      <p className="text-xs text-gray-500">of {formatBytes(systemInfo.memory_total)}</p>
                    </div>
                    <div className="bg-dark-700 rounded-xl p-3">
                      <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
                        <HardDrive size={14} /> Disk Free
                      </div>
                      <p className="text-xl font-bold text-white">{formatBytes(systemInfo.disk_free)}</p>
                      <p className="text-xs text-gray-500">of {formatBytes(systemInfo.disk_total)}</p>
                    </div>
                    <div className="bg-dark-700 rounded-xl p-3">
                      <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
                        Python
                      </div>
                      <p className="text-xl font-bold text-white">{systemInfo.python_version}</p>
                      <p className="text-xs text-gray-500">{systemInfo.platform}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'advanced' && (
            <div className="space-y-6">
              <div className="bg-dark-800 border border-dark-600 rounded-2xl p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Bell size={20} className="text-amber-400" />
                  <h3 className="text-lg font-semibold text-white">Heartbeat</h3>
                </div>
                <p className="text-sm text-gray-400 mb-4">Periodic ping to keep services alive</p>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Interval</label>
                    <input
                      value={heartbeat.every}
                      onChange={(e) => setHeartbeat({ ...heartbeat, every: e.target.value })}
                      className="input-base"
                      placeholder="e.g., 5m, 1h"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Target URL</label>
                    <input
                      value={heartbeat.target}
                      onChange={(e) => setHeartbeat({ ...heartbeat, target: e.target.value })}
                      className="input-base"
                      placeholder="https://..."
                    />
                  </div>
                </div>
              </div>

              <div className="bg-dark-800 border border-dark-600 rounded-2xl p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Zap size={20} className="text-purple-400" />
                  <h3 className="text-lg font-semibold text-white">Compaction</h3>
                </div>
                <p className="text-sm text-gray-400 mb-4">Manage context window usage</p>
                <div className="space-y-4">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={compaction.enabled}
                      onChange={(e) => setCompaction({ ...compaction, enabled: e.target.checked })}
                      className="w-5 h-5 rounded border-dark-500 bg-dark-700 text-claw-500"
                    />
                    <span className="text-white">Enable automatic compaction</span>
                  </label>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm text-gray-400 mb-2">Threshold (messages)</label>
                      <input
                        type="number"
                        value={compaction.threshold}
                        onChange={(e) => setCompaction({ ...compaction, threshold: Number(e.target.value) })}
                        className="input-base"
                      />
                    </div>
                    <div>
                      <label className="block text-sm text-gray-400 mb-2">Max Context Messages</label>
                      <input
                        type="number"
                        value={compaction.max_context_messages}
                        onChange={(e) => setCompaction({ ...compaction, max_context_messages: Number(e.target.value) })}
                        className="input-base"
                      />
                    </div>
                  </div>
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={compaction.context_pruning}
                      onChange={(e) => setCompaction({ ...compaction, context_pruning: e.target.checked })}
                      className="w-5 h-5 rounded border-dark-500 bg-dark-700 text-claw-500"
                    />
                    <span className="text-white">Enable context pruning</span>
                  </label>
                </div>
              </div>

              <div className="bg-dark-800 border border-dark-600 rounded-2xl p-6">
                <div className="flex items-center gap-3 mb-4">
                  <FolderOpen size={20} className="text-green-400" />
                  <h3 className="text-lg font-semibold text-white">Workspace</h3>
                </div>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Workspace Path</label>
                    <input
                      value={workspace.workspace}
                      onChange={(e) => setWorkspace({ ...workspace, workspace: e.target.value })}
                      className="input-base"
                      placeholder="/path/to/workspace"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm text-gray-400 mb-2">Timezone</label>
                      <select
                        value={workspace.timezone}
                        onChange={(e) => setWorkspace({ ...workspace, timezone: e.target.value })}
                        className="input-base"
                      >
                        {TIMEZONES.map((tz) => (
                          <option key={tz} value={tz}>{tz}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm text-gray-400 mb-2">Time Format</label>
                      <select
                        value={workspace.time_format}
                        onChange={(e) => setWorkspace({ ...workspace, time_format: e.target.value })}
                        className="input-base"
                      >
                        <option value="12h">12-hour</option>
                        <option value="24h">24-hour</option>
                      </select>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Bootstrap Max Characters</label>
                    <input
                      type="number"
                      value={workspace.bootstrap_max_chars}
                      onChange={(e) => setWorkspace({ ...workspace, bootstrap_max_chars: Number(e.target.value) })}
                      className="input-base"
                    />
                  </div>
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={workspace.skip_bootstrap}
                      onChange={(e) => setWorkspace({ ...workspace, skip_bootstrap: e.target.checked })}
                      className="w-5 h-5 rounded border-dark-500 bg-dark-700 text-claw-500"
                    />
                    <span className="text-white">Skip bootstrap</span>
                  </label>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'personality' && (
            <div className="bg-dark-800 border border-dark-600 rounded-2xl p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Personality Files</h3>
              <p className="text-sm text-gray-400 mb-4">Edit the AI's personality and behavior instructions</p>
              
              <div className="flex gap-2 mb-4">
                {PERSONALITY_FILES.map((file) => (
                  <button
                    key={file}
                    onClick={() => setSelectedFile(file)}
                    className={clsx(
                      'px-4 py-2 rounded-lg text-sm font-medium transition-all',
                      selectedFile === file
                        ? 'bg-claw-500/20 text-claw-400 border border-claw-500/30'
                        : 'bg-dark-700 text-gray-400 hover:text-white'
                    )}
                  >
                    {file}
                  </button>
                ))}
              </div>

              {fileLoading ? (
                <div className="flex items-center justify-center h-64">
                  <Loader2 className="w-8 h-8 animate-spin text-claw-500" />
                </div>
              ) : (
                <textarea
                  value={fileContent}
                  onChange={(e) => setFileContent(e.target.value)}
                  className="input-base min-h-[400px] font-mono text-sm"
                  placeholder={`Enter content for ${selectedFile}...`}
                />
              )}
            </div>
          )}

          {activeTab === 'env' && (
            <div className="bg-dark-800 border border-dark-600 rounded-2xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Environment Variables</h3>
                <button onClick={() => setShowAddEnv(true)} className="btn-secondary text-sm flex items-center gap-2">
                  <Plus size={14} /> Add
                </button>
              </div>

              <div className="mb-4">
                <p className="text-sm text-gray-400 mb-2">System Environment (from HF Secrets)</p>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(systemEnv).map(([key, isSet]) => (
                    <div key={key} className={`px-3 py-1 rounded-lg text-xs ${isSet ? 'bg-green-500/20 text-green-400' : 'bg-dark-700 text-gray-500'}`}>
                      {key}: {isSet ? 'Set' : 'Not set'}
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                {envVars.map((env) => (
                  <div key={env.key} className="flex items-center gap-3 bg-dark-700 rounded-xl p-3">
                    <Key size={16} className="text-gray-400" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-white">{env.key}</p>
                      <div className="flex items-center gap-2">
                        <p className="text-xs text-gray-400 font-mono">
                          {visibleKeys.has(env.key) ? env.value : '••••••••'}
                        </p>
                        <button onClick={() => {
                          const next = new Set(visibleKeys);
                          if (next.has(env.key)) next.delete(env.key);
                          else next.add(env.key);
                          setVisibleKeys(next);
                        }} className="text-gray-500 hover:text-white">
                          {visibleKeys.has(env.key) ? <EyeOff size={12} /> : <Eye size={12} />}
                        </button>
                      </div>
                    </div>
                    <button onClick={() => handleDeleteEnv(env.key)} className="text-gray-400 hover:text-red-400">
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))}
                {envVars.length === 0 && (
                  <p className="text-gray-500 text-sm text-center py-4">No custom environment variables</p>
                )}
              </div>

              {showAddEnv && (
                <div className="mt-4 p-4 bg-dark-700 rounded-xl space-y-3">
                  <input
                    value={newEnvKey}
                    onChange={(e) => setNewEnvKey(e.target.value)}
                    className="input-base text-sm"
                    placeholder="KEY_NAME"
                  />
                  <input
                    type="password"
                    value={newEnvValue}
                    onChange={(e) => setNewEnvValue(e.target.value)}
                    className="input-base text-sm"
                    placeholder="value"
                  />
                  <div className="flex gap-2">
                    <button onClick={handleAddEnv} disabled={saving || !newEnvKey || !newEnvValue} className="btn-primary text-sm">
                      {saving ? <Loader2 className="animate-spin" size={14} /> : 'Save'}
                    </button>
                    <button onClick={() => { setShowAddEnv(false); setNewEnvKey(''); setNewEnvValue(''); }} className="btn-secondary text-sm">
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'backup' && (
            <div className="space-y-6">
              <div className="bg-dark-800 border border-dark-600 rounded-2xl p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Backup & Restore</h3>
                <p className="text-sm text-gray-400 mb-4">Export or import your configuration</p>
                <div className="flex gap-3">
                  <button onClick={handleExport} disabled={exporting} className="btn-secondary flex items-center gap-2">
                    {exporting ? <Loader2 className="animate-spin" size={16} /> : <Download size={16} />}
                    Export Backup
                  </button>
                  <label className="btn-secondary flex items-center gap-2 cursor-pointer">
                    <Upload size={16} />
                    Import Backup
                    <input type="file" accept=".json" onChange={handleImport} className="hidden" disabled={saving} />
                  </label>
                </div>
              </div>

              <div className="bg-dark-800 border border-dark-600 rounded-2xl p-6">
                <h3 className="text-lg font-semibold text-white mb-4">About</h3>
                <div className="space-y-2 text-sm">
                  <p className="text-gray-400">Version: <span className="text-white">2.0.0</span></p>
                  <p className="text-gray-400">Build: <span className="text-white">Nuclear + React</span></p>
                  <p className="text-gray-400">License: <span className="text-white">MIT</span></p>
                  <p className="text-gray-400 mt-4">
                    <a href="https://github.com/motlaq2026-ux/openclaw-motlaq" target="_blank" rel="noopener" className="text-claw-500 hover:underline">
                      GitHub Repository
                    </a>
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
