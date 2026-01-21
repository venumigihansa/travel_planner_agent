import { Navbar } from "components/Navbar";
import { Footer } from "components/Footer";
import { useHotels } from "hooks/use-hotels";
import { motion } from "framer-motion";
import { Button } from "components/ui/button";
import { useLocation } from "wouter";
import { ArrowRight, Sparkles, MapPin, Star } from "lucide-react";

export default function Landing() {
  const { data: hotels } = useHotels();
  const [, setLocation] = useLocation();

  const trendingLocations = [
    { name: "Maldives", image: "https://images.unsplash.com/photo-1514282401047-d79a71a590e8?q=80&w=1000&auto=format&fit=crop" },
    { name: "Kyoto", image: "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?q=80&w=1000&auto=format&fit=crop" },
    { name: "Swiss Alps", image: "https://images.unsplash.com/photo-1531210483974-4f8c1f33fd35?q=80&w=1000&auto=format&fit=crop" }
  ];

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Navbar />
      
      <main className="flex-grow">
        {/* Hero Section */}
        <section className="relative h-[80vh] flex items-center justify-center overflow-hidden">
          <div className="absolute inset-0 z-0">
            <img 
              src="https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?q=80&w=2070&auto=format&fit=crop" 
              alt="Travel background" 
              className="w-full h-full object-cover brightness-50"
            />
          </div>
          
          <div className="relative z-10 text-center text-white px-4 max-w-4xl space-y-8">
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
            >
              <h1 className="text-5xl md:text-7xl font-display font-bold mb-6 drop-shadow-xl">
                Your Personal AI <br />
                <span className="text-accent">Travel Architect</span>
              </h1>
              <p className="text-xl md:text-2xl font-medium text-white/90 mb-10 drop-shadow-md">
                Stop searching. Start experiencing. Let our AI plan your entire journey.
              </p>
              <Button 
                size="lg" 
                onClick={() => setLocation("/assistant")}
                className="bg-accent hover:bg-accent/90 text-primary font-bold text-lg px-8 py-6 rounded-2xl h-auto group active-elevate-2 shadow-2xl"
              >
                Start Planning Now
                <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </Button>
            </motion.div>
          </div>
        </section>

        {/* Trending Locations */}
        <section className="py-20 container mx-auto px-4">
          <div className="flex items-center gap-3 mb-12">
            <Sparkles className="text-accent w-8 h-8" />
            <h2 className="text-4xl font-display font-bold">Trending Destinations</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {trendingLocations.map((loc, idx) => (
              <motion.div
                key={loc.name}
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: idx * 0.2 }}
                className="relative h-96 rounded-3xl overflow-hidden group cursor-pointer hover-elevate"
              >
                <img src={loc.image} alt={loc.name} className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110" />
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent flex items-end p-8">
                  <h3 className="text-3xl font-bold text-white font-display">{loc.name}</h3>
                </div>
              </motion.div>
            ))}
          </div>
        </section>

        {/* Featured Hotels */}
        <section className="py-20 bg-secondary/20">
          <div className="container mx-auto px-4">
            <div className="flex justify-between items-end mb-12">
              <div>
                <h2 className="text-4xl font-display font-bold mb-2">Editor's Choice</h2>
                <p className="text-muted-foreground">Hand-picked luxury stays around the world</p>
              </div>
              <Button variant="ghost" className="text-primary font-semibold" onClick={() => setLocation("/assistant")}>
                View all in chat
              </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {hotels?.slice(0, 3).map((hotel) => (
                <motion.div
                  key={hotel.id}
                  whileHover={{ y: -10 }}
                  className="bg-card rounded-3xl overflow-hidden shadow-xl border border-border/50 group"
                >
                  <div className="relative h-64 overflow-hidden">
                    <img src={hotel.imageUrl} alt={hotel.name} className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110" />
                    <div className="absolute top-4 right-4 bg-white/90 backdrop-blur-sm px-3 py-1 rounded-full flex items-center gap-1">
                      <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                      <span className="text-sm font-bold">{hotel.rating}</span>
                    </div>
                  </div>
                  <div className="p-6">
                    <div className="flex items-center gap-1 text-muted-foreground text-sm mb-2">
                      <MapPin className="w-3 h-3" />
                      {hotel.location}
                    </div>
                    <h3 className="text-xl font-bold mb-4 font-display line-clamp-1">{hotel.name}</h3>
                    <div className="flex justify-between items-center">
                      <div>
                        <span className="text-2xl font-bold text-primary">${hotel.pricePerNight}</span>
                        <span className="text-muted-foreground text-sm"> / night</span>
                      </div>
                      <Button onClick={() => setLocation(`/hotels/${hotel.id}`)} variant="outline" className="rounded-xl">View Details</Button>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
