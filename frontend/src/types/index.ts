/** SSE 事件类型 */
export type SSEEventType = 'state' | 'thought' | 'sql' | 'data' | 'viz_config' | 'error' | 'done';

/** 思考事件数据 */
export interface ThoughtData {
  content: string;
  done?: boolean;
}

/** SQL 事件数据 */
export interface SqlData {
  content: string;
  raw?: string;
}

/** 查询结果数据（data 事件） */
export interface QueryResultData {
  columns: string[];
  rows: (string | number | null)[][];
  row_count: number;
  execution_time_ms: number;
}

/** 可视化配置事件数据 */
export interface VizConfigData {
  echarts_option: Record<string, unknown>;
}

/** 错误事件数据 */
export interface ErrorData {
  code: string;
  message: string;
}

/** UI 状态 */
export type UIState = 'idle' | 'thinking' | 'showSQL' | 'showChart' | 'error';

/** 查询结果 */
export interface QueryResult {
  thinking: string;
  sql: string;
  echartsOption: Record<string, unknown> | null;
  data: QueryResultData | null;
  error: ErrorData | null;
}

/** 查询历史条目 */
export interface QueryHistoryItem {
  id: string;
  question: string;
  result: QueryResult;
  timestamp: Date;
}
