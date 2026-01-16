import React, { useState, useEffect } from 'react';
import { useHotelService } from '../services/hotelService';

const HotelSearch = () => {
  const [searchParams, setSearchParams] = useState({
    destination: '',
    checkInDate: '',
    checkOutDate: '',
    guests: 2,
    rooms: 1,
    minPrice: '',
    maxPrice: '',
    minRating: '',
    amenities: [],
    propertyTypes: [],
    page: 1,
    pageSize: 10
  });
  
  const [hotels, setHotels] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [initialLoad, setInitialLoad] = useState(true);
  const [showFilters, setShowFilters] = useState(true);
  const [collapsedSections, setCollapsedSections] = useState({
    dates: false,
    guests: false,
    price: false,
    rating: false,
    amenities: true,
    propertyType: true
  });

  const hotelService = useHotelService();

  // Common amenities for filter
  const commonAmenities = [
    { id: 'wifi', label: 'Free WiFi' },
    { id: 'pool', label: 'Swimming Pool' },
    { id: 'parking', label: 'Free Parking' },
    { id: 'breakfast', label: 'Breakfast Included' },
    { id: 'spa', label: 'Spa' },
    { id: 'gym', label: 'Fitness Center' },
    { id: 'restaurant', label: 'Restaurant' },
    { id: 'bar', label: 'Bar/Lounge' }
  ];

  // Property types for filter
  const propertyTypeOptions = [
    { id: 'hotel', label: 'Hotel' },
    { id: 'resort', label: 'Resort' },
    { id: 'apartment', label: 'Apartment' },
    { id: 'villa', label: 'Villa' },
    { id: 'hostel', label: 'Hostel' }
  ];

  // Function to get hotel image URL
  const getHotelImageUrl = (hotel) => {
    return `https://raw.githubusercontent.com/wso2con/2025-CMB-AI-tutorial/refs/heads/main/Lab-02-building-travel-planner/o2-business-apis/data/images/${hotel.hotelId}.jpeg`;
  };

  // Load initial hotels when component mounts
  useEffect(() => {
    const loadInitialHotels = async () => {
      setLoading(true);
      try {
        // Search with minimal parameters to get initial hotel list
        const result = await hotelService.searchHotels({
          page: 1,
          pageSize: 20
        });
        setHotels(result.hotels || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
        setInitialLoad(false);
      }
    };

    loadInitialHotels();
  }, []);

  const handleInputChange = (e) => {
    const { name, value, type } = e.target;
    
    if (type === 'checkbox') {
      const isChecked = e.target.checked;
      const field = name.split('-')[0]; // Extract field name (amenities or propertyTypes)
      const value = name.split('-')[1]; // Extract the value
      
      setSearchParams(prev => {
        const currentValues = [...prev[field]];
        
        if (isChecked) {
          return { ...prev, [field]: [...currentValues, value] };
        } else {
          return { ...prev, [field]: currentValues.filter(item => item !== value) };
        }
      });
    } else {
      setSearchParams(prev => ({
        ...prev,
        [name]: value
      }));
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const result = await hotelService.searchHotels(searchParams);
      setHotels(result.hotels || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const clearSearch = () => {
    setSearchParams({
      destination: '',
      checkInDate: '',
      checkOutDate: '',
      guests: 2,
      rooms: 1,
      minPrice: '',
      maxPrice: '',
      minRating: '',
      amenities: [],
      propertyTypes: [],
      page: 1,
      pageSize: 10
    });
  };

  const handleImageError = (e, hotel) => {
    // If the primary image fails, try the placeholder URL
    const placeholderUrl = `https://raw.githubusercontent.com/wso2con/2025-CMB-AI-tutorial/refs/heads/main/Lab-02-building-travel-planner/hotel-apis/data/images/${hotel.hotelId}`;
    if (e.target.src !== placeholderUrl) {
      e.target.src = placeholderUrl;
    } else {
      // If even the placeholder fails, use a generic placeholder
      e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZGRkIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkhvdGVsIEltYWdlPC90ZXh0Pjwvc3ZnPg==';
    }
  };

  // Toggle filters visibility on mobile
  const toggleFilters = () => {
    setShowFilters(!showFilters);
  };

  // Toggle section collapse
  const toggleSection = (sectionName) => {
    setCollapsedSections(prev => ({
      ...prev,
      [sectionName]: !prev[sectionName]
    }));
  };

  return (
    <div className="hotel-search">
      <div className="search-hero">
        <div className="search-hero-content">
          <h1>Find Your Perfect Stay</h1>
          <p>Search hotels, resorts, and vacation rentals around the world</p>
        </div>
      </div>

      <div className="search-results-layout">
        {/* Mobile Filter Toggle */}
        <button className="mobile-filter-toggle" onClick={toggleFilters}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M4 21V14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M4 10V3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M12 21V12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M12 8V3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M20 21V16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M20 12V3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M1 14H7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M9 8H15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M17 16H23" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          <span>{showFilters ? 'Hide Filters' : 'Show Filters'}</span>
        </button>

        {/* Search Filters Sidebar */}
        <div className={`search-filters-sidebar ${showFilters ? 'show' : 'hide'}`}>
          <div className="sidebar-header">
            <h2>Search Filters</h2>
            <button className="close-filters-button" onClick={toggleFilters}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          </div>

          <form onSubmit={handleSearch} className="search-form">
            {/* Destination */}
            <div className="filter-section">
              <h3 className="filter-section-title">
                Where are you going?
              </h3>
              <div className="filter-section-content">
                <div className="form-group destination-group">
                  <div className="input-with-icon">
                    <span className="input-icon">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M12 12.75C13.6569 12.75 15 11.4069 15 9.75C15 8.09315 13.6569 6.75 12 6.75C10.3431 6.75 9 8.09315 9 9.75C9 11.4069 10.3431 12.75 12 12.75Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        <path d="M19.5 9.75C19.5 16.5 12 21.75 12 21.75C12 21.75 4.5 16.5 4.5 9.75C4.5 7.76088 5.29018 5.85322 6.6967 4.4467C8.10322 3.04018 10.0109 2.25 12 2.25C13.9891 2.25 15.8968 3.04018 17.3033 4.4467C18.7098 5.85322 19.5 7.76088 19.5 9.75Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    </span>
                    <input
                      type="text"
                      name="destination"
                      value={searchParams.destination}
                      onChange={handleInputChange}
                      placeholder="City, destination or hotel name"
                      className="destination-input"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Dates */}
            <div className={`filter-section ${collapsedSections.dates ? 'collapsed' : ''}`}>
              <h3 
                className="filter-section-title"
                onClick={() => toggleSection('dates')}
              >
                When will you be staying?
              </h3>
              <div className="filter-section-content">
                <div className="form-group">
                  <label>Check-in date</label>
                  <div className="input-with-icon">
                    <span className="input-icon">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M8 2V6" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                        <path d="M16 2V6" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                        <path d="M3 10H21" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                        <rect x="3" y="4" width="18" height="18" rx="2" stroke="currentColor" strokeWidth="2"/>
                      </svg>
                    </span>
                    <input
                      type="date"
                      name="checkInDate"
                      value={searchParams.checkInDate}
                      onChange={handleInputChange}
                      className="date-input"
                    />
                  </div>
                </div>
                
                <div className="form-group">
                  <label>Check-out date</label>
                  <div className="input-with-icon">
                    <span className="input-icon">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M8 2V6" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                        <path d="M16 2V6" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                        <path d="M3 10H21" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                        <rect x="3" y="4" width="18" height="18" rx="2" stroke="currentColor" strokeWidth="2"/>
                      </svg>
                    </span>
                    <input
                      type="date"
                      name="checkOutDate"
                      value={searchParams.checkOutDate}
                      onChange={handleInputChange}
                      className="date-input"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Guests & Rooms */}
            <div className={`filter-section ${collapsedSections.guests ? 'collapsed' : ''}`}>
              <h3 
                className="filter-section-title"
                onClick={() => toggleSection('guests')}
              >
                Guests & Rooms
              </h3>
              <div className="filter-section-content">
                <div className="form-group">
                  <label>Number of guests</label>
                  <div className="input-with-icon">
                    <span className="input-icon">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M17 21V19C17 16.7909 15.2091 15 13 15H5C2.79086 15 1 16.7909 1 19V21" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                        <path d="M9 11C11.2091 11 13 9.20914 13 7C13 4.79086 11.2091 3 9 3C6.79086 3 5 4.79086 5 7C5 9.20914 6.79086 11 9 11Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                        <path d="M23 21V19C22.9986 17.1771 21.765 15.5857 20 15.13" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                        <path d="M16 3.13C17.7699 3.58317 19.0078 5.17946 19.0078 7.005C19.0078 8.83054 17.7699 10.4268 16 10.88" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                      </svg>
                    </span>
                    <select
                      name="guests"
                      value={searchParams.guests}
                      onChange={handleInputChange}
                      className="guests-input"
                    >
                      {Array.from({ length: 10 }, (_, i) => i + 1).map(num => (
                        <option key={num} value={num}>{num} Guest{num > 1 ? 's' : ''}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="form-group">
                  <label>Number of rooms</label>
                  <div className="number-selector">
                    <button 
                      type="button" 
                      className="selector-button"
                      onClick={() => setSearchParams(prev => ({ 
                        ...prev, 
                        rooms: Math.max(1, prev.rooms - 1) 
                      }))}
                    >
                      −
                    </button>
                    <input
                      type="number"
                      name="rooms"
                      value={searchParams.rooms}
                      onChange={handleInputChange}
                      min="1"
                      max="10"
                      className="rooms-input"
                    />
                    <button 
                      type="button" 
                      className="selector-button"
                      onClick={() => setSearchParams(prev => ({ 
                        ...prev, 
                        rooms: Math.min(10, prev.rooms + 1) 
                      }))}
                    >
                      +
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Price Range */}
            <div className={`filter-section ${collapsedSections.price ? 'collapsed' : ''}`}>
              <h3 
                className="filter-section-title"
                onClick={() => toggleSection('price')}
              >
                Price Range
              </h3>
              <div className="filter-section-content">
                <div className="price-range-inputs">
                  <div className="form-group">
                    <label>Minimum price</label>
                    <div className="input-with-icon">
                      <span className="input-icon">$</span>
                      <input
                        type="number"
                        name="minPrice"
                        value={searchParams.minPrice}
                        onChange={handleInputChange}
                        placeholder="Min price"
                        className="price-input"
                      />
                    </div>
                  </div>
                  
                  <div className="form-group">
                    <label>Maximum price</label>
                    <div className="input-with-icon">
                      <span className="input-icon">$</span>
                      <input
                        type="number"
                        name="maxPrice"
                        value={searchParams.maxPrice}
                        onChange={handleInputChange}
                        placeholder="Max price"
                        className="price-input"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Star Rating */}
            <div className={`filter-section ${collapsedSections.rating ? 'collapsed' : ''}`}>
              <h3 
                className="filter-section-title"
                onClick={() => toggleSection('rating')}
              >
                Star Rating
              </h3>
              <div className="filter-section-content">
                <div className="star-rating-options">
                  {[5, 4, 3, 2, 1].map(rating => (
                    <label key={rating} className="star-rating-option">
                      <input 
                        type="radio" 
                        name="minRating" 
                        value={rating}
                        checked={searchParams.minRating === rating.toString()}
                        onChange={handleInputChange}
                        className="star-rating-input"
                      />
                      <span className="star-rating-label">
                        <span className="star-icons">{'★'.repeat(rating)}{'☆'.repeat(5-rating)}</span>
                        <span className="star-text">{rating}+ Stars</span>
                      </span>
                    </label>
                  ))}
                  <label className="star-rating-option">
                    <input 
                      type="radio" 
                      name="minRating" 
                      value=""
                      checked={searchParams.minRating === ""}
                      onChange={handleInputChange}
                      className="star-rating-input"
                    />
                    <span className="star-rating-label">
                      <span className="star-text">Any Rating</span>
                    </span>
                  </label>
                </div>
              </div>
            </div>

            {/* Amenities */}
            <div className={`filter-section ${collapsedSections.amenities ? 'collapsed' : ''}`}>
              <h3 
                className="filter-section-title"
                onClick={() => toggleSection('amenities')}
              >
                Amenities
              </h3>
              <div className="filter-section-content">
                <div className="checkbox-grid">
                  {commonAmenities.map(amenity => (
                    <label key={amenity.id} className="checkbox-label">
                      <input
                        type="checkbox"
                        name={`amenities-${amenity.id}`}
                        checked={searchParams.amenities.includes(amenity.id)}
                        onChange={handleInputChange}
                        className="checkbox-input"
                      />
                      <span className="checkbox-text">{amenity.label}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            {/* Property Type */}
            <div className={`filter-section ${collapsedSections.propertyType ? 'collapsed' : ''}`}>
              <h3 
                className="filter-section-title"
                onClick={() => toggleSection('propertyType')}
              >
                Property Type
              </h3>
              <div className="filter-section-content">
                <div className="checkbox-grid">
                  {propertyTypeOptions.map(type => (
                    <label key={type.id} className="checkbox-label">
                      <input
                        type="checkbox"
                        name={`propertyTypes-${type.id}`}
                        checked={searchParams.propertyTypes.includes(type.id)}
                        onChange={handleInputChange}
                        className="checkbox-input"
                      />
                      <span className="checkbox-text">{type.label}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="filters-actions">
              <button 
                type="button" 
                onClick={clearSearch} 
                className="clear-button"
              >
                Clear All
              </button>
              
              <button type="submit" disabled={loading} className="apply-button">
                {loading ? (
                  <span className="button-loader"></span>
                ) : (
                  <>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <circle cx="11" cy="11" r="8" stroke="currentColor" strokeWidth="2"/>
                      <path d="M21 21L16.65 16.65" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                    </svg>
                    <span>Search Hotels</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Results Area */}
        <div className="search-results-area">
          {error && (
            <div className="error-message">
              <p>Error: {error}</p>
            </div>
          )}

          <div className="results-section">
            {initialLoad && loading ? (
              <div className="loading-hotels">
                <div className="spinner"></div>
                <p>Loading hotels...</p>
              </div>
            ) : (
              <>
                <div className="results-header">
                  <h3>
                    {hotels.length > 0 
                      ? `${hotels.length} hotel${hotels.length > 1 ? 's' : ''} found` 
                      : 'No hotels found'
                    }
                  </h3>
                  <div className="results-actions">
                    <select className="sort-select">
                      <option>Sort by: Recommended</option>
                      <option>Price: Low to High</option>
                      <option>Price: High to Low</option>
                      <option>Rating: Highest First</option>
                    </select>
                  </div>
                </div>

                {hotels.length > 0 && (
                  <div className="hotels-grid">
                    {hotels.map(hotel => (
                      <div key={hotel.hotelId} className="hotel-card">
                        <div className="hotel-image">
                          <img 
                            src={getHotelImageUrl(hotel)}
                            alt={hotel.hotelName}
                            onError={(e) => handleImageError(e, hotel)}
                            loading="lazy"
                          />
                          <div className="hotel-image-overlay">
                            <span className="hotel-id">ID: {hotel.hotelId}</span>
                          </div>
                          <div className="hotel-price-tag">
                            <span>${hotel.lowestPrice}</span>
                          </div>
                        </div>
                        
                        <div className="hotel-content">
                          <div className="hotel-header">
                            <h4>{hotel.hotelName}</h4>
                            <div className="hotel-rating">
                              <span className="rating-stars">
                                {'★'.repeat(Math.floor(hotel.rating))}
                                {'☆'.repeat(5 - Math.floor(hotel.rating))}
                              </span>
                              <span className="rating-text">{hotel.rating}</span>
                            </div>
                          </div>
                          
                          <p className="hotel-location">
                            <span className="location-icon">📍</span> {hotel.city}, {hotel.country}
                          </p>
                          
                          <div className="hotel-features">
                            <div className="amenities-list">
                              {hotel.amenities.slice(0, 3).map(amenity => (
                                <span key={amenity} className="amenity-tag">{amenity}</span>
                              ))}
                              {hotel.amenities.length > 3 && (
                                <span className="amenity-more">+{hotel.amenities.length - 3}</span>
                              )}
                            </div>
                            
                            <button 
                              className="view-hotel-button"
                              onClick={() => {
                                alert(`View details for ${hotel.hotelName} (ID: ${hotel.hotelId})`);
                              }}
                            >
                              View
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default HotelSearch;
