// API Test Utility
// This file helps debug API issues

export const testBooksAPI = async () => {
  console.log('🧪 Testing Books API');
  console.log('====================');
  
  try {
    // Test direct fetch
    console.log('Testing direct fetch...');
    const response = await fetch('https://0108izew87.execute-api.us-east-1.amazonaws.com/dev/query/books', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });

    console.log('Response status:', response.status);
    console.log('Response headers:', response.headers);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log('Response data:', data);
    
    // Handle API Gateway response structure
    let booksData;
    if (data.body) {
      // API Gateway wraps the response in a body field
      booksData = JSON.parse(data.body);
    } else {
      // Direct response
      booksData = data;
    }
    
    console.log('Processed books data:', booksData);
    console.log('Books count:', booksData.books?.length || 0);
    
    return booksData;
    
  } catch (error) {
    console.error('❌ API test failed:', error);
    throw error;
  }
};

export const testAPIWithClient = async () => {
  console.log('🧪 Testing API with client');
  console.log('===========================');
  
  try {
    const { listBooks } = await import('./api-client');
    const response = await listBooks();
    console.log('API client response:', response);
    return response;
  } catch (error) {
    console.error('❌ API client test failed:', error);
    throw error;
  }
}; 