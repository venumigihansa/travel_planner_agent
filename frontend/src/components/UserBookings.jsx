import React, { useCallback, useMemo, useState, useEffect } from 'react';
import { useAuth } from '@clerk/clerk-react';
import { createHotelService } from '../services/hotelService';

const UserBookings = () => {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const { getToken } = useAuth();
  const hotelService = useMemo(() => createHotelService({ getToken }), [getToken]);

  const formatter = useMemo(() => new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0
  }), []);

  const formatDate = (value) => {
    if (!value) {
      return 'Unknown';
    }
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) {
      return value;
    }
    return parsed.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const statusSummary = useMemo(() => {
    return bookings.reduce((acc, booking) => {
      const status = booking.bookingStatus || 'UNKNOWN';
      acc[status] = (acc[status] || 0) + 1;
      return acc;
    }, {});
  }, [bookings]);

  const fetchBookings = useCallback(async () => {
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
  }, [hotelService]);

  useEffect(() => {
    fetchBookings();
  }, [fetchBookings]);

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
      <div className="bookings-hero">
        <div>
          <p className="bookings-kicker">Travel History</p>
          <h2>My Bookings</h2>
          <p className="bookings-subtitle">Keep track of your stays, check-in dates, and confirmations.</p>
        </div>
        <button type="button" className="refresh-bookings" onClick={fetchBookings}>
          Refresh
        </button>
      </div>

      <div className="bookings-summary">
        <div className="summary-card">
          <span className="summary-label">Total bookings</span>
          <span className="summary-value">{bookings.length}</span>
        </div>
        <div className="summary-card">
          <span className="summary-label">Confirmed</span>
          <span className="summary-value">{statusSummary.CONFIRMED || 0}</span>
        </div>
        <div className="summary-card">
          <span className="summary-label">Cancelled</span>
          <span className="summary-value">{statusSummary.CANCELLED || 0}</span>
        </div>
      </div>

      {error && (
        <div className="error-message">
          <p>Error: {error}</p>
          <button type="button" className="retry-button" onClick={fetchBookings}>
            Try again
          </button>
        </div>
      )}

      {bookings.length === 0 ? (
        <div className="empty-state">
          <h3>No bookings yet</h3>
          <p>When you book a stay, it will show up here for quick access.</p>
        </div>
      ) : (
        <div className="bookings-list">
          {bookings.map(booking => (
            <div key={booking.bookingId} className="booking-card">
              <div className="booking-header">
                <h3>Booking #{booking.confirmationNumber}</h3>
                <span className={`booking-status ${(booking.bookingStatus || 'unknown').toLowerCase()}`}>
                  {booking.bookingStatus || 'Unknown'}
                </span>
              </div>
              
              <div className="booking-details">
                <p><strong>Hotel:</strong> {booking.hotelName || 'Unknown'}</p>
                <p><strong>Check-in:</strong> {formatDate(booking.checkInDate)}</p>
                <p><strong>Check-out:</strong> {formatDate(booking.checkOutDate)}</p>
                <p><strong>Guests:</strong> {booking.numberOfGuests}</p>
                <p><strong>Guest:</strong> {booking.primaryGuest?.firstName} {booking.primaryGuest?.lastName}</p>
                <p><strong>Total Amount:</strong> {formatter.format(booking.pricing[0]?.totalAmount || 0)}</p>
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
