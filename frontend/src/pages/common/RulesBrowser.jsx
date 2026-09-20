import { useState, useEffect } from 'react';
import { listRulesApi, createRuleVersionApi, toggleRuleVersionActivationApi } from '../../api/rules';
import { useAuth } from '../../context/AuthContext';
import StatusBadge from '../../components/StatusBadge';
import EmptyState from '../../components/EmptyState';
import { BookOpen, Search, Filter, ShieldCheck, CheckCircle2, Edit3, X, Save, AlertTriangle } from 'lucide-react';

const RulesBrowser = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');

  // Editing state
  const [editingRule, setEditingRule] = useState(null);
  const [editForm, setEditForm] = useState({
    statutory_reference: '',
    description_en: '',
    failure_message_template: '',
    severity: 'major',
    target_field: '',
    rule_type: 'presence',
    check_definition: {},
    requires_visual_measurement: false,
    measurement_unit: '',
    is_active: true,
  });
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);

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

  const handleOpenEdit = (rule) => {
    const v = rule.active_version || (rule.versions && rule.versions[0]) || {};
    setEditingRule(rule);
    setEditForm({
      statutory_reference: v.statutory_reference || '',
      description_en: v.description_en || '',
      failure_message_template: v.failure_message_template || '',
      severity: v.severity || 'major',
      target_field: v.target_field || 'general',
      rule_type: v.rule_type || 'presence',
      check_definition: v.check_definition || { operator: 'exists' },
      requires_visual_measurement: Boolean(v.requires_visual_measurement),
      measurement_unit: v.measurement_unit || '',
      is_active: v.is_active !== undefined ? v.is_active : true,
    });
    setSaveError(null);
  };

  const handleSaveRule = async (e) => {
    e.preventDefault();
    if (!editingRule) return;

    try {
      setSaving(true);
      setSaveError(null);

      const payload = {
        statutory_reference: editForm.statutory_reference.trim(),
        description_en: editForm.description_en.trim(),
        failure_message_template: editForm.failure_message_template.trim(),
        severity: editForm.severity,
        target_field: editForm.target_field.trim() || 'general',
        rule_type: editForm.rule_type,
        check_definition: typeof editForm.check_definition === 'string' 
          ? JSON.parse(editForm.check_definition) 
          : editForm.check_definition,
        requires_visual_measurement: editForm.requires_visual_measurement,
        measurement_unit: editForm.measurement_unit ? editForm.measurement_unit.trim() : null,
        is_active: editForm.is_active,
      };

      await createRuleVersionApi(editingRule.id, payload);
      setEditingRule(null);
      await fetchRules();
    } catch (err) {
      console.error('Failed to save rule version:', err);
      setSaveError(err.response?.data?.detail || err.message || 'Failed to publish new rule version.');
    } finally {
      setSaving(false);
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
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Legal Metrology Statutory Standards
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Standardized mandatory declarations under the Legal Metrology (Packaged Commodities) Rules, 2011.
          </p>
        </div>
        {isAdmin && (
          <div className="px-3 py-1.5 rounded-lg bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 text-xs font-semibold flex items-center gap-2">
            <ShieldCheck size={16} />
            <span>Admin Governance Mode: Version Authoring Enabled</span>
          </div>
        )}
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
                  <div className="flex items-center gap-3">
                    <div>
                      <span className="font-semibold text-slate-300">Severity:</span>{' '}
                      <span className="capitalize">{v.severity || 'major'}</span>
                    </div>
                    {isAdmin && (
                      <button
                        onClick={() => handleOpenEdit(rule)}
                        className="flex items-center gap-1 px-2.5 py-1 rounded bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs transition"
                      >
                        <Edit3 size={13} />
                        <span>Edit Rule</span>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Edit Rule Modal for Admin */}
      {editingRule && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-slate-800 border border-slate-700 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl animate-fade-in flex flex-col max-h-[90vh]">
            <div className="p-4 border-b border-slate-700 flex items-center justify-between bg-slate-900/50">
              <div className="flex items-center gap-2">
                <Edit3 className="text-indigo-400" size={18} />
                <div>
                  <h3 className="text-base font-bold text-white">
                    Edit Statutory Rule: {editingRule.rule_code}
                  </h3>
                  <p className="text-xs text-slate-400">
                    Category: {editingRule.category} (Publishing creates an immutable new version)
                  </p>
                </div>
              </div>
              <button
                onClick={() => setEditingRule(null)}
                className="text-slate-400 hover:text-white transition"
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSaveRule} className="p-6 overflow-y-auto space-y-4 text-xs">
              {saveError && (
                <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 flex items-center gap-2">
                  <AlertTriangle size={16} />
                  <span>{saveError}</span>
                </div>
              )}

              <div>
                <label className="block text-slate-300 font-semibold mb-1">
                  Statutory Reference
                </label>
                <input
                  type="text"
                  required
                  value={editForm.statutory_reference}
                  onChange={(e) => setEditForm({ ...editForm, statutory_reference: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-xs focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  placeholder="e.g. Legal Metrology (Packaged Commodities) Rules, 2011 - Rule 6(1)(a)"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">
                  Description (English)
                </label>
                <textarea
                  rows={2}
                  required
                  value={editForm.description_en}
                  onChange={(e) => setEditForm({ ...editForm, description_en: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-xs focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  placeholder="Official legal requirement and intent..."
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">
                  Failure Message Template
                </label>
                <input
                  type="text"
                  required
                  value={editForm.failure_message_template}
                  onChange={(e) => setEditForm({ ...editForm, failure_message_template: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-xs focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  placeholder="e.g. Mandatory declaration is missing or invalid on the packaging label."
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Severity</label>
                  <select
                    value={editForm.severity}
                    onChange={(e) => setEditForm({ ...editForm, severity: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-xs focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  >
                    <option value="critical">Critical</option>
                    <option value="major">Major</option>
                    <option value="minor">Minor</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Target Field</label>
                  <input
                    type="text"
                    required
                    value={editForm.target_field}
                    onChange={(e) => setEditForm({ ...editForm, target_field: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-xs focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Rule Type</label>
                  <select
                    value={editForm.rule_type}
                    onChange={(e) => setEditForm({ ...editForm, rule_type: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-xs focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  >
                    <option value="presence">Presence</option>
                    <option value="format">Format</option>
                    <option value="dimension">Dimension</option>
                    <option value="value_check">Value Check</option>
                    <option value="calculation">Calculation</option>
                    <option value="consistency">Consistency</option>
                  </select>
                </div>

                <div className="flex items-center gap-2 pt-5">
                  <input
                    type="checkbox"
                    id="is_active"
                    checked={editForm.is_active}
                    onChange={(e) => setEditForm({ ...editForm, is_active: e.target.checked })}
                    className="h-4 w-4 rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-indigo-500"
                  />
                  <label htmlFor="is_active" className="text-slate-300 font-medium select-none">
                    Activate this version immediately
                  </label>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-700 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setEditingRule(null)}
                  className="px-4 py-2 rounded-lg border border-slate-700 text-slate-300 hover:bg-slate-700/50 transition font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold flex items-center gap-1.5 transition disabled:opacity-50"
                >
                  {saving ? (
                    'Publishing...'
                  ) : (
                    <>
                      <Save size={14} />
                      <span>Publish New Version</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default RulesBrowser;
