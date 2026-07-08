import React from 'react';

export default function SearchForm({ 
  locations, 
  formData, 
  setFormData, 
  onSubmit 
}) {
  const handleLocationChange = (e) => {
    setFormData({ ...formData, location: e.target.value });
  };

  const handleBudgetSelect = (val) => {
    setFormData({ ...formData, budget: val });
  };

  const handleCuisineChange = (e) => {
    setFormData({ ...formData, cuisine: e.target.value });
  };

  const selectCuisineChip = (cuisine) => {
    setFormData({ ...formData, cuisine });
  };

  const handleRatingChange = (e) => {
    setFormData({ ...formData, minRating: parseFloat(e.target.value) });
  };

  const handleResultsStep = (step) => {
    const newVal = Math.max(1, Math.min(20, formData.results + step));
    setFormData({ ...formData, results: newVal });
  };

  const handlePreferencesChange = (e) => {
    setFormData({ ...formData, additionalPreferences: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit();
  };

  const ratingPct = (formData.minRating / 5.0) * 100;

  return (
    <form className="form-card" onSubmit={handleSubmit}>
      <div className="form-row-2">
        {/* Location Dropdown */}
        <div className="form-group">
          <label className="form-label">Location</label>
          <div className="input-container">
            <span className="material-symbols-outlined input-icon">location_on</span>
            <select 
              className="form-select" 
              value={formData.location} 
              onChange={handleLocationChange}
            >
              {locations.map((loc) => (
                <option key={loc} value={loc}>
                  {loc.charAt(0).toUpperCase() + loc.slice(1)}, Bangalore
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Budget Segmented Controls */}
        <div className="form-group">
          <label className="form-label">Budget</label>
          <div className="budget-segmented">
            <span 
              className={`budget-btn ${formData.budget === 'low' ? 'active' : ''}`}
              onClick={() => handleBudgetSelect('low')}
            >
              ₹
            </span>
            <span 
              className={`budget-btn ${formData.budget === 'medium' ? 'active' : ''}`}
              onClick={() => handleBudgetSelect('medium')}
            >
              ₹₹
            </span>
            <span 
              className={`budget-btn ${formData.budget === 'high' ? 'active' : ''}`}
              onClick={() => handleBudgetSelect('high')}
            >
              ₹₹₹
            </span>
          </div>
        </div>
      </div>

      {/* Cuisine Search Box */}
      <div className="form-group">
        <label className="form-label">Cuisine / Craving</label>
        <div className="input-container">
          <span className="material-symbols-outlined input-icon">restaurant_menu</span>
          <input 
            type="text" 
            className="form-input" 
            placeholder="e.g., Italian, Chinese, Filter Coffee..." 
            value={formData.cuisine}
            onChange={handleCuisineChange}
            required
          />
        </div>
        {/* Quick Suggestion Chips */}
        <div className="suggestion-chips no-scrollbar">
          {['South Indian', 'Craft Beer', 'Pan Asian', 'Dessert'].map((chip) => (
            <span 
              key={chip} 
              className={`cuisine-chip ${formData.cuisine === chip ? 'selected' : ''}`}
              onClick={() => selectCuisineChip(chip)}
            >
              {chip}
            </span>
          ))}
        </div>
      </div>

      <div className="form-row-2">
        {/* Minimum Rating Slider */}
        <div className="form-group">
          <label className="form-label" style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>Minimum Rating</span>
            <span style={{ color: 'var(--tertiary-fixed-dim)', fontWeight: '700' }}>
              {formData.minRating.toFixed(1)}+
            </span>
          </label>
          <div className="slider-container">
            <span className="material-symbols-outlined" style={{ color: 'var(--surface-container-highest)' }}>
              star
            </span>
            <div className="slider-wrapper">
              <div className="slider-track"></div>
              <div 
                className="slider-track-active" 
                style={{ width: `${ratingPct}%` }}
              ></div>
              <input 
                type="range" 
                min="0.0" 
                max="5.0" 
                step="0.5" 
                className="slider-input" 
                value={formData.minRating}
                onChange={handleRatingChange}
              />
              <div 
                className="slider-thumb" 
                style={{ left: `${ratingPct}%` }}
              ></div>
            </div>
            <span className="material-symbols-outlined fill" style={{ color: 'var(--tertiary-fixed-dim)' }}>
              star
            </span>
          </div>
        </div>

        {/* Results to Show Counter */}
        <div className="form-group" style={{ alignItems: 'center' }}>
          <label className="form-label" style={{ alignSelf: 'stretch', textAlign: 'center' }}>
            Results to show
          </label>
          <div className="stepper-container">
            <span 
              className="stepper-btn" 
              onClick={() => handleResultsStep(-1)}
            >
              <span className="material-symbols-outlined">remove</span>
            </span>
            <span className="stepper-value">{formData.results}</span>
            <span 
              className="stepper-btn" 
              onClick={() => handleResultsStep(1)}
            >
              <span className="material-symbols-outlined">add</span>
            </span>
          </div>
        </div>
      </div>

      {/* Additional Preferences Textarea */}
      <div className="form-group textarea-container">
        <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span className="material-symbols-outlined" style={{ color: 'var(--tertiary-fixed-dim)', fontSize: '16px' }}>
            spark
          </span>
          AI Instructions
        </label>
        <textarea 
          className="form-textarea" 
          placeholder="e.g., 'Quiet place for a date', 'Dog-friendly with good wifi', 'Open past midnight'" 
          rows="2"
          value={formData.additionalPreferences}
          onChange={handlePreferencesChange}
        />
      </div>

      {/* Primary CTA button */}
      <button type="submit" className="submit-btn">
        <span className="material-symbols-outlined">magic_button</span>
        Get Recommendations
      </button>
    </form>
  );
}
