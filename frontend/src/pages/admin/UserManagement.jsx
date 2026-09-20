import React, { useState, useEffect } from 'react';
import { 
  Users, 
  Shield, 
  UserCheck, 
  UserX, 
  AlertTriangle, 
  Search, 
  RefreshCw, 
  Filter, 
  Phone, 
  Mail, 
  Lock, 
  CheckCircle2, 
  XCircle,
  X,
  Store,
  User,
  ShieldAlert,
  Award,
  Clock,
  Check,
  Building,
  FileText,
  Trash2,
} from 'lucide-react';
import { 
  listUsersApi, 
  toggleUserStatusApi,
  listRoleApplicationsApi,
  approveRoleApplicationApi,
  rejectRoleApplicationApi,
  changeUserRoleApi,
  deleteUserApi,
} from '../../api/admin';
import { useAuth } from '../../context/AuthContext';

export default function UserManagement({ initialRole }) {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState(initialRole || 'all');
  const [statusFilter, setStatusFilter] = useState('all'); // 'all' | 'active' | 'suspended'
  const [actionLoading, setActionLoading] = useState(null);

  // Tab & Applications State
  const [activeTab, setActiveTab] = useState('users'); // 'users' | 'applications'
  const [applications, setApplications] = useState([]);
  const [loadingApps, setLoadingApps] = useState(false);
  const [appFilter, setAppFilter] = useState('pending'); // 'pending' | 'all' | 'approved' | 'rejected'
  const [appActionLoading, setAppActionLoading] = useState(null);

  useEffect(() => {
    if (initialRole) {
      setRoleFilter(initialRole);
    }
  }, [initialRole]);

  const fetchUsers = async (isManualRefresh = false) => {
    try {
      if (isManualRefresh) setRefreshing(true);
      else setLoading(true);
      setError(null);
      const data = await listUsersApi();
      const userList = Array.isArray(data) ? data : (data?.users || []);
      setUsers(userList);
    } catch (err) {
      console.error('Failed to load users:', err);
      setError('Unable to load user roster. Ensure administrative permissions are active.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const fetchApplications = async () => {
    try {
      setLoadingApps(true);
      const data = await listRoleApplicationsApi();
      setApplications(data?.applications || []);
    } catch (err) {
      console.error('Failed to load role applications:', err);
    } finally {
      setLoadingApps(false);
    }
  };

  useEffect(() => {
    fetchUsers();
    fetchApplications();
  }, []);

  const handleRefreshAll = async () => {
    setRefreshing(true);
    await Promise.all([fetchUsers(true), fetchApplications()]);
    setRefreshing(false);
  };

  const handleToggleStatus = async (targetUser) => {
    if (targetUser.id === currentUser?.id) {
      alert('Self-lockout protection: You cannot deactivate your own administrative account.');
      return;
    }

    const newStatus = !targetUser.is_active;
    const confirmMsg = newStatus 
      ? `Re-activate access for ${targetUser.full_name || targetUser.email}?` 
      : `Deactivate ${targetUser.full_name || targetUser.email}? They will immediately lose platform access.`;

    if (!window.confirm(confirmMsg)) return;

    try {
      setActionLoading(targetUser.id);
      await toggleUserStatusApi(targetUser.id, newStatus);
      setUsers(prev => prev.map(u => u.id === targetUser.id ? { ...u, is_active: newStatus } : u));
    } catch (err) {
      console.error('Status toggle failed:', err);
      alert(err.response?.data?.detail || 'Failed to update user account status.');
    } finally {
      setActionLoading(null);
    }
  };

  const handleRoleChange = async (targetUser, newRole) => {
    if (targetUser.email === 'admin@maars.gov.in') {
      alert('System Protection: The primary system administrator (admin@maars.gov.in) cannot be demoted or changed.');
      return;
    }
    if (targetUser.role === newRole) return;

    const confirmMsg = `Directly change role of "${targetUser.full_name || targetUser.email}" from ${targetUser.role.toUpperCase()} to ${newRole.toUpperCase()}?`;
    if (!window.confirm(confirmMsg)) return;

    try {
      setActionLoading(targetUser.id);
      await changeUserRoleApi(targetUser.id, newRole);
      setUsers(prev => prev.map(u => u.id === targetUser.id ? { ...u, role: newRole } : u));
    } catch (err) {
      console.error('Role update failed:', err);
      alert(err.response?.data?.detail || 'Failed to update user role.');
    } finally {
      setActionLoading(null);
    }
  };

  const handleDeleteUser = async (targetUser) => {
    if (targetUser.email === 'admin@maars.gov.in') {
      alert('System Protection: The primary system administrator (admin@maars.gov.in) cannot be deleted.');
      return;
    }
    if (targetUser.id === currentUser?.id) {
      alert('Self-deletion Protection: You cannot delete your own active administrator account.');
      return;
    }

    const confirmMsg = `Are you sure you want to permanently delete user "${targetUser.full_name || targetUser.email}" (${targetUser.role})? This cannot be undone.`;
    if (!window.confirm(confirmMsg)) return;

    try {
      setActionLoading(targetUser.id);
      await deleteUserApi(targetUser.id);
      setUsers(prev => prev.filter(u => u.id !== targetUser.id));
      await fetchApplications();
    } catch (err) {
      console.error('User deletion failed:', err);
      if (err.response?.status === 404) {
        // User is already removed from DB, clear from UI state
        setUsers(prev => prev.filter(u => u.id !== targetUser.id));
      } else {
        alert(err.response?.data?.detail || 'Failed to delete user.');
      }
    } finally {
      setActionLoading(null);
    }
  };

  const handleApproveApplication = async (app) => {
    const confirmMsg = `Approve ${app.applicant_name} as ${app.requested_role.toUpperCase()}? This will immediately elevate their platform permissions.`;
    if (!window.confirm(confirmMsg)) return;

    try {
      setAppActionLoading(app.id);
      await approveRoleApplicationApi(app.id);
      await Promise.all([fetchUsers(), fetchApplications()]);
    } catch (err) {
      console.error('Approval failed:', err);
      alert(err.response?.data?.detail || 'Failed to approve application.');
    } finally {
      setAppActionLoading(null);
    }
  };

  const handleRejectApplication = async (app) => {
    const remarks = window.prompt(`Provide reason for rejecting ${app.applicant_name}'s application:`, 'Credentials could not be verified.');
    if (remarks === null) return; // User cancelled

    try {
      setAppActionLoading(app.id);
      await rejectRoleApplicationApi(app.id, remarks);
      await fetchApplications();
    } catch (err) {
      console.error('Rejection failed:', err);
      alert(err.response?.data?.detail || 'Failed to reject application.');
    } finally {
      setAppActionLoading(null);
    }
  };

  // KPI Calculations
  const pendingApps = applications.filter(a => a.status === 'pending');
  const stats = {
    total: users.length,
    officers: users.filter(u => u.role === 'officer').length,
    admins: users.filter(u => u.role === 'admin').length,
    retailers: users.filter(u => u.role === 'retailer').length,
    active: users.filter(u => u.is_active).length,
    suspended: users.filter(u => !u.is_active).length,
    pendingAppsCount: pendingApps.length
  };

  const filteredUsers = (users || []).filter(u => {
    const badge = u.badge_number || u.employee_id || '';
    const matchesSearch = 
      (u.email && u.email.toLowerCase().includes(search.toLowerCase())) ||
      (u.full_name && u.full_name.toLowerCase().includes(search.toLowerCase())) ||
      badge.toLowerCase().includes(search.toLowerCase());
    
    const matchesRole = roleFilter === 'all' || u.role === roleFilter;
    const matchesStatus = 
      statusFilter === 'all' || 
      (statusFilter === 'active' && u.is_active) || 
      (statusFilter === 'suspended' && !u.is_active);

    return matchesSearch && matchesRole && matchesStatus;
  });

  const filteredApplications = applications.filter(a => {
    if (appFilter === 'all') return true;
    return a.status === appFilter;
  });

  const isOfficerRegistryOnly = initialRole === 'officer';

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              {isOfficerRegistryOnly ? 'Enforcement Division' : 'Governance & Directory'}
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight flex items-center gap-3">
            <div className="p-2 rounded-xl bg-indigo-600/10 border border-indigo-500/20 text-indigo-400">
              {isOfficerRegistryOnly ? <Shield className="h-6 w-6" /> : <Users className="h-6 w-6" />}
            </div>
            {isOfficerRegistryOnly ? 'Legal Metrology Officer Registry' : 'Personnel & Access Governance'}
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            {isOfficerRegistryOnly 
              ? 'Authorized roster of Legal Metrology field inspection officers and enforcement credentials.' 
              : 'Centralized directory for field inspectors, administrative governance, retail merchants, and consumer accounts.'}
          </p>
        </div>

        <button
          onClick={handleRefreshAll}
          disabled={loading || refreshing}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium border border-slate-700 hover:border-slate-600 transition-all shadow-sm self-start md:self-auto disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 text-indigo-400 ${refreshing ? 'animate-spin' : ''}`} />
          <span>{refreshing ? 'Refreshing...' : 'Refresh Roster'}</span>
        </button>
      </div>

      {/* KPI Stats Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
        <div className="bg-slate-900/60 border border-slate-800/90 rounded-xl p-4 flex items-center gap-3.5 shadow-sm">
          <div className="p-2.5 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <Users className="h-5 w-5" />
          </div>
          <div>
            <div className="text-xl font-bold text-white">{stats.total}</div>
            <div className="text-xs font-medium text-slate-400">Total Accounts</div>
          </div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800/90 rounded-xl p-4 flex items-center gap-3.5 shadow-sm">
          <div className="p-2.5 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <Shield className="h-5 w-5" />
          </div>
          <div>
            <div className="text-xl font-bold text-white">{stats.officers}</div>
            <div className="text-xs font-medium text-slate-400">Field Officers</div>
          </div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800/90 rounded-xl p-4 flex items-center gap-3.5 shadow-sm">
          <div className="p-2.5 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <Award className="h-5 w-5" />
          </div>
          <div>
            <div className="text-xl font-bold text-amber-400">{stats.pendingAppsCount}</div>
            <div className="text-xs font-medium text-slate-400">Pending Elevation Requests</div>
          </div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800/90 rounded-xl p-4 flex items-center gap-3.5 shadow-sm">
          <div className="p-2.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="h-5 w-5" />
          </div>
          <div>
            <div className="text-xl font-bold text-emerald-400">{stats.active}</div>
            <div className="text-xs font-medium text-slate-400">Active Personnel</div>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-center gap-3">
          <AlertTriangle className="h-5 w-5 text-rose-400 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Navigation Tabs (User Directory vs Role Elevation Requests) */}
      {!isOfficerRegistryOnly && (
        <div className="flex border-b border-slate-800 gap-6 text-sm font-medium">
          <button
            onClick={() => setActiveTab('users')}
            className={`pb-3 px-1 border-b-2 transition flex items-center gap-2 ${
              activeTab === 'users'
                ? 'border-indigo-500 text-white font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Users className="h-4 w-4" />
            <span>Personnel Directory ({stats.total})</span>
          </button>

          <button
            onClick={() => setActiveTab('applications')}
            className={`pb-3 px-1 border-b-2 transition flex items-center gap-2 ${
              activeTab === 'applications'
                ? 'border-indigo-500 text-white font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Award className="h-4 w-4 text-amber-400" />
            <span>Role Elevation Requests</span>
            {stats.pendingAppsCount > 0 && (
              <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-amber-500 text-slate-950">
                {stats.pendingAppsCount} pending
              </span>
            )}
          </button>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 1: USER ROSTER & PERSONNEL DIRECTORY                                   */}
      {/* ========================================================================= */}
      {activeTab === 'users' && (
        <>
          {/* Filter & Search Bar */}
          <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-4 space-y-3 shadow-sm backdrop-blur">
            <div className="flex flex-col md:flex-row items-center gap-3">
              {/* Search Field */}
              <div className="relative flex-1 w-full">
                <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search by personnel name, email address, or official badge ID..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full pl-10 pr-10 py-2.5 bg-slate-950/80 border border-slate-700/80 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all shadow-inner"
                />
                {search && (
                  <button 
                    onClick={() => setSearch('')}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white p-0.5 rounded"
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>

              {/* Role Filter */}
              {!isOfficerRegistryOnly && (
                <div className="flex items-center gap-2 w-full md:w-auto">
                  <span className="text-xs font-medium text-slate-400 whitespace-nowrap flex items-center gap-1.5">
                    <Filter className="h-3.5 w-3.5 text-slate-400" />
                    Role:
                  </span>
                  <select
                    value={roleFilter}
                    onChange={(e) => setRoleFilter(e.target.value)}
                    className="w-full md:w-auto px-3 py-2.5 bg-slate-950/80 border border-slate-700/80 text-slate-200 text-xs font-medium rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition cursor-pointer"
                  >
                    <option value="all">All Roles ({stats.total})</option>
                    <option value="officer">Field Officers ({stats.officers})</option>
                    <option value="admin">Administrators ({stats.admins})</option>
                    <option value="retailer">Retail Merchants ({stats.retailers})</option>
                    <option value="customer">Citizens / Consumers</option>
                  </select>
                </div>
              )}

              {/* Status Filter */}
              <div className="flex items-center gap-2 w-full md:w-auto">
                <span className="text-xs font-medium text-slate-400 whitespace-nowrap">Status:</span>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="w-full md:w-auto px-3 py-2.5 bg-slate-950/80 border border-slate-700/80 text-slate-200 text-xs font-medium rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition cursor-pointer"
                >
                  <option value="all">All Status</option>
                  <option value="active">Active Only ({stats.active})</option>
                  <option value="suspended">Suspended Only ({stats.suspended})</option>
                </select>
              </div>
            </div>

            {/* Active Filter Chips Bar */}
            {(search || (roleFilter !== 'all' && !isOfficerRegistryOnly) || statusFilter !== 'all') && (
              <div className="flex items-center gap-2 pt-2 border-t border-slate-800/80 text-xs text-slate-400 flex-wrap">
                <span className="font-medium text-slate-500">Active filters:</span>
                {search && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-800 text-slate-200 border border-slate-700">
                    Query: "{search}"
                    <button onClick={() => setSearch('')} className="hover:text-rose-400 ml-0.5"><X className="h-3 w-3" /></button>
                  </span>
                )}
                {roleFilter !== 'all' && !isOfficerRegistryOnly && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-indigo-500/10 text-indigo-300 border border-indigo-500/30 capitalize">
                    Role: {roleFilter}
                    <button onClick={() => setRoleFilter('all')} className="hover:text-rose-400 ml-0.5"><X className="h-3 w-3" /></button>
                  </span>
                )}
                {statusFilter !== 'all' && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-800 text-slate-200 border border-slate-700 capitalize">
                    Status: {statusFilter}
                    <button onClick={() => setStatusFilter('all')} className="hover:text-rose-400 ml-0.5"><X className="h-3 w-3" /></button>
                  </span>
                )}
                <button 
                  onClick={() => { setSearch(''); setRoleFilter(initialRole || 'all'); setStatusFilter('all'); }}
                  className="text-indigo-400 hover:text-indigo-300 font-medium underline ml-auto text-xs"
                >
                  Reset all filters
                </button>
              </div>
            )}
          </div>

          {/* User Table Container */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden shadow-xl backdrop-blur">
            {loading ? (
              <div className="py-20 text-center space-y-3">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-2 border-indigo-500 border-t-transparent" />
                <p className="text-slate-400 text-sm font-medium">Retrieving personnel credentials and access registry...</p>
              </div>
            ) : filteredUsers.length === 0 ? (
              <div className="py-16 text-center space-y-3">
                <div className="p-3 rounded-full bg-slate-800 inline-block text-slate-400">
                  <Users className="h-6 w-6" />
                </div>
                <h3 className="text-base font-semibold text-white">No personnel matching query</h3>
                <p className="text-xs text-slate-400 max-w-sm mx-auto">
                  No registered user accounts match the current filter or search criteria.
                </p>
                <button
                  onClick={() => { setSearch(''); setRoleFilter(initialRole || 'all'); setStatusFilter('all'); }}
                  className="mt-2 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition"
                >
                  Clear Filters
                </button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 bg-slate-950/70 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                      <th className="py-3.5 px-5">Personnel Name & Email</th>
                      <th className="py-3.5 px-4">Designation / Role</th>
                      <th className="py-3.5 px-4">Official Badge & Phone</th>
                      <th className="py-3.5 px-4">Access Status</th>
                      <th className="py-3.5 px-5 text-right">Access Governance</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-sm">
                    {filteredUsers.map((u) => {
                      const isSelf = u.id === currentUser?.id;
                      const isPrimaryAdmin = u.email === 'admin@maars.gov.in';
                      const isProtected = isPrimaryAdmin || isSelf;
                      const initial = (u.full_name ? u.full_name.charAt(0) : (u.email ? u.email.charAt(0) : 'U')).toUpperCase();
                      
                      return (
                        <tr 
                          key={u.id} 
                          className={`hover:bg-slate-800/40 transition-colors ${!u.is_active ? 'opacity-70 bg-rose-950/10' : ''}`}
                        >
                          {/* Name & Avatar */}
                          <td className="py-3.5 px-5">
                            <div className="flex items-center gap-3">
                              <div className={`w-9 h-9 rounded-xl flex items-center justify-center font-bold text-xs shrink-0 shadow-sm ${
                                u.role === 'admin' 
                                  ? 'bg-purple-600/20 text-purple-300 border border-purple-500/30' 
                                  : u.role === 'officer' 
                                  ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30' 
                                  : u.role === 'retailer' 
                                  ? 'bg-amber-600/20 text-amber-300 border border-amber-500/30' 
                                  : 'bg-slate-700/40 text-slate-300 border border-slate-600/40'
                              }`}>
                                {initial}
                              </div>
                              <div className="min-w-0">
                                <div className="font-semibold text-white truncate flex items-center gap-1.5">
                                  <span>{u.full_name || 'Unnamed Personnel'}</span>
                                  {isSelf && (
                                    <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                                      You
                                    </span>
                                  )}
                                </div>
                                <div className="text-xs text-slate-400 truncate flex items-center gap-1 mt-0.5">
                                  <Mail className="h-3 w-3 text-slate-500 shrink-0" />
                                  <span className="truncate">{u.email}</span>
                                </div>
                              </div>
                            </div>
                          </td>

                          {/* Role Badge & Quick Change */}
                          <td className="py-3.5 px-4">
                            {isPrimaryAdmin ? (
                              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-bold bg-amber-500/10 text-amber-300 border border-amber-500/30">
                                <Lock className="h-3 w-3 text-amber-400" />
                                Primary Admin (Protected)
                              </span>
                            ) : (
                              <div className="space-y-1.5">
                                <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-semibold capitalize ${
                                  u.role === 'admin' 
                                    ? 'bg-purple-500/10 text-purple-300 border border-purple-500/30' :
                                  u.role === 'officer' 
                                    ? 'bg-indigo-500/10 text-indigo-300 border border-indigo-500/30' :
                                  u.role === 'retailer' 
                                    ? 'bg-amber-500/10 text-amber-300 border border-amber-500/30' :
                                    'bg-slate-700/20 text-slate-300 border border-slate-600/30'
                                }`}>
                                  {u.role === 'admin' && <ShieldAlert className="h-3 w-3" />}
                                  {u.role === 'officer' && <Shield className="h-3 w-3" />}
                                  {u.role === 'retailer' && <Store className="h-3 w-3" />}
                                  {u.role === 'customer' && <User className="h-3 w-3" />}
                                  <span>{u.role === 'officer' ? 'Enforcement Officer' : (u.role === 'customer' ? 'Citizen' : u.role)}</span>
                                </span>

                                <div>
                                  <select
                                    value={u.role}
                                    onChange={(e) => handleRoleChange(u, e.target.value)}
                                    disabled={actionLoading === u.id}
                                    title="Assign new role directly"
                                    className="text-[11px] font-medium bg-slate-950 border border-slate-700 rounded-md px-2 py-1 text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 cursor-pointer hover:border-slate-500 transition"
                                  >
                                    <option value="officer">Role: Officer</option>
                                    <option value="retailer">Role: Retailer</option>
                                    <option value="admin">Role: Admin</option>
                                    <option value="customer">Role: Citizen</option>
                                  </select>
                                </div>
                              </div>
                            )}
                          </td>

                          {/* Badge / Phone */}
                          <td className="py-3.5 px-4 text-xs">
                            <div className="font-mono text-slate-200">
                              {(u.badge_number || u.employee_id) ? (
                                <span className="px-1.5 py-0.5 rounded bg-slate-800/80 border border-slate-700/60 text-slate-300 text-[11px]">
                                  {u.badge_number || u.employee_id}
                                </span>
                              ) : (
                                <span className="text-slate-500 font-sans italic">Not assigned</span>
                              )}
                            </div>
                            <div className="text-slate-400 flex items-center gap-1 mt-1">
                              <Phone className="h-3 w-3 text-slate-500 shrink-0" />
                              <span>{u.phone || u.phone_number || '—'}</span>
                            </div>
                          </td>

                          {/* Status */}
                          <td className="py-3.5 px-4">
                            <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
                              u.is_active 
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' 
                                : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                            }`}>
                              <span className={`h-1.5 w-1.5 rounded-full ${
                                u.is_active ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'
                              }`} />
                              {u.is_active ? 'Active' : 'Suspended'}
                            </span>
                          </td>

                          {/* Action Buttons: Status + Delete with Protection */}
                          <td className="py-3.5 px-5 text-right">
                            {isProtected ? (
                              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700 text-amber-300 text-xs font-semibold cursor-not-allowed">
                                <Lock className="h-3.5 w-3.5 text-amber-400" />
                                {isPrimaryAdmin ? 'Primary Admin (Protected)' : 'Self (Protected)'}
                              </span>
                            ) : (
                              <div className="flex items-center justify-end gap-1.5">
                                <button
                                  onClick={() => handleToggleStatus(u)}
                                  disabled={actionLoading === u.id}
                                  title={u.is_active ? "Suspend access" : "Activate account"}
                                  className={`inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold border transition-all duration-150 shadow-sm ${
                                    u.is_active
                                      ? 'border-slate-700 bg-slate-800/80 text-slate-300 hover:bg-amber-950/30 hover:border-amber-700/50 hover:text-amber-300'
                                      : 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300 hover:bg-emerald-500/20 hover:border-emerald-500/50'
                                  } disabled:opacity-50`}
                                >
                                  {actionLoading === u.id ? (
                                    <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                                  ) : u.is_active ? (
                                    <>
                                      <UserX className="h-3.5 w-3.5 text-slate-400" />
                                      <span>Suspend</span>
                                    </>
                                  ) : (
                                    <>
                                      <UserCheck className="h-3.5 w-3.5 text-emerald-400" />
                                      <span>Activate</span>
                                    </>
                                  )}
                                </button>

                                <button
                                  onClick={() => handleDeleteUser(u)}
                                  disabled={actionLoading === u.id}
                                  title="Permanently delete user"
                                  className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-semibold border border-rose-500/30 bg-rose-500/10 text-rose-300 hover:bg-rose-500/20 hover:border-rose-500/50 disabled:opacity-50 transition"
                                >
                                  <Trash2 className="h-3.5 w-3.5 text-rose-400" />
                                  <span>Delete</span>
                                </button>
                              </div>
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
        </>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: ROLE ELEVATION APPLICATIONS & ACCREDITATION GOVERNANCE              */}
      {/* ========================================================================= */}
      {activeTab === 'applications' && (
        <div className="space-y-4">
          {/* Status Filter Tabs */}
          <div className="flex items-center gap-2 bg-slate-900/60 p-1.5 rounded-xl border border-slate-800 w-fit">
            <button
              onClick={() => setAppFilter('pending')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                appFilter === 'pending'
                  ? 'bg-amber-500 text-slate-950 shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Pending Approval ({pendingApps.length})
            </button>
            <button
              onClick={() => setAppFilter('approved')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                appFilter === 'approved'
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Approved ({applications.filter(a => a.status === 'approved').length})
            </button>
            <button
              onClick={() => setAppFilter('rejected')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                appFilter === 'rejected'
                  ? 'bg-rose-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Declined ({applications.filter(a => a.status === 'rejected').length})
            </button>
            <button
              onClick={() => setAppFilter('all')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                appFilter === 'all'
                  ? 'bg-slate-700 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              All Records ({applications.length})
            </button>
          </div>

          {/* Applications Content */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden shadow-xl backdrop-blur">
            {loadingApps ? (
              <div className="py-20 text-center space-y-3">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-2 border-amber-500 border-t-transparent" />
                <p className="text-slate-400 text-sm font-medium">Fetching role elevation submissions...</p>
              </div>
            ) : filteredApplications.length === 0 ? (
              <div className="py-16 text-center space-y-3">
                <div className="p-3 rounded-full bg-slate-800 inline-block text-slate-400">
                  <Award className="h-6 w-6" />
                </div>
                <h3 className="text-base font-semibold text-white">No applications in this category</h3>
                <p className="text-xs text-slate-400 max-w-sm mx-auto">
                  There are currently no role elevation requests matching the '{appFilter}' status filter.
                </p>
              </div>
            ) : (
              <div className="divide-y divide-slate-800/70">
                {filteredApplications.map((app) => {
                  const isPending = app.status === 'pending';
                  const isOfficer = app.requested_role === 'officer';

                  return (
                    <div key={app.id} className="p-5 hover:bg-slate-800/30 transition space-y-3.5">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <div className="flex items-center gap-3">
                          <div className={`p-2.5 rounded-xl border ${
                            isOfficer 
                              ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30' 
                              : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                          }`}>
                            {isOfficer ? <Shield className="h-5 w-5" /> : <Store className="h-5 w-5" />}
                          </div>
                          <div>
                            <div className="font-semibold text-white text-sm flex items-center gap-2">
                              <span>{app.applicant_name}</span>
                              <span className="text-xs text-slate-400 font-normal">({app.applicant_email})</span>
                            </div>
                            <div className="text-xs text-slate-400 mt-0.5 flex items-center gap-2">
                              <span>Applied for:</span>
                              <span className="font-semibold text-white capitalize">
                                {isOfficer ? 'Legal Metrology Field Officer' : 'Retail Merchant'}
                              </span>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-2 self-start sm:self-auto">
                          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${
                            app.status === 'pending'
                              ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                              : app.status === 'approved'
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                              : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                          }`}>
                            <span className={`h-1.5 w-1.5 rounded-full ${
                              app.status === 'pending' ? 'bg-amber-400 animate-pulse' : app.status === 'approved' ? 'bg-emerald-400' : 'bg-rose-400'
                            }`} />
                            {app.status === 'pending' ? 'Pending Approval' : app.status === 'approved' ? 'Approved' : 'Declined'}
                          </span>

                          <span className="text-[11px] text-slate-500">
                            {app.created_at ? new Date(app.created_at).toLocaleDateString() : ''}
                          </span>
                        </div>
                      </div>

                      {/* Application Credentials Breakdown */}
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-slate-950/60 p-3.5 rounded-xl border border-slate-800 text-xs">
                        {isOfficer ? (
                          <>
                            <div>
                              <span className="text-slate-400 block text-[11px]">Official Badge / Employee ID:</span>
                              <span className="font-mono font-semibold text-indigo-300">{app.badge_number || 'Not provided'}</span>
                            </div>
                            <div>
                              <span className="text-slate-400 block text-[11px]">Jurisdiction / Zone:</span>
                              <span className="text-slate-200">{app.department || 'General Enforcement'}</span>
                            </div>
                            <div>
                              <span className="text-slate-400 block text-[11px]">Contact Phone:</span>
                              <span className="text-slate-200">{app.phone || '—'}</span>
                            </div>
                          </>
                        ) : (
                          <>
                            <div>
                              <span className="text-slate-400 block text-[11px]">Registered Business Name:</span>
                              <span className="font-semibold text-amber-300">{app.business_name || 'Not provided'}</span>
                            </div>
                            <div>
                              <span className="text-slate-400 block text-[11px]">Trade / License No:</span>
                              <span className="font-mono text-slate-200">{app.license_number || '—'}</span>
                            </div>
                            <div>
                              <span className="text-slate-400 block text-[11px]">Shop Address:</span>
                              <span className="text-slate-200">{app.shop_address || '—'}</span>
                            </div>
                          </>
                        )}
                      </div>

                      {app.notes && (
                        <div className="text-xs text-slate-300 bg-slate-950/60 px-3.5 py-2.5 rounded-lg border border-slate-800">
                          <span className="font-semibold text-amber-300">Mandatory Application Reason:</span> {app.notes}
                        </div>
                      )}

                      {app.admin_remarks && (
                        <div className="text-xs text-rose-300 bg-rose-950/30 px-3 py-2 rounded-lg border border-rose-900/50">
                          <span className="font-semibold text-rose-200">Rejection Note:</span> {app.admin_remarks}
                        </div>
                      )}

                      {/* Admin Governance Actions */}
                      {isPending && (
                        <div className="flex items-center justify-end gap-2.5 pt-2">
                          <button
                            onClick={() => handleRejectApplication(app)}
                            disabled={appActionLoading === app.id}
                            className="px-3 py-1.5 rounded-lg border border-rose-500/30 bg-rose-500/10 text-rose-300 hover:bg-rose-500/20 text-xs font-semibold transition disabled:opacity-50 inline-flex items-center gap-1.5"
                          >
                            <XCircle className="h-3.5 w-3.5" />
                            <span>Decline Request</span>
                          </button>
                          <button
                            onClick={() => handleApproveApplication(app)}
                            disabled={appActionLoading === app.id}
                            className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md transition disabled:opacity-50 inline-flex items-center gap-1.5"
                          >
                            {appActionLoading === app.id ? (
                              <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                            ) : (
                              <Check className="h-3.5 w-3.5" />
                            )}
                            <span>Approve Accreditation</span>
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
