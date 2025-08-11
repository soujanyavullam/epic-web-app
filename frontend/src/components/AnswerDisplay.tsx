import React from 'react';

interface AnswerDisplayProps {
  answer: {
    answer: string;
  };
}

const AnswerDisplay: React.FC<AnswerDisplayProps> = ({ answer }) => {
  return (
    <div className="answer-display">
      <div className="answer-section">
        <h3>Answer:</h3>
        <div className="answer-text">
          {answer.answer}
        </div>
      </div>
    </div>
  );
};

export default AnswerDisplay; 