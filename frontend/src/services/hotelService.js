import apiConfig from '../config/api';

export const useHotelService = () => {
  const request = async ({ url, method = 'GET', data }) => {
    const response = await fetch(url, {
      method,
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      body: data ? JSON.stringify(data) : undefined
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `Error: ${response.status} ${response.statusText}`);
    }

    if (response.status === 204) {
      return null;
    }

    return response.json();
  };

  const searchHotels = async (searchParams) => {
    const queryParams = new URLSearchParams();
    Object.entries(searchParams).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') {
        if (Array.isArray(value)) {
          value.forEach(item => queryParams.append(key, item));
        } else {
          queryParams.append(key, value);
        }
      }
    });

    return request({
      url: `${apiConfig.baseUrl}${apiConfig.endpoints.hotelSearch}?${queryParams}`
    });
  };

  const getHotelDetails = async (hotelId) => {
    return request({
      url: `${apiConfig.baseUrl}${apiConfig.endpoints.hotelDetails}/${hotelId}`
    });
  };

  const checkAvailability = async (hotelId, availabilityParams) => {
    const queryParams = new URLSearchParams(availabilityParams);

    return request({
      url: `${apiConfig.baseUrl}${apiConfig.endpoints.hotelAvailability.replace('{hotelId}', hotelId)}?${queryParams}`
    });
  };

  const createBooking = async (bookingData) => {
    return request({
      url: `${apiConfig.baseUrl}${apiConfig.endpoints.bookings}`,
      method: 'POST',
      data: bookingData
    });
  };

  const getBookings = async () => {
    return request({
      url: `${apiConfig.baseUrl}${apiConfig.endpoints.bookings}`
    });
  };

  const getBookingDetails = async (bookingId) => {
    return request({
      url: `${apiConfig.baseUrl}${apiConfig.endpoints.bookingDetails.replace('{bookingId}', bookingId)}`
    });
  };

  const cancelBooking = async (bookingId) => {
    return request({
      url: `${apiConfig.baseUrl}${apiConfig.endpoints.cancelBooking.replace('{bookingId}', bookingId)}`,
      method: 'PUT'
    });
  };

  const getHotelApiProfile = async () => {
    return request({
      url: `${apiConfig.baseUrl}${apiConfig.endpoints.profile}`
    });
  };

  return {
    searchHotels,
    getHotelDetails,
    checkAvailability,
    createBooking,
    getBookings,
    getBookingDetails,
    cancelBooking,
    getHotelApiProfile
  };
};
