import { Button } from "@/components/ui/button";
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from "@/components/ui/carousel";
import { AspectRatio } from "@/components/ui/aspect-ratio";
import { ChevronLeft, ChevronRight, Ticket } from "lucide-react";
import { useRef } from "react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";

// Movie data constants
const FEATURED_MOVIES = [
  {
    id: 65650,
    title: "The Good Doctor",
    description: "Dr. Martin Blake, who has spent his life looking for respect, meets an 18-year-old patient named Diane, suffering from a kidney infection, and gets a much-needed boost of self-esteem. However, when her health starts improving, Martin fears losing her, so he begins tampering with her treatment, keeping Diane sick and in the hospital right next to him.",
    image: "https://image.tmdb.org/t/p/original/jPlyFmmh9rHQqIuRtEv0gCsOVPK.jpg",
    rating: "N/A",
  },
  {
    id: 675353,
    title: "Sonic the Hedgehog 2",
    description: "After settling in Green Hills, Sonic is eager to prove he has what it takes to be a true hero. His test comes when Dr. Robotnik returns, this time with a new partner, Knuckles, in search for an emerald that has the power to destroy civilizations. Sonic teams up with his own sidekick, Tails, and together they embark on a globe-trotting journey to find the emerald before it falls into the wrong hands.",
    image: "https://image.tmdb.org/t/p/original/8wwXPG22aNMpPGuXnfm3galoxbI.jpg",
    rating: "N/A",
  },
  {
    id: 157336,
    title: "Interstellar",
    description: "The adventures of a group of explorers who make use of a newly discovered wormhole to surpass the limitations on human space travel and conquer the vast distances involved in an interstellar voyage.",
    image: "https://image.tmdb.org/t/p/original/vgnoBSVzWAV9sNQUORaDGvDp7wx.jpg",
    rating: "N/A",
  },
];

const RECOMMENDED_MOVIES = [
  {
    id: 1,
    title: "Soul",
    image: "https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=800&q=80",
    year: "2020",
  },
  {
    id: 2,
    title: "The Pope's Exorcist",
    image: "https://images.unsplash.com/photo-1559583109-3e7968136c99?auto=format&fit=crop&w=800&q=80",
    year: "2023",
  },
  {
    id: 3,
    title: "Oppenheimer",
    image: "https://images.unsplash.com/photo-1440404653325-ab127d49abc1?auto=format&fit=crop&w=800&q=80",
    year: "2023",
  },
  {
    id: 4,
    title: "Barbie",
    image: "https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=800&q=80",
    year: "2023",
  },
  {
    id: 5,
    title: "Avatar 2",
    image: "https://images.unsplash.com/photo-1559583109-3e7968136c99?auto=format&fit=crop&w=800&q=80",
    year: "2022",
  },
  {
    id: 6,
    title: "The Flash",
    image: "https://images.unsplash.com/photo-1440404653325-ab127d49abc1?auto=format&fit=crop&w=800&q=80",
    year: "2023",
  },
];

const THEATER_MOVIES = [
  {
    id: 1,
    title: "Soul",
    image: "https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=800&q=80",
    year: "2020",
  },
  {
    id: 2,
    title: "The Pope's Exorcist",
    image: "https://images.unsplash.com/photo-1559583109-3e7968136c99?auto=format&fit=crop&w=800&q=80",
    year: "2023",
  },
  {
    id: 3,
    title: "Soul",
    image: "https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=800&q=80",
    year: "2020",
  },
  {
    id: 4,
    title: "Soul",
    image: "https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=800&q=80",
    year: "2020",
  },
  {
    id: 5,
    title: "The Pope's Exorcist",
    image: "https://images.unsplash.com/photo-1559583109-3e7968136c99?auto=format&fit=crop&w=800&q=80",
    year: "2023",
  },
  {
    id: 6,
    title: "Soul",
    image: "https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=800&q=80",
    year: "2020",
  },
  {
    id: 7,
    title: "Soul",
    image: "https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=800&q=80",
    year: "2020",
  },
  {
    id: 8,
    title: "The Pope's Exorcist",
    image: "https://images.unsplash.com/photo-1559583109-3e7968136c99?auto=format&fit=crop&w=800&q=80",
    year: "2023",
  },
  {
    id: 9,
    title: "Soul",
    image: "https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=800&q=80",
    year: "2020",
  },
  {
    id: 10,
    title: "Soul",
    image: "https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=800&q=80",
    year: "2020",
  },
  {
    id: 11,
    title: "The Pope's Exorcist",
    image: "https://images.unsplash.com/photo-1559583109-3e7968136c99?auto=format&fit=crop&w=800&q=80",
    year: "2023",
  },
  {
    id: 12,
    title: "Soul",
    image: "https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=800&q=80",
    year: "2020",
  },
];

interface Movie {
  id: number;
  title: string;
  image: string;
  year?: string;
  description?: string;
  rating?: string;
}

function MoviePoster({ movie, className = "" }: { movie: Movie; className?: string }) {
  return (
    <div className={`flex flex-col gap-2 group relative ${className}`}>
      <AspectRatio ratio={2/3}>
        <img
          src={movie.image}
          alt={movie.title}
          className="w-full h-full object-cover rounded-[20px] transition-transform hover:scale-105"
        />
        <Sheet>
          <SheetTrigger asChild>
            <Button 
              className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-primary-300 hover:bg-primary-200 text-bg-100 rounded-full px-6 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-center gap-2"
            >
              <Ticket className="w-4 h-4" />
              Get Tickets
            </Button>
          </SheetTrigger>
          <SheetContent className="bg-bg-200 border-primary-200 text-text-100 z-[var(--z-modal)]">
            <SheetHeader>
              <SheetTitle className="text-text-100">Purchase Tickets</SheetTitle>
              <SheetDescription className="text-text-200">
                Select your tickets for {movie.title}
              </SheetDescription>
            </SheetHeader>
            <div className="mt-8 space-y-6">
              <div className="space-y-4">
                <h3 className="text-h4">Showtime</h3>
                <div className="grid grid-cols-3 gap-2">
                  {["12:30 PM", "3:00 PM", "5:30 PM", "8:00 PM", "10:30 PM"].map((time) => (
                    <Button
                      key={time}
                      variant="outline"
                      className="border-primary-200 text-text-100 hover:bg-primary-200/20"
                    >
                      {time}
                    </Button>
                  ))}
                </div>
              </div>
              
              <div className="space-y-4">
                <h3 className="text-h4">Tickets</h3>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span>Adult ($14.99)</span>
                    <div className="flex items-center gap-2">
                      <Button variant="outline" size="icon" className="h-8 w-8">-</Button>
                      <span className="w-8 text-center">0</span>
                      <Button variant="outline" size="icon" className="h-8 w-8">+</Button>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Child ($9.99)</span>
                    <div className="flex items-center gap-2">
                      <Button variant="outline" size="icon" className="h-8 w-8">-</Button>
                      <span className="w-8 text-center">0</span>
                      <Button variant="outline" size="icon" className="h-8 w-8">+</Button>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Senior ($12.99)</span>
                    <div className="flex items-center gap-2">
                      <Button variant="outline" size="icon" className="h-8 w-8">-</Button>
                      <span className="w-8 text-center">0</span>
                      <Button variant="outline" size="icon" className="h-8 w-8">+</Button>
                    </div>
                  </div>
                </div>
              </div>
              <div className="space-y-4">
                <h3 className="text-h4">Payment Information</h3>
                <input
                  type="text"
                  placeholder="Cardholder Name"
                  className="block w-full px-4 py-2 bg-bg-100 border border-primary-200 rounded-md text-text-100 focus:outline-none focus:ring-1 focus:ring-primary-200"
                />
                <input
                  type="text"
                  placeholder="Card Number"
                  className="block w-full px-4 py-2 bg-bg-100 border border-primary-200 rounded-md text-text-100 focus:outline-none focus:ring-1 focus:ring-primary-200"
                />
                <div className="flex gap-4">
                  <input
                    type="text"
                    placeholder="Expiry Date (MM/YY)"
                    className="block w-full px-4 py-2 bg-bg-100 border border-primary-200 rounded-md text-text-100 focus:outline-none focus:ring-1 focus:ring-primary-200"
                  />
                  <input
                    type="text"
                    placeholder="CVV"
                    className="block w-full px-4 py-2 bg-bg-100 border border-primary-200 rounded-md text-text-100 focus:outline-none focus:ring-1 focus:ring-primary-200"
                  />
                </div>
              </div>
              <div className="pt-4 border-t border-primary-200">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-h4">Total</span>
                  <span className="text-h4">$0.00</span>
                </div>
                <Button className="w-full bg-primary-300 hover:bg-primary-200 text-bg-100 rounded-full">
                  Continue to Seats
                </Button>
              </div>
            </div>
          </SheetContent>
        </Sheet>
      </AspectRatio>
      <div className="px-1">
        <h3 className="text-text-100 font-semibold truncate">{movie.title}</h3>
        <p className="text-text-200 text-sm">{movie.year}</p>
      </div>
    </div>
  );
}

export function Home() {
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  const scrollMovies = (direction: 'left' | 'right') => {
    if (!scrollContainerRef.current) return;
    
    const container = scrollContainerRef.current;
    const scrollAmount = 600;
    const targetScroll = direction === 'left' 
      ? container.scrollLeft - scrollAmount 
      : container.scrollLeft + scrollAmount;
    
    container.scrollTo({
      left: targetScroll,
      behavior: 'smooth'
    });
  };

  return (
    <main className="min-h-screen bg-bg-100">
      {/* Featured Movies Carousel */}
      <section className="relative w-full">
        <Carousel className="w-full">
          <CarouselContent>
            {FEATURED_MOVIES.map((movie) => (
              <CarouselItem key={movie.id}>
                <div className="relative">
                  <AspectRatio ratio={16/9}>
                    <div className="relative w-full h-full">
                      <img
                        src={movie.image}
                        alt={movie.title}
                        className="absolute inset-0 w-full h-full object-cover object-center"
                      />
                    </div>
                  </AspectRatio>
                  <div className="absolute inset-0 bg-gradient-to-t from-bg-100 via-bg-100/50 to-transparent" />
                  <div className="absolute bottom-16 left-16 right-16">
                    <div className="flex items-center gap-2 mb-2">
                      <img src="https://upload.wikimedia.org/wikipedia/commons/6/69/IMDB_Logo_2016.svg" alt="IMDB" className="h-6" />
                      <span className="text-text-100">{movie.rating}</span>
                    </div>
                    <h2 className="text-h2 text-text-100 mb-2">{movie.title}</h2>
                    <p className="text-text-200 max-w-xl mb-4">{movie.description}</p>
                    <div className="flex gap-4">
                      <Sheet>
                        <SheetTrigger asChild>
                          <Button className="bg-primary-300 hover:bg-primary-200 text-bg-100 flex items-center gap-2">
                            <Ticket className="w-4 h-4" />
                            CHECKOUT MOVIE
                          </Button>
                        </SheetTrigger>
                        <SheetContent className="bg-bg-200 border-primary-200 text-text-100 z-[var(--z-modal)]">
                          <SheetHeader>
                            <SheetTitle className="text-text-100">Purchase Tickets</SheetTitle>
                            <SheetDescription className="text-text-200">
                              Select your tickets for {movie.title}
                            </SheetDescription>
                          </SheetHeader>
                          <div className="mt-8 space-y-6">
                            <div className="space-y-4">
                              <h3 className="text-h4">Showtime</h3>
                              <div className="grid grid-cols-3 gap-2">
                                {["12:30 PM", "3:00 PM", "5:30 PM", "8:00 PM", "10:30 PM"].map((time) => (
                                  <Button
                                    key={time}
                                    variant="outline"
                                    className="border-primary-200 text-text-100 hover:bg-primary-200/20"
                                  >
                                    {time}
                                  </Button>
                                ))}
                              </div>
                            </div>
                            <div className="space-y-4">
                              <h3 className="text-h4">Payment Information</h3>
                              <input
                                type="text"
                                placeholder="Cardholder Name"
                                className="block w-full px-4 py-2 bg-bg-100 border border-primary-200 rounded-md text-text-100 focus:outline-none focus:ring-1 focus:ring-primary-200"
                              />
                              <input
                                type="text"
                                placeholder="Card Number"
                                className="block w-full px-4 py-2 bg-bg-100 border border-primary-200 rounded-md text-text-100 focus:outline-none focus:ring-1 focus:ring-primary-200"
                              />
                              <div className="flex gap-4">
                                <input
                                  type="text"
                                  placeholder="Expiry Date (MM/YY)"
                                  className="block w-full px-4 py-2 bg-bg-100 border border-primary-200 rounded-md text-text-100 focus:outline-none focus:ring-1 focus:ring-primary-200"
                                />
                                <input
                                  type="text"
                                  placeholder="CVV"
                                  className="block w-full px-4 py-2 bg-bg-100 border border-primary-200 rounded-md text-text-100 focus:outline-none focus:ring-1 focus:ring-primary-200"
                                />
                              </div>
                            </div>
                            <div className="pt-4 border-t border-primary-200">
                              <div className="flex items-center justify-between mb-4">
                                <span className="text-h4">Total</span>
                                <span className="text-h4">$0.00</span>
                              </div>
                              <Button className="w-full bg-primary-300 hover:bg-primary-200 text-bg-100 rounded-full">
                                Continue to Seats
                              </Button>
                            </div>
                          </div>
                        </SheetContent>
                      </Sheet>
                      <Button variant="outline" className="border-primary-300 text-primary-300 hover:bg-primary-300 hover:text-bg-100">
                        Add to Watchlist
                      </Button>
                    </div>
                  </div>
                </div>
              </CarouselItem>
            ))}
          </CarouselContent>
          <CarouselPrevious className="left-4 rounded-full bg-bg-200/80 hover:bg-bg-200 h-12 w-12" />
          <CarouselNext className="right-4 rounded-full bg-bg-200/80 hover:bg-bg-200 h-12 w-12" />
        </Carousel>
      </section>

      {/* Recommended Section - Horizontal Scroll */}
      <section className="max-w-[1400px] mx-auto px-4 py-12">
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-h3 text-text-100">Recommended For You</h2>
          <div className="flex gap-2">
            <Button 
              variant="outline" 
              size="icon" 
              className="rounded-full"
              onClick={() => scrollMovies('left')}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button 
              variant="outline" 
              size="icon" 
              className="rounded-full"
              onClick={() => scrollMovies('right')}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
        <div 
          ref={scrollContainerRef}
          className="flex gap-4 overflow-x-auto pb-4 scrollbar-hide scroll-smooth"
        >
          {RECOMMENDED_MOVIES.map((movie) => (
            <MoviePoster key={movie.id} movie={movie} className="min-w-[200px]" />
          ))}
        </div>
      </section>

      {/* Out In Theaters Now - Grid */}
      <section className="max-w-[1400px] mx-auto px-4 py-12">
        <h2 className="text-h3 text-text-100 mb-8">Out In Your Theater Now</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {THEATER_MOVIES.map((movie) => (
            <MoviePoster key={movie.id} movie={movie} />
          ))}
        </div>
        <div className="flex justify-center mt-8">
          <Button variant="outline" className="text-text-100">
            Load More
          </Button>
        </div>
      </section>
    </main>
  );
}