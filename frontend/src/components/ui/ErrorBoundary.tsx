import { Component, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen flex items-center justify-center bg-dark-950 p-4">
          <div className="bg-dark-800 border border-dark-600 rounded-2xl p-8 max-w-md text-center">
            <div className="text-5xl mb-4">😵</div>
            <h2 className="text-xl font-bold text-white mb-2">Something went wrong</h2>
            <p className="text-gray-400 mb-4 text-sm">
              {this.state.error?.message || 'An unexpected error occurred'}
            </p>
            <button
              onClick={() => {
                this.setState({ hasError: false, error: undefined });
                window.location.reload();
              }}
              className="btn-primary"
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export function ErrorMessage({ 
  message, 
  onRetry 
}: { 
  message: string; 
  onRetry?: () => void;
}) {
  return (
    <div className="bg-red-500/10 border border-red-500/30 rounded-2xl p-6 text-center">
      <div className="text-4xl mb-3">⚠️</div>
      <p className="text-red-400 mb-4">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="btn-secondary text-sm">
          Try Again
        </button>
      )}
    </div>
  );
}

export function EmptyState({ 
  icon, 
  title, 
  description, 
  action 
}: { 
  icon?: string;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="bg-dark-800 border border-dark-600 rounded-2xl p-12 text-center">
      {icon && <div className="text-5xl mb-4">{icon}</div>}
      <h3 className="text-lg font-medium text-white mb-2">{title}</h3>
      {description && <p className="text-gray-400 text-sm mb-4">{description}</p>}
      {action}
    </div>
  );
}
