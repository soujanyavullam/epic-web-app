// Authentication Debug Utility
// This file helps debug authentication issues

import { getCurrentUser, getAuthToken, isAuthenticated } from './simple-auth';

export const debugAuthStatus = async () => {
  console.log('🔍 Debugging Authentication Status');
  console.log('==================================');
  
  // Check current user
  const currentUser = getCurrentUser();
  console.log('Current User:', currentUser ? currentUser.getUsername() : 'None');
  
  // Check auth token
  try {
    const token = await getAuthToken();
    console.log('Auth Token:', token ? 'Present' : 'None');
    if (token) {
      console.log('Token length:', token.length);
    }
  } catch (error) {
    console.error('Error getting auth token:', error);
  }
  
  // Check authentication status
  try {
    const authenticated = await isAuthenticated();
    console.log('Is Authenticated:', authenticated);
  } catch (error) {
    console.error('Error checking authentication:', error);
  }
  
  // Check localStorage and sessionStorage
  console.log('localStorage cognito-token:', localStorage.getItem('cognito-token') ? 'Present' : 'None');
  console.log('sessionStorage cognito-token:', sessionStorage.getItem('cognito-token') ? 'Present' : 'None');
  
  console.log('==================================');
};

export const clearAllAuthData = () => {
  console.log('🧹 Clearing all authentication data...');
  
  // Clear storage
  localStorage.removeItem('cognito-token');
  sessionStorage.removeItem('cognito-token');
  
  // Clear any other potential auth data
  localStorage.removeItem('aws.cognito.identity-id');
  sessionStorage.removeItem('aws.cognito.identity-id');
  
  console.log('✅ All authentication data cleared');
}; 