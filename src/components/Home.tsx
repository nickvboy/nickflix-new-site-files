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
    id: 447404,
    title: "Pokémon Detective Pikachu",
    image: "https://image.tmdb.org/t/p/w500/uhWvnFgg3BNlcUz0Re1HfQqIcCD.jpg",
    year: "2019",
  },
  {
    id: 281338,
    title: "War for the Planet of the Apes",
    image: "https://image.tmdb.org/t/p/w500/mMA1qhBFgZX8O36qPPTC016kQl1.jpg",
    year: "2017",
  },
  {
    id: 795514,
    title: "The Fallout",
    image: "https://image.tmdb.org/t/p/w500/4ByHl9XRKR2iXbvF0ZilMRD1RcL.jpg",
    year: "2021",
  },
  {
    id: 364689,
    title: "Ferdinand",
    image: "https://image.tmdb.org/t/p/w500/rMm94JsRfcOPiPVsTRcBiiVBOhz.jpg",
    year: "2017",
  },
  {
    id: 268896,
    title: "Pacific Rim: Uprising",
    image: "https://image.tmdb.org/t/p/w500/nFWhttU8PM50t25NPdy7PE7rv3G.jpg",
    year: "2018",
  },
  {
    id: 864,
    title: "Cool Runnings",
    image: "https://image.tmdb.org/t/p/w500/6fXuGEb7EqGmAeUodxm7l5ELPZ.jpg",
    year: "1993",
  },
  {
    id: 1084244,
    title: "Toy Story 5",
    image: "https://image.tmdb.org/t/p/w500/i4UtdsApMwXQkGD2mBDroJSJZsk.jpg",
    year: "2026",
  },
  {
    id: 315635,
    title: "Spider-Man: Homecoming",
    image: "https://image.tmdb.org/t/p/w500/c24sv2weTHPsmDa7jEMN0m2P3RT.jpg",
    year: "2017",
  },
  {
    id: 20352,
    title: "Despicable Me",
    image: "https://image.tmdb.org/t/p/w500/9lOloREsAhBu0pEtU0BgeR1rHyo.jpg",
    year: "2010",
  },
  {
    id: 585083,
    title: "Hotel Transylvania: Transformania",
    image: "https://image.tmdb.org/t/p/w500/teCy1egGQa0y8ULJvlrDHQKnxBL.jpg",
    year: "2022",
  },
  {
    id: 507089,
    title: "Five Nights at Freddy's",
    image: "https://image.tmdb.org/t/p/w500/4dKRTUylqwXQ4VJz0BS84fqW2wa.jpg",
    year: "2023",
  }
];

const THEATER_MOVIES = [
  {
    id: 787699,
    title: "Wonka",
    image: "https://image.tmdb.org/t/p/w500/qhb1qOilapbapxWQn9jtRCMwXJF.jpg",
    year: "2023",
  },
  {
    id: 137,
    title: "Groundhog Day",
    image: "https://image.tmdb.org/t/p/w500/gCgt1WARPZaXnq523ySQEUKinCs.jpg",
    year: "1993",
  },
  {
    id: 99861,
    title: "Avengers: Age of Ultron",
    image: "https://image.tmdb.org/t/p/w500/4ssDuvEDkSArWEdyBl2X5EHvYKU.jpg",
    year: "2015",
  },
  {
    id: 14574,
    title: "The Boy in the Striped Pyjamas",
    image: "https://image.tmdb.org/t/p/w500/sLwYSEVVV3r047cjrpRAbGgNsfL.jpg",
    year: "2008",
  },
  {
    id: 337404,
    title: "Cruella",
    image: "https://image.tmdb.org/t/p/w500/wToO8opxkGwKgSfJ1JK8tGvkG6U.jpg",
    year: "2021",
  },
  {
    id: 760883,
    title: "Blood Red Sky",
    image: "https://image.tmdb.org/t/p/w500/v7aOJKI5vxCHotHvN8O7SR6SpP6.jpg",
    year: "2021",
  },
  {
    id: 20526,
    title: "TRON: Legacy",
    image: "https://image.tmdb.org/t/p/w500/vuifSABRpSnxCAOxEnWpNbZSXpp.jpg",
    year: "2010",
  },
  {
    id: 1710,
    title: "Copycat",
    image: "https://image.tmdb.org/t/p/w500/oMgwJb016znNZcpDR20eXxZoW8A.jpg",
    year: "1995",
  },
  {
    id: 11197,
    title: "Evil",
    image: "https://image.tmdb.org/t/p/w500/a4qQlHDWshHGEbJWfCoKKlzgsh.jpg",
    year: "2003",
  },
  {
    id: 260513,
    title: "Incredibles 2",
    image: "https://image.tmdb.org/t/p/w500/9lFKBtaVIhP7E2Pk0IY1CwTKTMZ.jpg",
    year: "2018",
  },
  {
    id: 1688,
    title: "Conquest of the Planet of the Apes",
    image: "https://image.tmdb.org/t/p/w500/lZ1pUxJCO14ObrhDuxTBuYm0tjN.jpg",
    year: "1972",
  },
  {
    id: 105864,
    title: "The Good Dinosaur",
    image: "https://image.tmdb.org/t/p/w500/8RSkxOO80btfKjyiC5ZiTaCHIT8.jpg",
    year: "2015",
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
      <AspectRatio ratio={2/3} className="w-full">
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
        <Carousel className="w-full" opts={{
          loop: true,
          align: "start",
        }}>
          <CarouselContent>
            {FEATURED_MOVIES.map((movie) => (
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
          {RECOMMENDED_MOVIES.map((movie) => (
            <MoviePoster key={movie.id} movie={movie} className="min-w-[160px] w-[160px] flex-shrink-0" />
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