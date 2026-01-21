import { Navbar } from "components/Navbar";
import { SearchHero } from "components/SearchHero";
import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";
import { Bot, User as UserIcon, Plus, History, MessageSquare } from "lucide-react";
import { Button } from "components/ui/button";

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

const CHAT_API_URL =
  process.env.REACT_APP_CHAT_API_URL || "http://localhost:9090/travelPlanner/chat";

const createSessionId = () =>
  `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;

export default function Home() {
  const [sessions, setSessions] = useState<ChatSession[]>([
    {
      id: '1',
      title: 'Current Session',
      sessionId: createSessionId(),
      messages: [
        {
          id: '1',
          role: 'assistant',
          content: "Hello! I'm your AI travel agent. Tell me about your dream trip, and I'll find the perfect places for you."
        }
      ]
    }
  ]);
  const [activeSessionId, setActiveSessionId] = useState('1');

  const activeSession = sessions.find(s => s.id === activeSessionId) || sessions[0];
  const messages = activeSession.messages;

  const handleNewChat = () => {
    const newId = Date.now().toString();
    const newSession: ChatSession = {
      id: newId,
      title: `New Trip Planning ${sessions.length + 1}`,
      sessionId: createSessionId(),
      messages: [
        {
          id: '1',
          role: 'assistant',
          content: "Hello! I'm your AI travel agent. Tell me about your dream trip, and I'll find the perfect places for you."
        }
      ]
    };
    setSessions(prev => [newSession, ...prev]);
    setActiveSessionId(newId);
  };

  const handleSearch = async (query: string) => {
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
      const response = await fetch(CHAT_API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: query,
          sessionId: activeSession.sessionId,
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
    }
  };

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
              {messages.map((msg) => (
                <motion.div
                  key={msg.id}
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
                      <p className="text-sm md:text-base leading-relaxed">{msg.content}</p>
                    </div>

                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>

          <div className="container mx-auto max-w-4xl sticky bottom-4">
            <SearchHero onSearch={handleSearch} />
          </div>
        </main>
      </div>
    </div>
  );
}
