/**
 * 松哥的智能数据分析系统 — 主应用
 */
import { useState, useCallback, useEffect } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import QueryInput from './components/QueryInput';
import ThinkingDisplay from './components/ThinkingDisplay';
import SqlPreview from './components/SqlPreview';
import EChartsRenderer from './components/EChartsRenderer';
import DataTable from './components/DataTable';
import ErrorDisplay from './components/ErrorDisplay';
import Skeleton from './components/Skeleton';
import { useSSE } from './hooks/useSSE';
import type { QueryHistoryItem } from './types';

const SUGGESTIONS = ['近30天销售趋势', '各城市用户分布', '热销商品 TOP10', '订单状态统计'];

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [history, setHistory] = useState<QueryHistoryItem[]>([]);
  const [dbConnected, setDbConnected] = useState(false);

  const { state, thinking, sql, echartsOption, queryData, error, sendQuery, reset } = useSSE();

  // 启动时检查后端健康状态
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch('/health');
        if (res.ok) {
          const data = await res.json();
          setDbConnected(data.database?.startsWith('connected') ?? false);
        }
      } catch {
        setDbConnected(false);
      }
    };
    checkHealth();
    // 每 30 秒检查一次
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleSend = useCallback((question: string) => {
    sendQuery(question);

    // 添加到历史
    setHistory((prev) => [
      {
        id: Date.now().toString(),
        question,
        result: { thinking: '', sql: '', echartsOption: null, data: null, error: null },
        timestamp: new Date(),
      },
      ...prev,
    ]);
  }, [sendQuery]);

  const handleSelectHistory = useCallback((item: QueryHistoryItem) => {
    handleSend(item.question);
    setSidebarOpen(false);
  }, [handleSend]);

  const isLoading = state === 'thinking' || state === 'showSQL';
  const hasResult = thinking || sql || echartsOption || queryData || error;

  return (
    <div className="flex flex-col h-screen" style={{ backgroundColor: 'var(--color-bg-primary)' }}>
      <Header
        dbConnected={dbConnected}
        onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
        onGoHome={reset}
      />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          history={history}
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
          onSelectHistory={handleSelectHistory}
        />

        <main className="flex-1 flex flex-col overflow-hidden">
          {/* 结果展示区 */}
          <div className="flex-1 overflow-y-auto p-4 md:p-6">
            <div className="max-w-4xl mx-auto">
              {/* 欢迎页 — 无结果时显示 */}
              {!hasResult && state === 'idle' && (
                <div className="text-center py-16 md:py-24 animate-fade-in">
                  <div
                    className="inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-6"
                    style={{ backgroundColor: 'var(--color-bg-tertiary)' }}
                  >
                    <span className="text-3xl">📊</span>
                  </div>
                  <h2
                    className="text-xl md:text-2xl font-bold mb-2"
                    style={{ color: 'var(--color-text-primary)' }}
                  >
                    欢迎使用智能数据分析系统
                  </h2>
                  <p
                    className="text-sm md:text-base mb-1"
                    style={{ color: 'var(--color-text-secondary)' }}
                  >
                    用自然语言描述你的数据查询需求
                  </p>
                  <p
                    className="text-sm"
                    style={{ color: 'var(--color-text-secondary)' }}
                  >
                    系统将自动生成 SQL 并可视化结果
                  </p>
                  {!dbConnected && (
                    <p
                      className="text-xs mt-4 px-3 py-1.5 inline-block rounded"
                      style={{ backgroundColor: 'rgba(239, 68, 68, 0.15)', color: 'var(--color-error)' }}
                    >
                      数据库未连接 — 请启动 Docker PostgreSQL
                    </p>
                  )}
                </div>
              )}

              {/* 结果区 */}
              {hasResult && (
                <div className="animate-fade-in">
                  {/* 思考过程 */}
                  {(thinking || state === 'thinking') && (
                    <ThinkingDisplay
                      content={thinking}
                      isStreaming={state === 'thinking'}
                    />
                  )}

                  {/* SQL 骨架屏 or SQL 预览 */}
                  {state === 'thinking' && !sql && <Skeleton type="sql" />}
                  {sql && <SqlPreview content={sql} />}

                  {/* 数据表格 */}
                  {queryData && <DataTable data={queryData} />}

                  {/* 图表骨架屏 or ECharts */}
                  {(state === 'thinking' || state === 'showSQL') && !echartsOption && (
                    <Skeleton type="chart" />
                  )}
                  {echartsOption && <EChartsRenderer option={echartsOption} />}

                  {/* 错误提示 */}
                  {error && (
                    <ErrorDisplay
                      code={error.code}
                      message={error.message}
                      onClose={reset}
                    />
                  )}
                </div>
              )}
            </div>
          </div>

          {/* 底部输入框 */}
          <QueryInput
            onSend={handleSend}
            disabled={isLoading}
            suggestions={!hasResult ? SUGGESTIONS : []}
          />
        </main>
      </div>
    </div>
  );
}

export default App;
