import React from 'react';

export default function LoaderView({ step }) {
  // Config class and icon mappings for the loading checklist steps
  const getStepClass = (itemStep) => {
    if (step > itemStep) return 'completed';
    if (step === itemStep) return 'active';
    return 'pending';
  };

  const getStepIcon = (itemStep) => {
    if (step > itemStep) return 'check_circle';
    if (step === itemStep) return 'auto_awesome';
    return itemStep === 3 ? 'list_alt' : 'auto_awesome';
  };

  return (
    <div style={{ position: 'relative', width: '100%', minHeight: '80vh' }}>
      {/* Background Skeletons for visual layout indicator */}
      <div className="skeletons-bg">
        {[1, 2, 3].map((i) => (
          <div key={i} className="skeleton-card">
            <div className="skeleton-image skeleton-shimmer"></div>
            <div className="skeleton-text-1 skeleton-shimmer"></div>
            <div className="skeleton-text-2 skeleton-shimmer"></div>
          </div>
        ))}
      </div>

      {/* Main Centered Loading Modal Overlay */}
      <div className="loading-overlay">
        <div className="loading-card">
          <div className="loader-ring"></div>
          <h2 className="form-label" style={{ fontSize: '20px', marginBottom: '8px', color: '#ffffff' }}>
            Finding and ranking restaurants...
          </h2>
          <p className="body-md" style={{ marginBottom: '16px' }}>
            Curating the best of Bangalore just for you.
          </p>

          <div className="loading-steps">
            {/* Step 1: Filtering */}
            <div className={`step-item ${getStepClass(1)}`}>
              <span className={`material-symbols-outlined step-icon ${step === 1 ? 'spin' : ''}`}>
                {getStepIcon(1)}
              </span>
              <span>Filtering matches</span>
            </div>

            {/* Step 2: Asking AI */}
            <div className={`step-item ${getStepClass(2)}`}>
              <span className={`material-symbols-outlined step-icon ${step === 2 ? 'spin' : ''}`}>
                {getStepIcon(2)}
              </span>
              <span>Asking AI</span>
            </div>

            {/* Step 3: Preparing list */}
            <div className={`step-item ${getStepClass(3)}`}>
              <span className={`material-symbols-outlined step-icon ${step === 3 ? 'spin' : ''}`}>
                {getStepIcon(3)}
              </span>
              <span>Preparing your list</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
