/**
 * ErrorDisplay — 错误提示条
 */
interface ErrorDisplayProps {
  code?: string;
  message: string;
  onClose?: () => void;
}

export default function ErrorDisplay({ code, message, onClose }: ErrorDisplayProps) {
  if (!message) return null;

  return (
    <div
      className="rounded-lg mb-4 px-4 py-3 flex items-start gap-3 animate-fade-in"
      style={{
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        border: '1px solid var(--color-error)',
      }}
    >
      <span className="text-base shrink-0 mt-0.5">⚠️</span>
      <div className="flex-1 min-w-0">
        {code && (
          <p className="text-xs font-mono mb-1" style={{ color: 'var(--color-error)' }}>
            {code}
          </p>
        )}
        <p className="text-sm" style={{ color: 'var(--color-text-primary)' }}>
          {message}
        </p>
      </div>
      {onClose && (
        <button
          className="shrink-0 p-1 rounded cursor-pointer"
          style={{ backgroundColor: 'transparent', border: 'none', color: 'var(--color-text-secondary)' }}
          onClick={onClose}
        >
          <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M3 3l8 8M11 3l-8 8" />
          </svg>
        </button>
      )}
    </div>
  );
}
