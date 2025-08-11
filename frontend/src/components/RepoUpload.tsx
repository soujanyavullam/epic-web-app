import React, { useState } from 'react';
import { uploadRepo } from '../utils/api-client';
import './RepoUpload.css';

interface RepoUploadProps {
  onUploadSuccess?: (bookTitle: string) => void;
}

const RepoUpload: React.FC<RepoUploadProps> = ({ onUploadSuccess }) => {
  const [githubUrl, setGithubUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [uploadProgress, setUploadProgress] = useState('');

  const validateGithubUrl = (url: string): boolean => {
    const githubPattern = /^https?:\/\/github\.com\/[^\/]+\/[^\/]+(?:\/.*)?$/;
    return githubPattern.test(url);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!githubUrl.trim()) {
      setError('Please enter a GitHub URL');
      return;
    }

    if (!validateGithubUrl(githubUrl)) {
      setError('Please enter a valid GitHub repository URL (e.g., https://github.com/owner/repo)');
      return;
    }

    setIsLoading(true);
    setError('');
    setSuccess('');
    setUploadProgress('Starting repository analysis...');

    try {
      console.log('Making request to upload repository:', githubUrl.trim());

      const response = await uploadRepo(githubUrl.trim());
      console.log('Success response:', response);

      setSuccess(`Repository documentation generated successfully!`);
      setUploadProgress(`Processed ${response.chunks_processed} chunks from ${response.owner}/${response.repo}`);

      // Clear the form
      setGithubUrl('');

      // Notify parent component
      if (onUploadSuccess) {
        onUploadSuccess(response.book_title);
      }

    } catch (err) {
      console.error('Upload error:', err);
      setError(err instanceof Error ? err.message : 'An error occurred while processing the repository');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setGithubUrl(e.target.value);
    setError('');
    setSuccess('');
  };

  return (
    <div className="repo-upload">
      <div className="repo-upload-container">
        <h2>Upload GitHub Repository</h2>
        <p className="repo-upload-description">
          Enter a public GitHub repository URL to automatically generate documentation and make it available for Q&A.
        </p>

        <form onSubmit={handleSubmit} className="repo-upload-form">
          <div className="form-group">
            <label htmlFor="github-url">GitHub Repository URL</label>
            <input
              type="url"
              id="github-url"
              value={githubUrl}
              onChange={handleUrlChange}
              placeholder="https://github.com/owner/repository"
              disabled={isLoading}
              className="github-url-input"
            />
            <small className="form-help">
              Enter the URL of a public GitHub repository (e.g., https://github.com/facebook/react)
            </small>
          </div>

          {error && (
            <div className="error-message">
              <span className="error-icon">⚠️</span>
              {error}
            </div>
          )}

          {success && (
            <div className="success-message">
              <span className="success-icon">✅</span>
              {success}
            </div>
          )}

          {isLoading && (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p className="loading-text">{uploadProgress}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading || !githubUrl.trim()}
            className="upload-button"
          >
            {isLoading ? 'Processing Repository...' : 'Generate Documentation'}
          </button>
        </form>

        <div className="repo-upload-info">
          <h3>What happens when you upload a repository?</h3>
          <ul>
            <li>📖 <strong>README Analysis</strong> - Extracts and processes README files</li>
            <li>🏗️ <strong>Project Structure</strong> - Analyzes the repository structure</li>
            <li>📝 <strong>Code Documentation</strong> - Extracts comments and documentation from code</li>
            <li>⚙️ <strong>Configuration Files</strong> - Processes package.json, requirements.txt, etc.</li>
            <li>🤖 <strong>AI Processing</strong> - Generates embeddings for intelligent Q&A</li>
            <li>📚 <strong>Knowledge Base</strong> - Makes the repository available for questions</li>
          </ul>
        </div>

        <div className="repo-upload-examples">
          <h3>Example Repositories</h3>
          <div className="example-repos">
            <button
              type="button"
              onClick={() => setGithubUrl('https://github.com/facebook/react')}
              className="example-repo"
            >
              React
            </button>
            <button
              type="button"
              onClick={() => setGithubUrl('https://github.com/microsoft/vscode')}
              className="example-repo"
            >
              VS Code
            </button>
            <button
              type="button"
              onClick={() => setGithubUrl('https://github.com/tensorflow/tensorflow')}
              className="example-repo"
            >
              TensorFlow
            </button>
            <button
              type="button"
              onClick={() => setGithubUrl('https://github.com/kubernetes/kubernetes')}
              className="example-repo"
            >
              Kubernetes
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RepoUpload; 