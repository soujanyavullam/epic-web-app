import { CognitoUserPool, CognitoUser } from 'amazon-cognito-identity-js';

// Replace with your actual Cognito User Pool configuration
const poolData = {
  UserPoolId: 'us-east-1_8d5MmHizq', // Replace with your User Pool ID
  ClientId: '73hfbldjkkbdjvsml57g671j4l' // Replace with your App Client ID
};

const userPool = new CognitoUserPool(poolData);

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

export const logout = (): void => {
  const currentUser = getCurrentUser();
  if (currentUser) {
    currentUser.signOut();
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