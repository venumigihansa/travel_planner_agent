import React from 'react';

const HotelImage = ({ hotel, className = '', showId = false }) => {
  const getHotelImageUrl = (hotel) => {
    // if (hotel.images && hotel.images.length > 0 && hotel.images[0]) {
    //   return hotel.images[0];
    // }
    return `https://raw.githubusercontent.com/wso2con/2025-CMB-AI-tutorial/refs/heads/main/Lab-02-building-travel-planner/o2-business-apis/data/images/${hotel.hotelId}.jpeg`;
  };

  const handleImageError = (e, hotel) => {
    const placeholderUrl = `https://raw.githubusercontent.com/wso2con/2025-CMB-AI-tutorial/refs/heads/main/Lab-02-building-travel-planner/o2-business-apis/data/images/${hotel.hotelId}.jpeg`;
    if (e.target.src !== placeholderUrl) {
      e.target.src = placeholderUrl;
    } else {
      // Generic SVG placeholder
      e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZGRkIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkhvdGVsIEltYWdlPC90ZXh0Pjwvc3ZnPg==';
    }
  };

  return (
    <div className={`hotel-image ${className}`}>
      <img 
        src={getHotelImageUrl(hotel)}
        // alt={hotel.hotelName}
        // onError={(e) => handleImageError(e, hotel)}
        loading="lazy"
      />
      {showId && (
        <div className="hotel-image-overlay">
          <span className="hotel-id">ID: {hotel.hotelId}</span>
        </div>
      )}
    </div>
  );
};

export default HotelImage;
