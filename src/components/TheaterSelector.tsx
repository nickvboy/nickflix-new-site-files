import { useState } from 'react';
import { ChevronLeft, ChevronRight, ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';

// Types for the theater selector
interface Theater {
  id: string;
  name: string;
  address: string;
}

interface ShowTime {
  id: string;
  time: string;
  theater: string;
  available: boolean;
}

interface MovieShowingProps {
  movieId?: string;
  className?: string;
  movieTitle?: string;
}

// Sample data with more dates
const sampleDates = [
  { day: 'Mon', date: '11' },
  { day: 'Tue', date: '12', active: true },
  { day: 'Wed', date: '13' },
  { day: 'Thu', date: '14' },
  { day: 'Fri', date: '15' },
  { day: 'Sat', date: '16' },
  { day: 'Sun', date: '17' },
  { day: 'Mon', date: '18' },
  { day: 'Tue', date: '19' },
  { day: 'Wed', date: '20' },
  { day: 'Thu', date: '21' },
  { day: 'Fri', date: '22' },
  { day: 'Sat', date: '23' },
  { day: 'Sun', date: '24' },
  { day: 'Mon', date: '25' },
  { day: 'Tue', date: '26' },
  { day: 'Wed', date: '27' },
  { day: 'Thu', date: '28' },
  { day: 'Fri', date: '29' },
  { day: 'Sat', date: '30' },
  { day: 'Sun', date: '31' },
];

const sampleTheaters: Theater[] = [
  { id: 't1', name: 'AMC Theater', address: '123 Main St, City' },
  { id: 't2', name: 'Regal Cinema', address: '456 Oak Ave, Town' },
  { id: 't3', name: 'Cinemark', address: '789 Pine Blvd, Village' },
];

const sampleShowtimes: ShowTime[] = [
  { id: 's1', time: '10:30 AM', theater: 't1', available: true },
  { id: 's2', time: '1:15 PM', theater: 't1', available: true },
  { id: 's3', time: '4:00 PM', theater: 't1', available: false },
  { id: 's4', time: '7:30 PM', theater: 't1', available: true },
  { id: 's5', time: '11:00 AM', theater: 't2', available: true },
  { id: 's6', time: '2:45 PM', theater: 't2', available: true },
  { id: 's7', time: '12:30 PM', theater: 't3', available: true },
  { id: 's8', time: '6:15 PM', theater: 't3', available: true },
];

const formatTypes = ["2D", "3D", "IMAX", "4DX"];

export function TheaterSelector({ movieId, className, movieTitle }: MovieShowingProps) {
  const [selectedDate, setSelectedDate] = useState<number>(1);
  const [dateOffset, setDateOffset] = useState<number>(0);
  const [selectedTheater, setSelectedTheater] = useState<string>(sampleTheaters[0].id);
  const [selectedTime, setSelectedTime] = useState<string>("");
  const [showTimeOptions, setShowTimeOptions] = useState<boolean>(false);
  const [showTypeOptions, setShowTypeOptions] = useState<boolean>(false);
  const [showTheaterOptions, setShowTheaterOptions] = useState<boolean>(false);
  const [selectedType, setSelectedType] = useState<string>("2D");

  const availableShowtimes = sampleShowtimes.filter(
    (showtime) => showtime.theater === selectedTheater
  );

  const selectedTheaterInfo = sampleTheaters.find(
    (theater) => theater.id === selectedTheater
  );

  // Calculate visible dates (7 at a time)
  const visibleDates = sampleDates.slice(dateOffset, dateOffset + 7);

  // Handle carousel navigation
  const handlePrevDates = () => {
    if (dateOffset > 0) {
      setDateOffset(dateOffset - 1);
    }
  };

  const handleNextDates = () => {
    if (dateOffset < sampleDates.length - 7) {
      setDateOffset(dateOffset + 1);
    }
  };

  return (
    <div className={cn("w-full bg-bg-400 text-text-100 p-4 rounded-xl", className)}>
      {/* All elements in a single row */}
      <div className="flex flex-col lg:flex-row items-center justify-between gap-6">
        {/* Date section */}
        <div className="flex items-center w-full lg:w-auto">
          <h3 className="text-lg font-semibold text-text-100 mr-5 w-16 flex-shrink-0">Date</h3>
          <div className="flex items-center">
            <button 
              className={cn(
                "text-primary-300 flex-shrink-0 mr-2",
                dateOffset === 0 ? "opacity-50 cursor-not-allowed" : ""
              )}
              onClick={handlePrevDates}
              disabled={dateOffset === 0}
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
            
            <div className="flex space-x-2 overflow-x-auto scrollbar-hide">
              {visibleDates.map((date, index) => {
                const actualIndex = index + dateOffset;
                return (
                  <button
                    key={`${date.day}-${date.date}`}
                    onClick={() => setSelectedDate(actualIndex)}
                    className={cn(
                      "flex-shrink-0 w-14 h-16 flex flex-col items-center justify-center transition-all rounded-xl",
                      selectedDate === actualIndex
                        ? "bg-primary-300 text-primary-100"
                        : "bg-bg-300 hover:bg-bg-300/80"
                    )}
                  >
                    <span className="text-xs">{date.day}</span>
                    <span className="text-base font-bold">{date.date}</span>
                  </button>
                );
              })}
            </div>
            
            <button 
              className={cn(
                "text-primary-300 flex-shrink-0 ml-2",
                dateOffset >= sampleDates.length - 7 ? "opacity-50 cursor-not-allowed" : ""
              )}
              onClick={handleNextDates}
              disabled={dateOffset >= sampleDates.length - 7}
            >
              <ChevronRight className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Time section */}
        <div className="flex items-center w-full lg:flex-1 lg:ml-6">
          <h3 className="text-lg font-semibold text-text-100 mr-5 w-16 flex-shrink-0">Time</h3>
          <div className="relative w-full">
            <button
              onClick={() => {
                setShowTimeOptions(!showTimeOptions);
                setShowTypeOptions(false);
                setShowTheaterOptions(false);
              }}
              className="w-full flex items-center justify-between bg-bg-300 px-4 py-2 rounded-lg min-w-[140px]"
            >
              <span className={selectedTime ? "text-text-100" : "text-text-200"}>
                {selectedTime || "Choose time"}
              </span>
              <ChevronDown className="h-4 w-4 text-primary-300 ml-2" />
            </button>
            
            {showTimeOptions && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-bg-300 rounded-lg p-2 z-30 max-h-[200px] overflow-y-auto shadow-lg">
                {availableShowtimes.map((showtime) => (
                  <button
                    key={showtime.id}
                    onClick={() => {
                      setSelectedTime(showtime.time);
                      setShowTimeOptions(false);
                    }}
                    disabled={!showtime.available}
                    className={cn(
                      "w-full p-2 my-1 rounded text-left",
                      selectedTime === showtime.time
                        ? "bg-primary-300 text-primary-100"
                        : showtime.available 
                          ? "hover:bg-primary-300 hover:text-primary-100" 
                          : "opacity-50 cursor-not-allowed"
                    )}
                  >
                    {showtime.time}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Type section - Buttons on mobile, dropdown on desktop */}
        <div className="flex items-center w-full lg:flex-1 lg:ml-6">
          <h3 className="text-lg font-semibold text-text-100 mr-5 w-16 flex-shrink-0">Type</h3>
          
          {/* Mobile buttons (shown on mobile, hidden on desktop) */}
          <div className="flex space-x-2 min-w-[180px] w-full lg:hidden">
            {formatTypes.map((type) => (
              <button
                key={type}
                onClick={() => setSelectedType(type)}
                className={cn(
                  "w-10 h-10 rounded-lg transition-all text-center flex items-center justify-center",
                  selectedType === type
                    ? "bg-primary-300 text-primary-100"
                    : "bg-bg-300 hover:bg-bg-300/80"
                )}
              >
                {type}
              </button>
            ))}
          </div>
          
          {/* Desktop dropdown (hidden on mobile, shown on desktop) */}
          <div className="hidden lg:block relative w-full">
            <button
              onClick={() => {
                setShowTypeOptions(!showTypeOptions);
                setShowTimeOptions(false);
                setShowTheaterOptions(false);
              }}
              className="w-full flex items-center justify-between bg-bg-300 px-4 py-2 rounded-lg"
            >
              <span className="text-text-100">{selectedType}</span>
              <ChevronDown className="h-4 w-4 text-primary-300 ml-2" />
            </button>
            
            {showTypeOptions && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-bg-300 rounded-lg p-2 z-30 shadow-lg">
                {formatTypes.map((type) => (
                  <button
                    key={type}
                    onClick={() => {
                      setSelectedType(type);
                      setShowTypeOptions(false);
                    }}
                    className={cn(
                      "w-full p-2 rounded text-left",
                      selectedType === type
                        ? "bg-primary-300 text-primary-100"
                        : "hover:bg-primary-300/20"
                    )}
                  >
                    {type}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Theater/Address section */}
        <div className="flex items-center w-full lg:flex-1 lg:ml-6">
          <h3 className="text-lg font-semibold text-text-100 mr-5 w-16 flex-shrink-0">Address</h3>
          <div className="relative w-full">
            <button
              onClick={() => {
                setShowTheaterOptions(!showTheaterOptions);
                setShowTimeOptions(false);
                setShowTypeOptions(false);
              }}
              className="w-full flex items-center justify-between bg-bg-300 px-4 py-2 rounded-lg text-left"
            >
              <div className="overflow-hidden">
                <div className="text-text-100">{selectedTheaterInfo?.name}</div>
                <div className="text-xs text-text-200 truncate">{selectedTheaterInfo?.address}</div>
              </div>
              <ChevronDown className="h-4 w-4 text-primary-300 flex-shrink-0 ml-2" />
            </button>
            
            {showTheaterOptions && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-bg-300 rounded-lg p-2 z-30 max-h-[200px] overflow-y-auto shadow-lg">
                {sampleTheaters.map((theater) => (
                  <button
                    key={theater.id}
                    onClick={() => {
                      setSelectedTheater(theater.id);
                      setShowTheaterOptions(false);
                    }}
                    className="w-full text-left p-2 hover:bg-primary-300 hover:text-primary-100 rounded"
                  >
                    <div>{theater.name}</div>
                    <div className="text-xs text-text-200">{theater.address}</div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/* Add this to your global CSS file or create a new CSS module */
/* 
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
*/ 