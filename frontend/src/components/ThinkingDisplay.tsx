/**
 * ThinkingDisplay — 思考过程打字机效果展示
 */
import { useState } from 'react';

interface ThinkingDisplayProps {
  content: string;
  isStreaming?: boolean;
}

export default function ThinkingDisplay({ content, isStreaming = false }: ThinkingDisplayProps) {
  const [collapsed, setCollapsed] = useState(false);

  if (!content) return null;

  return (
    <div
      className="rounded-lg mb-4 overflow-hidden transition-all"
      style={{
        backgroundColor: 'var(--color-bg-secondary)',
        border: '1px solid var(--color-border)',
      }}
    >
      {/* 标题栏 */}
      <button
        className="w-full flex items-center justify-between px-4 py-3 cursor-pointer"
        style={{ backgroundColor: 'transparent', border: 'none', color: 'var(--color-text-primary)' }}
        onClick={() => setCollapsed(!collapsed)}
      >
        <div className="flex items-center gap-2">
          <span className="text-base">💭</span>
          <span className="text-sm font-medium">思考过程</span>
          {isStreaming && (
            <span className="flex gap-1 ml-2">
              <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ backgroundColor: 'var(--color-accent)', animationDelay: '0ms' }} />
              <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ backgroundColor: 'var(--color-accent)', animationDelay: '150ms' }} />
              <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ backgroundColor: 'var(--color-accent)', animationDelay: '300ms' }} />
            </span>
          )}
        </div>
        <svg
          className={`w-4 h-4 transition-transform ${collapsed ? '' : 'rotate-180'}`}
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          viewBox="0 0 24 24"
        >
          <path d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* 内容区 */}
      {!collapsed && (
        <div
          className="px-4 pb-4 text-sm leading-relaxed"
          style={{ color: 'var(--color-text-secondary)' }}
        >
          {content}
          {isStreaming && <span className="inline-block w-0.5 h-4 ml-0.5 animate-pulse" style={{ backgroundColor: 'var(--color-accent)' }} />}
        </div>
      )}
    </div>
  );
}
