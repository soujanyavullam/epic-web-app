import { useState, useEffect } from 'react';

interface Book {
  title: string;
  filename: string;
  lastModified?: string;
  size?: number;
  type?: string;
}

interface UseBooksReturn {
  books: Book[];
  loading: boolean;
  error: string | null;
  refreshBooks: () => void;
}

const useBooks = (): UseBooksReturn => {
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchBooks = async () => {
    try {
      setLoading(true);
      setError(null);

      console.log('Fetching books from API...');
      
      // Try the centralized API client first
      try {
        const { listBooks } = await import('../utils/api-client');
        const response = await listBooks();
        console.log('Books response from API client:', response);
        
        // Handle both direct response and wrapped response
        let booksData;
        if (response && typeof response === 'object') {
          if (response.books) {
            booksData = response.books;
          } else if (response.body && typeof response.body === 'string') {
            try {
              booksData = JSON.parse(response.body).books;
            } catch (e) {
              console.error('Error parsing response body:', e);
              booksData = [];
            }
          } else if (Array.isArray(response)) {
            booksData = response;
          } else {
            booksData = [];
          }
        } else {
          booksData = [];
        }
        
        console.log('Processed books data:', booksData);
        setBooks(booksData || []);
        return;
      } catch (apiClientError) {
        console.error('API client error, trying direct fetch:', apiClientError);
      }

      // Fallback to direct fetch if API client fails
      const response = await fetch('https://0108izew87.execute-api.us-east-1.amazonaws.com/dev/books', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Direct fetch response:', data);
      
      // Handle API Gateway response structure
      let booksData;
      if (data.body) {
        // API Gateway wraps the response in a body field
        booksData = JSON.parse(data.body);
      } else {
        // Direct response
        booksData = data;
      }
      
      setBooks(booksData.books || []);
      
    } catch (err) {
      console.error('Error fetching books:', err);
      
      // Fallback to hardcoded books if API fails
      const fallbackBooks: Book[] = [
        { title: 'rhia', filename: 'rhia.txt', type: 'uploaded_book' },
      ];
      
      setBooks(fallbackBooks);
      setError(err instanceof Error ? err.message : 'Failed to fetch books from API, using fallback list');
    } finally {
      setLoading(false);
    }
  };

  const refreshBooks = () => {
    fetchBooks();
  };

  useEffect(() => {
    fetchBooks();
  }, []);

  return { books, loading, error, refreshBooks };
};

export default useBooks; 