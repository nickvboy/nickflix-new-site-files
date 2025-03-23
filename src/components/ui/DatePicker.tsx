import React, { useState, forwardRef, useEffect } from "react";
import ReactDatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import { Calendar as CalendarIcon } from "lucide-react";
import { Button } from "./button";
import { cn } from "@/lib/utils";

export interface DatePickerProps {
  /**
   * Selected date value
   */
  value?: Date | null;
  
  /**
   * Date change handler
   */
  onChange: (date: Date | null) => void;
  
  /**
   * Optional placeholder text
   */
  placeholder?: string;
  
  /**
   * Max date that can be selected
   */
  maxDate?: Date;
  
  /**
   * Min date that can be selected
   */
  minDate?: Date;
  
  /**
   * Optional CSS class names
   */
  className?: string;
  
  /**
   * Whether the input is disabled
   */
  disabled?: boolean;
  
  /**
   * Optional label for the date picker
   */
  label?: string;
  
  /**
   * Optional help text
   */
  helperText?: string;
  
  /**
   * Whether the field is required
   */
  required?: boolean;
  
  /**
   * Calculate and return age from selected date
   */
  showAge?: boolean;
}

/**
 * Calculate age from date of birth
 */
export function calculateAge(dob: Date): number {
  const today = new Date();
  let age = today.getFullYear() - dob.getFullYear();
  const monthDiff = today.getMonth() - dob.getMonth();
  
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < dob.getDate())) {
    age--;
  }
  
  return age;
}

export function DatePicker({
  value,
  onChange,
  placeholder = "Select date",
  maxDate,
  minDate,
  className,
  disabled = false,
  label,
  helperText,
  required = false,
  showAge = false,
}: DatePickerProps) {
  const [age, setAge] = useState<number | null>(null);
  
  // Update age when value changes
  useEffect(() => {
    if (value && showAge) {
      setAge(calculateAge(value));
    } else {
      setAge(null);
    }
  }, [value, showAge]);
  
  // Custom input component that matches the app's styling
  const CustomInput = forwardRef<HTMLButtonElement, React.ButtonHTMLAttributes<HTMLButtonElement>>(
    ({ value, onClick, onChange: _onChange, ...props }, ref) => (
      <Button
        type="button"
        variant="outline"
        onClick={onClick}
        ref={ref}
        className={cn(
          "w-full justify-start text-left font-normal bg-bg-400 border-primary-200 text-text-100 hover:text-accent-200 hover:bg-bg-400/90",
          !value && "text-text-200/50",
          className
        )}
        disabled={disabled}
        {...props}
      >
        <CalendarIcon className="mr-2 h-4 w-4" />
        {value ? value : placeholder}
        {showAge && age !== null && <span className="ml-2 text-xs text-accent-200">({age} years old)</span>}
      </Button>
    )
  );
  
  CustomInput.displayName = "CustomDatePickerInput";

  return (
    <div className="space-y-2">
      {label && (
        <label className="text-sm font-medium text-text-100 flex items-center gap-1">
          {label}
          {required && <span className="text-accent-200">*</span>}
        </label>
      )}
      
      <ReactDatePicker
        selected={value}
        onChange={onChange}
        customInput={<CustomInput />}
        maxDate={maxDate}
        minDate={minDate}
        disabled={disabled}
        calendarClassName="bg-bg-200 border border-primary-200/20 shadow-lg rounded-md p-2"
        dayClassName={date => 
          cn("rounded hover:bg-accent-100 hover:text-text-100", 
            date.getDate() === value?.getDate() && 
            date.getMonth() === value?.getMonth() && 
            date.getFullYear() === value?.getFullYear()
              ? "bg-accent-200 text-bg-300"
              : "text-text-100"
          )
        }
        monthClassName={() => "text-text-100"}
        weekDayClassName={() => "text-accent-200"}
        fixedHeight
        showYearDropdown
        scrollableYearDropdown
        yearDropdownItemNumber={100}
        popperClassName="date-picker-popper"
        popperPlacement="bottom-start"
      />
      
      {helperText && <p className="text-xs text-text-200">{helperText}</p>}
      
      {/* Add custom styles to override datepicker defaults */}
      <style>{`
        .react-datepicker {
          background-color: #272b33 !important;
          border-color: rgba(77, 100, 141, 0.2) !important;
          color: #FFFFFF !important;
          font-family: inherit !important;
        }
        .react-datepicker__header {
          background-color: #323640 !important;
          border-bottom-color: rgba(77, 100, 141, 0.2) !important;
        }
        .react-datepicker__current-month,
        .react-datepicker__day-name,
        .react-datepicker-time__header {
          color: #FFFFFF !important;
        }
        .react-datepicker__year-dropdown,
        .react-datepicker__month-dropdown {
          background-color: #323640 !important;
          border-color: rgba(77, 100, 141, 0.2) !important;
        }
        .react-datepicker__year-option,
        .react-datepicker__month-option {
          color: #FFFFFF !important;
        }
        .react-datepicker__year-option:hover,
        .react-datepicker__month-option:hover {
          background-color: #3D5A80 !important;
        }
        .react-datepicker__day--keyboard-selected {
          background-color: #3D5A80 !important;
        }
        .react-datepicker__day:hover {
          background-color: #4d648d !important;
        }
        .react-datepicker__day--selected {
          background-color: #cee8ff !important;
          color: #272b33 !important;
        }
        .react-datepicker__triangle {
          border-bottom-color: #323640 !important;
        }
        .react-datepicker__triangle::before {
          border-bottom-color: rgba(77, 100, 141, 0.2) !important;
        }
      `}</style>
    </div>
  );
} 