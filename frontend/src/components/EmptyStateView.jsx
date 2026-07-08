import React from 'react';

export default function EmptyStateView({ onAdjustFilters }) {
  return (
    <div className="empty-state-wrapper">
      <div className="empty-state-card">
        <div className="empty-icon-circle">
          <span className="material-symbols-outlined empty-icon">
            restaurant_menu
          </span>
        </div>
        <h2 className="empty-headline">No restaurants match</h2>
        <p className="empty-subtext">
          We couldn't find any spots matching your exact cravings. Try loosening your filters or exploring a different vibe.
        </p>
        <button className="empty-btn" onClick={onAdjustFilters}>
          Adjust filters
        </button>
      </div>
    </div>
  );
}
