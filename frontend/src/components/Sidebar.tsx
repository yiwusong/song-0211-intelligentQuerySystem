/**
 * Sidebar — 左侧查询历史栏（可折叠）
 */
import type { QueryHistoryItem } from '../types';

interface SidebarProps {
  history: QueryHistoryItem[];
  isOpen: boolean;
  onClose: () => void;
  onSelectHistory?: (item: QueryHistoryItem) => void;
}

export default function Sidebar({ history, isOpen, onClose, onSelectHistory }: SidebarProps) {
  const formatDate = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / 86400000);
    if (days === 0) return '今天';
    if (days === 1) return '昨天';
    if (days < 7) return `${days}天前`;
    return date.toLocaleDateString('zh-CN');
  };

  // 按日期分组
  const grouped = history.reduce<Record<string, QueryHistoryItem[]>>((acc, item) => {
    const key = formatDate(item.timestamp);
    if (!acc[key]) acc[key] = [];
    acc[key].push(item);
    return acc;
  }, {});

  return (
    <>
      {/* 移动端遮罩 */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-20 lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`
          fixed lg:relative z-30 lg:z-0
          w-[280px] h-full
          overflow-y-auto
          transition-transform duration-300 ease-in-out
          lg:translate-x-0
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
        style={{
          backgroundColor: 'var(--color-bg-secondary)',
          borderRight: '1px solid var(--color-border)',
        }}
      >
        <div className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h2
              className="text-xs font-semibold uppercase tracking-wider"
              style={{ color: 'var(--color-text-secondary)' }}
            >
              查询历史
            </h2>
            <button
              className="lg:hidden p-1 rounded cursor-pointer"
              style={{ color: 'var(--color-text-secondary)' }}
              onClick={onClose}
            >
              <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M4 4l8 8M12 4l-8 8" />
              </svg>
            </button>
          </div>

          {history.length === 0 ? (
            <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
              暂无历史记录
            </p>
          ) : (
            Object.entries(grouped).map(([date, items]) => (
              <div key={date} className="mb-4">
                <p
                  className="text-xs font-medium mb-2"
                  style={{ color: 'var(--color-text-secondary)' }}
                >
                  {date}
                </p>
                {items.map((item) => (
                  <button
                    key={item.id}
                    className="w-full text-left px-3 py-2 rounded-lg mb-1 text-sm truncate cursor-pointer transition-colors"
                    style={{
                      color: 'var(--color-text-primary)',
                      backgroundColor: 'transparent',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = 'var(--color-bg-tertiary)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'transparent';
                    }}
                    onClick={() => onSelectHistory?.(item)}
                    title={item.question}
                  >
                    {item.question}
                  </button>
                ))}
              </div>
            ))
          )}
        </div>
      </aside>
    </>
  );
}
