import React, { useState, useEffect } from 'react';
import { useHotelService } from '../services/hotelService';

const UserBookings = () => {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const hotelService = useHotelService();

  useEffect(() => {
    fetchBookings();
  }, []);

  const fetchBookings = async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await hotelService.getBookings();
      setBookings(Array.isArray(result) ? result : []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelBooking = async (bookingId) => {
    if (!window.confirm('Are you sure you want to cancel this booking?')) {
      return;
    }

    try {
      await hotelService.cancelBooking(bookingId);
      alert('Booking cancelled successfully');
      fetchBookings(); // Refresh the list
    } catch (err) {
      alert(`Error cancelling booking: ${err.message}`);
    }
  };

  if (loading) return <div className="loading">Loading bookings...</div>;

  return (
    <div className="user-bookings">
      <h2>My Bookings</h2>
      
      {error && (
        <div className="error-message">
          <p>Error: {error}</p>
        </div>
      )}

      {bookings.length === 0 ? (
        <p>No bookings found.</p>
      ) : (
        <div className="bookings-list">
          {bookings.map(booking => (
            <div key={booking.bookingId} className="booking-card">
              <div className="booking-header">
                <h3>Booking #{booking.confirmationNumber}</h3>
                <span className={`booking-status ${booking.bookingStatus.toLowerCase()}`}>
                  {booking.bookingStatus}
                </span>
              </div>
              
              <div className="booking-details">
                <p><strong>Hotel ID:</strong> {booking.hotelId}</p>
                <p><strong>Check-in:</strong> {booking.checkInDate}</p>
                <p><strong>Check-out:</strong> {booking.checkOutDate}</p>
                <p><strong>Guests:</strong> {booking.numberOfGuests}</p>
                <p><strong>Guest:</strong> {booking.primaryGuest.firstName} {booking.primaryGuest.lastName}</p>
                <p><strong>Total Amount:</strong> ${booking.pricing[0]?.totalAmount || 0}</p>
              </div>
              
              {booking.bookingStatus !== 'CANCELLED' && (
                <button 
                  onClick={() => handleCancelBooking(booking.bookingId)}
                  className="cancel-button"
                >
                  Cancel Booking
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default UserBookings;