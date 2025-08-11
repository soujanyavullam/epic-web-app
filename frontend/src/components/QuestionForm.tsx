import React, { useState } from 'react';

interface QuestionFormProps {
  onSubmit: (question: string) => void;
  disabled?: boolean;
}

const QuestionForm: React.FC<QuestionFormProps> = ({ onSubmit, disabled = false }) => {
  const [question, setQuestion] = useState<string>('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (question.trim() && !disabled) {
      onSubmit(question);
      setQuestion('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="question-form">
      <label htmlFor="question-input">
        Ask a question:
      </label>
      <textarea
        id="question-input"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="e.g., What is the main theme of the book? Who are the main characters?"
        rows={3}
        disabled={disabled}
      />
      <button
        type="submit"
        disabled={disabled || !question.trim()}
      >
        {disabled ? 'Loading...' : 'Ask Question'}
      </button>
    </form>
  );
};

export default QuestionForm; 