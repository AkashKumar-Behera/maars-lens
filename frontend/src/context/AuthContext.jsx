import { useState, useEffect, createContext, useContext } from 'react';
import { loginApi, registerApi } from '../api/auth';

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

  const register = async (formData) => {
    const payload = {
      full_name: formData.fullName || formData.full_name,
      email: formData.email,
      password: formData.password,
      phone: formData.phone || undefined,
      role: formData.role || 'citizen',

      // Retailer specific
      retailer_id: formData.retailer_id || formData.retailerId,
      business_name: formData.business_name || formData.businessName,
      registration_no: formData.registration_no || formData.registrationNo,
      business_type: formData.business_type || formData.businessType,
      address: formData.address,
      district: formData.district,
      state: formData.state,

      // Officer specific
      officer_id: formData.officer_id || formData.officerId,
      employee_id: formData.employee_id || formData.employeeId,
      designation: formData.designation,
      jurisdiction: formData.jurisdiction,

      // Admin specific
      admin_id: formData.admin_id || formData.adminId,
      department: formData.department,
      admin_secret_key: formData.admin_secret_key || formData.adminSecretKey,

      // Proof
      proof_filename: formData.proof_filename || formData.proofFilename,
      proof_data: formData.proof_data || formData.proofData,
    };

    const data = await registerApi(payload);

    if (data.access_token) {
      const userData = {
        id: data.user.id,
        email: data.user.email,
        name: data.user.full_name || (formData.email ? formData.email.split('@')[0].toUpperCase() : 'USER'),
        role: data.user.role || 'customer',
      };
      setUser(userData);
      setRole(userData.role);
      setToken(data.access_token);
      localStorage.setItem('user', JSON.stringify(userData));
      localStorage.setItem('token', data.access_token);
      return userData;
    }
    return data;
  };

  const logout = async () => {
    setUser(null);
    setRole(null);
    setToken(null);
    localStorage.removeItem('user');
    localStorage.removeItem('token');
  };

  return (
    <AuthContext.Provider value={{ user, role, token, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
