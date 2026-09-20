const StatusBadge = ({ status }) => {
  const normalized = (status || '').toLowerCase();

  const styles = {
    compliant: 'bg-emerald-950/80 text-emerald-300 border-emerald-700',
    pass: 'bg-emerald-950/80 text-emerald-300 border-emerald-700',
    non_compliant: 'bg-rose-950/80 text-rose-300 border-rose-700',
    fail: 'bg-rose-950/80 text-rose-300 border-rose-700',
    needs_review: 'bg-amber-950/80 text-amber-300 border-amber-700',
    under_review: 'bg-amber-950/80 text-amber-300 border-amber-700',
    open: 'bg-rose-950/80 text-rose-300 border-rose-700',
    resolved: 'bg-emerald-950/80 text-emerald-300 border-emerald-700',
    dismissed: 'bg-slate-800 text-slate-400 border-slate-700',
    appealed: 'bg-indigo-950/80 text-indigo-300 border-indigo-700',
    pending_quality_check: 'bg-slate-800 text-slate-300 border-slate-700',
    completed: 'bg-blue-950/80 text-blue-300 border-blue-700',
    demo: 'bg-purple-950/80 text-purple-300 border-purple-700',
    verified: 'bg-emerald-950/80 text-emerald-300 border-emerald-700',
    active: 'bg-emerald-950/80 text-emerald-300 border-emerald-700',
    inactive: 'bg-slate-800 text-slate-400 border-slate-700',
  };

  const labels = {
    compliant: 'Compliant',
    pass: 'Passed',
    non_compliant: 'Non-Compliant',
    fail: 'Failed',
    needs_review: 'Needs Review',
    under_review: 'Under Review',
    open: 'Open Violation',
    resolved: 'Resolved',
    dismissed: 'Dismissed',
    appealed: 'Appealed',
    pending_quality_check: 'Pending Quality Check',
    completed: 'Completed',
    demo: 'DEMO RULE',
    verified: 'OFFICIAL STATUTORY',
    active: 'Active',
    inactive: 'Inactive',
  };

  const currentStyle = styles[normalized] || 'bg-slate-800 text-slate-300 border-slate-700';
  const currentLabel = labels[normalized] || status;

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${currentStyle}`}
    >
      {currentLabel}
    </span>
  );
};

export default StatusBadge;
