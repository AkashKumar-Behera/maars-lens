import React, { useState, useEffect } from 'react';
import { Users, Shield, UserCheck, UserX, AlertTriangle, Search } from 'lucide-react';
import { listUsersApi, toggleUserStatusApi } from '../../api/admin';
import { useAuth } from '../../context/AuthContext';

export default function UserManagement() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [actionLoading, setActionLoading] = useState(null);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await listUsersApi();
      setUsers(data);
    } catch (err) {
      console.error('Failed to load users:', err);
      setError('Unable to load user roster. Ensure admin permissions.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleToggleStatus = async (targetUser) => {
    if (targetUser.id === currentUser?.id) {
      alert('Self-lockout guard: You cannot deactivate your own administrative account.');
      return;
    }

    const newStatus = !targetUser.is_active;
    const confirmMsg = newStatus 
      ? `Re-activate user ${targetUser.email}?` 
      : `Deactivate user ${targetUser.email}? They will lose platform access immediately.`;

    if (!window.confirm(confirmMsg)) return;

    try {
      setActionLoading(targetUser.id);
      await toggleUserStatusApi(targetUser.id, newStatus);
      // Update local state directly
      setUsers(prev => prev.map(u => u.id === targetUser.id ? { ...u, is_active: newStatus } : u));
    } catch (err) {
      console.error('Status toggle failed:', err);
      alert(err.response?.data?.detail || 'Failed to update user status.');
    } finally {
      setActionLoading(null);
    }
  };

  const filteredUsers = users.filter(u => {
    const matchesSearch = 
      (u.email && u.email.toLowerCase().includes(search.toLowerCase())) ||
      (u.full_name && u.full_name.toLowerCase().includes(search.toLowerCase())) ||
      (u.badge_number && u.badge_number.toLowerCase().includes(search.toLowerCase()));
    const matchesRole = roleFilter === 'all' || u.role === roleFilter;
    return matchesSearch && matchesRole;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Users className="h-6 w-6 text-brand-blue" />
            Personnel & Access Governance
          </h1>
          <p className="text-sm text-brand-muted">
            Manage field inspectors, administrative personnel, and stakeholder accounts.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm flex items-center gap-3">
          <AlertTriangle className="h-5 w-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Filter Bar */}
      <div className="bg-surface-card border border-surface-border rounded-xl p-4 flex flex-col sm:flex-row items-center gap-4">
        <div className="relative flex-1 w-full">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-brand-muted" />
          <input
            type="text"
            placeholder="Search by name, email, or officer badge..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-surface-dark border border-surface-border rounded-lg text-sm text-white placeholder-brand-muted focus:outline-none focus:border-brand-blue transition"
          />
        </div>
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <span className="text-xs text-brand-muted whitespace-nowrap">Role:</span>
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="bg-surface-dark border border-surface-border text-white text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-brand-blue"
          >
            <option value="all">All Roles</option>
            <option value="officer">Legal Metrology Officer</option>
            <option value="admin">System Administrator</option>
            <option value="retailer">Retail Merchant</option>
            <option value="customer">Consumer</option>
          </select>
        </div>
      </div>

      {/* User Table */}
      <div className="bg-surface-card border border-surface-border rounded-xl overflow-hidden shadow-sm">
        {loading ? (
          <div className="p-12 text-center text-brand-muted text-sm animate-pulse">
            Loading user registry...
          </div>
        ) : filteredUsers.length === 0 ? (
          <div className="p-12 text-center text-brand-muted text-sm">
            No personnel found matching the query criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="border-b border-surface-border bg-surface-dark/50 text-xs font-semibold text-brand-muted uppercase tracking-wider">
                  <th className="py-3 px-4">User</th>
                  <th className="py-3 px-4">Designation / Role</th>
                  <th className="py-3 px-4">Badge / Phone</th>
                  <th className="py-3 px-4">Account Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-border">
                {filteredUsers.map((u) => {
                  const isSelf = u.id === currentUser?.id;
                  return (
                    <tr key={u.id} className="hover:bg-surface-dark/30 transition">
                      <td className="py-3 px-4">
                        <div className="font-medium text-white">{u.full_name || 'Unnamed Personnel'}</div>
                        <div className="text-xs text-brand-muted">{u.email}</div>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold capitalize ${
                          u.role === 'admin' ? 'bg-purple-500/10 text-purple-400 border border-purple-500/20' :
                          u.role === 'officer' ? 'bg-brand-blue/10 text-brand-blue border border-brand-blue/20' :
                          u.role === 'retailer' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                          'bg-gray-500/10 text-gray-400 border border-gray-500/20'
                        }`}>
                          {u.role}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-xs text-brand-muted">
                        <div>{u.badge_number ? `Badge: ${u.badge_number}` : '—'}</div>
                        <div>{u.phone_number || ''}</div>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`inline-flex items-center gap-1.5 text-xs font-medium ${
                          u.is_active ? 'text-emerald-400' : 'text-red-400'
                        }`}>
                          <span className={`h-1.5 w-1.5 rounded-full ${u.is_active ? 'bg-emerald-400' : 'bg-red-400'}`} />
                          {u.is_active ? 'Active' : 'Suspended'}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        {isSelf ? (
                          <span className="text-xs text-brand-muted italic">Self (Protected)</span>
                        ) : (
                          <button
                            onClick={() => handleToggleStatus(u)}
                            disabled={actionLoading === u.id}
                            className={`px-3 py-1 rounded text-xs font-medium border transition ${
                              u.is_active
                                ? 'border-red-500/30 text-red-400 hover:bg-red-500/10'
                                : 'border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/10'
                            }`}
                          >
                            {actionLoading === u.id ? (
                              'Updating...'
                            ) : u.is_active ? (
                              <span className="flex items-center gap-1"><UserX className="h-3.5 w-3.5" /> Deactivate</span>
                            ) : (
                              <span className="flex items-center gap-1"><UserCheck className="h-3.5 w-3.5" /> Activate</span>
                            )}
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
