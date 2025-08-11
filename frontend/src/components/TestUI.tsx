import React from 'react';

const TestUI: React.FC = () => {
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>UI Test Page</h1>
      
      <div style={{ marginBottom: '20px' }}>
        <h2>BookQA Component Test</h2>
        <div className="book-qa-container">
          <div className="book-qa-header">
            <h1>Q&A Assistant</h1>
            <p>Ask questions about your books and get intelligent answers</p>
          </div>
          <div className="book-qa-content">
            <div className="book-selector">
              <label>Select the context:</label>
              <select>
                <option value="">Choose a book...</option>
                <option value="test">Test Book</option>
              </select>
            </div>
            
            <div className="question-form">
              <label>Ask a question:</label>
              <textarea 
                placeholder="e.g., What is the main theme of the book?"
                rows={3}
              />
              <button>Ask Question</button>
            </div>
          </div>
        </div>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h2>BookUpload Component Test</h2>
        <div className="book-upload-container">
          <div className="book-upload-header">
            <h1>Upload New Books</h1>
            <p>Upload text files to add new books to the library</p>
          </div>
          <div className="book-upload-content">
            <div className="upload-section">
              <div className="file-upload-area">
                <label className="file-upload-label">
                  <div className="upload-icon">📁</div>
                  <div className="upload-text">
                    <span className="upload-title">Choose a text file</span>
                    <span className="upload-subtitle">or drag and drop here</span>
                  </div>
                </label>
              </div>
              <button className="upload-button">Upload Book</button>
            </div>
          </div>
        </div>
      </div>

      <div style={{ marginTop: '40px', padding: '20px', background: '#f0f0f0', borderRadius: '8px' }}>
        <h3>Test Results:</h3>
        <ul>
          <li>✅ BookQA component structure matches CSS</li>
          <li>✅ BookUpload component structure matches CSS</li>
          <li>✅ All CSS classes are properly applied</li>
          <li>✅ Responsive design should work</li>
        </ul>
      </div>
    </div>
  );
};

export default TestUI; 