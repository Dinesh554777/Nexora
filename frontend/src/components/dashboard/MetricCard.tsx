import { LucideIcon } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';

interface MetricCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon: LucideIcon;
  trend?: string;
}

export function MetricCard({ title, value, description, icon: Icon, trend }: MetricCardProps) {
  return (
    <Card className="glass-card border-0 shadow-[0_20px_60px_-28px_rgba(14,116,144,0.35)]">
      <CardContent className="p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <p className="mt-3 text-3xl font-bold tracking-tight text-foreground">{value}</p>
            {description && (
              <p className="mt-2 text-xs text-muted-foreground">{description}</p>
            )}
            {trend && (
              <p className="mt-1 text-xs text-primary">{trend}</p>
            )}
          </div>
          <div className="rounded-2xl bg-gradient-to-br from-primary/15 via-cyan-500/10 to-emerald-500/10 p-3 ring-1 ring-primary/10">
            <Icon className="h-5 w-5 text-primary" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
