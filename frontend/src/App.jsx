import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import Footer from './components/Footer';
import HeroSection from './components/HeroSection';
import SearchForm from './components/SearchForm';
import LoaderView from './components/LoaderView';
import ResultsView from './components/ResultsView';
import EmptyStateView from './components/EmptyStateView';
import ErrorStateView from './components/ErrorStateView';

// API base URL configuration (FastAPI running on port 8000)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default function App() {
  const [activeTab, setActiveTab] = useState('explore');
  const [locations, setLocations] = useState(['basavanagudi', 'indiranagar', 'koramangala', 'hsr']);
  const [formData, setFormData] = useState({
    location: 'basavanagudi',
    budget: 'medium',
    cuisine: '',
    minRating: 3.0,
    results: 5,
    additionalPreferences: '',
  });

  const [isLoading, setIsLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);
  const [searchCriteria, setSearchCriteria] = useState(null);

  // Fetch location dropdown choices from FastAPI backend
  useEffect(() => {
    fetch(`${API_BASE_URL}/api/locations`)
      .then((res) => {
        if (!res.ok) throw new Error('API server returned error');
        return res.json();
      })
      .then((data) => {
        if (data && data.length > 0) {
          setLocations(data);
          // Set first available location as default
          setFormData((prev) => ({ ...prev, location: data[0] }));
        }
      })
      .catch((err) => {
        console.error('Failed to load locations from server:', err);
        // Fallback to local default locations array if backend is down
      });
  }, []);

  const triggerSearch = async (overrideData = null) => {
    const dataToSubmit = overrideData || formData;
    
    setError(null);
    setIsLoading(true);
    setLoadingStep(1);
    setActiveTab('search');

    // Simulate animated transition progress matching standard loader step states
    const stepTimer1 = setTimeout(() => setLoadingStep(2), 800);
    const stepTimer2 = setTimeout(() => setLoadingStep(3), 1600);

    try {
      const apiResponse = await fetch(`${API_BASE_URL}/api/recommend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          location: dataToSubmit.location,
          budget: dataToSubmit.budget,
          cuisine: dataToSubmit.cuisine || 'Any',
          min_rating: dataToSubmit.minRating,
          additional_preferences: dataToSubmit.additionalPreferences || null,
          results: dataToSubmit.results,
        }),
      });

      if (!apiResponse.ok) {
        throw new Error(await apiResponse.text() || 'Failed to fetch recommendations');
      }

      const resData = await apiResponse.json();

      // Ensure loading step finishes at least briefly for visual flow
      setTimeout(() => {
        setResponse(resData);
        setSearchCriteria({ ...dataToSubmit });
        setIsLoading(false);
        setLoadingStep(0);
      }, 2400);

    } catch (err) {
      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);
      setError(err.message || 'API request failed');
      setIsLoading(false);
      setLoadingStep(0);
    }
  };

  const handleRetry = () => {
    triggerSearch();
  };

  const handleAdjustFilters = () => {
    setActiveTab('explore');
    setResponse(null);
  };

  return (
    <div className="app-container">
      {/* Top Header Navbar */}
      <Header activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Body Layout */}
      <main className="main-content">
        {activeTab === 'explore' && (
          <div className="home-grid">
            <HeroSection selectedLocation={formData.location} />
            <SearchForm 
              locations={locations}
              formData={formData}
              setFormData={setFormData}
              onSubmit={triggerSearch}
            />
          </div>
        )}

        {activeTab === 'search' && (
          <>
            {isLoading ? (
              <LoaderView step={loadingStep} />
            ) : response ? (
              response.recommendations.length === 0 ? (
                <EmptyStateView onAdjustFilters={handleAdjustFilters} />
              ) : (
                <ResultsView 
                  response={response} 
                  searchCriteria={searchCriteria} 
                />
              )
            ) : (
              <EmptyStateView onAdjustFilters={handleAdjustFilters} />
            )}
          </>
        )}

        {activeTab === 'saved' && (
          <div style={{ textAlign: 'center', padding: '64px 0' }}>
            <span className="material-symbols-outlined" style={{ fontSize: '64px', color: 'var(--primary)', marginBottom: '16px' }}>
              bookmark_heart
            </span>
            <h2 className="heading-lg" style={{ fontSize: '24px', marginBottom: '8px' }}>Saved Recommendations</h2>
            <p className="body-md">Bookmarks you save will appear here for offline access.</p>
          </div>
        )}

        {activeTab === 'history' && (
          <div style={{ textAlign: 'center', padding: '64px 0' }}>
            <span className="material-symbols-outlined" style={{ fontSize: '64px', color: 'var(--primary)', marginBottom: '16px' }}>
              history
            </span>
            <h2 className="heading-lg" style={{ fontSize: '24px', marginBottom: '8px' }}>Recommendation History</h2>
            <p className="body-md">Your recent search query history is currently empty.</p>
          </div>
        )}
      </main>

      {/* Mobile Bottom Navigation Bar */}
      <nav className="mobile-nav-bar">
        <div 
          className={`mobile-nav-item ${activeTab === 'explore' ? 'active' : ''}`}
          onClick={() => setActiveTab('explore')}
        >
          <div className="mobile-nav-bg">
            <span className="material-symbols-outlined">explore</span>
          </div>
          <span>Discover</span>
        </div>
        <div 
          className={`mobile-nav-item ${activeTab === 'search' ? 'active' : ''}`}
          onClick={() => setActiveTab('search')}
        >
          <div className="mobile-nav-bg">
            <span className="material-symbols-outlined">search</span>
          </div>
          <span>Search</span>
        </div>
        <div 
          className={`mobile-nav-item ${activeTab === 'saved' ? 'active' : ''}`}
          onClick={() => setActiveTab('saved')}
        >
          <div className="mobile-nav-bg">
            <span className="material-symbols-outlined">bookmark</span>
          </div>
          <span>Favorites</span>
        </div>
        <div 
          className={`mobile-nav-item ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          <div className="mobile-nav-bg">
            <span className="material-symbols-outlined">person</span>
          </div>
          <span>Profile</span>
        </div>
      </nav>

      {/* Red Connections Error Alert */}
      <ErrorStateView errorMessage={error} onRetry={handleRetry} />

      {/* Footer Section */}
      <Footer />
    </div>
  );
}
