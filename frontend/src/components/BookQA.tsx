import React, { useState } from 'react';
import BookSelector from './BookSelector';
import QuestionForm from './QuestionForm';
import AnswerDisplay from './AnswerDisplay';
import { queryBook } from '../utils/api-client';
import './BookQA.css';

interface Answer {
  answer: string;
}

const BookQA: React.FC = () => {
  const [selectedBook, setSelectedBook] = useState<string>('');
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');

  const handleBookSelect = (bookTitle: string) => {
    setSelectedBook(bookTitle);
    setAnswer(null);
    setError('');
  };

  const handleQuestionSubmit = async (questionText: string) => {
    if (!selectedBook) {
      setError('Please select a book first');
      return;
    }

    if (!questionText.trim()) {
      setError('Please enter a question');
      return;
    }

    setLoading(true);
    setError('');
    setAnswer(null);

    try {
      console.log('Submitting question:', { question: questionText, book_title: selectedBook });
      
      const response = await queryBook(questionText, selectedBook);
      console.log('Query response:', response);
      
      // Handle both direct response and wrapped response
      const answerData = response.answer || response.body?.answer || response;
      setAnswer({ answer: answerData || 'No answer received' });
      
    } catch (err) {
      console.error('Error submitting question:', err);
      setError(err instanceof Error ? err.message : 'Failed to get answer. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="book-qa-container">
      <div className="book-qa-header">
        <h1>Q&A Assistant</h1>
        <p>Ask questions about your books and get intelligent answers</p>
      </div>

      <div className="book-qa-content">
        {error && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            {error}
          </div>
        )}

        <BookSelector 
          selectedBook={selectedBook}
          onBookSelect={handleBookSelect}
        />

        <QuestionForm 
          onSubmit={handleQuestionSubmit}
          disabled={loading || !selectedBook}
        />

        {loading && (
          <div className="loading-spinner">
            <div className="spinner"></div>
          </div>
        )}

        {answer && !loading && (
          <AnswerDisplay answer={answer} />
        )}
      </div>
    </div>
  );
};

export default BookQA; 