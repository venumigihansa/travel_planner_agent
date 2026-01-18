import React, { useEffect, useMemo, useState } from 'react';

const defaultInterests = [
  'Beach',
  'City breaks',
  'Mountains',
  'Museums',
  'Food & wine',
  'Nightlife',
  'Shopping',
  'Family friendly',
  'Wellness & spa',
  'Adventure',
  'Budget stays',
  'Luxury stays'
];

const InterestsModal = ({ isOpen, initialInterests, onSave, onSkip }) => {
  const [selected, setSelected] = useState([]);
  const options = useMemo(() => defaultInterests, []);

  useEffect(() => {
    if (isOpen) {
      setSelected(initialInterests || []);
    }
  }, [isOpen, initialInterests]);

  const toggleInterest = (interest) => {
    setSelected((prev) => {
      const exists = prev.includes(interest);
      if (exists) {
        return prev.filter((item) => item !== interest);
      }
      return [...prev, interest];
    });
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className="modal-overlay">
      <div className="modal-card">
        <h2>Pick your travel interests</h2>
        <p>Choose a few so we can tailor hotel suggestions.</p>
        <div className="chip-grid">
          {options.map((interest) => (
            <button
              key={interest}
              type="button"
              className={`chip ${selected.includes(interest) ? 'selected' : ''}`}
              onClick={() => toggleInterest(interest)}
            >
              {interest}
            </button>
          ))}
        </div>
        <div className="modal-actions">
          <button type="button" className="button secondary" onClick={onSkip}>
            Skip
          </button>
          <button
            type="button"
            className="button primary"
            onClick={() => onSave(selected)}
          >
            Save interests
          </button>
        </div>
      </div>
    </div>
  );
};

export default InterestsModal;
