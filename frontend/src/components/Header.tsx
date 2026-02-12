/**
 * Header — 顶部导航栏：YIWUSONG Logo + 系统名称 + DB 状态灯
 * 点击 Logo / 标题可返回首页
 */
interface HeaderProps {
  dbConnected?: boolean;
  onToggleSidebar?: () => void;
  onGoHome?: () => void;
}

export default function Header({ dbConnected = true, onToggleSidebar, onGoHome }: HeaderProps) {
  return (
    <header
      className="flex items-center justify-between px-4 md:px-6 shrink-0"
      style={{
        height: '56px',
        backgroundColor: 'var(--color-bg-secondary)',
        borderBottom: '1px solid var(--color-border)',
      }}
    >
      <div className="flex items-center gap-3">
        {/* 移动端汉堡按钮 */}
        <button
          className="lg:hidden p-1 rounded cursor-pointer"
          style={{ color: 'var(--color-text-secondary)' }}
          onClick={onToggleSidebar}
        >
          <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M3 6h18M3 12h18M3 18h18" />
          </svg>
        </button>

        {/* Logo + 标题 — 点击返回首页 */}
        <button
          className="flex items-center gap-3 cursor-pointer"
          style={{ background: 'none', border: 'none', padding: 0 }}
          onClick={onGoHome}
          title="返回首页"
        >
          <span
            className="text-xs font-bold tracking-widest px-2 py-1 rounded transition-opacity hover:opacity-80"
            style={{ backgroundColor: 'var(--color-accent)', color: '#fff' }}
          >
            YIWUSONG
          </span>
          <h1
            className="text-base md:text-lg font-semibold whitespace-nowrap transition-opacity hover:opacity-80"
            style={{ color: 'var(--color-text-primary)' }}
          >
            松哥的智能数据分析系统
          </h1>
        </button>
      </div>

      <div className="flex items-center gap-2">
        <span
          className="inline-block w-2 h-2 rounded-full transition-colors"
          style={{ backgroundColor: dbConnected ? 'var(--color-success)' : 'var(--color-error)' }}
        />
        <span className="text-xs md:text-sm" style={{ color: 'var(--color-text-secondary)' }}>
          DB: {dbConnected ? '已连接' : '未连接'}
        </span>
      </div>
    </header>
  );
}
