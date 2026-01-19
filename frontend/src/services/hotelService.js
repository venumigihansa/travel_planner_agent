import apiConfig from '../config/api';

export const createHotelService = (options = {}) => {
  const { getToken } = options;

  const request = async ({ url, method = 'GET', data, headers }) => {
    const response = await fetch(url, {
      method,
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        ...headers
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

  const buildBookingHeaders = async () => {
    if (!getToken) {
      return {};
    }
    const token = await getToken();
    if (!token) {
      throw new Error('Missing authentication token');
    }
    return {
      'x-jwt-assertion': token
    };
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
      url: `${apiConfig.bookingBaseUrl}${apiConfig.endpoints.bookings}`,
      method: 'POST',
      data: bookingData,
      headers: await buildBookingHeaders()
    });
  };

  const getBookings = async () => {
    return request({
      url: `${apiConfig.bookingBaseUrl}${apiConfig.endpoints.bookings}`,
      headers: await buildBookingHeaders()
    });
  };

  const getBookingDetails = async (bookingId) => {
    return request({
      url: `${apiConfig.bookingBaseUrl}${apiConfig.endpoints.bookingDetails.replace('{bookingId}', bookingId)}`,
      headers: await buildBookingHeaders()
    });
  };

  const cancelBooking = async (bookingId) => {
    return request({
      url: `${apiConfig.bookingBaseUrl}${apiConfig.endpoints.cancelBooking.replace('{bookingId}', bookingId)}`,
      method: 'PUT',
      headers: await buildBookingHeaders()
    });
  };

  const getHotelApiProfile = async () => {
    return request({
      url: `${apiConfig.bookingBaseUrl}${apiConfig.endpoints.profile}`,
      headers: await buildBookingHeaders()
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
