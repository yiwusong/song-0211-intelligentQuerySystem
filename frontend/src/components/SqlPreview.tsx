/**
 * SqlPreview — SQL 语法高亮预览 + 复制按钮
 */
import { useState, useEffect, useRef } from 'react';
import hljs from 'highlight.js/lib/core';
import sql from 'highlight.js/lib/languages/sql';
import 'highlight.js/styles/github-dark.css';

hljs.registerLanguage('sql', sql);

interface SqlPreviewProps {
  content: string;
}

export default function SqlPreview({ content }: SqlPreviewProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [copied, setCopied] = useState(false);
  const codeRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (codeRef.current && content) {
      codeRef.current.innerHTML = hljs.highlight(content, { language: 'sql' }).value;
    }
  }, [content]);

  if (!content) return null;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className="rounded-lg mb-4 overflow-hidden transition-all"
      style={{
        backgroundColor: 'var(--color-bg-secondary)',
        border: '1px solid var(--color-border)',
      }}
    >
      {/* 标题栏 */}
      <div className="flex items-center justify-between px-4 py-3">
        <button
          className="flex items-center gap-2 cursor-pointer"
          style={{ backgroundColor: 'transparent', border: 'none', color: 'var(--color-text-primary)' }}
          onClick={() => setCollapsed(!collapsed)}
        >
          <span className="text-base">📝</span>
          <span className="text-sm font-medium">SQL 查询</span>
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

        <button
          className="flex items-center gap-1 px-3 py-1 rounded text-xs cursor-pointer transition-colors"
          style={{
            backgroundColor: 'var(--color-bg-tertiary)',
            color: copied ? 'var(--color-success)' : 'var(--color-text-secondary)',
            border: 'none',
          }}
          onClick={handleCopy}
        >
          {copied ? '✓ 已复制' : '复制'}
        </button>
      </div>

      {/* 代码区 */}
      {!collapsed && (
        <div className="px-4 pb-4">
          <pre
            className="rounded-lg p-4 text-sm overflow-x-auto"
            style={{ backgroundColor: '#0d1117', margin: 0 }}
          >
            <code ref={codeRef} className="language-sql">
              {content}
            </code>
          </pre>
        </div>
      )}
    </div>
  );
}
