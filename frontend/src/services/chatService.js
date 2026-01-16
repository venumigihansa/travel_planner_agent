import chatConfig from '../config/chat';
import { v4 as uuidv4 } from 'uuid';

// Get session ID from storage or create a new one
const getSessionId = () => {
  let sessionId = localStorage.getItem('chat_session_id');
  
  if (!sessionId) {
    sessionId = uuidv4();
    localStorage.setItem('chat_session_id', sessionId);
  }
  
  return sessionId;
};

// Reset the session ID (e.g., for a new conversation)
export const resetChatSession = () => {
  const newSessionId = uuidv4();
  localStorage.setItem('chat_session_id', newSessionId);
  return newSessionId;
};

export const ChatService = {
  async sendMessage(message) {
    try {
      const sessionId = getSessionId();
      
      const response = await fetch(`${chatConfig.baseUrl}${chatConfig.endpoints.chat}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          message,
          sessionId
        }),
        signal: AbortSignal.timeout(chatConfig.timeout)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `Error: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Chat API error:', error);
      throw error;
    }
  },
  
  getSessionId() {
    return getSessionId();
  }
};