import { Link, useLocation } from "wouter";
import { Compass, User, Menu } from "lucide-react";
import { Button } from "components/ui/button";

export function Navbar() {
  const [location] = useLocation();

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-border/40 bg-white/80 backdrop-blur-md">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 group">
          <div className="bg-primary text-white p-1.5 rounded-lg group-hover:bg-primary/90 transition-colors">
            <Compass className="w-6 h-6" />
          </div>
          <span className="font-display font-bold text-xl text-primary tracking-tight">
            WanderAI
          </span>
        </Link>

        <div className="hidden md:flex items-center gap-8">
          <Link href="/" className={`text-sm font-medium transition-colors hover:text-primary ${location === '/' ? 'text-primary' : 'text-muted-foreground'}`}>
            Explore
          </Link>
          <span className="text-sm font-medium text-muted-foreground cursor-not-allowed">
            Trips
          </span>
          <span className="text-sm font-medium text-muted-foreground cursor-not-allowed">
            Saved
          </span>
        </div>

        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" className="md:hidden">
            <Menu className="w-5 h-5" />
          </Button>
          <Button variant="outline" size="sm" className="hidden md:flex gap-2 rounded-full border-primary/10 hover:border-primary/20 hover:bg-primary/5">
            <User className="w-4 h-4" />
            <span>Sign In</span>
          </Button>
          <Button size="sm" className="hidden md:flex rounded-full bg-primary hover:bg-primary/90 text-white shadow-lg shadow-primary/20">
            Start Planning
          </Button>
        </div>
      </div>
    </nav>
  );
}
