import { useState, useEffect } from 'react';
import { listRulesApi } from '../../api/rules';
import StatusBadge from '../../components/StatusBadge';
import EmptyState from '../../components/EmptyState';
import { BookOpen, Search, Filter, ShieldCheck, CheckCircle2 } from 'lucide-react';

const RulesBrowser = () => {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');

  useEffect(() => {
    fetchRules();
  }, []);

  const fetchRules = async () => {
    try {
      setLoading(true);
      const data = await listRulesApi({ only_active: false, per_page: 100 });
      setRules(data.rules || []);
    } catch (err) {
      console.error('Failed to load rules:', err);
    } finally {
      setLoading(false);
    }
  };

  const categories = Array.from(new Set(rules.map((r) => r.category).filter(Boolean)));

  const filteredRules = rules.filter((rule) => {
    const activeVersion = rule.active_version || (rule.versions && rule.versions[0]) || {};
    const matchesSearch =
      rule.rule_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      rule.category.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (activeVersion.statutory_reference || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (activeVersion.description_en || '').toLowerCase().includes(searchTerm.toLowerCase());

    const matchesCat = !categoryFilter || rule.category === categoryFilter;
    return matchesSearch && matchesCat;
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">
          Legal Metrology Statutory Standards
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Standardized mandatory declarations under the Legal Metrology (Packaged Commodities) Rules, 2011.
        </p>
      </div>

      {/* Statutory Disclaimer Banner */}
      <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl text-amber-300 text-xs flex items-center gap-2">
        <span className="px-1.5 py-0.5 bg-amber-500/20 text-amber-400 font-mono text-[10px] rounded font-bold uppercase">
          legal_verified: false
        </span>
        <span>
          Statutory rule citations and thresholds are unverified draft configurations subject to official review by the Legal Metrology Department.
        </span>
      </div>

      {/* Filter Bar */}
      <div className="bg-slate-800/90 border border-slate-700/80 p-4 rounded-xl flex flex-col md:flex-row gap-4 justify-between">
        <div className="relative flex-1 max-w-md">
          <Search size={16} className="absolute left-3 top-3 text-slate-400" />
          <input
            type="text"
            placeholder="Search by rule code, statutory section, or keyword..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div className="flex items-center space-x-2">
          <Filter size={16} className="text-slate-400" />
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Categories</option>
            {categories.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Rules Grid / List */}
      {loading ? (
        <div className="p-12 text-center text-slate-400 text-sm">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500 mb-3"></div>
          <p>Querying active compliance rule versions from database...</p>
        </div>
      ) : filteredRules.length === 0 ? (
        <EmptyState
          title="No rules found"
          message="No compliance rules matched your search query."
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredRules.map((rule) => {
            const v = rule.active_version || (rule.versions && rule.versions[0]) || {};
            return (
              <div
                key={rule.id}
                className="bg-slate-800/90 border border-slate-700/80 p-5 rounded-xl shadow-lg flex flex-col justify-between space-y-4"
              >
                <div>
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div>
                      <span className="text-xs font-mono font-bold text-indigo-400">
                        {rule.rule_code}
                      </span>
                      <span className="ml-2 px-2 py-0.5 bg-slate-700/60 text-slate-300 text-[10px] uppercase font-semibold rounded">
                        {rule.category}
                      </span>
                    </div>
                    <div className="flex items-center space-x-1.5">
                      <StatusBadge status={v.verification_status || 'demo'} />
                      {v.is_active ? (
                        <span className="px-2 py-0.5 bg-emerald-950 text-emerald-400 border border-emerald-800 text-[10px] font-semibold rounded">
                          Active (v{v.version})
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 bg-slate-800 text-slate-400 border border-slate-700 text-[10px] font-semibold rounded">
                          Inactive
                        </span>
                      )}
                    </div>
                  </div>

                  <h3 className="text-sm font-semibold text-white mt-1">
                    {v.statutory_reference || 'Statutory Citation'}
                  </h3>

                  <p className="text-xs text-slate-300 mt-2 line-clamp-2">
                    {v.description_en || 'Statutory requirement description.'}
                  </p>
                </div>

                <div className="pt-3 border-t border-slate-700/60 text-xs text-slate-400 flex items-center justify-between">
                  <div>
                    <span className="font-semibold text-slate-300">Target Field:</span>{' '}
                    <code className="text-indigo-300">{v.target_field || 'general'}</code>
                  </div>
                  <div>
                    <span className="font-semibold text-slate-300">Severity:</span>{' '}
                    <span className="capitalize">{v.severity || 'major'}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default RulesBrowser;
