import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { TicketOrder, ticketOrderService } from '@/components/TicketQueue';
import { BatchCheckout } from '@/components/BatchCheckout';
import { Ticket, ShoppingCart, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function CheckoutPage() {
  const [orders, setOrders] = useState<TicketOrder[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    // Load orders from storage
    const loadedOrders = ticketOrderService.getOrders();
    setOrders(loadedOrders);
    setIsLoading(false);
  }, []);

  const handleCheckoutComplete = (orderIds: string[]) => {
    // Remove processed orders from storage
    orderIds.forEach(id => {
      ticketOrderService.removeOrder(id);
    });
    
    // Redirect to tickets page (would be created in a real app)
    navigate('/tickets');
  };

  const handleCancel = () => {
    navigate(-1);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg-300">
        <p className="text-xl text-primary-300">Loading...</p>
      </div>
    );
  }

  if (orders.length === 0) {
    return (
      <div className="min-h-screen bg-bg-300 flex flex-col items-center justify-center p-4">
        <div className="w-20 h-20 bg-bg-400 rounded-full flex items-center justify-center mb-6">
          <ShoppingCart className="w-10 h-10 text-primary-300/50" />
        </div>
        <h1 className="text-2xl font-bold text-text-100 mb-2">Your Cart is Empty</h1>
        <p className="text-text-200 text-center max-w-md mb-6">
          You don't have any pending ticket orders. Browse movies and select tickets to add them to your cart.
        </p>
        <Button onClick={() => navigate('/movies')}>
          Browse Movies
        </Button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg-300 pt-24 pb-12 px-4">
      <div className="max-w-4xl mx-auto">
        <BatchCheckout 
          orders={orders}
          onComplete={handleCheckoutComplete}
          onCancel={handleCancel}
        />
      </div>
    </div>
  );
} 