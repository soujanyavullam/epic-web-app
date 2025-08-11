import React from 'react';
import useBooks from '../hooks/useBooks';

interface BookSelectorProps {
  selectedBook: string;
  onBookSelect: (bookTitle: string) => void;
}

const BookSelector: React.FC<BookSelectorProps> = ({ selectedBook, onBookSelect }) => {
  const { books, loading, error, refreshBooks } = useBooks();

  if (loading) {
    return (
      <div className="book-selector">
        <label>Select the context:</label>
        <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
          Loading books...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="book-selector">
        <label>Select:</label>
        <div style={{ 
          padding: '15px', 
          background: '#fee', 
          color: '#c53030', 
          borderRadius: '8px',
          marginTop: '10px'
        }}>
          Error loading books: {error}
          <button 
            onClick={refreshBooks} 
            style={{
              marginLeft: '10px',
              padding: '5px 10px',
              background: '#c53030',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="book-selector">
      <label htmlFor="book-select">
        Select the context:
      </label>
      <select
        id="book-select"
        value={selectedBook}
        onChange={(e) => onBookSelect(e.target.value)}
      >
        <option value="">Choose a book...</option>
        {books.map((book) => (
          <option key={book.title} value={book.title}>
            {book.title}
          </option>
        ))}
      </select>
      {books.length === 0 && (
        <div style={{ 
          padding: '15px', 
          background: '#f0f9ff', 
          color: '#0369a1', 
          borderRadius: '8px',
          marginTop: '10px',
          textAlign: 'center'
        }}>
          No books available. Please upload some books first.
        </div>
      )}
    </div>
  );
};

export default BookSelector; 