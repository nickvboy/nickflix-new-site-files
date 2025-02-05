import { Search, MapPin, User, Ticket } from "lucide-react";
import { Button } from "./ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Link } from "react-router-dom";
import { useEffect, useState } from "react";

export function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      const scrollPosition = window.scrollY;
      setIsScrolled(scrollPosition > 0);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <nav 
      className={`fixed top-0 left-0 right-0 transition-colors duration-200 border-b border-primary-200/20 z-[var(--z-sticky)] ${
        isScrolled ? 'bg-bg-300/50 backdrop-blur-sm' : 'bg-bg-300'
      }`}
    >
      <div className="max-w-[1400px] mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo and primary navigation */}
          <div className="flex items-center gap-8">
            <a href="/" className="flex items-center gap-2">
              <img
                src="https://mail.google.com/mail/u/0?ui=2&ik=9bae6faecf&attid=0.1&permmsgid=msg-a:r-7152086092968704690&th=194d2da24a2ab01d&view=fimg&fur=ip&permmsgid=msg-a:r-7152086092968704690&sz=s0-l75-ft&attbid=ANGjdJ-3GqqdNMs2oOrNSDMI_V8e2-TeCJgaPQ_YgWH_4lqDiROxRh9AQF6NungU7rdNG7bXB_wWvD1WMR-ubIkJsrq3b7AC-tsDMDI1QomU6MfOHW4Y1cOytOq8VEo&disp=emb&realattid=ii_m6qzn5cn0&zw"
                alt="Nickflix Logo"
                className="h-10 w-auto object-contain"
              />
              <span className="text-h3 text-text-100 font-bold">NICKFLIX</span>
            </a>
            <div className="hidden md:flex items-center gap-6">
              <Link to="/movies" className="text-text-100 hover:text-accent-200 transition-colors">
                Movies
              </Link>
              <Link to="/coming-soon" className="text-text-100 hover:text-accent-200 transition-colors">
                Coming Soon
              </Link>
              <Link to="/genres" className="text-text-100 hover:text-accent-200 transition-colors">
                Genres
              </Link>
            </div>
          </div>

          {/* Secondary navigation */}
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" className="text-text-100 hover:text-accent-200">
              <Search className="w-5 h-5" />
            </Button>
            <div className="hidden md:flex items-center gap-2 text-text-100">
              <MapPin className="w-5 h-5 text-accent-200" />
              <span className="text-small">FL, Edison Mall</span>
            </div>
            <Button variant="ghost" size="icon" className="text-text-100 hover:text-accent-200">
              <Ticket className="w-5 h-5" />
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="text-text-100 hover:text-accent-200">
                  <User className="w-5 h-5" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48 bg-bg-200 border-primary-200">
                <DropdownMenuItem asChild>
                  <Link to="/signin" className="text-text-100 hover:text-accent-200 cursor-pointer">
                    Sign In
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <Link to="/signup" className="text-text-100 hover:text-accent-200 cursor-pointer">
                    Join Now
                  </Link>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>
    </nav>
  );
}