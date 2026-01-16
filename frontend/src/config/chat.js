const chatConfig = {
  baseUrl: process.env.REACT_APP_CHAT_API_URL || "http://localhost:9090/travelPlanner",
  endpoints: {
    chat: "/chat"
  },
  timeout: 120000 // 2 minutes timeout
};

export default chatConfig;
