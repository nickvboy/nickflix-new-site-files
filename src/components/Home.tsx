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
import { useRef, useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";

// Movie interface
interface Movie {
  id: number;
  title: string;
  image?: string;
  poster_path?: string;
  backdrop_path?: string;
  year?: string;
  release_date?: string;
  description?: string;
  overview?: string;
  rating?: string;
  vote_average?: number;
}

function MoviePoster({ movie, className = "" }: { movie: Movie; className?: string }) {
  // Check if this is a recommended movie by checking if the className includes the min-width
  const isRecommended = className?.includes('min-w-[160px]');
  
  // Determine the image URL
  const imageUrl = movie.image || 
    (movie.poster_path ? `https://image.tmdb.org/t/p/w500${movie.poster_path}` : '');
  
  // Extract year from release_date if available
  const year = movie.year || (movie.release_date ? movie.release_date.substring(0, 4) : '');
  
  return (
    <div className={`flex flex-col gap-1 group relative ${className}`}>
      <Link to={`/movie/${movie.id}`} className="w-full h-full">
        <AspectRatio ratio={2/3} className="w-full overflow-hidden rounded-[20px]">
          <div className="relative w-full h-full">
            <div className="absolute inset-0 transform transition-all duration-300 group-hover:scale-105">
              <img
                src={imageUrl}
                alt={movie.title}
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-bg-100/90 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            </div>
            <Sheet>
              <SheetTrigger asChild>
                <Button 
                  className="absolute bottom-4 left-1/2 -translate-x-1/2 translate-y-8 group-hover:translate-y-0 bg-primary-300 hover:bg-primary-200 text-bg-100 rounded-full px-6 transition-all duration-300 flex items-center gap-2 opacity-0 group-hover:opacity-100"
                  onClick={(e) => e.stopPropagation()}
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
          </div>
        </AspectRatio>
        <div className="mt-2">
          <h3 className="text-text-100 font-medium truncate">{movie.title}</h3>
          {year && <p className="text-text-200 text-sm">{year}</p>}
        </div>
      </Link>
    </div>
  );
}

export function Home() {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [featuredMovies, setFeaturedMovies] = useState<Movie[]>([]);
  const [recommendedMovies, setRecommendedMovies] = useState<Movie[]>([]);
  const [theaterMovies, setTheaterMovies] = useState<Movie[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchMovies = async () => {
      try {
        const response = await fetch('/movie_data/movies_data.json');
        if (!response.ok) {
          throw new Error('Failed to fetch movie data');
        }
        
        const data = await response.json();
        
        // Select 3 random movies with backdrops for featured section
        const moviesWithBackdrops = data.filter((movie: any) => 
          movie.backdrop_path && movie.overview && movie.overview.length > 50
        );
        const randomFeatured = getRandomItems(moviesWithBackdrops, 3).map((movie: any) => ({
          id: movie.id,
          title: movie.title || movie.original_title,
          description: movie.overview,
          image: `https://image.tmdb.org/t/p/original${movie.backdrop_path}`,
          rating: movie.vote_average ? `${movie.vote_average.toFixed(1)}/10` : 'N/A',
        }));
        
        // Select random movies for recommended section
        const randomRecommended = getRandomItems(data, 11).map((movie: any) => ({
          id: movie.id,
          title: movie.title || movie.original_title,
          poster_path: movie.poster_path,
          release_date: movie.release_date,
        }));
        
        // Select random movies for theater section
        const randomTheater = getRandomItems(data, 12).map((movie: any) => ({
          id: movie.id,
          title: movie.title || movie.original_title,
          poster_path: movie.poster_path,
          release_date: movie.release_date,
        }));
        
        setFeaturedMovies(randomFeatured);
        setRecommendedMovies(randomRecommended);
        setTheaterMovies(randomTheater);
      } catch (error) {
        console.error('Error fetching movie data:', error);
        // Fallback to empty arrays if there's an error
        setFeaturedMovies([]);
        setRecommendedMovies([]);
        setTheaterMovies([]);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchMovies();
  }, []);
  
  // Helper function to get random items from an array
  const getRandomItems = (array: any[], count: number) => {
    const shuffled = [...array].sort(() => 0.5 - Math.random());
    return shuffled.slice(0, count);
  };

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

  // Show loading state if data is still being fetched
  if (isLoading) {
    return (
      <main className="min-h-screen bg-bg-100 flex items-center justify-center">
        <div className="text-text-100">Loading movies...</div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-bg-100">
      {/* Featured Movies Carousel */}
      <section className="relative w-full">
        <Carousel className="w-full" 
          opts={{
            loop: true,
            align: "start",
          }}
          autoScroll={true}
          autoScrollInterval={6000}
        >
          <CarouselContent>
            {featuredMovies.map((movie) => (
              <CarouselItem key={movie.id}>
                <div className="relative">
                  <div className="relative w-full h-[550px]">
                    <img
                      src={movie.image}
                      alt={movie.title}
                      className="absolute inset-0 w-full h-full object-cover object-center"
                    />
                  </div>
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
          {recommendedMovies.map((movie) => (
            <MoviePoster key={movie.id} movie={movie} className="min-w-[160px] w-[160px] flex-shrink-0" />
          ))}
        </div>
      </section>

      {/* Out In Theaters Now - Grid */}
      <section className="max-w-[1400px] mx-auto px-4 py-12">
        <h2 className="text-h3 text-text-100 mb-8">Out In Your Theater Now</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {theaterMovies.map((movie) => (
            <MoviePoster key={movie.id} movie={movie} className="w-full px-0" />
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