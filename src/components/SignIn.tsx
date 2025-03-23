import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Ticket, Users, Brain, MousePointerClick, CheckCircle, Gift } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { toast } from "sonner";
import { apiPost, ApiResponse, UserProfileData, testDatabaseConnection } from "@/lib/api";

export function SignIn() {
  const [formData, setFormData] = useState({
    email: "",
    password: ""
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [dbStatus, setDbStatus] = useState<boolean | null>(null);
  const navigate = useNavigate();

  // Check database connection on component mount
  useEffect(() => {
    const checkDbConnection = async () => {
      try {
        const isConnected = await testDatabaseConnection();
        setDbStatus(isConnected);
        
        if (!isConnected) {
          console.warn('Database connection test failed - login functionality may be limited');
        } else {
          console.log('Database connection test succeeded');
        }
      } catch (err) {
        console.error('Error during database connection test:', err);
        // Don't update status on unexpected errors
      }
    };
    
    checkDbConnection();
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    // Basic validation
    if (!formData.email.trim()) {
      setError('Email is required');
      setIsLoading(false);
      return;
    }

    if (!formData.password.trim()) {
      setError('Password is required');
      setIsLoading(false);
      return;
    }

    try {
      // If database connection is known to be down, warn the user but proceed anyway
      if (dbStatus === false) {
        console.warn('Attempting login despite known database connection issues');
      }

      const data = await apiPost<ApiResponse<UserProfileData>>('login.php', {
        email: formData.email,
        password: formData.password,
      });

      // Debug: Log the full response
      console.log('Login API response:', data);

      if (data.success && data.user) {
        // Format user profile data for app consistency
        const userProfile = {
          id: data.user.id,
          name: data.user.full_name || data.user.username || formData.email.split('@')[0],
          email: data.user.email,
          avatarUrl: data.user.avatar_url || null,
          username: data.user.username || formData.email.split('@')[0],
          full_name: data.user.full_name || null,
          avatar_url: data.user.avatar_url || null,
          membership: data.user.membership || "Free",
          date_of_birth: data.user.date_of_birth || null,
          age: data.user.age !== undefined ? data.user.age : null
        };
        
        // Log the user profile we're saving
        console.log('Saving user profile:', userProfile);
        
        // Save user profile data to localStorage
        localStorage.setItem('userProfile', JSON.stringify(userProfile));
        
        // Trigger storage event for other tabs/components
        window.dispatchEvent(new Event('storage'));
        
        toast.success('Successfully signed in!');
        navigate('/'); // Redirect to home page
      } else {
        // Handle failed login with more specific error message
        const errorMessage = data.message || 'Invalid email or password. Please try again.';
        setError(errorMessage);
        console.error('Login failed:', errorMessage);
      }
    } catch (error: any) {
      // Handle network or unexpected errors
      console.error('Login error:', error);
      
      // Only retest database connection if we haven't already determined it's working
      if (dbStatus !== true) {
        try {
          const isConnected = await testDatabaseConnection();
          setDbStatus(isConnected);
          
          if (!isConnected) {
            setError('Cannot connect to the database. The server may be down or experiencing issues. Please try again later.');
            return;
          }
        } catch (connErr) {
          console.error('Error testing database connection after login failure:', connErr);
        }
      }
      
      // Show a more user-friendly error message
      setError(error.message || 'Connection error. Please check your internet connection and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-bg-100 pt-16">
      <div className="max-w-[1200px] mx-auto p-8">
        {/* Container with mobile-first ordering */}
        <div className="flex flex-col md:flex-row gap-8 items-start">
          {/* Sign in form - Will appear first on mobile */}
          <div className="w-full md:order-2 md:w-[400px]">
            <Card className="border-none shadow-xl bg-bg-200 p-6">
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="text-center">
                  <h2 className="text-h4 text-text-100 mb-1">Welcome Back</h2>
                  <p className="text-small text-text-200">Sign in to continue</p>
                </div>

                <div className="space-y-4">
                  <div>
                    <Input 
                      type="email"
                      name="email"
                      placeholder="Email"
                      required
                      value={formData.email}
                      onChange={handleChange}
                      className="bg-bg-400 border-primary-200 text-text-100 placeholder:text-text-200/50"
                      disabled={isLoading}
                    />
                  </div>
                  <div>
                    <Input 
                      type="password"
                      name="password"
                      placeholder="Password"
                      required
                      value={formData.password}
                      onChange={handleChange}
                      className="bg-bg-400 border-primary-200 text-text-100 placeholder:text-text-200/50"
                      disabled={isLoading}
                    />
                  </div>
                </div>

                {dbStatus === false && (
                  <div className="p-2 bg-yellow-500/10 border border-yellow-500/50 rounded text-yellow-700 text-sm">
                    Warning: Database connection issues detected. Login may not work correctly.
                  </div>
                )}

                {error && (
                  <div className="p-2 bg-red-500/10 border border-red-500/50 rounded text-red-500 text-sm">
                    {error}
                  </div>
                )}

                <Button 
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-accent-100 hover:bg-primary-200 text-text-100"
                >
                  {isLoading ? 'Signing in...' : 'Sign In'}
                </Button>

                <div className="space-y-4 text-center">
                  <a href="#" className="text-small text-accent-200 hover:text-primary-300 block">
                    Forgot Password?
                  </a>
                  <p className="text-small text-text-200">
                    Don't have an account?{" "}
                    <Link to="/signup" className="text-accent-200 hover:text-primary-300">
                      Join Now
                    </Link>
                  </p>
                </div>
              </form>
            </Card>
          </div>

          {/* FlixBenifits - Will appear second on mobile */}
          <div className="flex-1 md:order-1">
            <h2 className="text-h2 mb-12 text-text-100 text-center">FLIXBENIFITS</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {/* Effortless Ticket Booking */}
              <div className="flex flex-col items-center text-center space-y-2">
                <div className="bg-bg-200 p-4 rounded-lg">
                  <Ticket className="w-8 h-8 text-accent-200" />
                </div>
                <h3 className="text-h4 text-text-100">Effortless Ticket Booking</h3>
                <p className="text-small text-text-200">Find movies, select seats, and check out in seconds.</p>
              </div>

              {/* Transparent Pricing */}
              <div className="flex flex-col items-center text-center space-y-2">
                <div className="bg-bg-200 p-4 rounded-lg">
                  <CheckCircle className="w-8 h-8 text-accent-200" />
                </div>
                <h3 className="text-h4 text-text-100">Transparent Pricing</h3>
                <p className="text-small text-text-200">No hidden fees or surprises. See the full cost upfront before you pay.</p>
              </div>

              {/* Collaborative Ticketing */}
              <div className="flex flex-col items-center text-center space-y-2">
                <div className="bg-bg-200 p-4 rounded-lg">
                  <Users className="w-8 h-8 text-accent-200" />
                </div>
                <h3 className="text-h4 text-text-100">Collaborative Ticketing</h3>
                <p className="text-small text-text-200">See the full cost upfront before you pay.</p>
              </div>

              {/* Smart Movie Recommendations */}
              <div className="flex flex-col items-center text-center space-y-2">
                <div className="bg-bg-200 p-4 rounded-lg">
                  <Brain className="w-8 h-8 text-accent-200" />
                </div>
                <h3 className="text-h4 text-text-100">Smart Movie Recommendations</h3>
                <p className="text-small text-text-200">Get personalized suggestions based on your preferences.</p>
              </div>

              {/* Real-Time Seat Selection */}
              <div className="flex flex-col items-center text-center space-y-2">
                <div className="bg-bg-200 p-4 rounded-lg">
                  <MousePointerClick className="w-8 h-8 text-accent-200" />
                </div>
                <h3 className="text-h4 text-text-100">Real-Time Seat Selection</h3>
                <p className="text-small text-text-200">Interactive seat map that updates in real time.</p>
              </div>

              {/* Loyalty Rewards */}
              <div className="flex flex-col items-center text-center space-y-2">
                <div className="bg-bg-200 p-4 rounded-lg">
                  <Gift className="w-8 h-8 text-accent-200" />
                </div>
                <h3 className="text-h4 text-text-100">Loyalty Rewards</h3>
                <p className="text-small text-text-200">Earn points on every purchase and unlock exclusive discounts and perks.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}