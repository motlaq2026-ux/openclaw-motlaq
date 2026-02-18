import { create } from 'zustand';
import { api, AIConfigOverview, OfficialProvider, MCPServer, Skill, Agent, ChannelConfig, TelegramAccount, LogEntry, UsageStats } from '../lib/api';

type Page = 'dashboard' | 'ai-config' | 'mcp' | 'skills' | 'channels' | 'agents' | 'logs' | 'settings';

interface AppState {
  currentPage: Page;
  loading: boolean;
  error: string | null;
  
  aiConfig: AIConfigOverview | null;
  officialProviders: OfficialProvider[];
  mcpServers: MCPServer[];
  skills: Skill[];
  agents: Agent[];
  channels: Record<string, ChannelConfig>;
  telegramAccounts: TelegramAccount[];
  logs: LogEntry[];
  usage: UsageStats | null;
  
  setCurrentPage: (page: Page) => void;
  loadAll: () => Promise<void>;
  loadAIConfig: () => Promise<void>;
  loadMCP: () => Promise<void>;
  loadSkills: () => Promise<void>;
  loadAgents: () => Promise<void>;
  loadChannels: () => Promise<void>;
  loadLogs: () => Promise<void>;
  loadUsage: () => Promise<void>;
}

export const useAppStore = create<AppState>((set, get) => ({
  currentPage: 'dashboard',
  loading: false,
  error: null,
  
  aiConfig: null,
  officialProviders: [],
  mcpServers: [],
  skills: [],
  agents: [],
  channels: {},
  telegramAccounts: [],
  logs: [],
  usage: null,
  
  setCurrentPage: (page) => set({ currentPage: page }),
  
  loadAll: async () => {
    set({ loading: true, error: null });
    try {
      const [officialProviders, aiConfig, mcpServers, skills, agents, channels, usage] = await Promise.all([
        api.getOfficialProviders(),
        api.getAIConfig(),
        api.getMCP(),
        api.getSkills(),
        api.getAgents(),
        api.getChannels(),
        api.getUsage(),
      ]);
      set({
        officialProviders: officialProviders.providers,
        aiConfig,
        mcpServers: mcpServers.servers,
        skills: skills.skills,
        agents: agents.agents,
        channels: channels.channels,
        usage,
        loading: false,
      });
    } catch (e) {
      set({ error: String(e), loading: false });
    }
  },
  
  loadAIConfig: async () => {
    try {
      const [officialProviders, aiConfig] = await Promise.all([
        api.getOfficialProviders(),
        api.getAIConfig(),
      ]);
      set({ officialProviders: officialProviders.providers, aiConfig });
    } catch (e) {
      set({ error: String(e) });
    }
  },
  
  loadMCP: async () => {
    try {
      const { servers } = await api.getMCP();
      set({ mcpServers: servers });
    } catch (e) {
      set({ error: String(e) });
    }
  },
  
  loadSkills: async () => {
    try {
      const { skills } = await api.getSkills();
      set({ skills });
    } catch (e) {
      set({ error: String(e) });
    }
  },
  
  loadAgents: async () => {
    try {
      const { agents } = await api.getAgents();
      set({ agents });
    } catch (e) {
      set({ error: String(e) });
    }
  },
  
  loadChannels: async () => {
    try {
      const [channels, { accounts }] = await Promise.all([
        api.getChannels(),
        api.getTelegramAccounts(),
      ]);
      set({ channels: channels.channels, telegramAccounts: accounts });
    } catch (e) {
      set({ error: String(e) });
    }
  },
  
  loadLogs: async () => {
    try {
      const { logs } = await api.getLogs(undefined, 100);
      set({ logs });
    } catch (e) {
      set({ error: String(e) });
    }
  },
  
  loadUsage: async () => {
    try {
      const usage = await api.getUsage();
      set({ usage });
    } catch (e) {
      set({ error: String(e) });
    }
  },
}));
