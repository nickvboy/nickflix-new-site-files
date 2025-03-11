import { useState, useEffect } from 'react';
import { Seat } from '@/components/SeatSelector';
import { Button } from '@/components/ui/button';
import { Plus, Minus, CheckSquare } from 'lucide-react';

// Types for the ticket checkout component
export type AgeCategory = 'adult' | 'teen' | 'child';

export interface TicketPrice {
  category: AgeCategory;
  price: number;
  label: string;
}

export interface TicketSelection {
  category: AgeCategory;
  quantity: number;
}

export interface MoviePricing {
  movieId: string | number;
  movieTitle: string;
  basePrice: number;
  taxRate: number;
  tickets: TicketPrice[];
}

interface TicketCheckoutProps {
  movieId: string | number;
  movieTitle: string;
  selectedSeats: Seat[];
  onComplete?: (data: CheckoutData) => void;
  className?: string;
}

export interface CheckoutData {
  movieId: string | number;
  movieTitle: string;
  selectedSeats: Seat[];
  ticketSelections: TicketSelection[];
  pricing: {
    subtotal: number;
    tax: number;
    total: number;
  };
}

// Helper function to generate random movie pricing
const generateMoviePricing = (movieId: string | number, movieTitle: string): MoviePricing => {
  // Generate a base price between $10-15
  const basePrice = 10 + Math.floor(Math.random() * 5);
  
  // 8% tax rate
  const taxRate = 0.08;
  
  // Create ticket prices for different age categories
  const tickets: TicketPrice[] = [
    { category: 'adult', price: basePrice, label: 'Adult' },
    { category: 'teen', price: basePrice * 0.85, label: 'Teen (13-17)' },
    { category: 'child', price: basePrice * 0.6, label: 'Child (3-12)' }
  ];
  
  return {
    movieId,
    movieTitle,
    basePrice,
    taxRate,
    tickets
  };
};

export function TicketCheckout({ 
  movieId, 
  movieTitle, 
  selectedSeats, 
  onComplete,
  className 
}: TicketCheckoutProps) {
  // Generate pricing based on movie ID (would come from API in real app)
  const [pricing] = useState<MoviePricing>(
    generateMoviePricing(movieId, movieTitle)
  );
  
  // Initialize ticket selections - one adult ticket per seat by default
  const [ticketSelections, setTicketSelections] = useState<TicketSelection[]>(() => {
    return pricing.tickets.map(ticket => ({
      category: ticket.category,
      quantity: ticket.category === 'adult' ? selectedSeats.length : 0
    }));
  });
  
  // Calculate totals
  const [totals, setTotals] = useState({
    subtotal: 0,
    tax: 0,
    total: 0
  });

  // Count total tickets selected
  const totalTicketsSelected = ticketSelections.reduce(
    (sum, selection) => sum + selection.quantity, 
    0
  );

  // Update totals when ticket selections change
  useEffect(() => {
    const calculateTotals = () => {
      const subtotal = ticketSelections.reduce((sum, selection) => {
        const ticketType = pricing.tickets.find(t => t.category === selection.category);
        return sum + (ticketType?.price || 0) * selection.quantity;
      }, 0);
      
      const tax = subtotal * pricing.taxRate;
      const total = subtotal + tax;
      
      setTotals({
        subtotal,
        tax,
        total
      });
    };
    
    calculateTotals();
  }, [ticketSelections, pricing]);

  // Handle ticket quantity changes
  const updateTicketQuantity = (category: AgeCategory, change: number) => {
    const newSelections = ticketSelections.map(selection => {
      if (selection.category === category) {
        // Calculate new quantity, ensuring it can't go below 0
        const newQuantity = Math.max(0, selection.quantity + change);
        
        // Ensure we don't select more tickets than seats
        if (totalTicketsSelected + change <= selectedSeats.length || change < 0) {
          return { ...selection, quantity: newQuantity };
        }
      }
      return selection;
    });
    
    setTicketSelections(newSelections);
  };

  // Handle checkout
  const handleCheckout = () => {
    // Ensure correct number of tickets
    if (totalTicketsSelected !== selectedSeats.length) {
      alert(`Please select exactly ${selectedSeats.length} tickets to match your selected seats.`);
      return;
    }
    
    const checkoutData: CheckoutData = {
      movieId,
      movieTitle,
      selectedSeats,
      ticketSelections,
      pricing: totals
    };
    
    if (onComplete) {
      onComplete(checkoutData);
    } else {
      console.log('Checkout completed:', checkoutData);
    }
  };
  
  // Format currency
  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  // Update ticket selections when seats change
  useEffect(() => {
    if (selectedSeats.length > 0) {
      // Always set a maximum of 4 adult tickets initially
      // to ensure warning is visible for larger seat counts
      const adultCount = Math.min(selectedSeats.length, 4);
      
      setTicketSelections(
        pricing.tickets.map(ticket => ({
          category: ticket.category,
          quantity: ticket.category === 'adult' ? adultCount : 0
        }))
      );
    }
  }, [selectedSeats, pricing.tickets]);

  // Check if we need to show warning
  const shouldShowWarning = selectedSeats.length > 0 && totalTicketsSelected !== selectedSeats.length;
  
  return (
    <div className="w-full max-w-md mx-auto bg-bg-400 rounded-xl p-4 text-text-100">
      <h2 className="text-xl font-bold mb-1">Ticket Checkout</h2>
      
      {selectedSeats.length === 0 ? (
        <div className="py-8">
          <p className="text-sm text-text-200 mb-6">
            Please select your seats first to continue with ticket selection.
          </p>
          <div className="flex flex-col items-center justify-center space-y-4">
            <div className="w-16 h-16 rounded-full bg-bg-300 flex items-center justify-center">
              <CheckSquare className="w-8 h-8 text-primary-300/50" />
            </div>
            <p className="text-center text-text-200">
              Your tickets will appear here once you've selected seats.
            </p>
            
            {/* Movie ticket pricing preview */}
            <div className="w-full mt-8 pt-4 border-t border-bg-300">
              <h3 className="text-sm font-semibold mb-3">Ticket Pricing</h3>
              <div className="space-y-2">
                {pricing.tickets.map(ticket => (
                  <div key={ticket.category} className="flex justify-between items-center text-sm">
                    <span>{ticket.label}</span>
                    <span className="text-primary-300">{formatCurrency(ticket.price)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      ) : (
        <>
          <p className="text-sm text-text-200 mb-4">
            {selectedSeats.length} seat{selectedSeats.length !== 1 ? 's' : ''} selected
            for {movieTitle}
          </p>
          
          {/* Ticket type selection */}
          <div className="space-y-3 mb-6">
            {pricing.tickets.map((ticket) => {
              const selection = ticketSelections.find(s => s.category === ticket.category);
              const quantity = selection?.quantity || 0;
              
              return (
                <div key={ticket.category} className="flex items-center justify-between bg-bg-300 p-3 rounded-lg">
                  <div>
                    <div className="font-medium">{ticket.label}</div>
                    <div className="text-sm text-text-200">{formatCurrency(ticket.price)}</div>
                  </div>
                  
                  <div className="flex items-center space-x-3">
                    <button
                      onClick={() => updateTicketQuantity(ticket.category, -1)}
                      disabled={quantity === 0}
                      className="w-7 h-7 rounded-full bg-bg-200 flex items-center justify-center 
                               hover:bg-primary-300/20 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Minus size={16} />
                    </button>
                    
                    <span className="w-5 text-center">{quantity}</span>
                    
                    <button
                      onClick={() => updateTicketQuantity(ticket.category, 1)}
                      disabled={totalTicketsSelected >= selectedSeats.length}
                      className="w-7 h-7 rounded-full bg-bg-200 flex items-center justify-center 
                               hover:bg-primary-300/20 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Plus size={16} />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
          
          {/* Selected seats */}
          <div className="mb-4">
            <h3 className="text-sm font-semibold mb-2">Selected Seats</h3>
            <div className="flex flex-wrap gap-1.5">
              {selectedSeats.map((seat) => (
                <div key={seat.id} className="bg-primary-300 text-primary-100 px-2 py-0.5 rounded text-xs">
                  {seat.row}{seat.number}
                </div>
              ))}
            </div>
          </div>
          
          {/* Ticket count warning - always show if count doesn't match */}
          {shouldShowWarning && (
            <div className="bg-yellow-600/20 border-2 border-yellow-500 text-yellow-100 p-3 rounded-lg mb-4 text-sm animate-pulse">
              <div className="font-semibold flex items-center gap-2">
                <svg 
                  xmlns="http://www.w3.org/2000/svg" 
                  viewBox="0 0 24 24" 
                  width="16" 
                  height="16" 
                  fill="none" 
                  stroke="currentColor" 
                  strokeWidth="2" 
                  strokeLinecap="round" 
                  strokeLinejoin="round"
                >
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="12" y1="8" x2="12" y2="12"></line>
                  <line x1="12" y1="16" x2="12.01" y2="16"></line>
                </svg>
                Ticket Count Warning
              </div>
              <p className="mt-1">
                Please select exactly {selectedSeats.length} tickets to match your seat selection.
                {totalTicketsSelected < selectedSeats.length ? 
                  ` You need ${selectedSeats.length - totalTicketsSelected} more ticket(s).` : 
                  ` You have ${totalTicketsSelected - selectedSeats.length} too many ticket(s).`}
              </p>
            </div>
          )}
          
          {/* Order summary */}
          <div className="bg-bg-300 p-3 rounded-lg mb-4">
            <h3 className="text-sm font-semibold mb-2">Order Summary</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span>Subtotal</span>
                <span>{formatCurrency(totals.subtotal)}</span>
              </div>
              <div className="flex justify-between">
                <span>Tax ({(pricing.taxRate * 100).toFixed(1)}%)</span>
                <span>{formatCurrency(totals.tax)}</span>
              </div>
              <div className="flex justify-between font-semibold text-base mt-2 pt-2 border-t border-bg-200">
                <span>Total</span>
                <span>{formatCurrency(totals.total)}</span>
              </div>
            </div>
          </div>
          
          {/* Checkout button */}
          <Button
            onClick={handleCheckout}
            disabled={totalTicketsSelected !== selectedSeats.length || totalTicketsSelected === 0}
            className="w-full bg-primary-300 hover:bg-primary-200 text-primary-100 py-2 rounded-lg"
          >
            Complete Order
          </Button>
        </>
      )}
    </div>
  );
} 