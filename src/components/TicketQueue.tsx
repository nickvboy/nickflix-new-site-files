import { useState, useEffect } from 'react';
import { Ticket, X, ShoppingCart } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Seat } from '@/components/SeatSelector';
import { Link } from 'react-router-dom';
import { AgeCategory } from '@/components/TicketCheckout';

export interface TicketOrder {
  id: string;
  movieId: string | number;
  movieTitle: string;
  theaterId?: string;
  theaterName: string;
  showtime?: string;
  selectedSeats: Seat[];
  ticketSelections: {
    category: AgeCategory;
    quantity: number;
  }[];
  pricing: {
    subtotal: number;
    tax: number;
    total: number;
  };
  createdAt: string;
}

interface TicketQueueProps {
  isOpen: boolean;
  onClose: () => void;
  orders: TicketOrder[];
  onCheckoutAll: () => void;
  onRemoveOrder: (orderId: string) => void;
}

export function TicketQueue({ 
  isOpen, 
  onClose, 
  orders, 
  onCheckoutAll,
  onRemoveOrder 
}: TicketQueueProps) {
  if (!isOpen) return null;

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const orderTotal = orders.reduce((sum, order) => sum + order.pricing.total, 0);
  const totalTickets = orders.reduce((sum, order) => {
    return sum + order.ticketSelections.reduce((tSum, selection) => tSum + selection.quantity, 0);
  }, 0);

  return (
    <div className="fixed inset-0 bg-bg-100/80 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="absolute inset-0" onClick={onClose}></div>
      <div className="relative bg-bg-300 rounded-xl shadow-xl max-w-xl w-full max-h-[80vh] overflow-hidden flex flex-col">
        <div className="border-b border-primary-200/20 p-4 flex justify-between items-center sticky top-0 bg-bg-300 z-10">
          <div className="flex items-center text-text-100">
            <Ticket className="w-5 h-5 mr-2 text-accent-200" />
            <h2 className="font-bold text-lg">Your Ticket Queue</h2>
            <div className="ml-2 px-2 py-0.5 rounded-full bg-accent-200 text-bg-300 text-xs">
              {orders.length}
            </div>
          </div>
          <Button size="icon" variant="ghost" onClick={onClose}>
            <X className="w-5 h-5" />
          </Button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {orders.length === 0 ? (
            <div className="text-center py-10 text-text-200">
              <Ticket className="w-12 h-12 mx-auto mb-4 text-primary-200/40" />
              <p>Your ticket queue is empty</p>
              <p className="text-sm mt-2">Add tickets by completing a movie order</p>
            </div>
          ) : (
            <>
              {orders.map((order) => (
                <div key={order.id} className="bg-bg-400 rounded-lg p-4 shadow-sm relative group">
                  <button 
                    onClick={() => onRemoveOrder(order.id)}
                    className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity text-text-200 hover:text-accent-200"
                  >
                    <X className="w-4 h-4" />
                  </button>
                  
                  <div className="flex items-start">
                    <div className="bg-primary-200/20 p-2 rounded-lg mr-3">
                      <Ticket className="w-5 h-5 text-accent-200" />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-medium text-text-100">{order.movieTitle}</h3>
                      <p className="text-sm text-text-200">
                        {order.theaterName} • {order.showtime || "Time TBA"}
                      </p>
                      
                      <div className="mt-2 flex flex-wrap gap-1">
                        {order.selectedSeats.map((seat) => (
                          <span 
                            key={seat.id} 
                            className="inline-block px-2 py-0.5 bg-bg-200 rounded text-xs text-text-200"
                          >
                            {seat.row}{seat.number}
                          </span>
                        ))}
                      </div>
                      
                      <div className="mt-3 flex items-center justify-between">
                        <div>
                          {order.ticketSelections.map((selection) => 
                            selection.quantity > 0 && (
                              <span 
                                key={selection.category} 
                                className="text-xs text-text-200 block"
                              >
                                {selection.quantity}× {selection.category.charAt(0).toUpperCase() + selection.category.slice(1)}
                              </span>
                            )
                          )}
                        </div>
                        <div className="text-accent-200 font-medium">
                          {formatCurrency(order.pricing.total)}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </>
          )}
        </div>
        
        {orders.length > 0 && (
          <div className="border-t border-primary-200/20 p-4 bg-bg-400 sticky bottom-0">
            <div className="flex justify-between items-center mb-3">
              <div className="text-text-200">
                <div>Total ({totalTickets} tickets)</div>
                <div className="text-xs">{orders.length} orders</div>
              </div>
              <div className="text-lg font-bold text-accent-200">
                {formatCurrency(orderTotal)}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Button variant="outline" onClick={onClose}>
                Continue Browsing
              </Button>
              <Button onClick={onCheckoutAll}>
                <ShoppingCart className="w-4 h-4 mr-2" />
                Checkout All
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// Utility function to create a ticket order storage service
export const ticketOrderService = {
  getOrders: (): TicketOrder[] => {
    const orders = localStorage.getItem('ticket-orders');
    if (!orders) return [];
    try {
      return JSON.parse(orders);
    } catch (e) {
      console.error('Failed to parse orders:', e);
      return [];
    }
  },
  
  addOrder: (order: Omit<TicketOrder, 'id' | 'createdAt'>) => {
    const orders = ticketOrderService.getOrders();
    const newOrder: TicketOrder = {
      ...order,
      id: `order-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
      createdAt: new Date().toISOString(),
    };
    
    localStorage.setItem('ticket-orders', JSON.stringify([...orders, newOrder]));
    return newOrder;
  },
  
  removeOrder: (orderId: string) => {
    const orders = ticketOrderService.getOrders();
    const updatedOrders = orders.filter(order => order.id !== orderId);
    localStorage.setItem('ticket-orders', JSON.stringify(updatedOrders));
    return updatedOrders;
  },
  
  clearOrders: () => {
    localStorage.setItem('ticket-orders', JSON.stringify([]));
  }
}; 