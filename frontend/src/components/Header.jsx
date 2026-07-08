import React from 'react';

export default function Header({ activeTab, setActiveTab }) {
  return (
    <header className="header-wrapper">
      <div className="header-container">
        <div className="brand-logo" onClick={() => setActiveTab('explore')}>
          TasteFinder
        </div>
        <nav className="header-nav">
          <span 
            className={`nav-link ${activeTab === 'explore' ? 'active' : ''}`}
            onClick={() => setActiveTab('explore')}
          >
            Explore
          </span>
          <span 
            className={`nav-link ${activeTab === 'search' ? 'active' : ''}`}
            onClick={() => setActiveTab('search')}
          >
            Search
          </span>
          <span 
            className={`nav-link ${activeTab === 'saved' ? 'active' : ''}`}
            onClick={() => setActiveTab('saved')}
          >
            Saved
          </span>
          <span 
            className={`nav-link ${activeTab === 'history' ? 'active' : ''}`}
            onClick={() => setActiveTab('history')}
          >
            History
          </span>
        </nav>
        <div className="header-actions">
          <button className="action-btn">
            <span className="material-symbols-outlined">location_on</span>
          </button>
          <button className="action-btn">
            <span className="material-symbols-outlined">account_circle</span>
          </button>
        </div>
      </div>
    </header>
  );
}
