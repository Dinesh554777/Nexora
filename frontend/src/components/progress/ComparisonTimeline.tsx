import { Calendar, ArrowRight } from 'lucide-react';

interface ComparisonTimelineProps {
  previousDate?: string;
  currentDate?: string;
}

export function ComparisonTimeline({ previousDate, currentDate }: ComparisonTimelineProps) {
  if (!previousDate && !currentDate) {
    return null;
  }

  const formatDisplayDate = (d?: string) => {
    if (!d) return 'Date not specified';
    try {
      const parsed = new Date(d);
      if (isNaN(parsed.getTime())) return d;
      return parsed.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return d;
    }
  };

  const getDaysDifference = () => {
    if (!previousDate || !currentDate) return null;
    const prev = new Date(previousDate).getTime();
    const curr = new Date(currentDate).getTime();
    if (isNaN(prev) || isNaN(curr)) return null;
    const diffTime = curr - prev;
    const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const daysDiff = getDaysDifference();

  return (
    <div className="rounded-xl border bg-card p-4 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-xs uppercase font-bold text-primary tracking-wider">
          Scan Comparison Timeline
        </h4>
        {daysDiff !== null && daysDiff >= 0 && (
          <span className="text-xs font-medium text-muted-foreground bg-muted/50 px-2.5 py-0.5 rounded-full border">
            {daysDiff === 0 ? 'Same Day' : `${daysDiff} day${daysDiff !== 1 ? 's' : ''} interval`}
          </span>
        )}
      </div>

      <div className="relative flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 py-2">
        {/* Previous Node */}
        <div className="flex items-center gap-3 z-10">
          <div className="h-10 w-10 rounded-full bg-slate-100 dark:bg-slate-800 border-2 border-slate-400 flex items-center justify-center text-slate-700 dark:text-slate-300 font-bold text-xs shadow-sm">
            T1
          </div>
          <div>
            <span className="text-[11px] font-semibold uppercase text-muted-foreground block">
              Previous Scan (Baseline)
            </span>
            <span className="text-sm font-bold text-foreground flex items-center gap-1.5">
              <Calendar className="h-3.5 w-3.5 text-primary" />
              {formatDisplayDate(previousDate)}
            </span>
          </div>
        </div>

        {/* Connecting Line */}
        <div className="hidden sm:flex flex-1 items-center justify-center px-4">
          <div className="w-full h-0.5 bg-border relative flex items-center justify-center">
            <ArrowRight className="h-4 w-4 text-muted-foreground absolute right-0" />
          </div>
        </div>

        {/* Current Node */}
        <div className="flex items-center gap-3 z-10">
          <div className="h-10 w-10 rounded-full bg-primary/10 border-2 border-primary flex items-center justify-center text-primary font-bold text-xs shadow-sm">
            T2
          </div>
          <div>
            <span className="text-[11px] font-semibold uppercase text-primary block">
              Current Scan (Follow-up)
            </span>
            <span className="text-sm font-bold text-foreground flex items-center gap-1.5">
              <Calendar className="h-3.5 w-3.5 text-primary" />
              {formatDisplayDate(currentDate)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

