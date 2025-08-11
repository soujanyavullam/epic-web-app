import React, { useState, useEffect } from 'react';
import { loginUser, registerUser, getCurrentUser, logout } from '../utils/simple-auth';
import './Auth.css';

interface AuthProps {
  onAuthStateChange: (isAuthenticated: boolean, user?: any) => void;
}

const Auth: React.FC<AuthProps> = ({ onAuthStateChange }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<any>(null);

  console.log('Auth component rendered, isAuthenticated:', isAuthenticated);

  useEffect(() => {
    // Check if user is already authenticated
    const currentUser = getCurrentUser();
    if (currentUser) {
      setIsAuthenticated(true);
      setUser(currentUser);
      onAuthStateChange(true, currentUser);
    }
  }, [onAuthStateChange]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      if (isLogin) {
        await handleLogin();
      } else {
        await handleRegister();
      }
    } catch (err) {
      console.error('Authentication error:', err);
      setError(err instanceof Error ? err.message : 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async () => {
    try {
      const cognitoUser = await loginUser(email, password);
      setIsAuthenticated(true);
      setUser(cognitoUser);
      onAuthStateChange(true, cognitoUser);
    } catch (err) {
      throw err;
    }
  };

  const handleRegister = async () => {
    try {
      await registerUser(email, password, name);
      setError('');
      setIsLogin(true);
      alert('Registration successful! Please check your email for verification.');
    } catch (err) {
      throw err;
    }
  };

  const handleLogout = () => {
    logout();
    setIsAuthenticated(false);
    setUser(null);
    onAuthStateChange(false);
    setEmail('');
    setPassword('');
    setName('');
  };

  if (isAuthenticated) {
    return (
      <div className="auth-container">
        <div className="auth-card">
          <h2>Welcome!</h2>
          <p>You are logged in as: {user?.getUsername()}</p>
          <button 
            className="auth-button logout-button" 
            onClick={handleLogout}
          >
            Logout
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>{isLogin ? 'Login' : 'Register'}</h2>
        
        <form onSubmit={handleSubmit} className="auth-form">
          {!isLogin && (
            <div className="form-group">
              <label htmlFor="name">Name</label>
              <input
                type="text"
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required={!isLogin}
                placeholder="Enter your name"
              />
            </div>
          )}
          
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="Enter your email"
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="Enter your password"
            />
          </div>
          
          {error && <div className="error-message">{error}</div>}
          
          <button 
            type="submit" 
            className="auth-button"
            disabled={loading}
          >
            {loading ? 'Loading...' : (isLogin ? 'Login' : 'Register')}
          </button>
        </form>
        
        <div className="auth-toggle">
          <p>
            {isLogin ? "Don't have an account? " : "Already have an account? "}
            <button 
              className="toggle-button"
              onClick={() => {
                setIsLogin(!isLogin);
                setError('');
              }}
            >
              {isLogin ? 'Register' : 'Login'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Auth; 