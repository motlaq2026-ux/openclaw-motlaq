from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class ModelConfig(BaseModel):
    id: str
    name: str
    provider: str
    model_id: str
    api_key_source: Literal["env", "direct"] = "env"
    api_key_env: Optional[str] = None
    api_key_value: Optional[str] = None
    base_url: str
    max_tokens: int = 4096
    temperature: float = 0.7
    capabilities: List[str] = ["text"]
    priority: int = 1


class SkillConfig(BaseModel):
    enabled: bool = True
    max_results: Optional[int] = None
    timeout: Optional[int] = None


class TelegramConfig(BaseModel):
    allowed_users: List[str] = []
    allowed_groups: List[str] = []
    require_mention_in_groups: bool = True


class LimitsConfig(BaseModel):
    max_threads: int = 100
    max_messages_per_thread: int = 50
    usage_history_days: int = 30
    max_log_size_mb: int = 10


class BackupConfig(BaseModel):
    enabled: bool = True
    interval_hours: int = 24


class AppConfig(BaseModel):
    version: str = "2.0.0"
    active_model_id: Optional[str] = None
    models: List[ModelConfig] = []
    system_prompt: str = "أنت مساعد ذكي."
    skills: Dict[str, SkillConfig] = {}
    telegram_enabled: bool = True
    telegram_config: TelegramConfig = TelegramConfig()
    limits: LimitsConfig = LimitsConfig()
    backup: BackupConfig = BackupConfig()
    metadata: Dict[str, Any] = {}


class Message(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None


class Thread(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    messages: List[Message] = []


class ChatRequest(BaseModel):
    message: str
    model_id: Optional[str] = None
    thread_id: Optional[str] = None


class MultimodalRequest(BaseModel):
    text: str
    image_data: Optional[str] = None
    model_id: Optional[str] = None


class CompareRequest(BaseModel):
    prompt: str
    model_ids: List[str]


class AddModelRequest(BaseModel):
    name: str
    provider: str
    model_id: str
    api_key_source: Literal["env", "direct"] = "env"
    api_key_env: Optional[str] = None
    api_key_value: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    capabilities: List[str] = ["text"]


class UpdateModelRequest(BaseModel):
    name: Optional[str] = None
    model_id: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    api_key_value: Optional[str] = None
    capabilities: Optional[List[str]] = None


class SkillToggleRequest(BaseModel):
    enabled: bool


class ProviderInfo(BaseModel):
    id: str
    name: str
    icon: str
    base_url: str
    free: Optional[bool] = None
    models: List[str] = []


class UsageStats(BaseModel):
    total_requests: int = 0
    total_tokens: int = 0
    daily: Dict[str, Dict[str, int]] = {}
    models: Dict[str, Dict[str, int]] = {}
    active_model: Optional[str] = None
    enabled_skills: List[str] = []


class HealthStatus(BaseModel):
    status: str
    version: str
    active_model: Optional[str] = None
    telegram_enabled: bool = True
    uptime_seconds: float = 0


class BackupData(BaseModel):
    config: Dict[str, Any]
    usage: Dict[str, Any]
    threads: Dict[str, Any]
    exported_at: str
    version: str = "2.0.0"


class AddMCPRequest(BaseModel):
    name: str
    transport: Literal["stdio", "sse"] = "stdio"
    command: Optional[str] = None
    args: Optional[List[str]] = None
    url: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    enabled: bool = True


class UpdateMCPRequest(BaseModel):
    command: Optional[str] = None
    args: Optional[List[str]] = None
    url: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    enabled: Optional[bool] = None


class AddAgentRequest(BaseModel):
    id: Optional[str] = None
    name: str
    description: str = ""
    system_prompt: str = ""
    model_id: Optional[str] = None
    workspace: str = ""
    is_default: bool = False
    allow_subagents: Optional[List[str]] = None
    channels: Optional[List[str]] = None
    max_depth: int = 3
    enabled: bool = True


class UpdateAgentRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model_id: Optional[str] = None
    workspace: Optional[str] = None
    is_default: Optional[bool] = None
    allow_subagents: Optional[List[str]] = None
    channels: Optional[List[str]] = None
    max_depth: Optional[int] = None
    enabled: Optional[bool] = None


class AddTaskRequest(BaseModel):
    id: Optional[str] = None
    name: str
    task_type: Literal["message", "prompt", "webhook", "script"] = "prompt"
    schedule: str = "0 9 * * *"
    config: Optional[Dict[str, Any]] = None
    enabled: bool = True


class UpdateTaskRequest(BaseModel):
    name: Optional[str] = None
    task_type: Optional[str] = None
    schedule: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None


class AddSkillRequest(BaseModel):
    id: str
    name: str
    description: str = ""
    icon: str = "🔧"
    category: str = "general"
    version: str = "1.0.0"
    author: str = "Unknown"
    source: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    enabled: bool = True


class PromptUpdateRequest(BaseModel):
    prompt: str


class TestAIRequest(BaseModel):
    message: str = "مرحبا"
    model_id: Optional[str] = None


class LogsQueryParams(BaseModel):
    level: Optional[str] = None
    source: Optional[str] = None
    limit: int = 100


class ThreadSearchQuery(BaseModel):
    q: str


# ============ AI Provider Models ============


class SuggestedModel(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    context_window: Optional[int] = None
    max_tokens: Optional[int] = None
    recommended: bool = False


class OfficialProvider(BaseModel):
    id: str
    name: str
    icon: str
    default_base_url: Optional[str] = None
    api_type: str = "openai-completions"
    suggested_models: List[SuggestedModel] = []
    requires_api_key: bool = True
    docs_url: Optional[str] = None


class ProviderModelConfig(BaseModel):
    id: str
    name: str
    api: Optional[str] = None
    input: List[str] = ["text"]
    context_window: Optional[int] = None
    max_tokens: Optional[int] = None
    reasoning: Optional[bool] = None
    cost: Optional[Dict[str, float]] = None


class ConfiguredModel(BaseModel):
    full_id: str
    id: str
    name: str
    api_type: Optional[str] = None
    context_window: Optional[int] = None
    max_tokens: Optional[int] = None
    is_primary: bool = False


class ConfiguredProvider(BaseModel):
    name: str
    base_url: str
    api_key_masked: Optional[str] = None
    has_api_key: bool = False
    models: List[ConfiguredModel] = []


class AIConfigOverview(BaseModel):
    primary_model: Optional[str] = None
    configured_providers: List[ConfiguredProvider] = []
    available_models: List[str] = []


class SaveProviderRequest(BaseModel):
    provider_name: str
    base_url: str
    api_key: Optional[str] = None
    api_type: str = "openai-completions"
    models: List[ProviderModelConfig] = []


class AITestResult(BaseModel):
    success: bool
    provider: str
    model: str
    response: Optional[str] = None
    error: Optional[str] = None
    latency_ms: Optional[int] = None


# ============ Channel Models ============


class TelegramAccount(BaseModel):
    id: str
    bot_token: Optional[str] = None
    dm_policy: Optional[str] = None
    group_policy: Optional[str] = None
    stream_mode: Optional[str] = None
    groups: Optional[Dict[str, Any]] = None
    exclusive_topics: Optional[List[str]] = None
    allow_from: Optional[List[str]] = None
    primary: Optional[bool] = None


class ChannelConfig(BaseModel):
    id: str
    channel_type: str
    enabled: bool = False
    config: Dict[str, Any] = {}


class ChannelField(BaseModel):
    key: str
    label: str
    type: str = "text"
    placeholder: Optional[str] = None
    options: Optional[List[Dict[str, str]]] = None
    required: bool = False


class ChannelInfo(BaseModel):
    name: str
    icon: str
    color: str
    fields: List[ChannelField] = []
    help_text: Optional[str] = None


# ============ Agent Routing Models ============


class MatchRule(BaseModel):
    channel: Optional[str] = None
    account_id: Optional[str] = None
    peer: Optional[Any] = None


class AgentBinding(BaseModel):
    agent_id: str
    match_rule: MatchRule


class SubagentConfig(BaseModel):
    allow_agents: Optional[List[str]] = None


class SubagentDefaults(BaseModel):
    max_spawn_depth: Optional[int] = None
    max_children_per_agent: Optional[int] = None
    max_concurrent: Optional[int] = None


class AgentInfo(BaseModel):
    id: str
    name: Optional[str] = None
    workspace: Optional[str] = None
    agent_dir: Optional[str] = None
    model: Optional[str] = None
    sandbox: Optional[bool] = None
    heartbeat: Optional[str] = None
    default: Optional[bool] = None
    subagents: Optional[SubagentConfig] = None


class AgentsConfigResponse(BaseModel):
    agents: List[AgentInfo] = []
    bindings: List[AgentBinding] = []
    subagent_defaults: SubagentDefaults = SubagentDefaults()


class RoutingTestResult(BaseModel):
    matched: bool
    agent_id: str
    agent_dir: Optional[str] = None
    model: Optional[str] = None
    system_prompt_preview: Optional[str] = None
    message: Optional[str] = None


# ============ Environment Models ============


class EnvConfig(BaseModel):
    key: str
    value: str


# ============ MCP Models ============


class MCPInstallRequest(BaseModel):
    url: str
    mode: Literal["plugin", "source"] = "source"


class MCPConfigDetail(BaseModel):
    command: str = ""
    args: List[str] = []
    env: Dict[str, str] = {}
    url: str = ""
    enabled: bool = True


# ============ Skill Models ============


class SkillMarketplaceItem(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    icon: str = "🔧"
    category: str = "general"
    version: str = "1.0.0"
    author: str = "Unknown"
    installed: bool = False
