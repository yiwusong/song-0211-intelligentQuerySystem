/**
 * useSSE — SSE 事件流 Hook
 * Phase 4: 对接真实后端 /api/query，保留 Mock 可切换
 */
import { useState, useCallback, useRef } from 'react';
import type { UIState, ErrorData, QueryResultData } from '../types';

/** 是否使用 Mock 模式（不依赖数据库和 LLM） */
const USE_MOCK = false;

interface UseSSEReturn {
  state: UIState;
  thinking: string;
  sql: string;
  echartsOption: Record<string, unknown> | null;
  queryData: QueryResultData | null;
  error: ErrorData | null;
  sendQuery: (question: string) => void;
  reset: () => void;
}

/** 解析 SSE 流并调用回调 */
async function parseSSEStream(
  response: Response,
  callbacks: {
    onThinkingDelta: (delta: string) => void;
    onThinkingDone: (full: string) => void;
    onSQL: (text: string) => void;
    onData: (data: QueryResultData) => void;
    onVizConfig: (option: Record<string, unknown>) => void;
    onError: (err: ErrorData) => void;
    onDone: () => void;
  },
): Promise<void> {
  if (!response.body) {
    callbacks.onError({ code: 'NO_BODY', message: '响应体为空' });
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    let currentEvent = '';
    for (const line of lines) {
      if (line.startsWith('event:')) {
        currentEvent = line.slice(6).trim();
      } else if (line.startsWith('data:')) {
        const data = line.slice(5).trim();
        if (!data) continue;
        try {
          const parsed = JSON.parse(data);
          switch (currentEvent) {
            case 'thought':
              if (parsed.done) {
                callbacks.onThinkingDone(parsed.content);
              } else {
                callbacks.onThinkingDelta(parsed.content);
              }
              break;
            case 'sql':
              callbacks.onSQL(parsed.content);
              break;
            case 'data':
              callbacks.onData(parsed);
              break;
            case 'viz_config':
              // 后端直接发送 ECharts option 对象
              callbacks.onVizConfig(parsed);
              break;
            case 'error':
              callbacks.onError(parsed);
              break;
            case 'done':
              callbacks.onDone();
              break;
            // 'state' 事件可用于调试，暂不处理
          }
        } catch {
          // ignore parse errors
        }
      }
    }
  }
}

/** 检查数据库是否可用 */
async function isDbConnected(): Promise<boolean> {
  try {
    const res = await fetch('/health');
    if (!res.ok) return false;
    const data = await res.json();
    return data.database?.startsWith('connected') ?? false;
  } catch {
    return false;
  }
}

/** 真实 SSE — 对接后端，数据库不可用时自动降级到 Mock 端点 */
async function realSSE(
  question: string,
  callbacks: {
    onThinkingDelta: (delta: string) => void;
    onThinkingDone: (full: string) => void;
    onSQL: (text: string) => void;
    onData: (data: QueryResultData) => void;
    onVizConfig: (option: Record<string, unknown>) => void;
    onError: (err: ErrorData) => void;
    onDone: () => void;
  },
): Promise<void> {
  // 先检查数据库状态，决定用真实接口还是 Mock
  const dbOk = await isDbConnected();
  const endpoint = dbOk ? '/api/query' : '/api/query/mock';

  if (!dbOk) {
    console.warn('[SSE] 数据库不可用，自动降级到 /api/query/mock');
  }

  let response: Response;
  try {
    response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    });
  } catch {
    callbacks.onError({ code: 'NETWORK_ERROR', message: '网络连接失败，请检查后端是否启动' });
    return;
  }

  if (!response.ok) {
    callbacks.onError({ code: 'FETCH_FAILED', message: `请求失败: ${response.status}` });
    return;
  }

  await parseSSEStream(response, callbacks);
}

/** Mock SSE — 模拟后端流式推送（无需后端/数据库） */
async function mockSSE(
  question: string,
  callbacks: {
    onThinkingDelta: (delta: string) => void;
    onThinkingDone: (full: string) => void;
    onSQL: (text: string) => void;
    onData: (data: QueryResultData) => void;
    onVizConfig: (option: Record<string, unknown>) => void;
    onDone: () => void;
  },
): Promise<void> {
  // 模拟思考过程（逐字推送）
  const thinkingText = `用户想查询"${question}"相关的数据。需要分析涉及的表：orders（订单表）、products（商品表）、users（用户表）。根据查询意图，需要关联订单明细表 order_items 来获取商品维度的统计数据。按时间维度聚合，使用 DATE_TRUNC 函数按天/周/月分组。`;

  for (let i = 0; i < thinkingText.length; i++) {
    await new Promise((r) => setTimeout(r, 15));
    callbacks.onThinkingDelta(thinkingText[i]);
  }
  callbacks.onThinkingDone(thinkingText);

  await new Promise((r) => setTimeout(r, 300));

  // 模拟 SQL
  const sqlText = `SELECT
  DATE_TRUNC('day', o.created_at) AS date,
  COUNT(DISTINCT o.id) AS order_count,
  SUM(o.total_amount) AS total_sales,
  COUNT(DISTINCT o.user_id) AS unique_users
FROM orders o
  JOIN order_items oi ON oi.order_id = o.id
  JOIN products p ON p.id = oi.product_id
WHERE o.created_at >= NOW() - INTERVAL '30 days'
  AND o.status IN ('paid', 'shipped', 'completed')
GROUP BY DATE_TRUNC('day', o.created_at)
ORDER BY date ASC
LIMIT 1000;`;

  callbacks.onSQL(sqlText);
  await new Promise((r) => setTimeout(r, 300));

  // 模拟查询结果
  const days = Array.from({ length: 30 }, (_, i) => {
    const d = new Date();
    d.setDate(d.getDate() - 29 + i);
    return `${d.getMonth() + 1}/${d.getDate()}`;
  });
  const sales = Array.from({ length: 30 }, () => Math.floor(Math.random() * 50000 + 10000));
  const orders = Array.from({ length: 30 }, () => Math.floor(Math.random() * 200 + 50));

  callbacks.onData({
    columns: ['日期', '销售额', '订单数'],
    rows: days.map((d, i) => [d, sales[i], orders[i]]),
    row_count: 30,
    execution_time_ms: 23.5,
  });

  await new Promise((r) => setTimeout(r, 200));

  // 模拟 ECharts 配置
  callbacks.onVizConfig({
    backgroundColor: 'transparent',
    title: {
      text: '近30天销售趋势',
      subtext: `查询：${question}`,
      textStyle: { color: '#f1f5f9', fontSize: 16 },
      subtextStyle: { color: '#94a3b8' },
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
    },
    legend: {
      data: ['销售额', '订单数'],
      textStyle: { color: '#94a3b8' },
      top: 40,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: 80,
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: days,
      axisLabel: { color: '#94a3b8', rotate: 45, fontSize: 10 },
      axisLine: { lineStyle: { color: '#334155' } },
    },
    yAxis: [
      {
        type: 'value',
        name: '销售额 (元)',
        nameTextStyle: { color: '#94a3b8' },
        axisLabel: { color: '#94a3b8' },
        splitLine: { lineStyle: { color: '#1e293b' } },
      },
      {
        type: 'value',
        name: '订单数',
        nameTextStyle: { color: '#94a3b8' },
        axisLabel: { color: '#94a3b8' },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: '销售额',
        type: 'bar',
        data: sales,
        itemStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: '#6366f1' },
              { offset: 1, color: '#4f46e5' },
            ],
          },
          borderRadius: [4, 4, 0, 0],
        },
      },
      {
        name: '订单数',
        type: 'line',
        yAxisIndex: 1,
        data: orders,
        smooth: true,
        itemStyle: { color: '#22c55e' },
        lineStyle: { width: 2 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(34, 197, 94, 0.3)' },
              { offset: 1, color: 'rgba(34, 197, 94, 0)' },
            ],
          },
        },
      },
    ],
  });

  callbacks.onDone();
}

export function useSSE(): UseSSEReturn {
  const [state, setState] = useState<UIState>('idle');
  const [thinking, setThinking] = useState('');
  const [sqlContent, setSql] = useState('');
  const [echartsOption, setEchartsOption] = useState<Record<string, unknown> | null>(null);
  const [queryData, setQueryData] = useState<QueryResultData | null>(null);
  const [error, setError] = useState<ErrorData | null>(null);
  const abortRef = useRef(false);
  const thinkingRef = useRef('');

  const reset = useCallback(() => {
    setState('idle');
    setThinking('');
    setSql('');
    setEchartsOption(null);
    setQueryData(null);
    setError(null);
    abortRef.current = false;
    thinkingRef.current = '';
  }, []);

  const sendQuery = useCallback((question: string) => {
    // 重置状态
    setThinking('');
    setSql('');
    setEchartsOption(null);
    setQueryData(null);
    setError(null);
    setState('thinking');
    abortRef.current = false;
    thinkingRef.current = '';

    const callbacks = {
      onThinkingDelta: (delta: string) => {
        if (abortRef.current) return;
        thinkingRef.current += delta;
        setThinking(thinkingRef.current);
      },
      onThinkingDone: (full: string) => {
        if (abortRef.current) return;
        thinkingRef.current = full;
        setThinking(full);
      },
      onSQL: (text: string) => {
        if (abortRef.current) return;
        setSql(text);
        setState('showSQL');
      },
      onData: (data: QueryResultData) => {
        if (abortRef.current) return;
        setQueryData(data);
      },
      onVizConfig: (opt: Record<string, unknown>) => {
        if (abortRef.current) return;
        setEchartsOption(opt);
        setState('showChart');
      },
      onError: (err: ErrorData) => {
        if (abortRef.current) return;
        setError(err);
        setState('error');
      },
      onDone: () => {
        // 查询完成
      },
    };

    const run = async () => {
      try {
        if (USE_MOCK) {
          await mockSSE(question, callbacks);
        } else {
          await realSSE(question, callbacks);
        }
      } catch (e) {
        if (!abortRef.current) {
          setError({ code: 'UNKNOWN', message: String(e) });
          setState('error');
        }
      }
    };

    run();
  }, []);

  return { state, thinking, sql: sqlContent, echartsOption, queryData, error, sendQuery, reset };
}
