import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Shield, AlertCircle, ArrowRight, Lock, Mail } from 'lucide-react';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const user = await login(email, password);
      navigate(`/${user.role}`);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Login failed. Please check credentials.');
    } finally {
      setLoading(false);
    }
  };

  const setDemoRole = (roleEmail) => {
    setEmail(roleEmail);
    setPassword('Password123!');
  };

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <div className="w-14 h-14 bg-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-500/30">
            <Shield className="text-white" size={32} />
          </div>
        </div>
        <h2 className="mt-4 text-center text-3xl font-extrabold text-white tracking-tight">
          MAARS Lens
        </h2>
        <p className="mt-1 text-center text-sm text-slate-400">
          Legal Metrology Compliance & Inspection Platform
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-slate-800 py-8 px-4 shadow-xl border border-slate-700 sm:rounded-xl sm:px-10">
          {error && (
            <div className="mb-5 bg-red-950/60 border border-red-800 text-red-300 p-3 rounded-lg text-sm flex items-start space-x-2">
              <AlertCircle size={18} className="shrink-0 mt-0.5 text-red-400" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                Official Email Address
              </label>
              <div className="relative rounded-lg shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <Mail size={18} />
                </div>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="e.g. officer@maars.gov.in"
                  className="block w-full pl-10 pr-3 py-2.5 bg-slate-900/80 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                Password
              </label>
              <div className="relative rounded-lg shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <Lock size={18} />
                </div>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="block w-full pl-10 pr-3 py-2.5 bg-slate-900/80 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center items-center py-2.5 px-4 border border-transparent rounded-lg shadow-md text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 transition duration-150"
            >
              {loading ? (
                <span className="inline-flex items-center">
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Authenticating...
                </span>
              ) : (
                <span className="inline-flex items-center">
                  Sign In to System <ArrowRight size={16} className="ml-2" />
                </span>
              )}
            </button>
          </form>

          <div className="mt-6 pt-5 border-t border-slate-700/80">
            <p className="text-xs text-slate-400 font-medium mb-2.5 text-center">Quick Role Simulation Access:</p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <button
                type="button"
                onClick={() => setDemoRole('officer@maars.gov.in')}
                className="px-2 py-1.5 bg-slate-900 border border-slate-700 hover:border-indigo-500 rounded text-xs text-slate-200 hover:text-white transition text-center"
              >
                Officer
              </button>
              <button
                type="button"
                onClick={() => setDemoRole('admin@maars.gov.in')}
                className="px-2 py-1.5 bg-slate-900 border border-slate-700 hover:border-indigo-500 rounded text-xs text-slate-200 hover:text-white transition text-center"
              >
                Admin
              </button>
              <button
                type="button"
                onClick={() => setDemoRole('retailer@store.in')}
                className="px-2 py-1.5 bg-slate-900 border border-slate-700 hover:border-indigo-500 rounded text-xs text-slate-200 hover:text-white transition text-center"
              >
                Retailer
              </button>
              <button
                type="button"
                onClick={() => setDemoRole('consumer@maars.gov.in')}
                className="px-2 py-1.5 bg-slate-900 border border-slate-700 hover:border-indigo-500 rounded text-xs text-slate-200 hover:text-white transition text-center"
              >
                Consumer
              </button>
            </div>
            <p className="mt-2 text-[11px] text-slate-400 text-center">
              Demo Password: <span className="text-indigo-400 font-mono font-semibold">Password123!</span> (Auto-fills on click)
            </p>
          </div>
        </div>

        <p className="mt-4 text-center text-xs text-slate-500">
          Government of India • Ministry of Consumer Affairs • Legal Metrology Division
        </p>
      </div>
    </div>
  );
};

export default Login;
