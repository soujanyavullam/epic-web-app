import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// Polyfill for global object (required by Amazon Cognito)
declare global {
  var global: any;
}

if (typeof global === 'undefined') {
  (window as any).global = window;
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
