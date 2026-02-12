/**
 * Skeleton — 骨架屏加载占位
 */

interface SkeletonProps {
  type: 'thinking' | 'sql' | 'chart';
}

export default function Skeleton({ type }: SkeletonProps) {
  const baseStyle = {
    backgroundColor: 'var(--color-bg-secondary)',
    border: '1px solid var(--color-border)',
  };

  if (type === 'thinking') {
    return (
      <div className="rounded-lg mb-4 p-4" style={baseStyle}>
        <div className="flex items-center gap-2 mb-3">
          <span className="text-base">💭</span>
          <div className="h-4 w-20 rounded animate-pulse" style={{ backgroundColor: 'var(--color-bg-tertiary)' }} />
        </div>
        <div className="space-y-2">
          <div className="h-3 w-full rounded animate-pulse" style={{ backgroundColor: 'var(--color-bg-tertiary)' }} />
          <div className="h-3 w-4/5 rounded animate-pulse" style={{ backgroundColor: 'var(--color-bg-tertiary)' }} />
          <div className="h-3 w-3/5 rounded animate-pulse" style={{ backgroundColor: 'var(--color-bg-tertiary)' }} />
        </div>
      </div>
    );
  }

  if (type === 'sql') {
    return (
      <div className="rounded-lg mb-4 p-4" style={baseStyle}>
        <div className="flex items-center gap-2 mb-3">
          <span className="text-base">📝</span>
          <div className="h-4 w-16 rounded animate-pulse" style={{ backgroundColor: 'var(--color-bg-tertiary)' }} />
        </div>
        <div className="rounded-lg p-4 space-y-2" style={{ backgroundColor: '#0d1117' }}>
          <div className="h-3 w-2/3 rounded animate-pulse" style={{ backgroundColor: '#161b22' }} />
          <div className="h-3 w-1/2 rounded animate-pulse" style={{ backgroundColor: '#161b22' }} />
        </div>
      </div>
    );
  }

  // chart
  return (
    <div className="rounded-lg mb-4 p-4" style={baseStyle}>
      <div className="flex items-center gap-2 mb-3">
        <span className="text-base">📊</span>
        <div className="h-4 w-24 rounded animate-pulse" style={{ backgroundColor: 'var(--color-bg-tertiary)' }} />
      </div>
      <div className="h-[300px] rounded-lg animate-pulse" style={{ backgroundColor: 'var(--color-bg-tertiary)' }} />
    </div>
  );
}
