import React, { useState, useEffect } from 'react';
import BookSelector from './BookSelector';
import QuestionForm from './QuestionForm';
import AnswerDisplay from './AnswerDisplay';
import LoadingSpinner from './LoadingSpinner';
import { queryBook } from '../utils/api-client';
import './BookQA.css';

interface Answer {
  answer: string;
}

const BookQA: React.FC = () => {
  const [selectedBook, setSelectedBook] = useState<string>('');
  const [question, setQuestion] = useState<string>('');
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  const handleQuestionSubmit = async (questionText: string) => {
    if (!selectedBook) {
      setError('Please select a book first');
      return;
    }

    if (!questionText.trim()) {
      setError('Please enter a question');
      return;
    }

    try {
      setIsLoading(true);
      setError('');
      setAnswer(null);

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
      setIsLoading(false);
    }
  };

  const handleBookSelect = (bookTitle: string) => {
    setSelectedBook(bookTitle);
    setAnswer(null);
    setError('');
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
          disabled={isLoading || !selectedBook}
        />

        {isLoading && (
          <div className="loading-spinner">
            <div className="spinner"></div>
            <p className="loading-message">Processing your question...</p>
          </div>
        )}

        {answer && !isLoading && (
          <AnswerDisplay answer={answer} />
        )}
      </div>
    </div>
  );
};

export default BookQA; 