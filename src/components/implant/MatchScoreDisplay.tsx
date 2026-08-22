import { Progress } from '@/components/ui/progress';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface MatchScoreDisplayProps {
  score: number;
  label?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function MatchScoreDisplay({ score, label = 'Match Score', size = 'md' }: MatchScoreDisplayProps) {
  const getScoreCategory = (score: number) => {
    if (score >= 90) return { label: 'Excellent Match', color: 'text-green-600' };
    if (score >= 75) return { label: 'Good Match', color: 'text-blue-600' };
    if (score >= 60) return { label: 'Acceptable Match', color: 'text-yellow-600' };
    return { label: 'Review Recommended', color: 'text-orange-600' };
  };

  const category = getScoreCategory(score);

  const sizeClasses = {
    sm: 'text-2xl',
    md: 'text-4xl',
    lg: 'text-5xl',
  };

  return (
    <Card className="border-2">
      <CardContent className="p-6">
        <div className="space-y-4">
          <div className="flex items-end justify-between">
            <div>
              <p className="text-sm text-muted-foreground mb-1">{label}</p>
              <p className={cn('font-bold', sizeClasses[size])}>{score}%</p>
            </div>
            <div className={cn('font-semibold text-sm', category.color)}>
              {category.label}
            </div>
          </div>
          <Progress value={score} className="h-3" />
        </div>
      </CardContent>
    </Card>
  );
}
