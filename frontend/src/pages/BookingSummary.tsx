import { Link } from "wouter";
import { useEffect, useState } from "react";
import { Navbar } from "components/Navbar";
import { Footer } from "components/Footer";
import { Button } from "components/ui/button";
import { Calendar, CheckCircle2, User } from "lucide-react";

type Booking = {
  bookingId: string;
  hotelName?: string;
  hotelId?: string;
  bookingStatus?: string;
  bookingDate?: string;
  checkInDate?: string;
  checkOutDate?: string;
  numberOfGuests?: number;
  numberOfRooms?: number;
  rooms?: Array<{
    roomId?: string;
    numberOfRooms?: number;
  }>;
  roomType?: string;
  provider?: string;
  confirmationNumber?: string;
  pricing?: Array<{
    roomRate?: number;
    totalAmount?: number;
    nights?: number;
    currency?: string;
  }>;
};

const API_BASE_URL =
  process.env.REACT_APP_API_BASE_URL || "http://localhost:9090";
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

const formatDate = (value?: string) => {
  if (!value) {
    return "TBD";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleDateString();
};

const formatCurrency = (value?: number, currency?: string) => {
  if (value === undefined || value === null) {
    return null;
  }
  const resolved = currency || "USD";
  try {
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency: resolved,
      maximumFractionDigits: 0,
    }).format(value);
  } catch {
    return `${value} ${resolved}`;
  }
};

export default function BookingSummary() {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    const loadBookings = async () => {
      try {
        const userId = getOrCreateUserId();
        const response = await fetch(`${API_BASE_URL}/bookings`, {
          headers: { "x-user-id": userId },
          signal: controller.signal,
        });
        if (!response.ok) {
          throw new Error(`Failed to load bookings: ${response.status}`);
        }
        const data = await response.json();
        if (Array.isArray(data)) {
          setBookings(data);
        } else {
          setBookings([]);
        }
      } catch (err) {
        if ((err as Error)?.name !== "AbortError") {
          setError("Unable to load bookings right now.");
        }
      } finally {
        setLoading(false);
      }
    };
    loadBookings();
    return () => controller.abort();
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-muted/20">
      <Navbar />

      <main className="flex-grow container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto space-y-10">
          <div className="bg-white rounded-3xl border border-border/60 shadow-lg p-8">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-full bg-primary/10 text-primary flex items-center justify-center">
                <CheckCircle2 className="w-7 h-7" />
              </div>
              <div>
                <h1 className="font-display text-3xl font-bold">My Bookings</h1>
                <p className="text-muted-foreground">
                  {loading ? "Loading your bookings..." : `${bookings.length} bookings`}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-3xl border border-border/60 shadow-lg p-8 space-y-6">
            {loading && (
              <p className="text-muted-foreground">Loading bookings...</p>
            )}
            {!loading && error && (
              <p className="text-destructive">{error}</p>
            )}
            {!loading && !error && bookings.length === 0 && (
              <p className="text-muted-foreground">0 bookings.</p>
            )}
            {!loading && !error && bookings.length > 0 && (
              <div className="space-y-4">
                {bookings.map((booking) => {
                  const pricing = booking.pricing?.[0];
                  const priceText = pricing
                    ? formatCurrency(pricing.totalAmount, pricing.currency)
                    : null;
                  const nightsText = pricing?.nights
                    ? `${pricing.nights} nights`
                    : null;
                  return (
                    <div
                      key={booking.bookingId}
                      className="border border-border/60 rounded-2xl p-6 flex flex-col md:flex-row md:items-center md:justify-between gap-6"
                    >
                      <div className="space-y-2">
                        <p className="text-sm text-muted-foreground">Booking ID</p>
                        <h3 className="text-xl font-semibold">
                          {booking.hotelName || booking.hotelId || "Hotel stay"}
                        </h3>
                        <p className="text-sm text-muted-foreground">
                          {booking.bookingId}
                        </p>
                      </div>
                      <div className="space-y-2 text-sm text-muted-foreground">
                        <div className="flex items-center gap-2">
                          <Calendar className="w-4 h-4 text-primary" />
                          <span>
                            {formatDate(booking.checkInDate)} - {formatDate(booking.checkOutDate)}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <User className="w-4 h-4 text-primary" />
                          <span>{booking.numberOfGuests || 0} guests</span>
                        </div>
                        <p>
                          Rooms:{" "}
                          <span className="font-semibold text-foreground">
                            {booking.numberOfRooms || booking.rooms?.length || 0}
                          </span>
                        </p>
                        <p>
                          Status:{" "}
                          <span className="font-semibold text-foreground">
                            {booking.bookingStatus || "PENDING"}
                          </span>
                        </p>
                        {booking.roomType && (
                          <p className="text-muted-foreground">
                            Room:{" "}
                            <span className="font-semibold text-foreground">
                              {booking.roomType}
                            </span>
                          </p>
                        )}
                        {!booking.roomType && booking.provider && (
                          <p className="text-muted-foreground">
                            Provider:{" "}
                            <span className="font-semibold text-foreground">
                              {booking.provider}
                            </span>
                          </p>
                        )}
                      </div>
                      <div className="text-right space-y-2">
                        {priceText && (
                          <p className="text-lg font-semibold text-primary">
                            {priceText}
                          </p>
                        )}
                        {nightsText && (
                          <p className="text-sm text-muted-foreground">{nightsText}</p>
                        )}
                        {booking.confirmationNumber && (
                          <p className="text-xs text-muted-foreground">
                            Confirmation {booking.confirmationNumber}
                          </p>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
            <div className="flex flex-wrap gap-3 pt-4">
              <Button asChild className="rounded-xl bg-primary text-white">
                <Link href="/assistant">Back to chat</Link>
              </Button>
              <Button asChild variant="outline" className="rounded-xl">
                <Link href="/">Explore stays</Link>
              </Button>
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
