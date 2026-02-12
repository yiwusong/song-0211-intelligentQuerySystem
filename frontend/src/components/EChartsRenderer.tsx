/**
 * EChartsRenderer — 通用声明式 ECharts 图表组件
 * 纯透传 option，不写任何绘图逻辑
 */
import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

interface EChartsRendererProps {
  option: Record<string, unknown> | null;
}

export default function EChartsRenderer({ option }: EChartsRendererProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);

  // 初始化 & 销毁
  useEffect(() => {
    if (!containerRef.current) return;

    chartRef.current = echarts.init(containerRef.current, 'dark');

    const observer = new ResizeObserver(() => {
      chartRef.current?.resize();
    });
    observer.observe(containerRef.current);

    return () => {
      observer.disconnect();
      chartRef.current?.dispose();
    };
  }, []);

  // 更新 option
  useEffect(() => {
    if (chartRef.current && option) {
      chartRef.current.setOption(option, true);
    }
  }, [option]);

  if (!option) return null;

  return (
    <div
      className="rounded-lg mb-4 overflow-hidden animate-fade-in"
      style={{
        backgroundColor: 'var(--color-bg-secondary)',
        border: '1px solid var(--color-border)',
      }}
    >
      <div className="flex items-center gap-2 px-4 py-3">
        <span className="text-base">📊</span>
        <span
          className="text-sm font-medium"
          style={{ color: 'var(--color-text-primary)' }}
        >
          数据可视化
        </span>
      </div>
      <div
        ref={containerRef}
        className="w-full px-4 pb-4"
        style={{ height: '400px' }}
      />
    </div>
  );
}
