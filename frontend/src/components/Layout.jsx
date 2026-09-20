import { useAuth } from '../context/AuthContext';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import {
  Shield,
  LayoutDashboard,
  Camera,
  History,
  AlertTriangle,
  BookOpen,
  BarChart3,
  Users,
  LogOut,
  Bell,
  Menu,
  X,
  UserCheck,
} from 'lucide-react';
import { useState } from 'react';

const Layout = ({ children }) => {
  const { user, role, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const navConfigs = {
    officer: [
      { label: 'Overview', path: '/officer', icon: LayoutDashboard },
      { label: 'New Inspection', path: '/officer/new-inspection', icon: Camera },
      { label: 'Inspection History', path: '/officer/inspections', icon: History },
      { label: 'Statutory Violations', path: '/officer/violations', icon: AlertTriangle },
      { label: 'Statutory Rules', path: '/officer/rules', icon: BookOpen },
    ],
    admin: [
      { label: 'Analytics Dashboard', path: '/admin', icon: BarChart3 },
      { label: 'Inspections Audit', path: '/admin/inspections', icon: History },
      { label: 'Statutory Rules', path: '/admin/rules', icon: BookOpen },
      { label: 'Violations Registry', path: '/admin/violations', icon: AlertTriangle },
      { label: 'Officer Registry', path: '/admin/officers', icon: Users },
      { label: 'User Registry', path: '/admin/users', icon: Users },
    ],
    retailer: [
      { label: 'Retailer Overview', path: '/retailer', icon: LayoutDashboard },
      { label: 'Compliance Inquiries', path: '/retailer/inspections', icon: History },
      { label: 'Statutory Rules', path: '/retailer/rules', icon: BookOpen },
    ],
    customer: [
      { label: 'Public Portal', path: '/customer', icon: LayoutDashboard },
      { label: 'Statutory Standards', path: '/customer/rules', icon: BookOpen },
    ],
  };

  const items = navConfigs[role] || [];

  return (
    <div className="flex h-screen bg-slate-900 text-slate-100 font-sans">
      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-slate-950 border-r border-slate-800 flex flex-col transform transition-transform duration-200 ease-in-out lg:static lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand Header */}
        <div className="h-16 flex items-center justify-between px-5 border-b border-slate-800/80 bg-slate-950/60">
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 bg-indigo-600 rounded-lg flex items-center justify-center shadow-md shadow-indigo-600/30">
              <Shield size={20} className="text-white" />
            </div>
            <div>
              <span className="text-base font-bold tracking-tight text-white block leading-tight">MAARS Lens</span>
              <span className="text-[10px] uppercase font-semibold tracking-wider text-indigo-400 block">LMPC Platform</span>
            </div>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden text-slate-400 hover:text-white p-1 rounded"
          >
            <X size={20} />
          </button>
        </div>

        {/* User Role Badge */}
        <div className="px-5 py-3 border-b border-slate-800/50 bg-slate-900/40">
          <div className="flex items-center space-x-2">
            <UserCheck size={15} className="text-emerald-400 shrink-0" />
            <div className="truncate">
              <p className="text-xs font-semibold text-slate-200 truncate">{user?.name || user?.email}</p>
              <p className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                Role: <span className="text-emerald-400">{role}</span>
              </p>
            </div>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {items.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setSidebarOpen(false)}
                className={`flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/20 font-semibold'
                    : 'text-slate-300 hover:bg-slate-900 hover:text-white'
                }`}
              >
                <Icon size={18} className={isActive ? 'text-white' : 'text-slate-400'} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Footer info */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-950/40 text-[11px] text-slate-500 text-center">
          Legal Metrology Act, 2009
          <br />
          Packaged Commodities Rules
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden bg-slate-900">
        {/* Top Header */}
        <header className="h-16 bg-slate-950 border-b border-slate-800 flex items-center justify-between px-4 sm:px-6">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden text-slate-400 hover:text-white p-1 rounded-md"
            >
              <Menu size={22} />
            </button>
            <div className="hidden sm:block text-xs text-slate-400">
              National Legal Metrology Digital Verification System
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="text-right hidden sm:block">
              <p className="text-xs font-medium text-slate-300">{user?.email}</p>
              <p className="text-[10px] text-emerald-400 font-semibold uppercase">Authorized Session</p>
            </div>
            <button
              onClick={handleLogout}
              title="Sign Out"
              className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-900 hover:bg-red-950/60 border border-slate-700 hover:border-red-700 text-slate-300 hover:text-red-300 text-xs font-medium rounded-lg transition"
            >
              <LogOut size={15} />
              <span className="hidden md:inline">Sign Out</span>
            </button>
          </div>
        </header>

        {/* Dynamic Main Body */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <div className="max-w-7xl mx-auto">{children}</div>
        </main>
      </div>
    </div>
  );
};

export default Layout;
