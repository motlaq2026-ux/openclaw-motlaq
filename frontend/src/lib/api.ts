const API_BASE = '/api';

// Get API key from storage
const getApiKey = (): string | null => {
  return localStorage.getItem('openclaw_api_key');
};

// Store API key
export const setApiKey = (key: string): void => {
  localStorage.setItem('openclaw_api_key', key);
};

// Clear API key
export const clearApiKey = (): void => {
  localStorage.removeItem('openclaw_api_key');
};

class APIError extends Error {
  constructor(
    public status: number,
    message: string,
    public data?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

interface RequestConfig extends RequestInit {
  skipAuth?: boolean;
}

async function request<T>(path: string, options: RequestConfig = {}): Promise<T> {
  const apiKey = getApiKey();
  
  // Check if API key exists (except for health check)
  if (!options.skipAuth && !apiKey) {
    throw new APIError(401, 'API key not configured. Please set your API key in settings.');
  }

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((options.headers as Record<string, string>) || {}),
  };

  // Add API key header
  if (!options.skipAuth && apiKey) {
    headers['X-API-Key'] = apiKey;
  }

  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
      redirect: 'follow',
    });

    // Handle specific error codes
    if (res.status === 401) {
      throw new APIError(401, 'Invalid or expired API key. Please check your API key in settings.');
    }
    
    if (res.status === 429) {
      throw new APIError(429, 'Rate limit exceeded. Too many requests. Please wait a moment.');
    }

    if (!res.ok) {
      let errorMessage = `HTTP ${res.status}: ${res.statusText}`;
      try {
        const errorData = await res.json();
        errorMessage = errorData.error || errorData.message || errorMessage;
      } catch {
        // If JSON parsing fails, use default message
      }
      throw new APIError(res.status, errorMessage);
    }

    // Handle empty responses
    const contentType = res.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return res.json();
    }
    
    return {} as T;
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }
    
    // Network errors
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new APIError(0, 'Network error. Please check your connection.');
    }
    
    throw new APIError(0, error instanceof Error ? error.message : 'Unknown error');
  }
}

export const api = {
  // Auth
  getApiKey,
  setApiKey,
  clearApiKey,
  
  // Health (no auth required)
  health: () => request<{ status: string; version: string }>('/health', { skipAuth: true }),
  
  // Config
  getConfig: () => request<Record<string, unknown>>('/config'),
  saveConfig: (config: unknown) => request('/config', { method: 'POST', body: JSON.stringify(config) }),
  getOfficialProviders: () => request<{ providers: OfficialProvider[] }>('/config/providers/official'),
  getAIConfig: () => request<AIConfigOverview>('/config/providers/ai-config'),
  
  // Providers (for backward compatibility)
  saveProvider: (data: SaveProviderRequest) => request('/providers/save', { method: 'POST', body: JSON.stringify(data) }),
  deleteProvider: (name: string) => request(`/providers/${name}`, { method: 'DELETE' }),
  setPrimaryModel: (modelId: string) => request('/providers/primary', { method: 'POST', body: JSON.stringify({ model_id: modelId }) }),
  testProvider: (data: TestProviderRequest) => request<AITestResult>('/providers/test', { method: 'POST', body: JSON.stringify(data) }),
  
  // Models
  getModels: () => request<{ models: ModelConfig[] }>('/models'),
  addModel: (data: AddModelRequest) => request('/models', { method: 'POST', body: JSON.stringify(data) }),
  deleteModel: (id: string) => request(`/models/${id}`, { method: 'DELETE' }),
  testModel: (id: string) => request<AITestResult>(`/models/${id}/test`, { method: 'POST' }),
  
  // Channels
  getChannels: () => request<{ channels: Record<string, ChannelConfig> }>('/channels'),
  getChannel: (type: string) => request<ChannelConfig>(`/channels/${type}`),
  saveChannel: (type: string, config: unknown) => request(`/channels/${type}`, { method: 'POST', body: JSON.stringify(config) }),
  testChannel: (type: string, config: unknown) => request(`/channels/${type}/test`, { method: 'POST', body: JSON.stringify(config) }),
  getTelegramAccounts: () => request<{ accounts: TelegramAccount[] }>('/channels/telegram/accounts'),
  saveTelegramAccount: (account: TelegramAccount) => request('/channels/telegram/accounts', { method: 'POST', body: JSON.stringify(account) }),
  deleteTelegramAccount: (id: string) => request(`/channels/telegram/accounts/${id}`, { method: 'DELETE' }),
  fetchTelegramUsers: (botToken: string) => request<{ users: TelegramUser[] }>(`/channels/telegram/users?bot_token=${encodeURIComponent(botToken)}`),
  
  // MCP
  getMCP: () => request<{ servers: MCPServer[] }>('/mcp'),
  addMCP: (data: AddMCPRequest) => request('/mcp', { method: 'POST', body: JSON.stringify(data) }),
  updateMCP: (name: string, data: unknown) => request(`/mcp/${name}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteMCP: (name: string) => request(`/mcp/${name}`, { method: 'DELETE' }),
  toggleMCP: (name: string, enabled: boolean) => request(`/mcp/${name}/toggle`, { method: 'POST', body: JSON.stringify({ enabled }) }),
  testMCP: (name: string) => request(`/mcp/${name}/test`, { method: 'POST' }),
  
  // Skills
  getSkills: () => request<{ skills: Skill[] }>('/skills/registry'),
  toggleSkill: (id: string, enabled: boolean) => request(`/skills/registry/${id}/${enabled ? 'enable' : 'disable'}`, { method: 'POST' }),
  installSkill: (name: string) => request('/skills/install', { method: 'POST', body: JSON.stringify({ name }) }),
  uninstallSkill: (id: string) => request(`/skills/${id}`, { method: 'DELETE' }),
  
  // Agents
  getAgents: () => request<{ agents: Agent[] }>('/agents'),
  addAgent: (data: AddAgentRequest) => request('/agents', { method: 'POST', body: JSON.stringify(data) }),
  updateAgent: (id: string, data: unknown) => request(`/agents/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteAgent: (id: string) => request(`/agents/${id}`, { method: 'DELETE' }),
  testRouting: (data: unknown) => request('/agents/routing/test', { method: 'POST', body: JSON.stringify(data) }),
  
  // System
  getSystemStatus: () => request<SystemStatus>('/system/status'),
  getUsage: () => request<UsageStats>('/system/usage'),
  getDiagnostics: () => request<DiagnosticsResult>('/system/diagnostics'),
  getNuclearStatus: () => request<NuclearStatus>('/system/nuclear'),
  startService: () => request('/system/service', { method: 'POST', body: JSON.stringify({ action: 'start' }) }),
  stopService: () => request('/system/service', { method: 'POST', body: JSON.stringify({ action: 'stop' }) }),
  restartService: () => request('/system/service', { method: 'POST', body: JSON.stringify({ action: 'restart' }) }),
  
  // Logs
  getLogs: (level?: string, limit?: number) => request<{ logs: LogEntry[] }>(`/logs${level ? `?level=${level}` : ''}${limit ? `${level ? '&' : '?'}limit=${limit}` : ''}`),
  clearLogs: () => request('/logs', { method: 'DELETE' }),
  
  // Backup
  getBackup: () => request<BackupData>('/backup'),
  restoreBackup: (data: unknown) => request('/restore', { method: 'POST', body: JSON.stringify(data) }),
  
  // Chat
  chat: (message: string, modelId?: string, history?: ChatMessage[]) => request<ChatResponse>('/chat', { 
    method: 'POST', 
    body: JSON.stringify({ message, model_id: modelId, history }) 
  }),
  webSearch: (query: string, maxResults?: number) => request<{ ok: boolean; query: string; results: Array<{ title: string; href: string; body: string }>; count: number }>('/chat/web-search', { 
    method: 'POST', 
    body: JSON.stringify({ query, max_results: maxResults }) 
  }),
  executeCode: (code: string, timeout?: number) => request<{ ok: boolean; output: string; error?: string }>('/chat/execute-code', { 
    method: 'POST', 
    body: JSON.stringify({ code, timeout }) 
  }),
};

export { APIError };

// TypeScript interfaces
export interface OfficialProvider {
  id: string;
  name: string;
  icon: string;
  default_base_url?: string;
  api_type: string;
  suggested_models: SuggestedModel[];
  requires_api_key: boolean;
  docs_url?: string;
}

export interface SuggestedModel {
  id: string;
  name: string;
  description?: string;
  context_window?: number;
  max_tokens?: number;
  recommended?: boolean;
}

export interface AIConfigOverview {
  primary_model?: string;
  configured_providers: ConfiguredProvider[];
  available_models: string[];
}

export interface ConfiguredProvider {
  name: string;
  base_url: string;
  api_key_masked?: string;
  has_api_key: boolean;
  models: ConfiguredModel[];
}

export interface ConfiguredModel {
  full_id: string;
  id: string;
  name: string;
  is_primary: boolean;
  api_type?: string;
  context_window?: number;
  max_tokens?: number;
}

export interface ModelConfig {
  id: string;
  name: string;
  provider: string;
  model_id: string;
  base_url: string;
  max_tokens: number;
  capabilities: string[];
}

export interface AddModelRequest {
  name: string;
  provider: string;
  model_id: string;
  base_url?: string;
  api_key_value?: string;
}

export interface AITestResult {
  success: boolean;
  provider: string;
  model: string;
  response?: string;
  error?: string;
  latency_ms?: number;
}

export interface SaveProviderRequest {
  provider_name: string;
  base_url: string;
  api_key?: string;
  api_type: string;
  models: { id: string; name: string; context_window?: number; max_tokens?: number }[];
}

export interface TestProviderRequest {
  provider: string;
  base_url: string;
  api_key?: string;
  model_id: string;
}

export interface TelegramUser {
  id: string;
  name: string;
  username?: string;
}

export interface ChannelConfig {
  enabled: boolean;
  config: Record<string, unknown>;
}

export interface TelegramAccount {
  id: string;
  bot_token?: string;
  dm_policy?: string;
  group_policy?: string;
  stream_mode?: string;
  groups?: Record<string, unknown>;
  exclusive_topics?: string[];
  allow_from?: string[];
  primary?: boolean;
}

export interface MCPServer {
  name: string;
  transport: string;
  command?: string;
  args?: string[];
  url?: string;
  enabled: boolean;
}

export interface AddMCPRequest {
  name: string;
  transport: string;
  command?: string;
  args?: string[];
  url?: string;
  enabled?: boolean;
  env?: Record<string, string>;
}

export interface Skill {
  id: string;
  name: string;
  description?: string;
  icon?: string;
  category?: string;
  enabled: boolean;
  installed?: boolean;
  version?: string;
  author?: string;
  tools?: string[];
}

export interface Agent {
  id: string;
  name: string;
  description?: string;
  system_prompt?: string;
  model_id?: string;
  enabled: boolean;
  workspace?: string;
  is_default?: boolean;
}

export interface AddAgentRequest {
  name: string;
  description?: string;
  system_prompt?: string;
  model_id?: string;
}

export interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
  source?: string;
}

export interface SystemStatus {
  status: string;
  version: string;
  uptime: number;
  python_version: string;
  platform: string;
  cpu_count: number;
  memory_total: number;
  memory_available: number;
  disk_total: number;
  disk_free: number;
}

export interface UsageStats {
  total_requests: number;
  total_tokens: number;
  providers: Record<string, { requests: number; tokens: number }>;
}

export interface DiagnosticsResult {
  checks: Array<{
    name: string;
    status: 'pass' | 'fail' | 'warn';
    message: string;
  }>;
  passed: number;
  failed: number;
  warnings: number;
}

export interface NuclearStatus {
  systems: Record<string, { running: boolean }>;
  uptime: number;
}

export interface BackupData {
  config: Record<string, unknown>;
  timestamp: string;
  version: string;
}

export interface ChatMessage {
  role: string;
  content: string;
}

export interface ChatResponse {
  response: string;
  model_used: string;
  tokens_used?: number;
  latency_ms?: number;
}
