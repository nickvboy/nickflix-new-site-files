import { useState, useEffect } from 'react';
import { X, Save, Check, Edit } from 'lucide-react';
import { cn } from '@/lib/utils';

// Types for the seat selector
export type SeatStatus = 'available' | 'selected' | 'occupied' | 'accessible' | 'empty';

export interface Seat {
  id: string;
  row: string;
  number: number;
  status: SeatStatus;
  originalStatus: SeatStatus;
}

export interface SeatLayout {
  id: string;
  name: string;
  seats: Seat[];
  createdAt: string;
  updatedAt: string;
}

export interface SeatSelectorProps {
  className?: string;
  onSelectSeats?: (selectedSeats: Seat[]) => void;
  initialLayout?: SeatLayout;
  showScreen?: boolean;
  onSaveLayout?: (layout: SeatLayout) => void;
  onLoadLayout?: (layoutId: string) => void;
  availableLayouts?: SeatLayout[];
}

// Sample data - seat layout
const generateSampleSeats = (): Seat[] => {
  const rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'];
  const seatsPerRow = 12;
  const seats: Seat[] = [];

  rows.forEach((row) => {
    for (let i = 1; i <= seatsPerRow; i++) {
      // Create some patterns for the demo
      let status: SeatStatus = 'available';
      
      // Middle seats in rows D-F are accessible
      if (['D', 'E', 'F'].includes(row) && i === 5) {
        status = 'accessible';
      }
      
      // Some seats in row H are selected as demo
      if (row === 'H' && [5, 6, 7].includes(i)) {
        status = 'selected';
      }
      
      // Create empty spaces in some areas
      if (i >= 4 && i <= 8 && ['A', 'B', 'C'].includes(row)) {
        if (i % 2 === 0) status = 'empty';
      }

      seats.push({
        id: `${row}${i}`,
        row,
        number: i,
        status,
        originalStatus: status,
      });
    }
  });

  return seats;
};

const sampleLayouts: SeatLayout[] = [
  {
    id: 'default',
    name: 'Default Layout',
    seats: generateSampleSeats(),
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
];

export function SeatSelector({ 
  className, 
  onSelectSeats, 
  initialLayout, 
  showScreen = true,
  onSaveLayout,
  onLoadLayout,
  availableLayouts = []
}: SeatSelectorProps) {
  const [seats, setSeats] = useState<Seat[]>(initialLayout?.seats || sampleLayouts[0].seats);
  const [selectedSeats, setSelectedSeats] = useState<Seat[]>([]);
  const [isAdminMode, setIsAdminMode] = useState<boolean>(false);
  const [editMode, setEditMode] = useState<boolean>(false);
  const [layoutName, setLayoutName] = useState<string>(initialLayout?.name || 'Default Layout');
  const [currentEditStatus, setCurrentEditStatus] = useState<SeatStatus>('available');
  const [showLayoutSelector, setShowLayoutSelector] = useState<boolean>(false);

  // Group seats by row for display
  const seatsByRow = seats.reduce((acc, seat) => {
    if (!acc[seat.row]) {
      acc[seat.row] = [];
    }
    acc[seat.row].push(seat);
    return acc;
  }, {} as Record<string, Seat[]>);

  // Sort rows for consistent display
  const sortedRows = Object.keys(seatsByRow).sort();

  // Handle seat click in user mode
  const handleSeatClick = (seat: Seat) => {
    if (editMode) {
      // In edit mode, change the seat status
      const updatedSeats = seats.map((s) => {
        if (s.id === seat.id) {
          return { ...s, status: currentEditStatus };
        }
        return s;
      });
      setSeats(updatedSeats);
    } else {
      // In user mode, select/deselect seat
      if (seat.status !== 'available' && seat.status !== 'accessible' && seat.status !== 'selected') {
        return; // Can't select occupied or empty seats
      }

      const updatedSeats = seats.map((s) => {
        if (s.id === seat.id) {
          // Toggle between selected and original status
          let newStatus: SeatStatus = 'selected';
          if (s.status === 'selected') {
            // If currently selected, revert to original status
            newStatus = s.originalStatus === 'accessible' ? 'accessible' : 'available';
          }
          return { ...s, status: newStatus };
        }
        return s;
      });

      setSeats(updatedSeats);
      
      // Update selected seats list
      const newSelectedSeats = updatedSeats.filter((s) => s.status === 'selected');
      setSelectedSeats(newSelectedSeats);
      
      if (onSelectSeats) {
        onSelectSeats(newSelectedSeats);
      }
    }
  };

  // Handle save layout in admin mode
  const handleSaveLayout = () => {
    if (!layoutName.trim()) {
      alert('Please enter a layout name');
      return;
    }

    const newLayout: SeatLayout = {
      id: initialLayout?.id || crypto.randomUUID(),
      name: layoutName,
      seats,
      createdAt: initialLayout?.createdAt || new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    onSaveLayout?.(newLayout);
    setEditMode(false);
    alert('Layout saved successfully!');
  };

  // Handle layout selection
  const handleLayoutSelect = (layoutId: string) => {
    onLoadLayout?.(layoutId);
    setShowLayoutSelector(false);
  };

  // Handle cancel edit in admin mode
  const handleCancelEdit = () => {
    // Reset to initial seats
    setSeats(initialLayout?.seats || sampleLayouts[0].seats);
    setEditMode(false);
  };

  // Reset selected seats when exiting admin mode
  useEffect(() => {
    if (!isAdminMode) {
      const selectedSeats = seats.filter((s) => s.status === 'selected');
      setSelectedSeats(selectedSeats);
    }
  }, [isAdminMode, seats]);

  return (
    <div className={cn("w-full max-w-3xl mx-auto bg-bg-400 text-text-100 p-4 rounded-xl", className)}>
      <div className="flex flex-col items-center">
        {/* Header section with title and controls */}
        <div className="w-full flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold">Select Your Seats</h2>
          
          {/* Admin toggle button */}
          <button
            onClick={() => setIsAdminMode(!isAdminMode)}
            className={cn(
              "px-4 py-2 rounded-lg flex items-center text-sm",
              isAdminMode 
                ? "bg-primary-300 text-primary-100"
                : "bg-bg-300 hover:bg-bg-300/80 text-primary-300"
            )}
          >
            {isAdminMode ? 'Exit Admin Mode' : 'Admin Mode'}
          </button>
        </div>

        {/* Admin controls */}
        {isAdminMode && (
          <div className="w-full bg-bg-300 p-3 rounded-lg mb-4">
            {!editMode ? (
              <div className="flex justify-between items-center">
                <div>
                  <h3 className="text-lg font-semibold mb-1">Admin Panel</h3>
                  <p className="text-xs text-text-200">Manage seat layouts</p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setShowLayoutSelector(!showLayoutSelector)}
                    className="bg-bg-400 hover:bg-bg-400/80 text-text-100 px-3 py-1.5 rounded-lg flex items-center gap-1 text-sm"
                  >
                    Load Layout
                  </button>
                  <button
                    onClick={() => setEditMode(true)}
                    className="bg-primary-300 hover:bg-primary-200 text-primary-100 px-3 py-1.5 rounded-lg flex items-center gap-1 text-sm"
                  >
                    <Edit size={16} />
                    Edit Layout
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleCancelEdit()}
                      className="bg-bg-400 hover:bg-bg-400/80 text-text-100 px-3 py-1.5 rounded-lg flex items-center gap-1 text-sm"
                    >
                      <X size={16} />
                      Cancel
                    </button>
                    <button
                      onClick={() => handleSaveLayout()}
                      className="bg-green-600 hover:bg-green-700 text-white px-3 py-1.5 rounded-lg flex items-center gap-1 text-sm"
                    >
                      <Save size={16} />
                      Save Layout
                    </button>
                  </div>
                  <div className="text-right">
                    <label className="block text-xs mb-1">Layout Name:</label>
                    <input
                      type="text"
                      value={layoutName}
                      onChange={(e) => setLayoutName(e.target.value)}
                      className="bg-bg-200 border border-bg-100 rounded px-2 py-1 text-text-100 text-sm w-40"
                      placeholder="Enter layout name"
                    />
                  </div>
                </div>

                {/* Seat type selection tools */}
                <div>
                  <label className="block text-xs mb-1">Click to add or remove seats:</label>
                  <div className="flex gap-2 flex-wrap">
                    <label className="flex items-center gap-1 cursor-pointer">
                      <input
                        type="radio"
                        name="seatType"
                        checked={currentEditStatus === 'available'}
                        onChange={() => setCurrentEditStatus('available')}
                        className="hidden"
                      />
                      <div className={cn(
                        "w-6 h-6 rounded border-2 flex items-center justify-center", 
                        currentEditStatus === 'available' ? "border-primary-300" : "border-transparent"
                      )}>
                        <div className="w-4 h-4 bg-bg-200 rounded"></div>
                      </div>
                      <span className="text-xs">Available</span>
                    </label>
                    
                    <label className="flex items-center gap-1 cursor-pointer">
                      <input
                        type="radio"
                        name="seatType"
                        checked={currentEditStatus === 'accessible'}
                        onChange={() => setCurrentEditStatus('accessible')}
                        className="hidden"
                      />
                      <div className={cn(
                        "w-6 h-6 rounded border-2 flex items-center justify-center", 
                        currentEditStatus === 'accessible' ? "border-primary-300" : "border-transparent"
                      )}>
                        <div className="w-4 h-4 bg-blue-500 rounded flex items-center justify-center">
                          <span className="text-xs text-white">♿</span>
                        </div>
                      </div>
                      <span className="text-xs">Accessible</span>
                    </label>
                    
                    <label className="flex items-center gap-1 cursor-pointer">
                      <input
                        type="radio"
                        name="seatType"
                        checked={currentEditStatus === 'empty'}
                        onChange={() => setCurrentEditStatus('empty')}
                        className="hidden"
                      />
                      <div className={cn(
                        "w-6 h-6 rounded border-2 flex items-center justify-center", 
                        currentEditStatus === 'empty' ? "border-primary-300" : "border-transparent"
                      )}>
                        <div className="w-4 h-4 border border-dashed border-gray-500 rounded"></div>
                      </div>
                      <span className="text-xs">Empty</span>
                    </label>
                  </div>
                </div>
              </div>
            )}

            {/* Layout Selector Modal */}
            {showLayoutSelector && (
              <div className="absolute top-full left-0 w-full bg-bg-300 p-4 rounded-lg mt-2 shadow-lg z-50">
                <h4 className="text-sm font-semibold mb-2">Available Layouts</h4>
                {availableLayouts.length > 0 ? (
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {availableLayouts.map((layout) => (
                      <button
                        key={layout.id}
                        onClick={() => handleLayoutSelect(layout.id)}
                        className="w-full text-left p-2 hover:bg-bg-400 rounded-lg flex justify-between items-center"
                      >
                        <span className="text-sm">{layout.name}</span>
                        <span className="text-xs text-text-200">
                          {new Date(layout.updatedAt).toLocaleDateString()}
                        </span>
                      </button>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-text-200">No saved layouts available</p>
                )}
              </div>
            )}
          </div>
        )}

        {/* Screen visualization */}
        {showScreen && (
          <div className="w-full max-w-lg mx-auto mb-8 flex flex-col items-center">
            <div className="w-full h-10 relative">
              <svg className="w-full h-full" viewBox="0 0 300 40" preserveAspectRatio="none">
                <path
                  d="M10,35 C50,10 250,10 290,35"
                  className="stroke-primary-300"
                  fill="none"
                  strokeWidth="3"
                  strokeLinecap="round"
                  style={{
                    filter: 'drop-shadow(0 0 5px rgba(172, 194, 239, 0.7)) drop-shadow(0 0 10px rgba(172, 194, 239, 0.5))'
                  }}
                />
              </svg>
            </div>
            <div className="text-xs text-text-200 mt-1">Screen</div>
          </div>
        )}

        {/* Seat grid */}
        <div className="max-w-lg mx-auto w-full grid grid-cols-[auto_1fr] gap-x-3 gap-y-1">
          {sortedRows.map((row) => (
            <div key={row} className="contents">
              {/* Row label */}
              <div className="flex items-center justify-center font-semibold text-sm w-6">
                {row}
              </div>
              
              {/* Seats in this row */}
              <div className="grid grid-cols-12 gap-x-1.5 gap-y-1">
                {seatsByRow[row].map((seat) => (
                  <button
                    key={seat.id}
                    onClick={() => handleSeatClick(seat)}
                    disabled={!editMode && (seat.status === 'occupied' || seat.status === 'empty')}
                    className={cn(
                      "w-7 h-7 rounded flex items-center justify-center transition-all",
                      seat.status === 'available' && "bg-bg-200 hover:bg-bg-100",
                      seat.status === 'selected' && "bg-primary-300 text-primary-100",
                      seat.status === 'occupied' && "bg-gray-600 cursor-not-allowed",
                      seat.status === 'accessible' && "bg-blue-500 text-white hover:bg-blue-600",
                      seat.status === 'empty' && "border border-dashed border-gray-500 bg-transparent cursor-default",
                      editMode && "cursor-pointer hover:opacity-80"
                    )}
                    title={`${seat.row}${seat.number}`}
                  >
                    {seat.status === 'accessible' && <span className="text-[10px]">♿</span>}
                    {seat.status === 'selected' && <Check size={12} />}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Legend */}
        <div className="mt-6 flex flex-wrap gap-4 justify-center">
          <div className="flex items-center gap-1.5">
            <div className="w-4 h-4 bg-bg-200 rounded"></div>
            <span className="text-xs">Available</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-4 h-4 bg-primary-300 rounded flex items-center justify-center text-primary-100">
              <Check size={10} />
            </div>
            <span className="text-xs">Selected</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-4 h-4 bg-blue-500 rounded flex items-center justify-center text-white">
              <span className="text-[8px]">♿</span>
            </div>
            <span className="text-xs">Accessible</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-4 h-4 border border-dashed border-gray-500 rounded"></div>
            <span className="text-xs">Empty</span>
          </div>
        </div>

        {/* Selected seats information */}
        {!isAdminMode && selectedSeats.length > 0 && (
          <div className="mt-6 bg-bg-300 p-3 rounded-lg w-full">
            <h3 className="text-sm font-semibold mb-2">Selected Seats</h3>
            <div className="flex flex-wrap gap-1.5">
              {selectedSeats.map((seat) => (
                <div key={seat.id} className="bg-primary-300 text-primary-100 px-2 py-0.5 rounded text-xs">
                  {seat.row}{seat.number}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 