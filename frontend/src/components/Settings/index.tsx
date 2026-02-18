import { useAppStore } from '../../stores/appStore';
import { api } from '../../lib/api';
import { useState, useEffect } from 'react';
import { Download, Upload, Save, Loader2, Key, Plus, Trash2, Eye, EyeOff, Cpu, HardDrive, MemoryStick } from 'lucide-react';

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

export function Settings() {
  const { loadAll } = useAppStore();
  const [saving, setSaving] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [envVars, setEnvVars] = useState<EnvVar[]>([]);
  const [systemEnv, setSystemEnv] = useState<Record<string, boolean>>({});
  const [showAddEnv, setShowAddEnv] = useState(false);
  const [newEnvKey, setNewEnvKey] = useState('');
  const [newEnvValue, setNewEnvValue] = useState('');
  const [visibleKeys, setVisibleKeys] = useState<Set<string>>(new Set());
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);

  useEffect(() => {
    loadEnvVars();
    loadSystemInfo();
  }, []);

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

  return (
    <div className="h-full overflow-y-auto scroll-container p-6">
      <h2 className="text-2xl font-bold text-white mb-2">Settings</h2>
      <p className="text-gray-400 mb-8">System configuration</p>

      <div className="space-y-6 max-w-4xl">
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
                  {key}: {isSet ? '✓ Set' : '✗ Not set'}
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
                GitHub Repository →
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
