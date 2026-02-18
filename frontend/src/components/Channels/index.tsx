import { useAppStore } from '../../stores/appStore';
import { useEffect, useState } from 'react';
import { api } from '../../lib/api';
import { Loader2, MessageCircle, Hash, Slack, Users, CheckCircle, XCircle, TestTube, Plus, Trash2, Eye, EyeOff, Bot, ChevronDown, ChevronUp, Apple, Bell, MessageSquare, MessagesSquare } from 'lucide-react';
import clsx from 'clsx';

const channelTypes = [
  { id: 'telegram', name: 'Telegram', icon: MessageCircle, color: 'text-blue-400', description: 'Telegram bot integration' },
  { id: 'discord', name: 'Discord', icon: Hash, color: 'text-indigo-400', description: 'Discord bot integration' },
  { id: 'slack', name: 'Slack', icon: Slack, color: 'text-purple-400', description: 'Slack bot integration' },
  { id: 'feishu', name: 'Feishu', icon: MessagesSquare, color: 'text-blue-500', description: 'Feishu/Lark integration' },
  { id: 'imessage', name: 'iMessage', icon: Apple, color: 'text-green-400', description: 'macOS iMessage integration' },
  { id: 'whatsapp', name: 'WhatsApp', icon: MessageCircle, color: 'text-green-500', description: 'WhatsApp integration' },
  { id: 'wechat', name: 'WeChat', icon: MessageSquare, color: 'text-green-600', description: 'WeChat integration' },
  { id: 'dingtalk', name: 'DingTalk', icon: Bell, color: 'text-blue-600', description: 'DingTalk integration' },
];

interface TelegramUser {
  id: string;
  name: string;
  username?: string;
}

interface TelegramAccount {
  id: string;
  bot_token?: string;
  dm_policy?: string;
  group_policy?: string;
  stream_mode?: string;
  groups?: Record<string, GroupSettings>;
  exclusive_topics?: string[];
  allow_from?: string[];
  primary?: boolean;
}

interface GroupSettings {
  requireMention?: boolean;
  enabled?: boolean;
  groupPolicy?: string;
  systemPrompt?: string;
}

function DmAllowListEditor({
  allowedUsers = [],
  onUpdate,
  botToken,
}: {
  allowedUsers: string[];
  onUpdate: (users: string[]) => void;
  botToken?: string;
}) {
  const [inputVal, setInputVal] = useState('');
  const [fetching, setFetching] = useState(false);
  const [discovered, setDiscovered] = useState<TelegramUser[]>([]);

  const fetchUsers = async () => {
    if (!botToken) {
      alert('Bot Token is required.');
      return;
    }
    setFetching(true);
    setDiscovered([]);
    try {
      const { users } = await api.fetchTelegramUsers(botToken);
      setDiscovered(users);
      if (users.length === 0) {
        alert('No users found. Make sure someone sent /start to the bot.');
      }
    } catch (e) {
      alert('Failed to fetch users: ' + e);
    } finally {
      setFetching(false);
    }
  };

  const addUser = (id: string) => {
    const val = id.trim();
    if (val && !allowedUsers.includes(val)) {
      onUpdate([...allowedUsers, val]);
    }
  };

  const removeUser = (id: string) => {
    onUpdate(allowedUsers.filter((u) => u !== id));
  };

  return (
    <div className="p-3 bg-dark-600 rounded-lg border border-dark-500 space-y-2 mt-3">
      <div className="flex items-center justify-between">
        <label className="text-xs text-gray-400 font-semibold">Allowed DM Users (User ID)</label>
        <button
          onClick={fetchUsers}
          disabled={fetching || !botToken}
          className="btn-secondary text-xs py-1 px-2 flex items-center gap-1"
        >
          {fetching ? <Loader2 size={12} className="animate-spin" /> : <Users size={12} />}
          Fetch Users
        </button>
      </div>

      {discovered.length > 0 && (
        <div className="space-y-1 p-2 bg-dark-700 rounded-lg border border-blue-500/30">
          <p className="text-xs text-blue-400 font-semibold mb-1">Discovered Users (click + to add)</p>
          {discovered.map((u) => {
            const alreadyAdded = allowedUsers.includes(u.id);
            return (
              <div key={u.id} className="flex items-center justify-between text-xs bg-dark-600 px-2 py-1 rounded">
                <div className="flex items-center gap-2 min-w-0">
                  <span className="text-gray-200 truncate">{u.name}</span>
                  {u.username && <span className="text-gray-500 text-[10px]">@{u.username}</span>}
                  <span className="font-mono text-gray-400 text-[10px]">{u.id}</span>
                </div>
                {alreadyAdded ? (
                  <span className="text-green-400 text-[10px] flex items-center gap-0.5">
                    <CheckCircle size={10} /> Added
                  </span>
                ) : (
                  <button onClick={() => addUser(u.id)} className="text-blue-400 hover:text-blue-300 p-0.5">
                    <Plus size={12} />
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}

      <div className="flex gap-2">
        <input
          type="text"
          value={inputVal}
          onChange={(e) => setInputVal(e.target.value)}
          placeholder="e.g. 123456789"
          className="input-base text-xs flex-1"
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              addUser(inputVal);
              setInputVal('');
            }
          }}
        />
        <button
          onClick={() => {
            addUser(inputVal);
            setInputVal('');
          }}
          className="btn-secondary p-1.5"
        >
          <Plus size={14} />
        </button>
      </div>

      <div className="space-y-1 max-h-32 overflow-y-auto">
        {allowedUsers.map((id) => (
          <div key={id} className="flex items-center justify-between text-xs bg-dark-500 px-2 py-1 rounded">
            <span className="font-mono text-gray-300">{id}</span>
            <button onClick={() => removeUser(id)} className="text-gray-500 hover:text-red-400">
              <Trash2 size={12} />
            </button>
          </div>
        ))}
        {allowedUsers.length === 0 && (
          <p className="text-[10px] text-gray-500 italic text-center py-1">No users added yet</p>
        )}
      </div>
    </div>
  );
}

export function Channels() {
  const { channels, loadChannels, loading } = useAppStore();
  const [selected, setSelected] = useState<string>('telegram');
  const [config, setConfig] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [showPassword, setShowPassword] = useState(false);

  // Telegram multi-account state
  const [telegramAccounts, setTelegramAccounts] = useState<TelegramAccount[]>([]);
  const [showAddAccount, setShowAddAccount] = useState(false);
  const [expandedAccount, setExpandedAccount] = useState<string | null>(null);
  const [accountForm, setAccountForm] = useState<Partial<TelegramAccount>>({});

  // Group settings
  const [allowedGroups, setAllowedGroups] = useState<Record<string, GroupSettings>>({});
  const [newGroupInput, setNewGroupInput] = useState('');

  useEffect(() => {
    loadChannels();
    loadTelegramAccounts();
  }, []);

  const loadTelegramAccounts = async () => {
    try {
      const { accounts } = await api.getTelegramAccounts();
      setTelegramAccounts(accounts as TelegramAccount[]);
    } catch (e) {
      console.error('Failed to load telegram accounts:', e);
    }
  };

  const handleTest = async () => {
    if (!selected) return;
    setTesting(true);
    setTestResult(null);
    try {
      const result = await api.testChannel(selected, config) as { success: boolean; bot_username?: string; error?: string };
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

  const handleSave = async () => {
    if (!selected) return;
    setSaving(true);
    setTestResult(null);
    try {
      const saveConfig: Record<string, unknown> = { ...config };
      if (Object.keys(allowedGroups).length > 0) {
        saveConfig.groups = allowedGroups;
      }
      await api.saveChannel(selected, { enabled: true, config: saveConfig });
      
      // Save all telegram accounts
      if (selected === 'telegram') {
        for (const account of telegramAccounts) {
          await api.saveTelegramAccount(account as any);
        }
      }
      
      await loadChannels();
      setTestResult({ success: true, message: 'Configuration saved!' });
    } catch (e) {
      setTestResult({ success: false, message: String(e) });
    } finally {
      setSaving(false);
    }
  };

  const handleAddAccount = async () => {
    if (!accountForm.id || !accountForm.bot_token) {
      alert('Account ID and Bot Token are required');
      return;
    }
    setSaving(true);
    try {
      const account: TelegramAccount = {
        id: accountForm.id,
        bot_token: accountForm.bot_token,
        dm_policy: accountForm.dm_policy || 'pairing',
        group_policy: accountForm.group_policy || 'open',
        stream_mode: accountForm.stream_mode || 'partial',
        allow_from: accountForm.allow_from || [],
        primary: telegramAccounts.length === 0,
      };
      await api.saveTelegramAccount(account);
      await loadTelegramAccounts();
      setShowAddAccount(false);
      setAccountForm({});
    } catch (e) {
      alert('Failed to save account: ' + e);
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteAccount = async (id: string) => {
    if (!confirm(`Delete account ${id}?`)) return;
    try {
      await api.deleteTelegramAccount(id);
      await loadTelegramAccounts();
    } catch (e) {
      alert('Failed to delete account: ' + e);
    }
  };

  const handleSetPrimary = async (id: string) => {
    const updated = telegramAccounts.map((a) => ({
      ...a,
      primary: a.id === id,
    }));
    setTelegramAccounts(updated);
    for (const account of updated) {
      await api.saveTelegramAccount(account);
    }
  };

  const addGroup = () => {
    const id = newGroupInput.trim();
    if (id && !(id in allowedGroups)) {
      setAllowedGroups({
        ...allowedGroups,
        [id]: { requireMention: false, enabled: true, groupPolicy: 'open', systemPrompt: '' },
      });
      setNewGroupInput('');
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
                className={clsx(
                  'w-full flex items-center gap-3 p-4 rounded-xl border transition-all',
                  isActive ? 'bg-dark-700 border-claw-500' : 'bg-dark-800 border-dark-600 hover:border-dark-500'
                )}
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
          <div className="bg-dark-800 border border-dark-600 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">Configure {selected}</h3>
              <div className="flex gap-2">
                <button onClick={handleTest} disabled={testing} className="btn-secondary text-sm flex items-center gap-2">
                  {testing ? <Loader2 className="animate-spin" size={14} /> : <TestTube size={14} />}
                  Test
                </button>
              </div>
            </div>

            {testResult && (
              <div
                className={clsx(
                  'mb-4 p-3 rounded-xl',
                  testResult.success ? 'bg-green-500/10 border border-green-500/30' : 'bg-red-500/10 border border-red-500/30'
                )}
              >
                <p className={clsx('text-sm', testResult.success ? 'text-green-400' : 'text-red-400')}>{testResult.message}</p>
              </div>
            )}

            {selected === 'telegram' && (
              <div className="space-y-6">
                {/* Multi-account banner */}
                {telegramAccounts.length > 0 && (
                  <div className="p-3 bg-blue-500/10 rounded-xl border border-blue-500/30 flex items-start gap-2">
                    <Bot size={16} className="text-blue-400 mt-0.5 shrink-0" />
                    <p className="text-xs text-gray-300">
                      <strong className="text-blue-400">Multi-bot mode active.</strong> Each bot has its own settings below.
                    </p>
                  </div>
                )}

                {/* Telegram Accounts List */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-medium text-gray-400">Bot Accounts</h4>
                    <button onClick={() => setShowAddAccount(true)} className="btn-secondary text-xs py-1 px-2 flex items-center gap-1">
                      <Plus size={12} /> Add Bot
                    </button>
                  </div>

                  {telegramAccounts.map((account) => (
                    <div key={account.id} className="bg-dark-700 rounded-xl border border-dark-500 overflow-hidden">
                      <div
                        className="flex items-center justify-between p-3 cursor-pointer hover:bg-dark-600/50"
                        onClick={() => setExpandedAccount(expandedAccount === account.id ? null : account.id)}
                      >
                        <div className="flex items-center gap-3">
                          <div className={clsx('w-8 h-8 rounded-lg flex items-center justify-center', account.primary ? 'bg-claw-500/20' : 'bg-dark-600')}>
                            <Bot size={16} className={account.primary ? 'text-claw-400' : 'text-gray-500'} />
                          </div>
                          <div>
                            <p className="text-sm font-medium text-white flex items-center gap-2">
                              {account.id}
                              {account.primary && <span className="text-xs text-yellow-400">★ Primary</span>}
                            </p>
                            <p className="text-xs text-gray-500">
                              DM: {account.dm_policy || 'pairing'} | Group: {account.group_policy || 'open'}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {!account.primary && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleSetPrimary(account.id);
                              }}
                              className="text-xs text-gray-500 hover:text-yellow-400"
                            >
                              Set Primary
                            </button>
                          )}
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteAccount(account.id);
                            }}
                            className="text-gray-500 hover:text-red-400"
                          >
                            <Trash2 size={14} />
                          </button>
                          {expandedAccount === account.id ? <ChevronUp size={16} className="text-gray-500" /> : <ChevronDown size={16} className="text-gray-500" />}
                        </div>
                      </div>

                      {expandedAccount === account.id && (
                        <div className="border-t border-dark-600 p-4 space-y-4">
                          {/* DM Policy */}
                          <div>
                            <label className="block text-xs text-gray-400 mb-1">DM Policy</label>
                            <select
                              value={account.dm_policy || 'pairing'}
                              onChange={(e) => {
                                const updated = telegramAccounts.map((a) =>
                                  a.id === account.id ? { ...a, dm_policy: e.target.value } : a
                                );
                                setTelegramAccounts(updated);
                              }}
                              className="input-base text-sm"
                            >
                              <option value="pairing">Pairing Mode</option>
                              <option value="open">Open Mode</option>
                              <option value="disabled">Disabled</option>
                            </select>
                          </div>

                          {/* Group Policy */}
                          <div>
                            <label className="block text-xs text-gray-400 mb-1">Group Policy</label>
                            <select
                              value={account.group_policy || 'open'}
                              onChange={(e) => {
                                const updated = telegramAccounts.map((a) =>
                                  a.id === account.id ? { ...a, group_policy: e.target.value } : a
                                );
                                setTelegramAccounts(updated);
                              }}
                              className="input-base text-sm"
                            >
                              <option value="open">Open (Respond to all)</option>
                              <option value="allowlist">Allowlist Only</option>
                              <option value="disabled">Disabled</option>
                            </select>
                          </div>

                          {/* Stream Mode */}
                          <div>
                            <label className="block text-xs text-gray-400 mb-1">Stream Mode</label>
                            <select
                              value={account.stream_mode || 'partial'}
                              onChange={(e) => {
                                const updated = telegramAccounts.map((a) =>
                                  a.id === account.id ? { ...a, stream_mode: e.target.value } : a
                                );
                                setTelegramAccounts(updated);
                              }}
                              className="input-base text-sm"
                            >
                              <option value="partial">Partial (Default)</option>
                              <option value="block">Block</option>
                              <option value="off">Off</option>
                            </select>
                          </div>

                          {/* DM Allowlist */}
                          <DmAllowListEditor
                            allowedUsers={account.allow_from || []}
                            onUpdate={(users) => {
                              const updated = telegramAccounts.map((a) =>
                                a.id === account.id ? { ...a, allow_from: users } : a
                              );
                              setTelegramAccounts(updated);
                            }}
                            botToken={account.bot_token}
                          />

                          {/* Allowed Groups */}
                          <div className="p-3 bg-dark-600 rounded-lg border border-dark-500">
                            <label className="block text-xs text-gray-400 font-semibold mb-2">Allowed Groups</label>
                            <div className="flex gap-2 mb-2">
                              <input
                                type="text"
                                value={newGroupInput}
                                onChange={(e) => setNewGroupInput(e.target.value)}
                                placeholder="e.g. -1001234567890"
                                className="input-base text-xs flex-1"
                                onKeyDown={(e) => e.key === 'Enter' && addGroup()}
                              />
                              <button onClick={addGroup} className="btn-secondary p-1.5">
                                <Plus size={14} />
                              </button>
                            </div>
                            <div className="space-y-2 max-h-40 overflow-y-auto">
                              {Object.entries(account.groups || {}).map(([gid, settings]) => (
                                <div key={gid} className="bg-dark-500 rounded-lg p-2 border border-dark-400">
                                  <div className="flex items-center justify-between mb-2">
                                    <span className="font-mono text-xs text-gray-300">{gid}</span>
                                    <div className="flex gap-1">
                                      <button
                                        onClick={() => {
                                          const updated = telegramAccounts.map((a) =>
                                            a.id === account.id
                                              ? {
                                                  ...a,
                                                  groups: {
                                                    ...a.groups,
                                                    [gid]: { ...(a.groups?.[gid] || {}), enabled: !settings?.enabled },
                                                  },
                                                }
                                              : a
                                          );
                                          setTelegramAccounts(updated);
                                        }}
                                        className={clsx(
                                          'text-[10px] px-1.5 py-0.5 rounded-full border',
                                          settings?.enabled !== false
                                            ? 'border-green-500/50 bg-green-500/10 text-green-400'
                                            : 'border-red-500/50 bg-red-500/10 text-red-400'
                                        )}
                                      >
                                        {settings?.enabled !== false ? 'enabled' : 'disabled'}
                                      </button>
                                      <button
                                        onClick={() => {
                                          const updated = telegramAccounts.map((a) =>
                                            a.id === account.id
                                              ? {
                                                  ...a,
                                                  groups: {
                                                    ...a.groups,
                                                    [gid]: { ...(a.groups?.[gid] || {}), requireMention: !settings?.requireMention },
                                                  },
                                                }
                                              : a
                                          );
                                          setTelegramAccounts(updated);
                                        }}
                                        className={clsx(
                                          'text-[10px] px-1.5 py-0.5 rounded-full border',
                                          settings?.requireMention
                                            ? 'border-yellow-500/50 bg-yellow-500/10 text-yellow-400'
                                            : 'border-green-500/50 bg-green-500/10 text-green-400'
                                        )}
                                      >
                                        {settings?.requireMention ? '@mention' : 'all'}
                                      </button>
                                    </div>
                                  </div>
                                  <input
                                    type="text"
                                    placeholder="System prompt for this group..."
                                    value={settings?.systemPrompt || ''}
                                    onChange={(e) => {
                                      const updated = telegramAccounts.map((a) =>
                                        a.id === account.id
                                          ? {
                                              ...a,
                                              groups: {
                                                ...a.groups,
                                                [gid]: { ...(a.groups?.[gid] || {}), systemPrompt: e.target.value },
                                              },
                                            }
                                          : a
                                      );
                                      setTelegramAccounts(updated);
                                    }}
                                    className="input-base text-xs"
                                  />
                                </div>
                              ))}
                              {Object.keys(account.groups || {}).length === 0 && (
                                <p className="text-xs text-gray-500 text-center py-2">No groups added</p>
                              )}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}

                  {telegramAccounts.length === 0 && (
                    <div className="bg-dark-700 rounded-xl border border-dark-500 p-8 text-center">
                      <Bot size={32} className="text-gray-500 mx-auto mb-3" />
                      <p className="text-gray-400 mb-4">No bot accounts configured</p>
                      <button onClick={() => setShowAddAccount(true)} className="btn-primary">
                        Add Your First Bot
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}

            {selected === 'discord' && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Bot Token</label>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={config.botToken || ''}
                      onChange={(e) => setConfig({ ...config, botToken: e.target.value })}
                      className="input-base pr-10"
                      placeholder="Discord Bot Token"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white"
                    >
                      {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
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
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={config.botToken || ''}
                      onChange={(e) => setConfig({ ...config, botToken: e.target.value })}
                      className="input-base pr-10"
                      placeholder="xoxb-..."
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white"
                    >
                      {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
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

            {selected === 'feishu' && (
              <div className="space-y-4">
                <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl">
                  <p className="text-xs text-amber-400">Requires @m1heng-clawd/feishu plugin</p>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">App ID</label>
                  <input
                    value={config.appId || ''}
                    onChange={(e) => setConfig({ ...config, appId: e.target.value })}
                    className="input-base"
                    placeholder="Feishu App ID"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">App Secret</label>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={config.appSecret || ''}
                      onChange={(e) => setConfig({ ...config, appSecret: e.target.value })}
                      className="input-base pr-10"
                      placeholder="Feishu App Secret"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white"
                    >
                      {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Connection Mode</label>
                  <select
                    value={config.connectionMode || 'websocket'}
                    onChange={(e) => setConfig({ ...config, connectionMode: e.target.value })}
                    className="input-base"
                  >
                    <option value="websocket">WebSocket (Recommended)</option>
                    <option value="webhook">Webhook</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Deployment Region</label>
                  <select
                    value={config.domain || 'feishu'}
                    onChange={(e) => setConfig({ ...config, domain: e.target.value })}
                    className="input-base"
                  >
                    <option value="feishu">China (feishu.cn)</option>
                    <option value="lark">International (larksuite.com)</option>
                  </select>
                </div>
              </div>
            )}

            {selected === 'imessage' && (
              <div className="space-y-4">
                <div className="p-3 bg-blue-500/10 border border-blue-500/30 rounded-xl">
                  <p className="text-xs text-blue-400">macOS only - requires Messages access permission</p>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">DM Policy</label>
                  <select
                    value={config.dmPolicy || 'pairing'}
                    onChange={(e) => setConfig({ ...config, dmPolicy: e.target.value })}
                    className="input-base"
                  >
                    <option value="pairing">Pairing Mode</option>
                    <option value="open">Open Mode</option>
                    <option value="disabled">Disabled</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Group Policy</label>
                  <select
                    value={config.groupPolicy || 'open'}
                    onChange={(e) => setConfig({ ...config, groupPolicy: e.target.value })}
                    className="input-base"
                  >
                    <option value="open">Open (Respond to all)</option>
                    <option value="allowlist">Allowlist Only</option>
                    <option value="disabled">Disabled</option>
                  </select>
                </div>
              </div>
            )}

            {selected === 'whatsapp' && (
              <div className="space-y-4">
                <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl">
                  <p className="text-xs text-amber-400">Requires QR code scan to login</p>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">DM Policy</label>
                  <select
                    value={config.dmPolicy || 'pairing'}
                    onChange={(e) => setConfig({ ...config, dmPolicy: e.target.value })}
                    className="input-base"
                  >
                    <option value="pairing">Pairing Mode</option>
                    <option value="open">Open Mode</option>
                    <option value="disabled">Disabled</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Group Policy</label>
                  <select
                    value={config.groupPolicy || 'open'}
                    onChange={(e) => setConfig({ ...config, groupPolicy: e.target.value })}
                    className="input-base"
                  >
                    <option value="open">Open (Respond to all)</option>
                    <option value="allowlist">Allowlist Only</option>
                    <option value="disabled">Disabled</option>
                  </select>
                </div>
              </div>
            )}

            {selected === 'wechat' && (
              <div className="space-y-4">
                <div className="p-3 bg-green-500/10 border border-green-500/30 rounded-xl">
                  <p className="text-xs text-green-400">WeChat Official Account / Enterprise WeChat</p>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">App ID</label>
                  <input
                    value={config.appId || ''}
                    onChange={(e) => setConfig({ ...config, appId: e.target.value })}
                    className="input-base"
                    placeholder="WeChat Open Platform App ID"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">App Secret</label>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={config.appSecret || ''}
                      onChange={(e) => setConfig({ ...config, appSecret: e.target.value })}
                      className="input-base pr-10"
                      placeholder="WeChat App Secret"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white"
                    >
                      {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {selected === 'dingtalk' && (
              <div className="space-y-4">
                <div className="p-3 bg-blue-500/10 border border-blue-500/30 rounded-xl">
                  <p className="text-xs text-blue-400">DingTalk Open Platform integration</p>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">App Key</label>
                  <input
                    value={config.appKey || ''}
                    onChange={(e) => setConfig({ ...config, appKey: e.target.value })}
                    className="input-base"
                    placeholder="DingTalk App Key"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">App Secret</label>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={config.appSecret || ''}
                      onChange={(e) => setConfig({ ...config, appSecret: e.target.value })}
                      className="input-base pr-10"
                      placeholder="DingTalk App Secret"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white"
                    >
                      {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                </div>
              </div>
            )}

            <div className="flex gap-3 mt-6">
              <button onClick={handleSave} disabled={saving} className="btn-primary flex items-center gap-2">
                {saving && <Loader2 className="animate-spin" size={16} />} Save Configuration
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Add Account Dialog */}
      {showAddAccount && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-dark-800 border border-dark-600 rounded-2xl p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold text-white mb-4">Add Telegram Bot</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Account ID</label>
                <input
                  value={accountForm.id || ''}
                  onChange={(e) => setAccountForm({ ...accountForm, id: e.target.value })}
                  className="input-base"
                  placeholder="e.g. my-bot-1"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Bot Token</label>
                <input
                  type="password"
                  value={accountForm.bot_token || ''}
                  onChange={(e) => setAccountForm({ ...accountForm, bot_token: e.target.value })}
                  className="input-base"
                  placeholder="From @BotFather"
                />
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button onClick={handleAddAccount} disabled={saving} className="btn-primary flex items-center gap-2">
                {saving && <Loader2 className="animate-spin" size={16} />} Add Bot
              </button>
              <button onClick={() => { setShowAddAccount(false); setAccountForm({}); }} className="btn-secondary">
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
