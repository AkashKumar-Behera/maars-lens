import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Store, ShieldCheck, AlertTriangle, BookOpen, ExternalLink, RefreshCw } from 'lucide-react';
import { listRulesApi } from '../../api/rules';
import { listScansApi } from '../../api/scans';
import StatusBadge from '../../components/StatusBadge';

export default function RetailerDashboard() {
  const [rules, setRules] = useState([]);
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(false);
        const [rulesData, scansData] = await Promise.all([
          listRulesApi().catch(() => []),
          listScansApi().catch(() => [])
        ]);
        setRules(rulesData);
        setScans(scansData);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Store className="h-6 w-6 text-brand-blue" />
            Merchant Compliance Portal
          </h1>
          <p className="text-sm text-brand-muted">
            Self-assessment benchmarks, mandatory labeling requirements, and store audit logs.
          </p>
        </div>
        <Link
          to="/retailer/rules"
          className="px-4 py-2 rounded-lg bg-surface-card border border-surface-border hover:bg-surface-border text-white text-xs font-semibold flex items-center gap-2 transition"
        >
          <BookOpen className="h-4 w-4" />
          Browse Declarations Standards
        </Link>
      </div>

      {/* Advisory Notice */}
      <div className="p-4 rounded-xl bg-brand-blue/10 border border-brand-blue/30 text-blue-300 text-xs leading-relaxed space-y-1">
        <strong className="text-white block font-semibold">Legal Metrology (Packaged Commodities) Self-Compliance Advisory</strong>
        <span>All pre-packaged goods displayed for sale must carry legible declarations of: MRP (inclusive of all taxes), Net Quantity, Manufacturing/Packing Date, and Complete Manufacturer Contact Details.</span>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-surface-card border border-surface-border rounded-xl p-5">
          <span className="text-xs font-semibold text-brand-muted uppercase tracking-wider">Active Legal Standards</span>
          <div className="mt-2 text-2xl font-bold text-white">{rules.length} Registered Rules</div>
          <p className="mt-1 text-xs text-brand-muted">Pre-packaged commodity specifications</p>
        </div>
        <div className="bg-surface-card border border-surface-border rounded-xl p-5">
          <span className="text-xs font-semibold text-brand-muted uppercase tracking-wider">Premises Inspections</span>
          <div className="mt-2 text-2xl font-bold text-white">{scans.length} Audits Logged</div>
          <p className="mt-1 text-xs text-brand-muted">Regulatory and verification scans</p>
        </div>
        <div className="bg-surface-card border border-surface-border rounded-xl p-5">
          <span className="text-xs font-semibold text-brand-muted uppercase tracking-wider">Premises Standing</span>
          <div className="mt-2 text-2xl font-bold text-emerald-400">
            {scans.some(s => s.final_compliance === 'non_compliant') ? (
              <span className="text-red-400">Notices Pending</span>
            ) : (
              <span className="text-emerald-400">Compliant</span>
            )}
          </div>
          <p className="mt-1 text-xs text-brand-muted">Based on recorded premises audits</p>
        </div>
      </div>

      {/* Recent Inspections on Premises */}
      <div className="bg-surface-card border border-surface-border rounded-xl p-6">
        <h2 className="text-base font-semibold text-white mb-4">Recent Label Verifications</h2>
        {loading ? (
          <p className="text-xs text-brand-muted">Loading audit records...</p>
        ) : scans.length === 0 ? (
          <p className="text-xs text-brand-muted">No inspection records logged for this retail establishment.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-surface-border text-brand-muted uppercase font-semibold">
                  <th className="py-2">Commodity</th>
                  <th className="py-2">Status</th>
                  <th className="py-2">Audit Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-border">
                {scans.slice(0, 5).map(s => (
                  <tr key={s.id} className="text-white">
                    <td className="py-3 font-medium">{s.product_name || 'Packaged Commodity'}</td>
                    <td className="py-3"><StatusBadge status={s.final_compliance || s.automated_compliance} /></td>
                    <td className="py-3 text-brand-muted">{new Date(s.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
