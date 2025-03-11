import * as React from "react";
import { Check } from "lucide-react";

export interface CheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
  checked?: boolean;
  onCheckedChange?: (checked: boolean) => void;
}

export const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className, checked, onCheckedChange, ...props }, ref) => {
    return (
      <div className="relative inline-flex items-center justify-center">
        <input
          type="checkbox"
          className="sr-only"
          ref={ref}
          checked={checked}
          onChange={(e) => onCheckedChange?.(e.target.checked)}
          {...props}
        />
        <div
          className={`
            h-5 w-5 rounded border flex items-center justify-center
            ${checked 
              ? 'bg-accent-200 border-accent-200' 
              : 'border-primary-200/30 bg-bg-200'
            }
            transition-colors cursor-pointer
          `}
          onClick={() => onCheckedChange?.(!checked)}
          tabIndex={0}
          role="checkbox"
          aria-checked={checked}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              onCheckedChange?.(!checked);
            }
          }}
        >
          {checked && <Check className="h-3.5 w-3.5 text-bg-300" />}
        </div>
      </div>
    );
  }
);
