import React, { useState, useRef, useEffect } from 'react';
import { ChatService } from '../services/chatService';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const AIAssistant = () => {
  const [messages, setMessages] = useState([
    { 
      role: 'assistant', 
      content: '# Welcome to your Travel Planner! 👋\n\nI\'m your AI travel assistant, ready to help you plan your next adventure. I can help with finding destinations, recommending hotels, suggesting activities, and providing travel tips.\n\n**How can I assist with your travel plans today?**'
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [chatView, setChatView] = useState(false);
  const messagesEndRef = useRef(null);
  const [error, setError] = useState(null);

  // Scroll to bottom of messages on new message
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    // Add user message
    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);
    setError(null);

    try {
      // Send message to the chat API
      const response = await ChatService.sendMessage(input);
      
      // Add assistant response
      if (response && response.message) {
        setMessages(prev => [...prev, { role: 'assistant', content: response.message }]);
      } else {
        throw new Error('Invalid response from chat server');
      }
    } catch (err) {
      console.error('Chat error:', err);
      setError(err.message || 'Failed to communicate with the AI assistant');
      
      // Add error message to the chat
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: '⚠️ **Sorry!** I encountered an error while processing your request. Please try again later.',
        isError: true
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  // Format timestamp
  const formatTime = () => {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Toggle chat view
  const toggleChatView = () => {
    setChatView(true);
  };

  // Exit chat view
  const exitChatView = () => {
    setChatView(false);
  };

  return (
    <div className={`travel-assistant-container ${chatView ? 'chat-view-active' : ''}`}>
      {/* Main Intro View (shown when chat is not active) */}
      <div className="travel-intro-view">
        <div className="travel-intro-content">
          <div className="travel-assistant-logo">
            <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg" className="travel-logo-svg">
              <circle cx="32" cy="32" r="30" fill="url(#paint0_linear)" />
              <path d="M42 22C42 27.523 37.523 32 32 32C26.477 32 22 27.523 22 22C22 16.477 26.477 12 32 12C37.523 12 42 16.477 42 22Z" fill="white" />
              <path d="M54 53.9999C54 42.9411 44.0589 33.9999 33 33.9999H31C19.9411 33.9999 10 42.9411 10 53.9999" stroke="white" strokeWidth="4" strokeLinecap="round" />
              <path d="M23 23L26 26" stroke="#1976D2" strokeWidth="2" strokeLinecap="round" />
              <path d="M41 23L38 26" stroke="#1976D2" strokeWidth="2" strokeLinecap="round" />
              <path d="M32 28C33.6569 28 35 26.6569 35 25C35 23.3431 33.6569 22 32 22C30.3431 22 29 23.3431 29 25C29 26.6569 30.3431 28 32 28Z" fill="#1976D2" />
              <path d="M26 22C26 22 28 18 32 18C36 18 38 22 38 22" stroke="#1976D2" strokeWidth="2" strokeLinecap="round" />
              <path d="M23 43L27 41.5L23 40L19 41.5L23 43Z" fill="white" />
              <path d="M16 47L20 45.5L16 44L12 45.5L16 47Z" fill="white" />
              <path d="M32 47L36 45.5L32 44L28 45.5L32 47Z" fill="white" />
              <path d="M41 43L45 41.5L41 40L37 41.5L41 43Z" fill="white" />
              <path d="M48 47L52 45.5L48 44L44 45.5L48 47Z" fill="white" />
              <defs>
                <linearGradient id="paint0_linear" x1="2" y1="2" x2="62" y2="62" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#1976D2" />
                  <stop offset="1" stopColor="#0D47A1" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          
          <h1>AI Travel Planner</h1>
          <p>Your personal AI assistant for planning the perfect trip. Get destination recommendations, hotel suggestions, and travel advice tailored just for you.</p>
          
          <div className="travel-features">
            <div className="feature-item">
              <div className="feature-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 21C16.9706 21 21 16.9706 21 12C21 7.02944 16.9706 3 12 3C7.02944 3 3 7.02944 3 12C3 16.9706 7.02944 21 12 21Z" stroke="currentColor" strokeWidth="2" />
                  <path d="M3.6001 9H20.4001" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                  <path d="M3.6001 15H20.4001" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                  <path d="M12 3C14.3386 5.06152 15.6528 8.30385 15.6001 11.7C15.6528 15.0962 14.3386 18.3385 12 20.4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                  <path d="M12 3C9.66144 5.06152 8.34718 8.30385 8.3999 11.7C8.34718 15.0962 9.66144 18.3385 12 20.4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                </svg>
              </div>
              <div className="feature-text">Find Destinations</div>
            </div>
            <div className="feature-item">
              <div className="feature-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M3 7V19C3 20.1046 3.89543 21 5 21H19C20.1046 21 21 20.1046 21 19V7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                  <path d="M21 7H3C1.89543 7 1 6.10457 1 5V5C1 3.89543 1.89543 3 3 3H21C22.1046 3 23 3.89543 23 5V5C23 6.10457 22.1046 7 21 7Z" stroke="currentColor" strokeWidth="2" />
                  <path d="M9 13H15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                  <path d="M9 17H15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                </svg>
              </div>
              <div className="feature-text">Book Hotels</div>
            </div>
            <div className="feature-item">
              <div className="feature-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M9 6L21 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M9 12H21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M9 18H21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M5 6C5 6.55228 4.55228 7 4 7C3.44772 7 3 6.55228 3 6C3 5.44772 3.44772 5 4 5C4.55228 5 5 5.44772 5 6Z" fill="currentColor" />
                  <path d="M5 12C5 12.5523 4.55228 13 4 13C3.44772 13 3 12.5523 3 12C3 11.4477 3.44772 11 4 11C4.55228 11 5 11.4477 5 12Z" fill="currentColor" />
                  <path d="M5 18C5 18.5523 4.55228 19 4 19C3.44772 19 3 18.5523 3 18C3 17.4477 3.44772 17 4 17C4.55228 17 5 17.4477 5 18Z" fill="currentColor" />
                </svg>
              </div>
              <div className="feature-text">Create Itineraries</div>
            </div>
            <div className="feature-item">
              <div className="feature-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M20.0001 12V17C20.0001 18.6569 18.6569 20 17.0001 20H7.00006C5.34321 20 4.00006 18.6569 4.00006 17V12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M16 6L12 2L8 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M12 2V14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
              <div className="feature-text">Travel Tips</div>
            </div>
          </div>
          
          <button className="start-chat-button" onClick={toggleChatView}>
            <span className="button-text">Start Planning</span>
            <svg className="button-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M8 5L15 12L8 19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>
      </div>

      {/* Chat View (slides up when active) */}
      {chatView && (
        <div className="travel-chat-view">
          <div className="chat-header">
            <div className="chat-header-left">
              <button className="back-button" onClick={exitChatView}>
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M19 12H5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M12 19L5 12L12 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
              <div className="chat-title-container">
                <div className="chat-icon">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 21C16.9706 21 21 16.9706 21 12C21 7.02944 16.9706 3 12 3C7.02944 3 3 7.02944 3 12C3 16.9706 7.02944 21 12 21Z" stroke="currentColor" strokeWidth="2" />
                    <path d="M3.6001 9H20.4001" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                    <path d="M3.6001 15H20.4001" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                    <path d="M12 3C14.3386 5.06152 15.6528 8.30385 15.6001 11.7C15.6528 15.0962 14.3386 18.3385 12 20.4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                    <path d="M12 3C9.66144 5.06152 8.34718 8.30385 8.3999 11.7C8.34718 15.0962 9.66144 18.3385 12 20.4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                  </svg>
                </div>
                <div className="chat-title">Travel Planner</div>
              </div>
            </div>
            <div className="feature-icons">
              <div className="feature-chip">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 21C16.9706 21 21 16.9706 21 12C21 7.02944 16.9706 3 12 3C7.02944 3 3 7.02944 3 12C3 16.9706 7.02944 21 12 21Z" stroke="currentColor" strokeWidth="2" />
                  <path d="M3.6001 9H20.4001" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                </svg>
              </div>
              <div className="feature-chip">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M3 7V19C3 20.1046 3.89543 21 5 21H19C20.1046 21 21 20.1046 21 19V7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                </svg>
              </div>
              <div className="feature-chip">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M9 6L21 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
              <div className="feature-chip">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M20.0001 12V17C20.0001 18.6569 18.6569 20 17.0001 20H7.00006C5.34321 20 4.00006 18.6569 4.00006 17V12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
            </div>
          </div>

          <div className="chat-messages">
            {error && (
              <div className="error-notification">
                <span>Connection error: {error}</span>
              </div>
            )}
            
            <div className="messages-list">
              {messages.map((message, index) => (
                <div 
                  key={index} 
                  className={`chat-message ${message.role === 'user' ? 'user-message' : 'assistant-message'} ${message.isError ? 'error-message' : ''}`}
                >
                  <div className="message-avatar">
                    {message.role === 'user' ? (
                      <div className="user-avatar">G</div>
                    ) : (
                      <div className="assistant-avatar">
                        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M12 21C16.9706 21 21 16.9706 21 12C21 7.02944 16.9706 3 12 3C7.02944 3 3 7.02944 3 12C3 16.9706 7.02944 21 12 21Z" stroke="currentColor" strokeWidth="2" />
                          <path d="M3.6001 9H20.4001" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                          <path d="M3.6001 15H20.4001" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                          <path d="M12 3C14.3386 5.06152 15.6528 8.30385 15.6001 11.7C15.6528 15.0962 14.3386 18.3385 12 20.4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                          <path d="M12 3C9.66144 5.06152 8.34718 8.30385 8.3999 11.7C8.34718 15.0962 9.66144 18.3385 12 20.4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                        </svg>
                      </div>
                    )}
                  </div>
                  <div className="message-content">
                    <div className="message-bubble">
                      {message.role === 'assistant' ? (
                        <div className="markdown-content">
                          <ReactMarkdown 
                            remarkPlugins={[remarkGfm]}
                            components={{
                              img: ({node, ...props}) => (
                                <img className="markdown-image" {...props} />
                              ),
                              a: ({node, ...props}) => (
                                <a target="_blank" rel="noopener noreferrer" {...props} />
                              )
                            }}
                          >
                            {message.content}
                          </ReactMarkdown>
                        </div>
                      ) : (
                        <div className="message-text">{message.content}</div>
                      )}
                      <div className="message-time">{formatTime()}</div>
                    </div>
                  </div>
                </div>
              ))}
              
              {isTyping && (
                <div className="chat-message assistant-message">
                  <div className="message-avatar">
                    <div className="assistant-avatar">
                      <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M12 21C16.9706 21 21 16.9706 21 12C21 7.02944 16.9706 3 12 3C7.02944 3 3 7.02944 3 12C3 16.9706 7.02944 21 12 21Z" stroke="currentColor" strokeWidth="2" />
                        <path d="M3.6001 9H20.4001" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                        <path d="M3.6001 15H20.4001" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                        <path d="M12 3C14.3386 5.06152 15.6528 8.30385 15.6001 11.7C15.6528 15.0962 14.3386 18.3385 12 20.4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                        <path d="M12 3C9.66144 5.06152 8.34718 8.30385 8.3999 11.7C8.34718 15.0962 9.66144 18.3385 12 20.4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                      </svg>
                    </div>
                  </div>
                  <div className="message-content">
                    <div className="message-bubble">
                      <div className="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>
          
          <form onSubmit={handleSubmit} className="chat-input-form">
            <div className="input-container">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask me about your travel plans..."
                className="chat-input"
                disabled={isTyping}
              />
              <button 
                type="submit" 
                className="send-button"
                disabled={isTyping || !input.trim()}
              >
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M22 2L11 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};

export default AIAssistant;
