import React from 'react';
import { AlertCircle, Clock, CheckCircle2, XCircle } from 'lucide-react';
import { cn } from './Card';

type DataState = 'FRESH' | 'STALE' | 'UNAVAILABLE' | 'INSUFFICIENT_DATA' | 'FAILED' | 'LOADING';

interface DataStateIndicatorProps {
  state: DataState;
  className?: string;
  message?: string;
}

export const DataStateIndicator: React.FC<DataStateIndicatorProps> = ({ state, className, message }) => {
  const configs = {
    FRESH: { icon: CheckCircle2, class: 'badge-success', label: 'Fresh' },
    STALE: { icon: Clock, class: 'badge-warning', label: 'Stale Data' },
    UNAVAILABLE: { icon: AlertCircle, class: 'badge-stale', label: 'Unavailable' },
    INSUFFICIENT_DATA: { icon: AlertCircle, class: 'badge-warning', label: 'Insufficient Data' },
    FAILED: { icon: XCircle, class: 'badge-danger', label: 'Failed' },
    LOADING: { icon: Clock, class: 'badge-info', label: 'Loading...' },
  };

  const config = configs[state];
  const Icon = config.icon;

  return (
    <div className={cn("inline-flex items-center gap-1.5 badge", config.class, className)} title={message}>
      <Icon size={12} className={state === 'LOADING' ? 'animate-spin' : ''} />
      <span>{config.label}</span>
    </div>
  );
};
