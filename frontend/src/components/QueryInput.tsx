/**
 * QueryInput — 底部固定输入框
 * - Enter 发送，Shift+Enter 换行
 * - 查询中禁用态
 * - 推荐问题气泡
 */
import { useState, useRef, useEffect } from 'react';

interface QueryInputProps {
  onSend: (question: string) => void;
  disabled?: boolean;
  suggestions?: string[];
}

export default function QueryInput({ onSend, disabled = false, suggestions = [] }: QueryInputProps) {
  const [value, setValue] = useState('');
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!disabled && inputRef.current) {
      inputRef.current.focus();
    }
  }, [disabled]);

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSuggestionClick = (q: string) => {
    if (disabled) return;
    onSend(q);
  };

  return (
    <div
      className="shrink-0"
      style={{
        backgroundColor: 'var(--color-bg-secondary)',
        borderTop: '1px solid var(--color-border)',
      }}
    >
      {/* 推荐问题 */}
      {suggestions.length > 0 && !disabled && value === '' && (
        <div className="px-4 pt-3 pb-0 max-w-4xl mx-auto">
          <div className="flex flex-wrap gap-2">
            {suggestions.map((q) => (
              <button
                key={q}
                className="px-3 py-1.5 rounded-full text-xs cursor-pointer transition-all hover:scale-105"
                style={{
                  border: '1px solid var(--color-border)',
                  color: 'var(--color-text-secondary)',
                  backgroundColor: 'transparent',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = 'var(--color-accent)';
                  e.currentTarget.style.color = 'var(--color-accent)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'var(--color-border)';
                  e.currentTarget.style.color = 'var(--color-text-secondary)';
                }}
                onClick={() => handleSuggestionClick(q)}
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 输入区 */}
      <div className="p-4 max-w-4xl mx-auto">
        <div className="flex gap-3 items-end">
          <textarea
            ref={inputRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={disabled ? '查询中，请稍候...' : '请输入你的数据查询问题...'}
            disabled={disabled}
            rows={1}
            className="flex-1 px-4 py-3 rounded-lg text-sm outline-none resize-none transition-all"
            style={{
              backgroundColor: disabled ? 'var(--color-bg-tertiary)' : 'var(--color-bg-primary)',
              color: 'var(--color-text-primary)',
              border: '1px solid var(--color-border)',
              opacity: disabled ? 0.6 : 1,
              maxHeight: '120px',
            }}
            onFocus={(e) => {
              if (!disabled) e.currentTarget.style.borderColor = 'var(--color-accent)';
            }}
            onBlur={(e) => {
              e.currentTarget.style.borderColor = 'var(--color-border)';
            }}
          />
          <button
            className="px-6 py-3 rounded-lg text-sm font-medium text-white cursor-pointer transition-all shrink-0"
            style={{
              backgroundColor: disabled ? '#6366f1' : 'var(--color-accent)',
              opacity: disabled ? 0.6 : 1,
            }}
            onClick={handleSend}
            disabled={disabled}
          >
            {disabled ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                查询中
              </span>
            ) : '发送'}
          </button>
        </div>
      </div>
    </div>
  );
}
