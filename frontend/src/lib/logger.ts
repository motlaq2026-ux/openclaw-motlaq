type LogLevel = 'debug' | 'info' | 'warn' | 'error' | 'api' | 'action' | 'state';

interface LogEntry {
  level: LogLevel;
  message: string;
  data?: unknown;
  timestamp: Date;
}

class Logger {
  private name: string;
  private logs: LogEntry[] = [];
  private maxLogs: number = 1000;
  private listeners: Set<(entry: LogEntry) => void> = new Set();

  constructor(name: string) {
    this.name = name;
  }

  private log(level: LogLevel, message: string, data?: unknown) {
    const entry: LogEntry = {
      level,
      message: `[${this.name}] ${message}`,
      data,
      timestamp: new Date(),
    };

    this.logs.push(entry);
    if (this.logs.length > this.maxLogs) {
      this.logs.shift();
    }

    this.listeners.forEach(listener => listener(entry));

    const styles: Record<LogLevel, string> = {
      debug: 'color: gray',
      info: 'color: #22c55e',
      warn: 'color: #eab308',
      error: 'color: #ef4444',
      api: 'color: #3b82f6',
      action: 'color: #a855f7',
      state: 'color: #06b6d4',
    };

    const icons: Record<LogLevel, string> = {
      debug: '🔍',
      info: '✓',
      warn: '⚠',
      error: '✗',
      api: '→',
      action: '⚡',
      state: '📊',
    };

    console.log(
      `%c${icons[level]} ${entry.message}`,
      styles[level],
      data !== undefined ? data : ''
    );
  }

  debug(message: string, data?: unknown) {
    this.log('debug', message, data);
  }

  info(message: string, data?: unknown) {
    this.log('info', message, data);
  }

  warn(message: string, data?: unknown) {
    this.log('warn', message, data);
  }

  error(message: string, data?: unknown) {
    this.log('error', message, data);
  }

  apiCall(endpoint: string, params?: unknown) {
    this.log('api', `CALL ${endpoint}`, params);
  }

  apiResponse(endpoint: string, response?: unknown) {
    this.log('api', `RESPONSE ${endpoint}`, response);
  }

  apiError(endpoint: string, error: unknown) {
    this.log('error', `API ERROR ${endpoint}`, error);
  }

  action(message: string, data?: unknown) {
    this.log('action', message, data);
  }

  state(message: string, data?: unknown) {
    this.log('state', message, data);
  }

  getLogs(): LogEntry[] {
    return [...this.logs];
  }

  clearLogs() {
    this.logs = [];
  }

  subscribe(listener: (entry: LogEntry) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }
}

export const appLogger = new Logger('App');
export const apiLogger = new Logger('API');
export const setupLogger = new Logger('Setup');
export const testingLogger = new Logger('Testing');
export const serviceLogger = new Logger('Service');
export const dashboardLogger = new Logger('Dashboard');

export function createLogger(name: string): Logger {
  return new Logger(name);
}

export type { LogEntry, LogLevel };
