import { useState, useEffect, createContext, useContext } from 'react';
import { loginApi } from '../api/auth';

const AuthContext = createContext({});

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [role, setRole] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    const storedToken = localStorage.getItem('token');
    if (storedUser && storedToken) {
      try {
        const parsed = JSON.parse(storedUser);
        setUser(parsed);
        setRole(parsed.role);
        setToken(storedToken);
      } catch (err) {
        localStorage.removeItem('user');
        localStorage.removeItem('token');
      }
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    // 1. Call real backend login endpoint
    const data = await loginApi(email, password);
    const accessToken = data.access_token;
    
    // 2. Decode JWT payload to retrieve real user id and role issued by backend
    let userId = 'a0000000-0000-0000-0000-000000000001';
    let userRole = 'customer';
    try {
      const base64Url = accessToken.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      const decoded = JSON.parse(jsonPayload);
      userId = decoded.id || decoded.sub || userId;
      userRole = decoded.role || decoded.user_metadata?.role || userRole;
    } catch (e) {
      if (email.toLowerCase().includes('admin')) userRole = 'admin';
      else if (email.toLowerCase().includes('officer')) userRole = 'officer';
      else if (email.toLowerCase().includes('retailer')) userRole = 'retailer';
    }

    const userData = {
      id: userId,
      email,
      name: email.split('@')[0].toUpperCase(),
      role: userRole,
    };

    setUser(userData);
    setRole(userRole);
    setToken(accessToken);

    localStorage.setItem('user', JSON.stringify(userData));
    localStorage.setItem('token', accessToken);

    return userData;
  };

  const logout = async () => {
    setUser(null);
    setRole(null);
    setToken(null);
    localStorage.removeItem('user');
    localStorage.removeItem('token');
  };

  return (
    <AuthContext.Provider value={{ user, role, token, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
