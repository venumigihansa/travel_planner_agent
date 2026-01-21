import { useState } from "react";
import { Sparkles, ArrowRight } from "lucide-react";
import { motion } from "framer-motion";

interface SearchHeroProps {
  onSearch?: (query: string) => void;
}

export function SearchHero({ onSearch }: SearchHeroProps) {
  const [query, setQuery] = useState("");

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    onSearch?.(query);
    setQuery("");
  };

  return (
    <div className="relative overflow-hidden rounded-3xl bg-primary text-white py-8 px-6 shadow-2xl shadow-primary/20">
      <div className="relative z-10 max-w-3xl mx-auto space-y-6">
        <form 
          onSubmit={handleSearch}
          className="relative"
        >
          <div className="relative group">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask me where you want to go..."
              className="w-full h-14 pl-6 pr-14 rounded-2xl bg-white text-foreground placeholder:text-muted-foreground shadow-xl focus:outline-none focus:ring-4 focus:ring-accent/30 transition-all text-base md:text-lg font-medium"
            />
            <button 
              type="submit"
              className="absolute right-2 top-2 bottom-2 aspect-square bg-primary hover:bg-primary/90 text-white rounded-xl flex items-center justify-center transition-transform active:scale-95 shadow-sm"
            >
              <ArrowRight className="w-5 h-5" />
            </button>
          </div>
        </form>
        
        <div className="flex flex-wrap justify-center gap-4 text-xs md:text-sm text-white/70 font-medium">
          <span className="flex items-center gap-1"><Sparkles className="w-3 h-3 text-accent" /> Try:</span>
          <button onClick={() => { setQuery("Romantic Paris getaway"); onSearch?.("Romantic Paris getaway"); }} className="hover:text-accent transition-colors underline decoration-dotted">Honeymoon in Paris</button>
          <button onClick={() => { setQuery("Skiing in the Alps"); onSearch?.("Skiing in the Alps"); }} className="hover:text-accent transition-colors underline decoration-dotted">Skiing in Alps</button>
          <button onClick={() => { setQuery("Kyoto Cherry Blossoms"); onSearch?.("Kyoto Cherry Blossoms"); }} className="hover:text-accent transition-colors underline decoration-dotted">Kyoto Cherry Blossom</button>
        </div>
      </div>
    </div>
  );
}
