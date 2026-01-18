const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:9090';

const buildHeaders = (token) => ({
  'Content-Type': 'application/json',
  Authorization: `Bearer ${token}`
});

const requireToken = async (getToken) => {
  const token = await getToken();
  if (!token) {
    throw new Error('Missing authentication token');
  }
  return token;
};

const handleResponse = async (response) => {
  if (response.ok) {
    return response.json();
  }
  const errorBody = await response.json().catch(() => ({}));
  const message = errorBody.detail || errorBody.message || `${response.status} ${response.statusText}`;
  throw new Error(message);
};

export const createUserProfileService = (getToken) => ({
  async createOrUpdateUser(payload) {
    const token = await requireToken(getToken);
    const response = await fetch(`${API_BASE_URL}/users`, {
      method: 'POST',
      headers: buildHeaders(token),
      body: JSON.stringify(payload)
    });
    return handleResponse(response);
  },

  async fetchUserProfile(userId) {
    const token = await requireToken(getToken);
    const response = await fetch(`${API_BASE_URL}/users/${userId}`, {
      headers: buildHeaders(token)
    });
    return handleResponse(response);
  },

  async updateInterests(userId, interests) {
    const token = await requireToken(getToken);
    const response = await fetch(`${API_BASE_URL}/users/${userId}/interests`, {
      method: 'PUT',
      headers: buildHeaders(token),
      body: JSON.stringify({ interests })
    });
    return handleResponse(response);
  }
});
