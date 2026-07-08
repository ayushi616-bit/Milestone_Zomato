import React from 'react';

export default function ErrorStateView({ errorMessage, onRetry }) {
  if (!errorMessage) return null;

  return (
    <div className="error-toast">
      <div className="error-toast-card">
        <span className="material-symbols-outlined error-toast-icon">
          error
        </span>
        <div className="error-toast-text">
          Something went wrong: {errorMessage}. Check your connection and try again.
        </div>
        {onRetry && (
          <button className="error-toast-retry" onClick={onRetry}>
            Retry
          </button>
        )}
      </div>
    </div>
  );
}
