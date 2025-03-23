import { Search, MapPin, User, Ticket, LogOut } from "lucide-react";
import { Button } from "./ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { Link, useNavigate } from "react-router-dom";
import { useEffect, useState, useRef } from "react";
import { TicketQueue, TicketOrder, ticketOrderService } from "./TicketQueue";
import { ProfileCard, getCurrentUserProfile } from "./ProfileCard";
import { logout } from "@/lib/api";
import { toast } from "sonner";

export function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [dropdownScrollState, setDropdownScrollState] = useState(false);
  const [isTicketQueueOpen, setIsTicketQueueOpen] = useState(false);
  const [orders, setOrders] = useState<TicketOrder[]>([]);
  const [userProfile, setUserProfile] = useState(() => getCurrentUserProfile());
  const prevOrdersRef = useRef<TicketOrder[]>([]);
  const navigate = useNavigate();
  
  // Fallback user data if no profile exists
  const fallbackUser = {
    name: "Guest User",
    email: "guest@example.com",
    avatarUrl: undefined,
    membership: "Free"
  };

  useEffect(() => {
    const handleScroll = () => {
      const scrollPosition = window.scrollY;
      setIsScrolled(scrollPosition > 0);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Update user profile when storage changes (login/logout events)
  useEffect(() => {
    const handleStorageChange = () => {
      // Re-fetch the user profile from localStorage
      setUserProfile(getCurrentUserProfile());
    };
    
    // Listen for storage events (login/logout)
    window.addEventListener('storage', handleStorageChange);
    
    return () => {
      window.removeEventListener('storage', handleStorageChange);
    };
  }, []);

  useEffect(() => {
    // Load ticket orders from storage
    const loadedOrders = ticketOrderService.getOrders();
    setOrders(loadedOrders);
    
    // Set up a storage event listener to update orders when they change
    const handleStorageChange = () => {
      const updatedOrders = ticketOrderService.getOrders();
      setOrders(updatedOrders);
    };
    
    window.addEventListener('storage', handleStorageChange);
    
    // Check for order updates every 2 seconds to catch updates from other components
    const intervalId = setInterval(() => {
      const updatedOrders = ticketOrderService.getOrders();
      if (JSON.stringify(updatedOrders) !== JSON.stringify(orders)) {
        setOrders(updatedOrders);
      }
    }, 2000);
    
    return () => {
      window.removeEventListener('storage', handleStorageChange);
      clearInterval(intervalId);
    };
  }, []);

  const handleDropdownOpen = (open: boolean) => {
    if (open) {
      // Capture current scroll state when dropdown opens
      setDropdownScrollState(isScrolled);
    }
  };
  
  const openTicketQueue = () => {
    setIsTicketQueueOpen(true);
  };
  
  const closeTicketQueue = () => {
    setIsTicketQueueOpen(false);
  };
  
  const handleCheckoutAll = () => {
    closeTicketQueue();
    window.location.href = '/checkout';
  };
  
  const handleRemoveOrder = (orderId: string) => {
    const updatedOrders = ticketOrderService.removeOrder(orderId);
    setOrders(updatedOrders);
  };

  // Calculate user initials for avatar
  const getUserInitials = () => {
    if (!userProfile?.name) return "GU";
    
    return userProfile.name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .slice(0, 2)
      .toUpperCase();
  };

  return (
    <>
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
                <Link to="/movies" className="text-text-100 hover:text-accent-200 transition-colors relative group">
                  <span>Movies</span>
                  <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-accent-200 group-hover:animate-nav-underline" />
                </Link>
                <Link to="/coming-soon" className="text-text-100 hover:text-accent-200 transition-colors relative group">
                  <span>Coming Soon</span>
                  <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-accent-200 group-hover:animate-nav-underline" />
                </Link>
                <Link to="/genres" className="text-text-100 hover:text-accent-200 transition-colors relative group">
                  <span>Genres</span>
                  <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-accent-200 group-hover:animate-nav-underline" />
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
              <Button 
                variant="ghost" 
                size="icon" 
                className="text-text-100 hover:text-accent-200 relative"
                onClick={openTicketQueue}
              >
                <Ticket className="w-5 h-5" />
                {orders.length > 0 && (
                  <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-accent-200 text-bg-300 text-xs flex items-center justify-center">
                    {orders.length}
                  </span>
                )}
              </Button>
              <DropdownMenu onOpenChange={handleDropdownOpen}>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" className="text-text-100 hover:text-accent-200 p-0 overflow-hidden">
                    {userProfile ? (
                      userProfile.avatarUrl ? (
                        <div className="w-9 h-9 rounded-full overflow-hidden">
                          <img 
                            src={userProfile.avatarUrl} 
                            alt={userProfile.name} 
                            className="w-full h-full object-cover"
                          />
                        </div>
                      ) : (
                        <div className="w-9 h-9 rounded-full bg-accent-200 flex items-center justify-center text-bg-300 font-medium">
                          {getUserInitials()}
                        </div>
                      )
                    ) : (
                      <User className="w-5 h-5" />
                    )}
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent 
                  align="end" 
                  className={`w-64 ${
                    dropdownScrollState ? 'bg-bg-300/50 backdrop-blur-sm' : 'bg-bg-300'
                  } border-primary-200/20 p-0 shadow-lg transition-colors duration-200`}
                >
                  <ProfileCard 
                    name={userProfile?.name || fallbackUser.name}
                    email={userProfile?.email || fallbackUser.email}
                    avatarUrl={userProfile?.avatarUrl || fallbackUser.avatarUrl}
                    membership={userProfile?.membership || fallbackUser.membership}
                    dateOfBirth={userProfile?.date_of_birth}
                    age={userProfile?.age}
                  />
                  
                  <div className="p-1">
                    {userProfile && (
                      <>
                        <DropdownMenuItem asChild className="py-2 px-4 text-text-100 hover:bg-bg-200/50">
                          <Link to="/profile">
                            My Profile
                          </Link>
                        </DropdownMenuItem>
                        <DropdownMenuItem asChild className="py-2 px-4 text-text-100 hover:bg-bg-200/50">
                          <Link to="/tickets">
                            My Tickets
                          </Link>
                        </DropdownMenuItem>
                        <DropdownMenuItem asChild className="py-2 px-4 text-text-100 hover:bg-bg-200/50">
                          <Link to="/watchlist">
                            My Watchlist
                          </Link>
                        </DropdownMenuItem>
                        
                        <DropdownMenuSeparator className="my-1 h-px bg-primary-200/20" />
                        
                        <DropdownMenuItem 
                          className="py-2 px-4 text-text-100 hover:bg-bg-200/50"
                          onClick={async () => {
                            await logout();
                            setUserProfile(null);
                            toast.success("Logged out successfully");
                            navigate("/");
                          }}
                        >
                          <LogOut className="w-4 h-4 mr-2" />
                          Log Out
                        </DropdownMenuItem>
                      </>
                    )}
                    
                    {!userProfile && (
                      <>
                        <DropdownMenuItem asChild className="py-2 px-4 text-text-100 hover:bg-bg-200/50">
                          <Link to="/signin">
                            Sign In
                          </Link>
                        </DropdownMenuItem>
                        <DropdownMenuItem asChild className="py-2 px-4 text-text-100 hover:bg-bg-200/50">
                          <Link to="/signup">
                            Join Now
                          </Link>
                        </DropdownMenuItem>
                      </>
                    )}
                  </div>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </div>
      </nav>
      
      {/* Ticket Queue Modal */}
      <TicketQueue 
        isOpen={isTicketQueueOpen} 
        onClose={closeTicketQueue} 
        orders={orders}
        onCheckoutAll={handleCheckoutAll}
        onRemoveOrder={handleRemoveOrder}
      />
    </>
  );
}