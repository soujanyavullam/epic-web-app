import { CognitoUserPool, CognitoUser, AuthenticationDetails, CognitoUserAttribute } from 'amazon-cognito-identity-js';

// Cognito configuration
const poolData = {
  UserPoolId: 'us-east-1_8d5MmHizq',
  ClientId: '73hfbldjkkbdjvsml57g671j4l'
};

const userPool = new CognitoUserPool(poolData);

// API configuration
const API_BASE_URL = 'https://your-api-gateway-url.amazonaws.com/prod'; // Update with your API Gateway URL

export interface AuthUser {
  username: string;
  email: string;
  name?: string;
}

export const getCurrentUser = (): CognitoUser | null => {
  try {
    const user = userPool.getCurrentUser();
    if (user) {
      console.log('Current user found:', user.getUsername());
    } else {
      console.log('No current user found');
    }
    return user;
  } catch (error) {
    console.error('Error getting current user:', error);
    return null;
  }
};

export const getAuthToken = (): Promise<string | null> => {
  return new Promise((resolve) => {
    try {
      const currentUser = getCurrentUser();
      if (!currentUser) {
        console.log('No current user found, no token available');
        resolve(null);
        return;
      }

      currentUser.getSession((err: any, session: any) => {
        if (err) {
          console.error('Error getting session:', err);
          resolve(null);
        } else if (session && session.isValid()) {
          const token = session.getIdToken().getJwtToken();
          console.log('Valid token found');
          resolve(token);
        } else {
          console.log('No valid session found');
          resolve(null);
        }
      });
    } catch (error) {
      console.error('Error in getAuthToken:', error);
      resolve(null);
    }
  });
};

export const isAuthenticated = async (): Promise<boolean> => {
  try {
    const currentUser = getCurrentUser();
    if (!currentUser) {
      console.log('No current user found, not authenticated');
      return false;
    }

    const token = await getAuthToken();
    if (!token) {
      console.log('No valid token found, not authenticated');
      return false;
    }

    console.log('User is authenticated with valid token');
    return true;
  } catch (error) {
    console.error('Error checking authentication status:', error);
    return false;
  }
};

export const logout = async (): Promise<void> => {
  try {
    console.log('Starting enhanced logout process...');
    
    // 1. Get current auth token before clearing user
    let token: string | null = null;
    try {
      token = await getAuthToken();
    } catch (error) {
      console.log('No valid token found, proceeding with logout');
    }
    
    // 2. Call backend logout handler if token exists
    if (token) {
      try {
        console.log('Calling backend logout handler...');
        const response = await fetch(`${API_BASE_URL}/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
        
        if (response.ok) {
          const result = await response.json();
          console.log('Backend logout successful:', result);
        } else {
          console.warn('Backend logout failed, continuing with frontend logout');
        }
      } catch (error) {
        console.warn('Error calling backend logout, continuing with frontend logout:', error);
      }
    }
    
    // 3. Safely clear all authentication state first
    safeClearAuth();
    
    // 4. Try to sign out from Cognito (but don't fail if it errors)
    try {
      const currentUser = getCurrentUser();
      if (currentUser) {
        console.log('Signing out from Cognito...');
        currentUser.signOut();
        console.log('Cognito signOut called successfully');
      }
    } catch (error) {
      console.warn('Error during Cognito signOut, continuing with logout:', error);
    }
    
    console.log('Enhanced logout completed successfully');
    
    // 5. Force page reload to clear all state
    window.location.reload();
    
  } catch (error) {
    console.error('Error during enhanced logout:', error);
    // Force logout even if there's an error
    safeClearAuth();
    window.location.reload();
  }
};

export const getAuthHeaders = async (): Promise<Record<string, string>> => {
  const token = await getAuthToken();
  if (token) {
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  }
  return {
    'Content-Type': 'application/json',
  };
};

export const authenticatedFetch = async (
  url: string, 
  options: RequestInit = {}
): Promise<Response> => {
  const headers = await getAuthHeaders();
  
  const fetchOptions: RequestInit = {
    ...options,
    headers: {
      ...headers,
      ...options.headers,
    },
  };

  return fetch(url, fetchOptions);
};

export const getUserInfo = async (): Promise<AuthUser | null> => {
  try {
    const currentUser = getCurrentUser();
    if (!currentUser) {
      console.log('No current user found, returning null');
      return null;
    }

    // Check if user has a valid session before calling getUserAttributes
    try {
      const token = await getAuthToken();
      if (!token) {
        console.log('No valid session found, user may be signed out');
        return null;
      }
    } catch (error) {
      console.log('Error checking session, user may be signed out');
      return null;
    }

    return new Promise((resolve, reject) => {
      currentUser.getUserAttributes((err, attributes) => {
        if (err) {
          console.error('Error getting user attributes:', err);
          reject(err);
          return;
        }

        if (attributes) {
          const userInfo: AuthUser = {
            username: currentUser.getUsername(),
            email: '',
            name: '',
          };

          attributes.forEach(attr => {
            if (attr.getName() === 'email') {
              userInfo.email = attr.getValue();
            }
            if (attr.getName() === 'name') {
              userInfo.name = attr.getValue();
            }
          });

          resolve(userInfo);
        } else {
          console.log('No user attributes found');
          resolve(null);
        }
      });
    });
  } catch (error) {
    console.error('Error getting user info:', error);
    return null;
  }
};

// Simple login function that doesn't use SRP
export const loginUser = async (email: string, password: string): Promise<any> => {
  return new Promise((resolve, reject) => {
    const authenticationDetails = new AuthenticationDetails({
      Username: email,
      Password: password,
    });

    const cognitoUser = new CognitoUser({
      Username: email,
      Pool: userPool,
    });

    cognitoUser.authenticateUser(authenticationDetails, {
      onSuccess: (result) => {
        console.log('Login successful:', result);
        resolve(cognitoUser);
      },
      onFailure: (err) => {
        console.error('Login failed:', err);
        reject(err);
      },
    });
  });
};

// Simple registration function
export const registerUser = async (email: string, password: string, name: string): Promise<any> => {
  return new Promise((resolve, reject) => {
    const attributeList = [
      new CognitoUserAttribute({
        Name: 'email',
        Value: email,
      }),
      new CognitoUserAttribute({
        Name: 'name',
        Value: name,
      }),
    ];

    userPool.signUp(email, password, attributeList, [], (err, result) => {
      if (err) {
        console.error('Registration failed:', err);
        reject(err);
      } else {
        console.log('Registration successful:', result);
        resolve(result);
      }
    });
  });
};

// Confirm registration with verification code
export const confirmRegistration = async (email: string, code: string): Promise<any> => {
  return new Promise((resolve, reject) => {
    const cognitoUser = new CognitoUser({
      Username: email,
      Pool: userPool,
    });

    cognitoUser.confirmRegistration(code, true, (err, result) => {
      if (err) {
        console.error('Confirmation failed:', err);
        reject(err);
      } else {
        console.log('Confirmation successful:', result);
        resolve(result);
      }
    });
  });
};

// Safe function to clear all authentication state without triggering errors
export const safeClearAuth = (): void => {
  try {
    console.log('Safely clearing all authentication state...');
    
    // Clear all storage
    const storageKeys = [
      'cognito-token',
      'aws.cognito.identity-id',
      'api_key',
      'user_info',
      'auth_token',
      'cognitoUserPool',
      'cognitoUser'
    ];
    
    storageKeys.forEach(key => {
      try {
        localStorage.removeItem(key);
        sessionStorage.removeItem(key);
      } catch (error) {
        console.warn(`Error removing storage key ${key}:`, error);
      }
    });
    
    // Clear any Cognito-related keys
    for (let i = localStorage.length - 1; i >= 0; i--) {
      try {
        const key = localStorage.key(i);
        if (key && (key.includes('cognito') || key.includes('aws') || key.includes('auth'))) {
          localStorage.removeItem(key);
        }
      } catch (error) {
        console.warn('Error clearing localStorage key:', error);
      }
    }
    
    // Clear sessionStorage as well
    for (let i = sessionStorage.length - 1; i >= 0; i--) {
      try {
        const key = sessionStorage.key(i);
        if (key && (key.includes('cognito') || key.includes('aws') || key.includes('auth'))) {
          sessionStorage.removeItem(key);
        }
      } catch (error) {
        console.warn('Error clearing sessionStorage key:', error);
      }
    }
    
    console.log('Authentication state cleared successfully');
  } catch (error) {
    console.error('Error clearing authentication state:', error);
  }
}; 