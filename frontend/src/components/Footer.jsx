import React from 'react';

export default function Footer() {
  return (
    <footer className="footer-wrapper">
      <div className="footer-brand">
        <span className="footer-logo">TasteFinder</span>
        <span className="footer-copyright">
          © 2026 TasteFinder AI. Curated for Bangalore.
        </span>
      </div>
      <div className="footer-links">
        <a href="#" className="footer-link">Privacy Policy</a>
        <a href="#" className="footer-link">Terms of Service</a>
        <a href="#" className="footer-link">AI Methodology</a>
        <a href="#" className="footer-link">Contact Support</a>
      </div>
    </footer>
  );
}
