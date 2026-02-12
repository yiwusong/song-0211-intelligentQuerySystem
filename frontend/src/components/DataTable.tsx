/**
 * DataTable — 查询结果数据表格
 */
import { useState } from 'react';
import type { QueryResultData } from '../types';

interface DataTableProps {
  data: QueryResultData;
}

export default function DataTable({ data }: DataTableProps) {
  const [collapsed, setCollapsed] = useState(false);
  const maxDisplay = 100;
  const displayRows = data.rows.slice(0, maxDisplay);

  return (
    <div
      className="rounded-lg mb-4 overflow-hidden animate-fade-in"
      style={{
        backgroundColor: 'var(--color-bg-secondary)',
        border: '1px solid var(--color-border)',
      }}
    >
      {/* 标题栏 */}
      <button
        className="w-full flex items-center justify-between px-4 py-3 cursor-pointer"
        style={{ backgroundColor: 'transparent', border: 'none', color: 'var(--color-text-primary)' }}
        onClick={() => setCollapsed(!collapsed)}
      >
        <div className="flex items-center gap-2">
          <span className="text-base">📋</span>
          <span className="text-sm font-medium">查询结果</span>
          <span
            className="text-xs px-2 py-0.5 rounded-full"
            style={{ backgroundColor: 'var(--color-bg-tertiary)', color: 'var(--color-text-secondary)' }}
          >
            {data.row_count} 行 / {data.execution_time_ms}ms
          </span>
        </div>
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

      {/* 表格内容 */}
      {!collapsed && (
        <div className="overflow-x-auto px-4 pb-4">
          <table className="w-full text-sm">
            <thead>
              <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                {data.columns.map((col, i) => (
                  <th
                    key={i}
                    className="px-3 py-2 text-left font-medium whitespace-nowrap"
                    style={{ color: 'var(--color-text-primary)' }}
                  >
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {displayRows.map((row, rowIdx) => (
                <tr
                  key={rowIdx}
                  style={{
                    borderBottom: '1px solid var(--color-border)',
                    backgroundColor: rowIdx % 2 === 0 ? 'transparent' : 'var(--color-bg-tertiary)',
                  }}
                >
                  {row.map((cell, cellIdx) => (
                    <td
                      key={cellIdx}
                      className="px-3 py-2 whitespace-nowrap"
                      style={{ color: 'var(--color-text-secondary)' }}
                    >
                      {cell === null ? (
                        <span style={{ color: 'var(--color-text-tertiary)', fontStyle: 'italic' }}>NULL</span>
                      ) : (
                        String(cell)
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          {data.row_count > maxDisplay && (
            <p className="text-xs mt-2 text-center" style={{ color: 'var(--color-text-tertiary)' }}>
              仅展示前 {maxDisplay} 行（共 {data.row_count} 行）
            </p>
          )}
        </div>
      )}
    </div>
  );
}
