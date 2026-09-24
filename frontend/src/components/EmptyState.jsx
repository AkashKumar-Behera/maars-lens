import React from 'react';
import { FolderSearch } from 'lucide-react';

const EmptyState = ({
  title = 'No records found',
  message,
  description,
  icon: Icon = FolderSearch,
  action,
}) => {
  const displayMsg = message || description || 'There is nothing to display here right now.';

  return (
    <div className="flex flex-col items-center justify-center p-12 text-center bg-[#080d1a]/80 border border-dashed border-slate-800 rounded-2xl shadow-inner backdrop-blur">
      <div className="w-16 h-16 bg-indigo-500/10 border border-indigo-500/20 rounded-2xl flex items-center justify-center mb-4 shadow-lg shadow-indigo-500/5">
        <Icon size={28} className="text-indigo-400" />
      </div>
      <h3 className="text-base font-bold text-white tracking-tight">{title}</h3>
      <p className="mt-1.5 text-xs text-slate-400 max-w-md leading-relaxed">{displayMsg}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
};

export default EmptyState;
