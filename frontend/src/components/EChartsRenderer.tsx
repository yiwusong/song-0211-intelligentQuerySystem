/**
 * EChartsRenderer — 通用声明式 ECharts 图表组件
 * 支持三种图表类型切换：柱形图 (bar) / 饼状图 (pie) / 曲线图 (line)
 * AI 推荐默认类型，用户可自由切换
 */
import { useEffect, useRef, useMemo } from 'react';
import * as echarts from 'echarts';
import type { ChartType, QueryResultData } from '../types';

/** 三种图表类型的配置 */
const CHART_TYPE_CONFIG: Record<ChartType, { label: string; icon: string }> = {
  bar: { label: '柱形图', icon: '📊' },
  line: { label: '曲线图', icon: '📈' },
  pie: { label: '饼状图', icon: '🥧' },
};

/** 主题色板 */
const COLORS = ['#6366f1', '#22c55e', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#14b8a6', '#f97316'];

interface EChartsRendererProps {
  /** AI 推荐的默认 ECharts option */
  option: Record<string, unknown> | null;
  /** 原始查询数据（用于切换图表类型时重新构建 option） */
  queryData: QueryResultData | null;
  /** AI 推荐的默认图表类型 */
  chartType: ChartType;
  /** 用户当前选择的图表类型 */
  activeChartType: ChartType;
  /** 图表类型切换回调 */
  onChartTypeChange: (type: ChartType) => void;
}

/**
 * 从原始数据构建柱形图 option
 */
function buildBarOption(data: QueryResultData): Record<string, unknown> {
  const categories = data.rows.map((row) => String(row[0]));
  const valueColumns = data.columns.slice(1);

  return {
    backgroundColor: 'transparent',
    title: { text: '', textStyle: { color: '#f1f5f9' } },
    tooltip: { trigger: 'axis' },
    legend: valueColumns.length > 1 ? { data: valueColumns, textStyle: { color: '#94a3b8' }, top: 30 } : undefined,
    grid: { left: '3%', right: '4%', bottom: '3%', top: valueColumns.length > 1 ? 70 : 40, containLabel: true },
    xAxis: {
      type: 'category',
      data: categories,
      axisLabel: { color: '#94a3b8', rotate: categories.length > 10 ? 45 : 0, fontSize: 10 },
      axisLine: { lineStyle: { color: '#334155' } },
    },
    yAxis: { type: 'value', axisLabel: { color: '#94a3b8' }, splitLine: { lineStyle: { color: '#1e293b' } } },
    series: valueColumns.map((col, i) => ({
      name: col,
      type: 'bar',
      data: data.rows.map((row) => row[i + 1]),
      itemStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: COLORS[i % COLORS.length] },
            { offset: 1, color: COLORS[i % COLORS.length] + 'cc' },
          ],
        },
        borderRadius: [4, 4, 0, 0],
      },
    })),
  };
}

/**
 * 从原始数据构建曲线图 option
 */
function buildLineOption(data: QueryResultData): Record<string, unknown> {
  const categories = data.rows.map((row) => String(row[0]));
  const valueColumns = data.columns.slice(1);

  return {
    backgroundColor: 'transparent',
    title: { text: '', textStyle: { color: '#f1f5f9' } },
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    legend: valueColumns.length > 1 ? { data: valueColumns, textStyle: { color: '#94a3b8' }, top: 30 } : undefined,
    grid: { left: '3%', right: '4%', bottom: '3%', top: valueColumns.length > 1 ? 70 : 40, containLabel: true },
    xAxis: {
      type: 'category',
      data: categories,
      axisLabel: { color: '#94a3b8', rotate: categories.length > 10 ? 45 : 0, fontSize: 10 },
      axisLine: { lineStyle: { color: '#334155' } },
    },
    yAxis: { type: 'value', axisLabel: { color: '#94a3b8' }, splitLine: { lineStyle: { color: '#1e293b' } } },
    series: valueColumns.map((col, i) => ({
      name: col,
      type: 'line',
      data: data.rows.map((row) => row[i + 1]),
      smooth: true,
      itemStyle: { color: COLORS[i % COLORS.length] },
      lineStyle: { width: 2 },
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: COLORS[i % COLORS.length] + '4d' },
            { offset: 1, color: COLORS[i % COLORS.length] + '00' },
          ],
        },
      },
    })),
  };
}

/**
 * 从原始数据构建饼状图 option
 */
function buildPieOption(data: QueryResultData): Record<string, unknown> {
  // 饼图：第一列为 name，第二列为 value
  const pieData = data.rows.map((row, i) => ({
    name: String(row[0]),
    value: row[1],
    itemStyle: { color: COLORS[i % COLORS.length] },
  }));

  return {
    backgroundColor: 'transparent',
    title: { text: '', textStyle: { color: '#f1f5f9' } },
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: {
      orient: 'vertical',
      right: '5%',
      top: 'center',
      textStyle: { color: '#94a3b8' },
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['40%', '50%'],
        data: pieData,
        label: { color: '#94a3b8' },
        emphasis: {
          itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' },
        },
      },
    ],
  };
}

/** 根据图表类型和原始数据构建 ECharts option */
function buildOptionFromData(type: ChartType, data: QueryResultData, title?: string): Record<string, unknown> {
  let option: Record<string, unknown>;
  switch (type) {
    case 'bar':
      option = buildBarOption(data);
      break;
    case 'line':
      option = buildLineOption(data);
      break;
    case 'pie':
      option = buildPieOption(data);
      break;
  }
  // 继承标题
  if (title) {
    option.title = { text: title, textStyle: { color: '#f1f5f9' } };
  }
  return option;
}

export default function EChartsRenderer({
  option,
  queryData,
  chartType,
  activeChartType,
  onChartTypeChange,
}: EChartsRendererProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);

  // 根据用户选择的图表类型计算最终 option
  const finalOption = useMemo(() => {
    // 如果用户选择的类型和 AI 推荐的一样，直接用原始 option
    if (activeChartType === chartType && option) {
      return option;
    }
    // 否则根据原始数据重建 option
    if (queryData) {
      const title = option?.title && typeof option.title === 'object' && 'text' in (option.title as Record<string, unknown>)
        ? String((option.title as Record<string, unknown>).text)
        : undefined;
      return buildOptionFromData(activeChartType, queryData, title);
    }
    return option;
  }, [activeChartType, chartType, option, queryData]);

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
    if (chartRef.current && finalOption) {
      // 切换图表类型时需要 clear 再 setOption，否则 echarts 可能残留旧类型配置
      chartRef.current.clear();
      chartRef.current.setOption(finalOption, true);
    }
  }, [finalOption]);

  if (!finalOption) return null;

  return (
    <div
      className="rounded-lg mb-4 overflow-hidden animate-fade-in"
      style={{
        backgroundColor: 'var(--color-bg-secondary)',
        border: '1px solid var(--color-border)',
      }}
    >
      {/* 标题栏 + 图表类型切换按钮 */}
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="text-base">{CHART_TYPE_CONFIG[activeChartType].icon}</span>
          <span
            className="text-sm font-medium"
            style={{ color: 'var(--color-text-primary)' }}
          >
            数据可视化
          </span>
        </div>

        {/* 图表类型切换按钮组 */}
        <div className="flex items-center gap-1 p-1 rounded-lg" style={{ backgroundColor: 'var(--color-bg-tertiary)' }}>
          {(Object.keys(CHART_TYPE_CONFIG) as ChartType[]).map((type) => {
            const isActive = type === activeChartType;
            const isRecommended = type === chartType;
            return (
              <button
                key={type}
                onClick={() => onChartTypeChange(type)}
                className="flex items-center gap-1 px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-200"
                style={{
                  backgroundColor: isActive ? 'var(--color-accent)' : 'transparent',
                  color: isActive ? '#ffffff' : 'var(--color-text-secondary)',
                  cursor: 'pointer',
                  border: 'none',
                  position: 'relative',
                }}
                title={isRecommended ? `${CHART_TYPE_CONFIG[type].label}（AI 推荐）` : CHART_TYPE_CONFIG[type].label}
              >
                <span>{CHART_TYPE_CONFIG[type].icon}</span>
                <span>{CHART_TYPE_CONFIG[type].label}</span>
                {isRecommended && !isActive && (
                  <span
                    className="absolute -top-1 -right-1 w-1.5 h-1.5 rounded-full"
                    style={{ backgroundColor: '#22c55e' }}
                  />
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* 图表区域 */}
      <div
        ref={containerRef}
        className="w-full px-4 pb-4"
        style={{ height: '400px' }}
      />
    </div>
  );
}
