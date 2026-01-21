import { Switch, Route, useLocation } from "wouter";
import { useEffect } from "react";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "components/ui/toaster";
import { TooltipProvider } from "components/ui/tooltip";
import NotFound from "pages/not-found";
import Home from "pages/Home";
import Landing from "pages/Landing";
import HotelDetails from "pages/HotelDetails";
import BookingSummary from "pages/BookingSummary";

function BookingsRedirect() {
  const [, setLocation] = useLocation();
  useEffect(() => {
    setLocation("/assistant");
  }, [setLocation]);
  return null;
}

function Router() {
  return (
    <Switch>
      <Route path="/" component={Landing} />
      <Route path="/assistant" component={Home} />
      <Route path="/bookings" component={BookingsRedirect} />
      <Route path="/hotels/:id" component={HotelDetails} />
      <Route path="/book/:hotelId" component={BookingSummary} />
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Router />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
