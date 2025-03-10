import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ChevronLeft, Play } from "lucide-react";
import { AspectRatio } from "@/components/ui/aspect-ratio";
import { TheaterSelector } from "@/components/TheaterSelector";

interface Movie {
  id: number;
  title: string;
  original_title?: string;
  overview?: string;
  release_date?: string;
  vote_average?: number;
  poster_path?: string;
  backdrop_path?: string;
  backdrops?: string[];
  genres?: { id: number; name: string }[];
  runtime?: number;
  tagline?: string;
  directors?: {
    id: number;
    name: string;
    job: string;
    profile_path?: string;
  }[];
  cast?: {
    id: number;
    name: string;
    character: string;
    profile_path?: string;
  }[];
}

export function MovieDetails() {
  const { id } = useParams<{ id: string }>();
  const [movie, setMovie] = useState<Movie | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMovieDetails = async () => {
      setIsLoading(true);
      try {
        const response = await fetch("/movie_data/movies_data.json");
        if (!response.ok) {
          throw new Error("Failed to fetch movie data");
        }
        
        const data = await response.json();
        const movieData = data.find((m: Movie) => m.id.toString() === id);
        
        if (!movieData) {
          setError("Movie not found");
          return;
        }
        
        setMovie(movieData);
      } catch (err) {
        setError("An error occurred while fetching movie data");
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    if (id) {
      fetchMovieDetails();
    }
  }, [id]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg-300">
        <p className="text-xl text-primary-300">Loading...</p>
      </div>
    );
  }

  if (error || !movie) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-bg-300">
        <p className="text-xl text-red-500 mb-4">{error || "Movie not found"}</p>
        <Link to="/">
          <Button className="bg-primary-300 hover:bg-primary-200 text-primary-100 rounded-full">
            Back to Home
          </Button>
        </Link>
      </div>
    );
  }

  // Format runtime from minutes to hours and minutes
  const formatRuntime = (minutes?: number) => {
    if (!minutes) return "N/A";
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
  };

  // Background image URL - prioritize backdrops array
  const backgroundImage = movie.backdrops && movie.backdrops.length > 0 
    ? movie.backdrops[0] // Use the first backdrop URL directly from the array
    : movie.backdrop_path 
      ? `https://image.tmdb.org/t/p/original${movie.backdrop_path}`
      : "";

  return (
    <main className="min-h-screen bg-bg-300">
      {/* Hero section with movie backdrop */}
      <div 
        className="relative w-full h-[60vh] bg-cover bg-center"
        style={{ 
          backgroundImage: `url(${backgroundImage})`,
          backgroundSize: "cover",
          backgroundPosition: "center top"
        }}
      >
        {/* Overlay gradient */}
        <div className="absolute inset-0 bg-gradient-to-t from-bg-300 via-bg-300/70 to-transparent"></div>
        
        {/* Content */}
        <div className="container mx-auto px-4 relative z-10 h-full flex flex-col justify-end pb-4">
          <div className="flex flex-col md:flex-row gap-4 items-start">
            {/* Movie poster */}
            <div className="w-1/3 md:w-1/4 lg:w-1/5 -mb-16 md:-mb-24 transform scale-100 origin-top">
              <AspectRatio ratio={2/3} className="overflow-hidden rounded-[16px] shadow-xl border border-primary-200/30">
                <img 
                  src={movie.poster_path ? `https://image.tmdb.org/t/p/w500${movie.poster_path}` : ""} 
                  alt={movie.title} 
                  className="w-full h-full object-cover"
                />
              </AspectRatio>
            </div>
            
            {/* Movie info */}
            <div className="w-full md:w-3/4 lg:w-4/5 text-white">
              <div className="flex flex-col md:flex-row gap-2">
                <div className="w-full md:w-2/3 md:pr-8">
                  <h1 className="text-3xl md:text-5xl font-bold mb-1">{movie.title}</h1>
                  
                  {/* Genre pills */}
                  <div className="flex flex-wrap gap-1 mb-2">
                    {movie.genres && movie.genres.length > 0 ? (
                      movie.genres.slice(0, 3).map(genre => (
                        <span key={genre.id} className="px-2 py-0.5 bg-primary-100 text-primary-300 text-xs rounded-full">
                          {genre.name}
                        </span>
                      ))
                    ) : null}
                  </div>
                  
                  {/* Metadata row */}
                  <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs md:text-sm mb-2 text-text-200">
                    {movie.release_date && (
                      <span>{new Date(movie.release_date).getFullYear()}</span>
                    )}
                    {movie.runtime && (
                      <span>{formatRuntime(movie.runtime)}</span>
                    )}
                    {movie.vote_average && (
                      <span className="flex items-center">
                        <span className="mr-1 text-yellow-500">★</span>
                        {movie.vote_average.toFixed(1)}/10
                      </span>
                    )}
                  </div>
                  
                  {/* Tagline */}
                  {movie.tagline && (
                    <p className="text-primary-300 italic mb-2 text-base">{movie.tagline}</p>
                  )}
                  
                  {/* Overview */}
                  {movie.overview && (
                    <p className="text-xs md:text-sm text-text-200 mb-4 max-w-3xl leading-relaxed">
                      {movie.overview}
                    </p>
                  )}
                  
                  {/* Action buttons */}
                  <div className="flex flex-wrap gap-3 mb-4 md:mb-0">
                    <Button className="bg-primary-300 hover:bg-primary-200 text-primary-100 rounded-full px-6 py-3 text-sm">
                      Add to Watchlist
                    </Button>
                    <Button 
                      variant="outline" 
                      className="border-primary-300 text-primary-300 hover:bg-primary-300/20 rounded-full px-6 py-3 text-sm flex items-center gap-2"
                    >
                      <Play className="h-4 w-4" />
                      Watch Trailer
                    </Button>
                  </div>
                </div>
                
                {/* Credits section - right side */}
                <div className="w-full md:w-1/3 space-y-4 md:-mt-1">
                  {/* Directors section */}
                  <div>
                    <h2 className="text-lg font-bold mb-1 text-text-100 border-b-4 border-primary-200 pb-1">
                      Director
                    </h2>
                    {movie.directors && movie.directors.length > 0 ? (
                      <div className="space-y-0.5 pt-0.5">
                        {movie.directors.map(director => (
                          <div key={director.id} className="text-text-200 text-sm">
                            {director.name} {director.job === "Director" ? "" : `(${director.job})`}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-gray-400 text-sm">Information not available</div>
                    )}
                  </div>
                  
                  {/* Writers section - using directors for demo */}
                  <div>
                    <h2 className="text-lg font-bold mb-1 text-text-100 border-b-4 border-primary-200 pb-1">
                      Writers
                    </h2>
                    {movie.directors && movie.directors.length > 0 ? (
                      <div className="space-y-0.5 pt-0.5">
                        {movie.directors.map(director => (
                          <div key={director.id} className="text-text-200 text-sm">
                            {director.name}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-gray-400 text-sm">Information not available</div>
                    )}
                  </div>
                  
                  {/* Stars section */}
                  <div>
                    <h2 className="text-lg font-bold mb-1 text-text-100 border-b-4 border-primary-200 pb-1">
                      Stars
                    </h2>
                    {movie.cast && movie.cast.length > 0 ? (
                      <div className="space-y-0.5 pt-0.5">
                        {movie.cast.slice(0, 3).map(actor => (
                          <div key={actor.id} className="text-text-200 text-sm">
                            {actor.name}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-gray-400 text-sm">Information not available</div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Theater Selector Section */}
      <div className="container mx-auto px-4 py-8 mt-24 md:mt-28">
        <div className="mb-6">
          <h2 className="text-2xl md:text-3xl font-bold text-text-100">Select a Showtime</h2>
          <p className="text-text-200 text-sm md:text-base">Choose a date, time, format, and theater to watch {movie.title}</p>
        </div>
        
        <TheaterSelector movieId={id} movieTitle={movie.title} className="mt-4" />
        
        <div className="mt-8 flex justify-center">
          <Button className="bg-primary-300 hover:bg-primary-200 text-primary-100 rounded-full px-10 py-6 text-lg">
            Continue to Seats
          </Button>
        </div>
      </div>
    </main>
  );
} 