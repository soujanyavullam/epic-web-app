// API Client for secure requests
const API_BASE_URL = 'https://0108izew87.execute-api.us-east-1.amazonaws.com/dev';

// Get API key from environment or localStorage
const getApiKey = (): string => {
  // For API Key protection - use localStorage or environment variable
  // In browser, we'll use localStorage instead of process.env
  return localStorage.getItem('api_key') || '';
};

// Get auth token for Cognito protection
const getAuthToken = async (): Promise<string> => {
  // For Cognito authentication
  try {
    const { getAuthToken } = await import('./simple-auth');
    return await getAuthToken() || '';
  } catch (error) {
    console.error('Error getting auth token:', error);
    return '';
  }
};

// Determine which security method to use
const getSecurityHeaders = async (): Promise<Record<string, string>> => {
  const baseHeaders = {
    'Content-Type': 'application/json',
  };

  // Try API Key first
  const apiKey = getApiKey();
  if (apiKey) {
    return {
      ...baseHeaders,
      'x-api-key': apiKey,
    };
  }

  // Try Cognito token
  const token = await getAuthToken();
  if (token) {
    return {
      ...baseHeaders,
      'Authorization': `Bearer ${token}`,
    };
  }

  // No authentication (for development)
  return baseHeaders;
};

// Generic API request function
export const apiRequest = async (
  endpoint: string,
  method: 'GET' | 'POST' = 'POST',
  data?: any
): Promise<any> => {
  const headers = await getSecurityHeaders();
  
  const config: RequestInit = {
    method,
    headers,
  };

  if (data && method === 'POST') {
    config.body = JSON.stringify(data);
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
  }

  return response.json();
};

// Specific API functions
export const queryBook = async (question: string, bookTitle: string) => {
  return apiRequest('/query', 'POST', { question, book_title: bookTitle });
};

export const listBooks = async () => {
  return apiRequest('/books', 'GET');
};

export const uploadBook = async (bookData: any) => {
  return apiRequest('/upload', 'POST', bookData);
};

export const uploadRepo = async (githubUrl: string) => {
  return apiRequest('/repo', 'POST', { github_url: githubUrl });
}; 