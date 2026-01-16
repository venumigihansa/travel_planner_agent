import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom';
import AIAssistant from './components/AIAssistant';
import './App.css';

// Magic wand icon for AI Assistant
const MagicIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M14.5 2.5C14.5 3.05228 14.0523 3.5 13.5 3.5C12.9477 3.5 12.5 3.05228 12.5 2.5C12.5 1.94772 12.9477 1.5 13.5 1.5C14.0523 1.5 14.5 1.94772 14.5 2.5Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M8.5 16.5C8.5 17.0523 8.05228 17.5 7.5 17.5C6.94772 17.5 6.5 17.0523 6.5 16.5C6.5 15.9477 6.94772 15.5 7.5 15.5C8.05228 15.5 8.5 15.9477 8.5 16.5Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M3 7H5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M19 7H21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M7 3V5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M7 19V21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M18.4246 3.92871L16.5354 5.81792" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M3.92871 18.4246L5.81792 16.5354" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M16.2426 15.7574L5.94975 5.46457C5.7545 5.26932 5.7545 4.95274 5.94975 4.75749L7.75736 2.94989C7.95261 2.75463 8.26919 2.75463 8.46444 2.94989L18.7574 13.2428C18.9526 13.438 18.9526 13.7546 18.7574 13.9498L16.9498 15.7574C16.7545 15.9527 16.4379 15.9527 16.2426 15.7574Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M9.87866 7.87866L16.2426 14.2426" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

function AppContent() {
  const location = useLocation();

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <Link to="/assistant" className="logo">
            <div className="logo-container">
              <div className="logo-icon">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M2 17L12 22L22 17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M2 12L12 17L22 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <div className="logo-text">
                <h1>O2 Trips</h1>
                <span className="logo-subtitle">Your Travel Companion</span>
              </div>
            </div>
          </Link>

          <div className="user-header">
            <div className="user-info">
              <div className="user-avatar">G</div>
              <div className="user-details">
                <span className="welcome-text">Welcome,</span>
                <span className="user-name">Guest Traveler</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <nav className="app-nav">
        <div className="nav-content">
          <div className="nav-links">
            <Link 
              to="/assistant" 
              className={`nav-link ${location.pathname === '/assistant' ? 'active' : ''}`}
            >
              <MagicIcon />
              <span>AI Assistant</span>
            </Link>
          </div>
          
          <div className="nav-indicator">
            <div className="indicator-line"></div>
          </div>
        </div>
      </nav>

      <main className="app-main">
        <div className="main-content">
          <Routes>
            <Route path="/" element={<Navigate to="/assistant" replace />} />
            <Route path="/assistant" element={<AIAssistant />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}

export default App;
