import React, { useState } from 'react';
import { useHotelService } from '../services/hotelService';

const UserProfile = () => {
  const [hotelProfileData, setHotelProfileData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const hotelService = useHotelService();

  const fetchHotelProfile = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await hotelService.getHotelApiProfile();
      setHotelProfileData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="user-profile">
      <h2>User Profile</h2>
      
      {/* Hotel API Profile */}
      <div className="api-profile-section">
        <h3>Hotel Booking Profile</h3>
        <button onClick={fetchHotelProfile} disabled={loading} className="fetch-button">
          {loading ? 'Loading...' : 'Fetch Hotel Profile'}
        </button>

        {error && (
          <div className="error-message">
            <p>Error: {error}</p>
            <p className="error-note">
              Note: This requires your hotel API to be running and configured properly.
            </p>
          </div>
        )}

        {hotelProfileData && (
          <div className="api-profile-data">
            <div className="profile-item">
              <strong>User ID:</strong> {hotelProfileData.userId}
            </div>
            <div className="profile-item">
              <strong>Name:</strong> {hotelProfileData.firstName} {hotelProfileData.lastName}
            </div>
            <div className="profile-item">
              <strong>Email:</strong> {hotelProfileData.email}
            </div>
            <div className="profile-item">
              <strong>Phone:</strong> {hotelProfileData.phoneNumber || 'N/A'}
            </div>
            <div className="profile-item">
              <strong>User Type:</strong> {hotelProfileData.userType}
            </div>
            <div className="profile-item">
              <strong>Registration Date:</strong> {hotelProfileData.registrationDate}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default UserProfile;
