import { Link } from "wouter";
import { Navbar } from "components/Navbar";
import { Footer } from "components/Footer";
import { Button } from "components/ui/button";
import { CheckCircle2 } from "lucide-react";

export default function BookingSummary() {
  return (
    <div className="min-h-screen flex flex-col bg-muted/20">
      <Navbar />

      <main className="flex-grow container mx-auto px-4 py-16">
        <div className="max-w-2xl mx-auto bg-white rounded-3xl border border-border/60 shadow-lg p-8 text-center space-y-6">
          <div className="w-16 h-16 rounded-full bg-primary/10 text-primary flex items-center justify-center mx-auto">
            <CheckCircle2 className="w-8 h-8" />
          </div>
          <h1 className="font-display text-3xl font-bold">Bookings are coming soon</h1>
          <p className="text-muted-foreground">
            We removed booking checkout for now while we finalize the flow. You can still explore
            stays and plan trips with the assistant.
          </p>
          <div className="flex justify-center gap-3">
            <Button asChild className="rounded-xl bg-primary text-white">
              <Link href="/assistant">Back to chat</Link>
            </Button>
            <Button asChild variant="outline" className="rounded-xl">
              <Link href="/">Explore stays</Link>
            </Button>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
