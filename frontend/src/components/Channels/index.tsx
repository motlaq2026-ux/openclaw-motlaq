import { useAppStore } from '../../stores/appStore';
import { useEffect, useState } from 'react';
import { api } from '../../lib/api';
import { Loader2, MessageCircle, Hash, Slack, Plus, Trash2, Users, CheckCircle, XCircle, TestTube } from 'lucide-react';

const channelTypes = [
  { id: 'telegram', name: 'Telegram', icon: MessageCircle, color: 'text-blue-400', description: 'Telegram bot integration' },
  { id: 'discord', name: 'Discord', icon: Hash, color: 'text-indigo-400', description: 'Discord bot integration' },
  { id: 'slack', name: 'Slack', icon: Slack, color: 'text-purple-400', description: 'Slack bot integration' },
];

interface TelegramUser {
  id: string;
  name: string;
  username?: string;
}

export function Channels() {
  const { channels, loadChannels, loading } = useAppStore();
  const [selected, setSelected] = useState<string | null>(null);
  const [config, setConfig] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [users, setUsers] = useState<TelegramUser[]>([]);
  const [fetching, setFetching] = useState(false);

  useEffect(() => {
    loadChannels();
  }, []);

  useEffect(() => {
    if (selected && channels[selected]) {
      const channelConfig = channels[selected].config || {};
      const formConfig: Record<string, string> = {};
      Object.entries(channelConfig).forEach(([key, value]) => {
        if (typeof value === 'string' || typeof value === 'number') {
          formConfig[key] = String(value);
        }
      });
      setConfig(formConfig);
    } else {
      setConfig({});
    }
    setTestResult(null);
  }, [selected, channels]);

  const handleSave = async () => {
    if (!selected) return;
    setSaving(true);
    setTestResult(null);
    try {
      await api.saveChannel(selected, { enabled: true, config });
      await loadChannels();
      setTestResult({ success: true, message: 'Configuration saved!' });
    } catch (e) {
      setTestResult({ success: false, message: String(e) });
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    if (!selected) return;
    setTesting(true);
    setTestResult(null);
    try {
      const result = await api.testChannel(selected, config);
      setTestResult({
        success: result.success,
        message: result.success ? `Connected! Bot: @${result.bot_username || 'unknown'}` : result.error || 'Failed',
      });
    } catch (e) {
      setTestResult({ success: false, message: String(e) });
    } finally {
      setTesting(false);
    }
  };

  const handleFetchUsers = async () => {
    const botToken = config.botToken;
    if (!botToken) return;
    setFetching(true);
    try {
      const { users } = await api.fetchTelegramUsers(botToken);
      setUsers(users);
    } catch (e) {
      console.error('Failed to fetch users:', e);
    } finally {
      setFetching(false);
    }
  };

  const handleClear = async () => {
    if (!selected) return;
    if (!confirm('Clear configuration for ' + selected + '?')) return;
    try {
      await api.clearChannel(selected);
      await loadChannels();
      setConfig({});
      setTestResult(null);
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><Loader2 className="w-8 h-8 animate-spin text-claw-500" /></div>;
  }

  return (
    <div className="h-full overflow-y-auto scroll-container p-6">
      <h2 className="text-2xl font-bold text-white mb-2">Channels</h2>
      <p className="text-gray-400 mb-8">Configure message channels for your AI assistant</p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="space-y-2">
          {channelTypes.map((ch) => {
            const Icon = ch.icon;
            const isActive = selected === ch.id;
            const isConfigured = channels[ch.id]?.enabled;
            return (
              <button
                key={ch.id}
                onClick={() => setSelected(ch.id)}
                className={`w-full flex items-center gap-3 p-4 rounded-xl border transition-all ${
                  isActive ? 'bg-dark-700 border-claw-500' : 'bg-dark-800 border-dark-600 hover:border-dark-500'
                }`}
              >
                <Icon className={ch.color} size={20} />
                <div className="text-left flex-1">
                  <span className="font-medium text-white">{ch.name}</span>
                  <p className="text-xs text-gray-500">{ch.description}</p>
                </div>
                {isConfigured ? (
                  <CheckCircle className="text-green-500" size={16} />
                ) : (
                  <XCircle className="text-gray-600" size={16} />
                )}
              </button>
            );
          })}
        </div>

        <div className="md:col-span-2">
          {selected ? (
            <div className="bg-dark-800 border border-dark-600 rounded-2xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Configure {selected}</h3>
                <div className="flex gap-2">
                  <button onClick={handleTest} disabled={testing} className="btn-secondary text-sm flex items-center gap-2">
                    {testing ? <Loader2 className="animate-spin" size={14} /> : <TestTube size={14} />}
                    Test
                  </button>
                  <button onClick={handleClear} className="btn-secondary text-sm text-red-400">
                    Clear
                  </button>
                </div>
              </div>

              {testResult && (
                <div className={`mb-4 p-3 rounded-xl ${testResult.success ? 'bg-green-500/10 border border-green-500/30' : 'bg-red-500/10 border border-red-500/30'}`}>
                  <p className={`text-sm ${testResult.success ? 'text-green-400' : 'text-red-400'}`}>
                    {testResult.message}
                  </p>
                </div>
              )}
              
              {selected === 'telegram' && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Bot Token</label>
                    <input
                      type="password"
                      value={config.botToken || ''}
                      onChange={(e) => setConfig({ ...config, botToken: e.target.value })}
                      className="input-base"
                      placeholder="From @BotFather"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Allowed Users (comma-separated IDs)</label>
                    <input
                      value={config.allowedUsers || ''}
                      onChange={(e) => setConfig({ ...config, allowedUsers: e.target.value })}
                      className="input-base"
                      placeholder="123456789, 987654321"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Allowed Groups (comma-separated IDs)</label>
                    <input
                      value={config.allowedGroups || ''}
                      onChange={(e) => setConfig({ ...config, allowedGroups: e.target.value })}
                      className="input-base"
                      placeholder="-1001234567890"
                    />
                  </div>
                  <button onClick={handleFetchUsers} disabled={fetching || !config.botToken} className="btn-secondary flex items-center gap-2">
                    <Users size={16} />
                    {fetching ? <Loader2 className="animate-spin" size={16} /> : 'Fetch Users from Bot'}
                  </button>
                  {users.length > 0 && (
                    <div className="bg-dark-700 rounded-xl p-3 max-h-40 overflow-y-auto">
                      <p className="text-xs text-gray-400 mb-2">Recent users (click to add):</p>
                      {users.map((u) => (
                        <button
                          key={u.id}
                          onClick={() => {
                            const current = config.allowedUsers || '';
                            if (!current.includes(u.id)) {
                              setConfig({ ...config, allowedUsers: current ? `${current}, ${u.id}` : u.id });
                            }
                          }}
                          className="w-full flex items-center justify-between py-1 px-2 hover:bg-dark-600 rounded text-left"
                        >
                          <span className="text-sm text-white">{u.name}</span>
                          <span className="text-xs text-gray-400">{u.id}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {selected === 'discord' && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Bot Token</label>
                    <input
                      type="password"
                      value={config.botToken || ''}
                      onChange={(e) => setConfig({ ...config, botToken: e.target.value })}
                      className="input-base"
                      placeholder="Discord Bot Token"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Test Channel ID</label>
                    <input
                      value={config.testChannelId || ''}
                      onChange={(e) => setConfig({ ...config, testChannelId: e.target.value })}
                      className="input-base"
                      placeholder="Channel ID for testing"
                    />
                  </div>
                </div>
              )}

              {selected === 'slack' && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Bot Token (xoxb-)</label>
                    <input
                      type="password"
                      value={config.botToken || ''}
                      onChange={(e) => setConfig({ ...config, botToken: e.target.value })}
                      className="input-base"
                      placeholder="xoxb-..."
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">App Token (xapp-)</label>
                    <input
                      type="password"
                      value={config.appToken || ''}
                      onChange={(e) => setConfig({ ...config, appToken: e.target.value })}
                      className="input-base"
                      placeholder="xapp-..."
                    />
                  </div>
                </div>
              )}

              <div className="flex gap-3 mt-6">
                <button onClick={handleSave} disabled={saving} className="btn-primary flex items-center gap-2">
                  {saving && <Loader2 className="animate-spin" size={16} />} Save Configuration
                </button>
              </div>
            </div>
          ) : (
            <div className="bg-dark-800 border border-dark-600 rounded-2xl p-12 text-center">
              <p className="text-gray-400">Select a channel to configure</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
