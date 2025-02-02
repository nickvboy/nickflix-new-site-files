import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Ticket, Clock, Users, Brain, MousePointerClick, CheckCircle } from "lucide-react";
import { Link } from "react-router-dom";

export function SignUp() {
  return (
    <main className="min-h-screen bg-bg-100 pt-16">
      <div className="max-w-[1200px] mx-auto p-8">
        {/* Container with mobile-first ordering */}
        <div className="flex flex-col md:flex-row gap-8 items-start">
          {/* Sign up form - Will appear first on mobile */}
          <div className="w-full md:order-2 md:w-[400px]">
            <Card className="border-none shadow-xl bg-bg-200 p-6">
              <div className="space-y-4">
                <div className="text-center">
                  <h2 className="text-h4 text-text-100 mb-1">Join For Free</h2>
                  <p className="text-small text-text-200">*Indicates a required field</p>
                </div>

                <div className="space-y-4">
                  <div>
                    <Input 
                      placeholder="First Name*"
                      required
                      className="bg-bg-400 border-primary-200 text-text-100 placeholder:text-text-200/50"
                    />
                  </div>
                  <div>
                    <Input 
                      placeholder="Last Name"
                      className="bg-bg-400 border-primary-200 text-text-100 placeholder:text-text-200/50"
                    />
                  </div>
                  <div>
                    <Input 
                      placeholder="Email*"
                      type="email"
                      required
                      className="bg-bg-400 border-primary-200 text-text-100 placeholder:text-text-200/50"
                    />
                  </div>
                  <div>
                    <Input 
                      placeholder="Username*"
                      required
                      className="bg-bg-400 border-primary-200 text-text-100 placeholder:text-text-200/50"
                    />
                    <p className="text-xs text-text-200 mt-1">*Use 8 or more characters</p>
                  </div>
                  <div>
                    <Input 
                      type="password"
                      placeholder="Password"
                      required
                      className="bg-bg-400 border-primary-200 text-text-100 placeholder:text-text-200/50"
                    />
                  </div>
                </div>

                <Button 
                  className="w-full bg-accent-100 hover:bg-primary-200 text-text-100"
                >
                  Join Now
                </Button>

                <p className="text-small text-center text-text-200">
                  Already a member?{" "}
                  <Link to="/signin" className="text-accent-200 hover:text-primary-300">
                    SIGN IN
                  </Link>
                </p>
              </div>
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

              {/* Effortless Ticket Booking (second instance) */}
              <div className="flex flex-col items-center text-center space-y-2">
                <div className="bg-bg-200 p-4 rounded-lg">
                  <Clock className="w-8 h-8 text-accent-200" />
                </div>
                <h3 className="text-h4 text-text-100">Effortless Ticket Booking</h3>
                <p className="text-small text-text-200">Find movies, select seats, and check out in seconds.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}