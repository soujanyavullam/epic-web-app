import React, { useState, useEffect } from 'react';
import { loginUser, registerUser, confirmRegistration, getCurrentUser, logout } from '../utils/simple-auth';
import './Auth.css';

interface AuthProps {
  onAuthStateChange: (isAuthenticated: boolean, user?: any) => void;
}

const Auth: React.FC<AuthProps> = ({ onAuthStateChange }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [isVerifying, setIsVerifying] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<any>(null);

  console.log('Auth component rendered, isAuthenticated:', isAuthenticated);

  useEffect(() => {
    // Check if user is already authenticated
    try {
      const currentUser = getCurrentUser();
      if (currentUser) {
        // Verify the user has a valid session before setting as authenticated
        currentUser.getSession((err: any, session: any) => {
          if (err) {
            console.log('Error getting session for existing user:', err);
            setIsAuthenticated(false);
            setUser(null);
            onAuthStateChange(false);
          } else if (session && session.isValid()) {
            console.log('Valid session found for existing user');
            setIsAuthenticated(true);
            setUser(currentUser);
            onAuthStateChange(true, currentUser);
          } else {
            console.log('No valid session for existing user');
            setIsAuthenticated(false);
            setUser(null);
            onAuthStateChange(false);
          }
        });
      } else {
        console.log('No existing user found');
        setIsAuthenticated(false);
        setUser(null);
        onAuthStateChange(false);
      }
    } catch (error) {
      console.error('Error checking existing user:', error);
      setIsAuthenticated(false);
      setUser(null);
      onAuthStateChange(false);
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
      setIsVerifying(true);
      alert('Registration successful! Please check your email for verification code and enter it below.');
    } catch (err) {
      throw err;
    }
  };

  const handleVerification = async () => {
    try {
      setLoading(true);
      setError('');
      await confirmRegistration(email, verificationCode);
      setError('');
      setIsVerifying(false);
      setIsLogin(true);
      alert('Email verified successfully! You can now login.');
    } catch (err) {
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    try {
      console.log('Auth component: Logging out user...');
      
      // Clear local state first
      setIsAuthenticated(false);
      setUser(null);
      
      // Then call the logout function
      logout();
      
      // Clear form fields
      setEmail('');
      setPassword('');
      setName('');
      
      // Notify parent component
      onAuthStateChange(false);
      
      console.log('Auth component: Logout completed successfully');
    } catch (error) {
      console.error('Auth component: Error during logout:', error);
      // Force logout even if there's an error
      setIsAuthenticated(false);
      setUser(null);
      setEmail('');
      setPassword('');
      setName('');
      onAuthStateChange(false);
    }
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

  if (isVerifying) {
    return (
      <div className="auth-container">
        <div className="auth-card">
          <h2>Verify Your Email</h2>
          <p>We sent a verification code to: <strong>{email}</strong></p>
          <p>Please check your email and enter the code below:</p>
          
          <form onSubmit={(e) => { e.preventDefault(); handleVerification(); }} className="auth-form">
            <div className="form-group">
              <label htmlFor="verificationCode">Verification Code</label>
              <input
                type="text"
                id="verificationCode"
                value={verificationCode}
                onChange={(e) => setVerificationCode(e.target.value)}
                required
                placeholder="Enter verification code"
                maxLength={6}
              />
            </div>
            
            {error && <div className="error-message">{error}</div>}
            
            <button 
              type="submit" 
              className="auth-button"
              disabled={loading || !verificationCode.trim()}
            >
              {loading ? 'Verifying...' : 'Verify Email'}
            </button>
          </form>
          
          <div className="auth-toggle">
            <p>
              <button 
                className="toggle-button"
                onClick={() => {
                  setIsVerifying(false);
                  setIsLogin(true);
                  setError('');
                  setVerificationCode('');
                }}
              >
                Back to Login
              </button>
            </p>
          </div>
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