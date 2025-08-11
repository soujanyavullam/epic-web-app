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
  return userPool.getCurrentUser();
};

export const getAuthToken = (): Promise<string | null> => {
  return new Promise((resolve, reject) => {
    const currentUser = getCurrentUser();
    if (!currentUser) {
      resolve(null);
      return;
    }

    currentUser.getSession((err: any, session: any) => {
      if (err) {
        console.error('Error getting session:', err);
        reject(err);
      } else if (session && session.isValid()) {
        resolve(session.getIdToken().getJwtToken());
      } else {
        resolve(null);
      }
    });
  });
};

export const isAuthenticated = (): Promise<boolean> => {
  return getAuthToken().then(token => !!token);
};

export const logout = async (): Promise<void> => {
  try {
    console.log('Starting enhanced logout process...');
    
    // 1. Get current auth token
    const token = await getAuthToken();
    
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
    
    // 3. Sign out from Cognito
    const currentUser = getCurrentUser();
    if (currentUser) {
      await new Promise<void>((resolve, reject) => {
        currentUser.signOut((err) => {
          if (err) {
            console.error('Cognito signOut error:', err);
            reject(err);
          } else {
            console.log('Cognito signOut successful');
            resolve();
          }
        });
      });
    }
    
    // 4. Clear all storage
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
      localStorage.removeItem(key);
      sessionStorage.removeItem(key);
    });
    
    // 5. Clear any Cognito-related keys
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && (key.includes('cognito') || key.includes('aws') || key.includes('auth'))) {
        localStorage.removeItem(key);
      }
    }
    
    // 6. Clear sessionStorage as well
    for (let i = 0; i < sessionStorage.length; i++) {
      const key = sessionStorage.key(i);
      if (key && (key.includes('cognito') || key.includes('aws') || key.includes('auth'))) {
        sessionStorage.removeItem(key);
      }
    }
    
    console.log('Enhanced logout completed successfully');
    
    // 7. Force page reload to clear all state
    window.location.reload();
    
  } catch (error) {
    console.error('Error during enhanced logout:', error);
    // Force logout even if there's an error
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
    if (!currentUser) return null;

    return new Promise((resolve, reject) => {
      currentUser.getUserAttributes((err, attributes) => {
        if (err) {
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