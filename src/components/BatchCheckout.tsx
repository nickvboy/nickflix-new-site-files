import { useState } from 'react';
import { Ticket, ShoppingCart, ArrowLeft, CreditCard, Check, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { TicketOrder } from '@/components/TicketQueue';
import { Checkbox } from '@/components/ui/checkbox';
import { Link } from 'react-router-dom';

interface BatchCheckoutProps {
  orders: TicketOrder[];
  onComplete: (orderIds: string[]) => void;
  onCancel: () => void;
}

export function BatchCheckout({ orders, onComplete, onCancel }: BatchCheckoutProps) {
  const [selectedOrderIds, setSelectedOrderIds] = useState<string[]>(() => 
    orders.map(order => order.id)
  );
  const [paymentStep, setPaymentStep] = useState<'select' | 'payment' | 'confirmation'>('select');
  const [processingPayment, setProcessingPayment] = useState(false);
  const [availableOrders, setAvailableOrders] = useState<TicketOrder[]>(orders);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const toggleOrderSelection = (orderId: string) => {
    if (selectedOrderIds.includes(orderId)) {
      setSelectedOrderIds(selectedOrderIds.filter(id => id !== orderId));
    } else {
      setSelectedOrderIds([...selectedOrderIds, orderId]);
    }
  };

  const toggleSelectAll = () => {
    if (selectedOrderIds.length === availableOrders.length) {
      setSelectedOrderIds([]);
    } else {
      setSelectedOrderIds(availableOrders.map(order => order.id));
    }
  };

  const handleDeleteSelected = () => {
    if (selectedOrderIds.length === 0) return;
    
    const updatedOrders = availableOrders.filter(order => !selectedOrderIds.includes(order.id));
    setAvailableOrders(updatedOrders);
    
    setSelectedOrderIds([]);
  };

  const selectedOrders = availableOrders.filter(order => selectedOrderIds.includes(order.id));
  const totalAmount = selectedOrders.reduce((sum, order) => sum + order.pricing.total, 0);
  const totalTickets = selectedOrders.reduce((sum, order) => {
    return sum + order.ticketSelections.reduce((tSum, selection) => tSum + selection.quantity, 0);
  }, 0);

  const handleContinueToPayment = () => {
    if (selectedOrderIds.length === 0) return;
    setPaymentStep('payment');
  };

  const handleCompletePayment = () => {
    setProcessingPayment(true);
    // Simulate payment processing
    setTimeout(() => {
      setProcessingPayment(false);
      setPaymentStep('confirmation');
    }, 1500);
  };

  const handleFinish = () => {
    onComplete(selectedOrderIds);
  };

  return (
    <div className="max-w-4xl mx-auto bg-bg-300 rounded-xl shadow-lg overflow-hidden min-h-[70vh] flex flex-col">
      {/* Header */}
      <div className="bg-bg-400 p-4 border-b border-primary-200/20">
        <div className="flex items-center">
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={paymentStep === 'select' ? onCancel : () => setPaymentStep('select')}
            disabled={paymentStep === 'confirmation'}
          >
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <h1 className="text-xl font-bold ml-2 text-text-100">
            {paymentStep === 'select' && 'Select Orders for Checkout'}
            {paymentStep === 'payment' && 'Payment Details'}
            {paymentStep === 'confirmation' && 'Order Confirmation'}
          </h1>
        </div>
        
        {paymentStep === 'select' && (
          <div className="flex items-center justify-between mt-4">
            <div className="flex items-center gap-2">
              <Checkbox 
                id="select-all" 
                checked={selectedOrderIds.length === availableOrders.length && availableOrders.length > 0}
                onCheckedChange={toggleSelectAll}
              />
              <label htmlFor="select-all" className="text-sm text-text-200">
                Select All ({availableOrders.length} orders)
              </label>
            </div>
            <div className="flex items-center gap-2">
              <div className="text-sm text-text-200">
                {selectedOrderIds.length} of {availableOrders.length} selected
              </div>
              {selectedOrderIds.length > 0 && (
                <Button 
                  variant="destructive" 
                  size="sm"
                  onClick={handleDeleteSelected}
                  className="ml-2 bg-red-500 hover:bg-red-600"
                >
                  <Trash2 className="w-4 h-4 mr-1" /> Delete
                </Button>
              )}
            </div>
          </div>
        )}
        
        {paymentStep === 'payment' && (
          <div className="mt-2 text-sm text-text-200">
            Processing {selectedOrderIds.length} order{selectedOrderIds.length !== 1 ? 's' : ''} with {totalTickets} tickets
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 p-4 overflow-y-auto">
        {paymentStep === 'select' && (
          <div className="space-y-4">
            {availableOrders.map((order) => (
              <div 
                key={order.id} 
                className={`border rounded-lg overflow-hidden transition-all ${
                  selectedOrderIds.includes(order.id) 
                    ? 'border-accent-200 bg-bg-400' 
                    : 'border-primary-200/20 bg-bg-300'
                }`}
              >
                <div className="p-4 flex items-start">
                  <Checkbox 
                    id={`order-${order.id}`}
                    checked={selectedOrderIds.includes(order.id)}
                    onCheckedChange={() => toggleOrderSelection(order.id)}
                    className="mt-1 mr-3"
                  />
                  <div className="flex-1">
                    <div className="flex items-start justify-between">
                      <div>
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
                      </div>
                      <div className="text-accent-200 font-medium">
                        {formatCurrency(order.pricing.total)}
                      </div>
                    </div>
                    
                    <div className="mt-3">
                      {order.ticketSelections.map((selection) => 
                        selection.quantity > 0 && (
                          <span 
                            key={selection.category} 
                            className="text-xs text-text-200 mr-3"
                          >
                            {selection.quantity}× {selection.category.charAt(0).toUpperCase() + selection.category.slice(1)}
                          </span>
                        )
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
        
        {paymentStep === 'payment' && (
          <div className="max-w-lg mx-auto">
            <div className="bg-bg-400 rounded-lg p-4 mb-6">
              <h2 className="text-lg font-medium mb-3 text-text-100">Order Summary</h2>
              
              <div className="space-y-2 mb-4">
                {selectedOrders.map((order) => (
                  <div key={order.id} className="flex justify-between text-sm">
                    <span className="text-text-200">
                      {order.movieTitle} ({order.selectedSeats.length} seats)
                    </span>
                    <span className="text-text-100">{formatCurrency(order.pricing.total)}</span>
                  </div>
                ))}
              </div>
              
              <div className="pt-3 border-t border-primary-200/20">
                <div className="flex justify-between font-medium">
                  <span className="text-text-100">Total Amount</span>
                  <span className="text-accent-200">{formatCurrency(totalAmount)}</span>
                </div>
              </div>
            </div>
            
            {/* Payment Form */}
            <div className="bg-bg-400 rounded-lg p-4">
              <h2 className="text-lg font-medium mb-4 text-text-100 flex items-center">
                <CreditCard className="w-5 h-5 mr-2 text-accent-200" />
                Payment Information
              </h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-text-200 mb-1">Cardholder Name</label>
                  <input 
                    type="text" 
                    className="w-full p-2 rounded bg-bg-300 border border-primary-200/20 text-text-100"
                    placeholder="John Doe"
                  />
                </div>
                
                <div>
                  <label className="block text-sm text-text-200 mb-1">Card Number</label>
                  <input 
                    type="text" 
                    className="w-full p-2 rounded bg-bg-300 border border-primary-200/20 text-text-100"
                    placeholder="0000 0000 0000 0000"
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-text-200 mb-1">Expiration Date</label>
                    <input 
                      type="text" 
                      className="w-full p-2 rounded bg-bg-300 border border-primary-200/20 text-text-100"
                      placeholder="MM/YY"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm text-text-200 mb-1">CVV</label>
                    <input 
                      type="text" 
                      className="w-full p-2 rounded bg-bg-300 border border-primary-200/20 text-text-100"
                      placeholder="123"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {paymentStep === 'confirmation' && (
          <div className="max-w-lg mx-auto text-center py-8">
            <div className="w-20 h-20 bg-accent-200/20 rounded-full flex items-center justify-center mx-auto mb-6">
              <Check className="w-10 h-10 text-accent-200" />
            </div>
            
            <h2 className="text-2xl font-bold text-text-100 mb-2">Payment Successful!</h2>
            <p className="text-text-200 mb-6">
              Your order for {totalTickets} tickets has been confirmed.
            </p>
            
            <div className="bg-bg-400 rounded-lg p-4 mb-6 text-left">
              <h3 className="font-medium text-text-100 mb-3">Order Details</h3>
              
              <div className="space-y-4">
                {selectedOrders.map((order) => (
                  <div key={order.id} className="pb-3 border-b border-primary-200/20 last:border-b-0 last:pb-0">
                    <div className="flex justify-between">
                      <span className="font-medium text-text-100">{order.movieTitle}</span>
                      <span className="text-accent-200">{formatCurrency(order.pricing.total)}</span>
                    </div>
                    <p className="text-sm text-text-200 mb-1">
                      {order.theaterName} • {order.showtime || "Time TBA"}
                    </p>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {order.selectedSeats.map((seat) => (
                        <span 
                          key={seat.id} 
                          className="inline-block px-2 py-0.5 bg-bg-200 rounded text-xs text-text-200"
                        >
                          {seat.row}{seat.number}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="mt-4 pt-3 border-t border-primary-200/20">
                <div className="flex justify-between font-medium">
                  <span className="text-text-100">Total Amount Paid</span>
                  <span className="text-accent-200">{formatCurrency(totalAmount)}</span>
                </div>
                <p className="text-xs text-text-200 mt-1">
                  Payment processed on {new Date().toLocaleDateString()}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="bg-bg-400 p-4 border-t border-primary-200/20">
        {paymentStep === 'select' && (
          <div className="flex items-center justify-between">
            <div className="text-text-100">
              <div className="font-medium">Total: {formatCurrency(totalAmount)}</div>
              <div className="text-xs text-text-200">{totalTickets} tickets</div>
            </div>
            <Button 
              onClick={handleContinueToPayment}
              disabled={selectedOrderIds.length === 0}
              className="bg-primary-300 hover:bg-primary-300/90 text-primary-100"
            >
              Continue to Payment
            </Button>
          </div>
        )}
        
        {paymentStep === 'payment' && (
          <div className="flex justify-end">
            <Button 
              onClick={handleCompletePayment}
              disabled={processingPayment}
              className="bg-primary-300 hover:bg-primary-300/90 text-primary-100"
            >
              {processingPayment ? (
                <>
                  <div className="w-4 h-4 rounded-full border-2 border-t-transparent border-primary-100 animate-spin mr-2"></div>
                  Processing...
                </>
              ) : (
                <>Pay {formatCurrency(totalAmount)}</>
              )}
            </Button>
          </div>
        )}
        
        {paymentStep === 'confirmation' && (
          <div className="flex justify-end">
            <Button 
              onClick={handleFinish}
              className="bg-primary-300 hover:bg-primary-300/90 text-primary-100"
            >
              <Ticket className="w-4 h-4 mr-2" />
              View My Tickets
            </Button>
          </div>
        )}
      </div>
    </div>
  );
} 