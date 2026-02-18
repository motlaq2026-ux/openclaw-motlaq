import { useAppStore } from '../../stores/appStore';
import { useEffect, useState } from 'react';
import { api } from '../../lib/api';
import { Loader2, MessageCircle, Hash, Slack, Plus, Trash2, Users } from 'lucide-react';

const channelTypes = [
  { id: 'telegram', name: 'Telegram', icon: MessageCircle, color: 'text-blue-400' },
  { id: 'discord', name: 'Discord', icon: Hash, color: 'text-indigo-400' },
  { id: 'slack', name: 'Slack', icon: Slack, color: 'text-purple-400' },
];

export function Channels() {
  const { channels, telegramAccounts, loadChannels, loading } = useAppStore();
  const [selected, setSelected] = useState<string | null>(null);
  const [config, setConfig] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [users, setUsers] = useState<{ id: string; name: string }[]>([]);
  const [fetching, setFetching] = useState(false);

  useEffect(() => {
    loadChannels();
  }, []);

  useEffect(() => {
    if (selected && channels[selected]) {
      setConfig(channels[selected].config as Record<string, string>);
    }
  }, [selected, channels]);

  const handleSave = async () => {
    if (!selected) return;
    setSaving(true);
    try {
      await api.saveChannel(selected, { enabled: true, config });
      await loadChannels();
    } finally {
      setSaving(false);
    }
  };

  const handleFetchUsers = async () => {
    if (!config.botToken) return;
    setFetching(true);
    try {
      const { users } = await api.fetchTelegramUsers(config.botToken);
      setUsers(users);
    } finally {
      setFetching(false);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><Loader2 className="w-8 h-8 animate-spin text-claw-500" /></div>;
  }

  return (
    <div className="h-full overflow-y-auto scroll-container p-6">
      <h2 className="text-2xl font-bold text-white mb-2">Channels</h2>
      <p className="text-gray-400 mb-8">Configure message channels</p>

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
                <span className="font-medium text-white">{ch.name}</span>
                {isConfigured && <span className="text-xs text-green-400 ml-auto">Configured</span>}
              </button>
            );
          })}
        </div>

        <div className="md:col-span-2">
          {selected ? (
            <div className="bg-dark-800 border border-dark-600 rounded-2xl p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Configure {selected}</h3>
              
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
                  <button onClick={handleFetchUsers} disabled={fetching || !config.botToken} className="btn-secondary flex items-center gap-2">
                    <Users size={16} />
                    {fetching ? <Loader2 className="animate-spin" size={16} /> : 'Fetch Users'}
                  </button>
                  {users.length > 0 && (
                    <div className="bg-dark-700 rounded-xl p-3 max-h-40 overflow-y-auto">
                      {users.map((u) => (
                        <div key={u.id} className="flex items-center justify-between py-1">
                          <span className="text-sm text-white">{u.name}</span>
                          <span className="text-xs text-gray-400">{u.id}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <div className="flex gap-3 mt-6">
                <button onClick={handleSave} disabled={saving} className="btn-primary flex items-center gap-2">
                  {saving && <Loader2 className="animate-spin" size={16} />} Save
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
