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
