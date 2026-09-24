import React from 'react';

const DataTable = ({ columns, data, onRowClick }) => {
  if (!data || data.length === 0) {
    return (
      <div className="p-6 text-center text-slate-400 bg-slate-900/80 rounded-2xl border border-slate-800 text-xs">
        No data available
      </div>
    );
  }

  return (
    <div className="overflow-x-auto bg-slate-900/90 rounded-2xl border border-slate-800 shadow-xl">
      <table className="min-w-full divide-y divide-slate-800">
        <thead className="bg-slate-950">
          <tr>
            {columns.map((col, idx) => (
              <th
                key={idx}
                className="px-6 py-3.5 text-left text-[11px] font-bold text-slate-400 uppercase tracking-wider"
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/80">
          {data.map((row, rowIndex) => (
            <tr
              key={rowIndex}
              onClick={() => onRowClick && onRowClick(row)}
              className={onRowClick ? 'cursor-pointer hover:bg-slate-800/50 transition-colors' : 'hover:bg-slate-800/30 transition'}
            >
              {columns.map((col, colIndex) => (
                <td key={colIndex} className="px-6 py-4 whitespace-nowrap text-xs text-slate-200">
                  {col.cell ? col.cell(row) : row[col.accessor]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default DataTable;
