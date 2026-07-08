export default function ResultsView({ response, searchCriteria }) {
  const { summary, recommendations, relaxed } = response;

  return (
    <div className="results-wrapper">
      {/* Degraded AI Fallback Warning Banner */}
      {relaxed && (
        <div className="fallback-alert">
          <span className="material-symbols-outlined fallback-icon">info</span>
          <div>
            <p className="body-md" style={{ color: '#ffffff', fontWeight: '500' }}>
              <strong>AI ranking unavailable</strong> — showing top-rated matches from your filters.
            </p>
          </div>
        </div>
      )}

      {/* AI Summary Banner */}
      {summary && (
        <section className="summary-banner">
          <span className="material-symbols-outlined summary-icon">auto_awesome</span>
          <div className="summary-text">{summary}</div>
        </section>
      )}

      {/* Fallback Headers if relaxed */}
      {relaxed && (
        <div className="fallback-title-block">
          <h2 className="fallback-title">Top Rated Nearby</h2>
          <p className="body-md">Showing standard results based on ratings and distance.</p>
        </div>
      )}

      {/* Recommendation Card List */}
      <section className="cards-container">
        {recommendations.map((rec) => {
          const ratingVal = rec.rating.replace('★', '');

          return (
            <article key={rec.rank} className="recommendation-card">
              {/* Card Details */}
              <div className="card-details-section">
                <div>
                  {/* Rank Badge */}
                  {rec.rank === 1 ? (
                    <div className="card-badge gold">
                      <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>
                        military_tech
                      </span>
                      #1 Pick
                    </div>
                  ) : (
                    <div className="card-badge default">
                      #{rec.rank} Pick
                    </div>
                  )}

                  <div className="card-header-row">
                    <h3 className="restaurant-name">{rec.name}</h3>
                    <div className="rating-pill">
                      <span>{ratingVal}</span>
                      <span className="material-symbols-outlined rating-star-icon">star</span>
                    </div>
                  </div>
                  
                  {/* Location subtitle */}
                  <p className="body-md" style={{ color: 'var(--on-surface-variant)', marginTop: '4px' }}>
                    Bangalore, {rec.location || searchCriteria.location}
                  </p>

                  <div className="card-meta-chips">
                    <span className="meta-chip">{rec.cost}</span>
                    {rec.cuisine.split(',').map((c) => {
                      const cleanCuisine = c.trim();
                      if (!cleanCuisine) return null;
                      return (
                        <span key={cleanCuisine} className="meta-chip">
                          {cleanCuisine}
                        </span>
                      );
                    })}
                  </div>
                </div>

                {/* AI Explanation block */}
                <div className="explanation-box">
                  <span className="material-symbols-outlined explanation-icon">auto_awesome</span>
                  <div>
                    <strong className="explanation-title">Why we picked this</strong>
                    <p className="explanation-text">{rec.explanation}</p>
                  </div>
                </div>
              </div>
            </article>
          );
        })}
      </section>

      {/* Accordion Search Details */}
      {searchCriteria && (
        <details className="accordion-details">
          <summary className="accordion-summary">
            Search details
            <span className="material-symbols-outlined accordion-arrow">expand_more</span>
          </summary>
          <div className="accordion-content">
            <p><strong>Location:</strong> {searchCriteria.location}</p>
            <p><strong>Cuisine:</strong> {searchCriteria.cuisine || 'Any'}</p>
            <p><strong>Budget:</strong> {searchCriteria.budget?.toUpperCase()}</p>
            <p><strong>Minimum Rating:</strong> {searchCriteria.minRating}★</p>
            {searchCriteria.additionalPreferences && (
              <p><strong>Vibe / Notes:</strong> {searchCriteria.additionalPreferences}</p>
            )}
            <p><strong>Results Cap:</strong> {searchCriteria.results}</p>
          </div>
        </details>
      )}
    </div>
  );
}
