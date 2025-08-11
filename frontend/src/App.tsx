import { useState, useEffect } from 'react';
import BookQA from './components/BookQA';
import BookUpload from './components/BookUpload';
import RepoUpload from './components/RepoUpload';
import Auth from './components/Auth';
import { isAuthenticated as checkAuth, getUserInfo, logout } from './utils/simple-auth';
// Debug imports - commented out since debug buttons are hidden
// import { debugAuthStatus } from './utils/auth-debug';
// import { testBooksAPI } from './utils/api-test';
import './App.css';

function App() {
  const [currentPage, setCurrentPage] = useState<'qa' | 'upload' | 'repo'>('qa');
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [user, setUser] = useState<any>(null);
  const [userFullName, setUserFullName] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      console.log('Checking authentication status...');
      const timeoutPromise = new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Auth check timeout')), 3000)
      );
      const authenticated = await Promise.race([checkAuth(), timeoutPromise]) as boolean;
      console.log('Authentication result:', authenticated);
      setIsAuthenticated(authenticated);
      
      if (authenticated) {
        // Get user info including full name, but don't fail if it errors
        try {
          const userInfo = await getUserInfo();
          if (userInfo?.name) {
            setUserFullName(userInfo.name);
          }
        } catch (error) {
          console.error('Error getting user info during auth check:', error);
          // Continue with authentication even if getUserInfo fails
          setUserFullName('');
        }
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      // If auth check fails, assume not authenticated and show login
      setIsAuthenticated(false);
      setUserFullName('');
    } finally {
      setLoading(false);
    }
  };

  const handleAuthStateChange = async (authenticated: boolean, user?: any) => {
    setIsAuthenticated(authenticated);
    setUser(user);
    
    if (authenticated && user) {
      // Only try to get user info if we're authenticated and have a user
      try {
        const userInfo = await getUserInfo();
        if (userInfo?.name) {
          setUserFullName(userInfo.name);
        }
      } catch (error) {
        console.error('Error getting user info:', error);
        // Don't fail the auth state change if getUserInfo fails
        setUserFullName('');
      }
    } else {
      setUserFullName('');
    }
  };

  const handleLogout = () => {
    try {
      console.log('Logging out user...');
      
      // Clear user info first to prevent getUserInfo errors
      setUserFullName('');
      setUser(null);
      setIsAuthenticated(false);
      
      // Then call the actual logout function
      logout(); // Sign out from Cognito
      
      setCurrentPage('qa'); // Reset to default page
      console.log('Logout completed successfully');
    } catch (error) {
      console.error('Error during logout:', error);
      // Force logout even if there's an error
      setIsAuthenticated(false);
      setUser(null);
      setUserFullName('');
      setCurrentPage('qa');
    }
  };

  // Debug functions - commented out since debug buttons are hidden
  /*
  const handleDebugAuth = async () => {
    console.log('🔍 Debugging authentication...');
    await debugAuthStatus();
  };

  const handleTestAPI = async () => {
    console.log('🧪 Testing API...');
    try {
      await testBooksAPI();
    } catch (error) {
      console.error('API test failed:', error);
    }
  };
  */

  const handleRepoUploadSuccess = (bookTitle: string) => {
    // Switch to Q&A page after successful repository upload
    console.log(`Repository ${bookTitle} uploaded successfully`);
    setCurrentPage('qa');
  };

  if (loading) {
    console.log('App is loading...');
    return (
      <div className="App">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    console.log('User not authenticated, showing Auth component');
    return <Auth onAuthStateChange={handleAuthStateChange} />;
  }

  return (
    <div className="App">
      <nav className="app-navigation">
        <div className="nav-container">
          <div className="nav-brand">
            <h2>📚 Epic Library</h2>
          </div>
          <div className="nav-links">
            <button 
              className={`nav-link ${currentPage === 'qa' ? 'active' : ''}`}
              onClick={() => setCurrentPage('qa')}
            >
              Ask Questions
            </button>
            <button 
              className={`nav-link ${currentPage === 'upload' ? 'active' : ''}`}
              onClick={() => setCurrentPage('upload')}
            >
              Upload Books
            </button>
            <button 
              className={`nav-link ${currentPage === 'repo' ? 'active' : ''}`}
              onClick={() => setCurrentPage('repo')}
            >
              Upload Repo
            </button>
          </div>
          <div className="nav-user">
            <span>Welcome, {userFullName || user?.getUsername()}</span>
            <button 
              className="logout-btn"
              onClick={handleLogout}
            >
              Logout
            </button>
            {/* Temporary debug buttons - remove in production */}
            {/* <button 
              className="debug-btn"
              onClick={handleDebugAuth}
              style={{ 
                marginLeft: '10px', 
                padding: '5px 10px', 
                fontSize: '12px',
                background: '#ff6b6b',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Debug Auth
            </button>
            <button 
              className="test-api-btn"
              onClick={handleTestAPI}
              style={{ 
                marginLeft: '10px', 
                padding: '5px 10px', 
                fontSize: '12px',
                background: '#4ecdc4',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Test API
            </button> */}
          </div>
        </div>
      </nav>

      {currentPage === 'qa' && <BookQA />}
      {currentPage === 'upload' && <BookUpload />}
      {currentPage === 'repo' && <RepoUpload onUploadSuccess={handleRepoUploadSuccess} />}
    </div>
  );
}

export default App;
