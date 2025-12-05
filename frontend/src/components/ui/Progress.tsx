'use client';

import { forwardRef } from 'react';
import * as ProgressPrimitive from '@radix-ui/react-progress';
import { cn } from '@/lib/utils';

interface ProgressProps extends React.ComponentPropsWithoutRef<typeof ProgressPrimitive.Root> {
  value?: number;
  label?: string;
  showValue?: boolean;
}

const Progress = forwardRef<
  React.ElementRef<typeof ProgressPrimitive.Root>,
  ProgressProps
>(({ className, value = 0, label, showValue = false, ...props }, ref) => (
  <div className="w-full">
    {(label || showValue) && (
      <div className="flex justify-between mb-1">
        {label && <span className="text-sm font-medium text-secondary-700">{label}</span>}
        {showValue && <span className="text-sm font-medium text-secondary-500">{value}%</span>}
      </div>
    )}
    <ProgressPrimitive.Root
      ref={ref}
      className={cn(
        'relative h-2 w-full overflow-hidden rounded-full bg-secondary-100',
        className
      )}
      {...props}
    >
      <ProgressPrimitive.Indicator
        className="h-full bg-primary-600 transition-all duration-500 ease-out"
        style={{ width: `${value}%` }}
      />
    </ProgressPrimitive.Root>
  </div>
));

Progress.displayName = 'Progress';

export { Progress };
