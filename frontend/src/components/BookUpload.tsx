import React, { useState } from 'react';
import { uploadBook } from '../utils/api-client';
import './BookUpload.css';

interface BookUploadProps {
  onUploadSuccess?: () => void;
}

const BookUpload: React.FC<BookUploadProps> = ({ onUploadSuccess }) => {
  const [file, setFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError('');
      setSuccess('');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!file) {
      setError('Please select a file');
      return;
    }

    if (file.size > 50 * 1024 * 1024) { // 50MB limit
      setError('File size must be less than 50MB');
      return;
    }

    setIsLoading(true);
    setError('');
    setSuccess('');

    try {
      const reader = new FileReader();
      reader.onload = async (event) => {
        try {
          const content = event.target?.result as string;
          const base64Content = btoa(content);

          const bookData = {
            filename: file.name,
            content: base64Content,
            content_type: file.type || 'text/plain'
          };

          console.log('Uploading book:', file.name);
          const response = await uploadBook(bookData);
          console.log('Upload response:', response);

          setSuccess('Book uploaded successfully!');
          setFile(null);
          
          // Reset file input
          const fileInput = document.getElementById('file-input') as HTMLInputElement;
          if (fileInput) {
            fileInput.value = '';
          }

          if (onUploadSuccess) {
            onUploadSuccess();
          }

        } catch (err) {
          console.error('Error uploading book:', err);
          setError(err instanceof Error ? err.message : 'Failed to upload book');
        } finally {
          setIsLoading(false);
        }
      };

      reader.onerror = () => {
        setError('Error reading file');
        setIsLoading(false);
      };

      reader.readAsText(file);

    } catch (err) {
      console.error('Error processing file:', err);
      setError('Error processing file');
      setIsLoading(false);
    }
  };

  return (
    <div className="book-upload-container">
      <div className="book-upload-header">
        <h1>Upload New Books</h1>
        <p>Upload text files to add new books to the library</p>
      </div>

      <div className="book-upload-content">
        <div className="upload-section">
          <div className="file-upload-area">
            <label htmlFor="file-input" className="file-upload-label">
              <div className="upload-icon">📁</div>
              <div className="upload-text">
                <span className="upload-title">Choose a text file</span>
                <span className="upload-subtitle">or drag and drop here</span>
              </div>
            </label>
            <input
              type="file"
              id="file-input"
              accept=".txt,.md,.doc,.docx"
              onChange={handleFileChange}
              disabled={isLoading}
              className="file-input"
            />
          </div>

          {file && (
            <div className="selected-file">
              <div className="file-info">
                <span className="file-name">📄 {file.name}</span>
                <span className="file-size">({(file.size / 1024).toFixed(1)} KB)</span>
              </div>
            </div>
          )}

          <button
            onClick={handleSubmit}
            disabled={!file || isLoading}
            className="upload-button"
          >
            {isLoading ? 'Uploading...' : 'Upload Book'}
          </button>

          {error && (
            <div className="upload-message error">
              {error}
            </div>
          )}

          {success && (
            <div className="upload-message success">
              {success}
            </div>
          )}
        </div>

        <div className="upload-instructions">
          <h3>📋 Upload Instructions</h3>
          <ul>
            <li>Supported formats: <strong>.txt, .md, .doc, .docx</strong></li>
            <li>File size should be under <strong>50MB</strong></li>
            <li>Text should be in <strong>UTF-8 encoding</strong></li>
            <li>Books will be automatically processed for embeddings</li>
            <li>Processing may take a few minutes for large files</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default BookUpload; 