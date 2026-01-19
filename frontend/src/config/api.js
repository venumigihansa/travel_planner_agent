const baseUrl = process.env.REACT_APP_HOTEL_API_BASE_URL || "http://localhost:9090";

const apiConfig = {
  baseUrl,
  bookingBaseUrl: process.env.REACT_APP_BOOKING_API_BASE_URL || baseUrl,
  endpoints: {
    profile: "/auth/profile",
    hotelSearch: "/hotels/search",
    hotelDetails: "/hotels",
    hotelAvailability: "/hotels/{hotelId}/availability",
    bookings: "/bookings",
    bookingDetails: "/bookings/{bookingId}",
    cancelBooking: "/bookings/{bookingId}/cancel",
    hotelReviews: "/hotels/{hotelId}/reviews",
    allReviews: "/reviews"
  }
};

export default apiConfig;
