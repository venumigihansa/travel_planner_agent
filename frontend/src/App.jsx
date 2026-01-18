import React, { useEffect, useMemo, useRef, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom';
import { SignedIn, SignedOut, SignIn, SignUp, UserButton, useAuth, useUser } from '@clerk/clerk-react';
import AIAssistant from './components/AIAssistant';
import InterestsModal from './components/InterestsModal';
import { createUserProfileService } from './services/userProfileService';
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

const bestAvailableName = (user) => {
  if (!user) {
    return null;
  }
  if (user.fullName) {
    return user.fullName;
  }
  const combined = [user.firstName, user.lastName].filter(Boolean).join(' ').trim();
  if (combined) {
    return combined;
  }
  if (user.username) {
    return user.username;
  }
  return user.primaryEmailAddress?.emailAddress || null;
};

const AuthScreen = () => {
  const [showSignUp, setShowSignUp] = useState(false);

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="auth-copy">
          <h1>O2 Trips</h1>
          <p>Sign in to personalize your next stay and get tailored hotel picks.</p>
          <button
            type="button"
            className="auth-toggle"
            onClick={() => setShowSignUp((prev) => !prev)}
          >
            {showSignUp ? 'Already have an account? Sign in' : 'New here? Create an account'}
          </button>
        </div>
        <div className="auth-widget">
          {showSignUp ? (
            <SignUp routing="virtual" />
          ) : (
            <SignIn routing="virtual" />
          )}
        </div>
      </div>
    </div>
  );
};

const SignedInApp = () => {
  const location = useLocation();
  const { user, isLoaded } = useUser();
  const { getToken } = useAuth();
  const profileService = useMemo(() => createUserProfileService(getToken), [getToken]);
  const [profile, setProfile] = useState({ interests: [], username: null });
  const [showInterestsModal, setShowInterestsModal] = useState(false);
  const initRef = useRef(null);

  useEffect(() => {
    if (!isLoaded || !user) {
      return;
    }
    if (initRef.current === user.id) {
      return;
    }
    initRef.current = user.id;
    const initializeProfile = async () => {
      try {
        const username = bestAvailableName(user);
        await profileService.createOrUpdateUser({ userId: user.id, username });
        const fetched = await profileService.fetchUserProfile(user.id);
        setProfile(fetched);
        if (!fetched.interests || fetched.interests.length === 0) {
          setShowInterestsModal(true);
        }
      } catch (error) {
        console.error('Failed to initialize user profile:', error);
      }
    };
    initializeProfile();
  }, [isLoaded, profileService, user]);

  const handleSaveInterests = async (interests) => {
    if (!user) {
      return;
    }
    try {
      const updated = await profileService.updateInterests(user.id, interests);
      setProfile(updated);
      setShowInterestsModal(false);
    } catch (error) {
      console.error('Failed to save interests:', error);
    }
  };

  const handleSkipInterests = () => {
    setShowInterestsModal(false);
  };

  const displayName = profile.username || bestAvailableName(user) || 'Traveler';
  const avatarLetter = displayName ? displayName.charAt(0).toUpperCase() : 'T';

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
              <div className="user-avatar">{avatarLetter}</div>
              <div className="user-details">
                <span className="welcome-text">Welcome,</span>
                <span className="user-name">{displayName}</span>
              </div>
            </div>
            <UserButton />
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
            <Route
              path="/assistant"
              element={<AIAssistant userId={user?.id} userName={displayName} />}
            />
          </Routes>
        </div>
      </main>

      <InterestsModal
        isOpen={showInterestsModal}
        initialInterests={profile.interests}
        onSave={handleSaveInterests}
        onSkip={handleSkipInterests}
      />
    </div>
  );
};

function AppContent() {
  return (
    <>
      <SignedOut>
        <AuthScreen />
      </SignedOut>
      <SignedIn>
        <SignedInApp />
      </SignedIn>
    </>
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
