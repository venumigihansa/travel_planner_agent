import { Navbar } from "components/Navbar";
import { SearchHero } from "components/SearchHero";
import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { useAsgardeo } from "@asgardeo/react";
import { Bot, User as UserIcon, Plus, History, MessageSquare } from "lucide-react";
import { Button } from "components/ui/button";
import { ChatHotelResults } from "components/ChatHotelResults";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  sessionId: string;
}

type HotelResult = {
  hotelId: string;
  hotelName: string;
  city: string;
  country: string;
  rating: number;
  lowestPrice: number;
  amenities: string[];
  mapUrl: string;
  imageUrl: string;
};

type HotelResultsPayload = {
  type: "hotel_search";
  summary: string;
  currency: string;
  hotels: HotelResult[];
};

const HOTEL_RESULTS_MARKER = "HOTEL_RESULTS_JSON";

const stripCodeFence = (value: string) => {
  const trimmed = value.trim();
  if (trimmed.startsWith("```")) {
    const withoutFirst = trimmed.replace(/^```[a-zA-Z]*\n?/, "");
    return withoutFirst.replace(/```$/, "").trim();
  }
  return trimmed;
};

const tryParseHotelResults = (jsonText: string): HotelResultsPayload | null => {
  if (!jsonText) {
    return null;
  }
  try {
    const parsed = JSON.parse(jsonText) as HotelResultsPayload;
    if (parsed?.type !== "hotel_search" || !Array.isArray(parsed.hotels)) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
};

const parseHotelResults = (content: string): HotelResultsPayload | null => {
  const markerIndex = content.indexOf(HOTEL_RESULTS_MARKER);
  if (markerIndex !== -1) {
    const jsonText = stripCodeFence(
      content.slice(markerIndex + HOTEL_RESULTS_MARKER.length).trim()
    );
    const parsed = tryParseHotelResults(jsonText);
    if (parsed) {
      return parsed;
    }
  }

  const firstBrace = content.indexOf("{");
  const lastBrace = content.lastIndexOf("}");
  if (firstBrace !== -1 && lastBrace > firstBrace) {
    const candidate = stripCodeFence(content.slice(firstBrace, lastBrace + 1));
    return tryParseHotelResults(candidate);
  }

  return null;
};

const CHAT_API_URL =
  process.env.REACT_APP_CHAT_API_URL || "http://localhost:9090/travelPlanner/chat";
const CHAT_SESSIONS_URL = `${CHAT_API_URL}/sessions`;
const USER_ID_STORAGE_KEY = "travelPlannerUserId";

const createSessionId = () =>
  `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;

const getOrCreateUserId = () => {
  if (typeof window === "undefined") {
    return "default";
  }
  const existing = localStorage.getItem(USER_ID_STORAGE_KEY);
  if (existing) {
    return existing;
  }
  const newId =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : createSessionId();
  localStorage.setItem(USER_ID_STORAGE_KEY, newId);
  return newId;
};

const buildWelcomeMessage = (): Message => ({
  id: createSessionId(),
  role: "assistant",
  content: "Hello! I'm your AI travel agent. Tell me about your dream trip, and I'll find the perfect places for you.",
});

const buildNewSession = (): ChatSession => {
  const sessionId = createSessionId();
  return {
    id: sessionId,
    title: "Current Session",
    sessionId,
    messages: [buildWelcomeMessage()],
  };
};

export default function Home() {
  const { isSignedIn, getAccessToken, user } = useAsgardeo();
  const [sessions, setSessions] = useState<ChatSession[]>(() => [buildNewSession()]);
  const [activeSessionId, setActiveSessionId] = useState(sessions[0]?.id ?? "");
  const [userId, setUserId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const lastMessageRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let isMounted = true;
    const loadUserId = async () => {
      if (!isSignedIn) {
        return;
      }
      try {
        const resolved = user?.sub || user?.username || getOrCreateUserId();
        if (isMounted) {
          setUserId(resolved);
        }
      } catch {
        if (isMounted) {
          setUserId(getOrCreateUserId());
        }
      }
    };
    loadUserId();
    return () => {
      isMounted = false;
    };
  }, [isSignedIn, user]);

  useEffect(() => {
    if (!userId) {
      return;
    }
    const loadSessions = async () => {
      try {
        const token = isSignedIn ? await getAccessToken() : "";
        const headers: Record<string, string> = { Accept: "application/json" };
        if (token) {
          headers.Authorization = `Bearer ${token}`;
        }
        const response = await fetch(
          `${CHAT_SESSIONS_URL}?userId=${encodeURIComponent(userId)}`,
          { headers }
        );
        if (!response.ok) {
          return;
        }
        const data = await response.json();
        if (Array.isArray(data?.sessions) && data.sessions.length > 0) {
          setSessions(data.sessions);
          setActiveSessionId(data.sessions[0].id);
        }
      } catch (error) {
        if ((error as Error)?.name !== "AbortError") {
          console.error("Failed to load chat sessions", error);
        }
      }
    };
    loadSessions();
  }, [getAccessToken, isSignedIn, userId]);

  const activeSession = sessions.find(s => s.id === activeSessionId) || sessions[0];
  const messages = activeSession.messages;

  const handleNewChat = () => {
    const newSession = buildNewSession();
    newSession.title = `New Trip Planning ${sessions.length + 1}`;
    setSessions(prev => [newSession, ...prev]);
    setActiveSessionId(newSession.id);
  };

  const handleSearch = async (query: string) => {
    const effectiveUserId = userId ?? getOrCreateUserId();
    if (!userId) {
      setUserId(effectiveUserId);
    }
    if (!activeSession) {
      return;
    }
    setIsLoading(true);
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: query
    };

    setSessions(prev => prev.map(s => 
      s.id === activeSessionId 
        ? { ...s, messages: [...s.messages, userMessage] }
        : s
    ));

    try {
      const token = isSignedIn ? await getAccessToken() : "";
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }
      const response = await fetch(CHAT_API_URL, {
        method: "POST",
        headers,
        body: JSON.stringify({
          message: query,
          sessionId: activeSession.sessionId,
          userId: effectiveUserId,
        }),
      });

      if (!response.ok) {
        throw new Error(`Chat API error: ${response.status}`);
      }

      const data = await response.json();
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data?.message || "Sorry, I couldn't generate a response.",
      };

      setSessions(prev => prev.map(s =>
        s.id === activeSessionId
          ? {
              ...s,
              messages: [...s.messages, assistantMessage],
              title: s.title.startsWith('New Trip') ? query.slice(0, 20) + '...' : s.title
            }
          : s
      ));
    } catch (error) {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: "Sorry, I couldn't reach the travel assistant. Please try again.",
      };
      setSessions(prev => prev.map(s =>
        s.id === activeSessionId
          ? { ...s, messages: [...s.messages, assistantMessage] }
          : s
      ));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!lastMessageRef.current) {
      return;
    }
    lastMessageRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [messages, isLoading]);

  return (
    <div className="min-h-screen flex bg-background">
      {/* Sidebar */}
      <aside className="w-80 border-r border-border bg-card hidden md:flex flex-col">
        <div className="p-4 border-b border-border">
          <Button onClick={handleNewChat} className="w-full justify-start gap-2 bg-primary hover:bg-primary/90 text-white rounded-xl">
            <Plus className="w-4 h-4" />
            New Trip
          </Button>
        </div>
        
        <div className="flex-grow overflow-y-auto p-2 space-y-1">
          <div className="px-3 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
            <History className="w-3 h-3" />
            Recent Plans
          </div>
          {sessions.map(s => (
            <button
              key={s.id}
              onClick={() => setActiveSessionId(s.id)}
              className={`w-full text-left px-3 py-3 rounded-xl transition-all flex items-center gap-3 ${
                activeSessionId === s.id 
                ? 'bg-secondary text-primary font-bold shadow-sm' 
                : 'hover:bg-muted text-muted-foreground'
              }`}
            >
              <MessageSquare className="w-4 h-4 shrink-0" />
              <span className="truncate text-sm">{s.title}</span>
            </button>
          ))}
        </div>
      </aside>

      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        <Navbar />
        
        <main className="flex-grow overflow-y-auto p-4 flex flex-col">
          <div className="flex-grow space-y-8 mb-8 container mx-auto max-w-4xl px-2 pt-4">
            <AnimatePresence mode="popLayout">
              {messages.map((msg, index) => {
                const hotelPayload =
                  msg.role === "assistant" ? parseHotelResults(msg.content) : null;
                const isLast = index === messages.length - 1 && !isLoading;
                return (
                <motion.div
                  key={msg.id}
                  ref={isLast ? lastMessageRef : undefined}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
                >
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 shadow-sm ${
                    msg.role === 'assistant' ? 'bg-primary text-white' : 'bg-accent text-accent-foreground'
                  }`}>
                    {msg.role === 'assistant' ? <Bot className="w-5 h-5" /> : <UserIcon className="w-5 h-5" />}
                  </div>
                  
                  <div className={`space-y-4 max-w-[85%] ${msg.role === 'user' ? 'items-end' : ''}`}>
                    <div className={`p-4 rounded-2xl shadow-sm ${
                      msg.role === 'assistant' 
                        ? 'bg-white border border-border text-foreground rounded-tl-none' 
                        : 'bg-primary text-white rounded-tr-none'
                    }`}>
                      {hotelPayload ? (
                        <ChatHotelResults payload={hotelPayload} />
                      ) : msg.role === "assistant" ? (
                        <div className="chat-markdown text-sm md:text-base leading-relaxed">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                              a: ({ children, ...props }) => (
                                <a {...props} target="_blank" rel="noopener noreferrer">
                                  {children}
                                </a>
                              ),
                            }}
                          >
                            {msg.content}
                          </ReactMarkdown>
                        </div>
                      ) : (
                        <p className="text-sm md:text-base leading-relaxed whitespace-pre-line">{msg.content}</p>
                      )}
                    </div>

                  </div>
                </motion.div>
                );
              })}
              {isLoading && (
                <motion.div
                  ref={lastMessageRef}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex gap-4"
                >
                  <div className="w-10 h-10 rounded-full flex items-center justify-center shrink-0 shadow-sm bg-primary text-white">
                    <Bot className="w-5 h-5" />
                  </div>
                  <div className="space-y-4 max-w-[85%]">
                    <div className="p-4 rounded-2xl shadow-sm bg-white border border-border text-foreground rounded-tl-none">
                      <div className="typing-dots" aria-label="Assistant is typing">
                        <span />
                        <span />
                        <span />
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <div className="container mx-auto max-w-4xl sticky bottom-4">
            <SearchHero onSearch={handleSearch} compact />
          </div>
        </main>
      </div>
    </div>
  );
}
