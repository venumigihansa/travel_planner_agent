import { Link, useLocation } from "wouter";
import { Compass, LogOut, Menu } from "lucide-react";
import { Button } from "components/ui/button";
import { SignedIn, SignedOut, SignInButton, SignOutButton, useAsgardeo } from "@asgardeo/react";

export function Navbar() {
  const [location] = useLocation();
  const { isLoading, user } = useAsgardeo();
  const displayName = (() => {
    const raw =
      user?.displayName ||
      user?.given_name ||
      user?.preferred_username ||
      user?.username ||
      user?.email ||
      null;
    if (!raw) {
      return null;
    }
    if (raw.includes("@")) {
      return raw.split("@")[0];
    }
    return raw;
  })();

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-border/40 bg-white/80 backdrop-blur-md">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 group">
          <div className="bg-primary text-white p-1.5 rounded-lg group-hover:bg-primary/90 transition-colors">
            <Compass className="w-6 h-6" />
          </div>
          <span className="font-display font-bold text-xl text-primary tracking-tight">
            Travel Planner
          </span>
        </Link>

        <div className="hidden md:flex items-center gap-8">
          <Link href="/" className={`text-sm font-medium transition-colors hover:text-primary ${location === '/' ? 'text-primary' : 'text-muted-foreground'}`}>
            Explore
          </Link>
          <Link href="/bookings" className={`text-sm font-medium transition-colors hover:text-primary ${location === '/bookings' ? 'text-primary' : 'text-muted-foreground'}`}>
            My Bookings
          </Link>
        </div>

        <div className="flex items-center gap-3">
          <SignedOut>
            <SignInButton className="rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-white hover:bg-primary/90">
              Sign In
            </SignInButton>
          </SignedOut>
          <SignedIn>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-4 rounded-full border border-white/20 bg-white/10 px-4 py-2 backdrop-blur-md">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-base font-semibold text-white shadow-sm">
                  {(displayName || "U").charAt(0).toUpperCase()}
                </div>
                <div className="hidden sm:flex flex-col items-start">
                  <span className="text-xs text-muted-foreground">Welcome back,</span>
                  <span className="text-sm font-semibold text-foreground">
                    {isLoading ? "..." : displayName || "there"}
                  </span>
                </div>
              </div>
              <SignOutButton className="flex items-center gap-2 rounded-full border border-border bg-white/10 px-4 py-2 text-sm font-medium text-foreground transition hover:-translate-y-0.5 hover:bg-muted/40">
                <LogOut className="h-4 w-4" />
                <span>Sign Out</span>
              </SignOutButton>
            </div>
          </SignedIn>
          <Button variant="ghost" size="icon" className="md:hidden">
            <Menu className="w-5 h-5" />
          </Button>
        </div>
      </div>
    </nav>
  );
}
