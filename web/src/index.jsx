import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

/**
 * Entry point for the React application
 * Renders the App component into the DOM
 */
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);