import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { FilterX } from 'lucide-react';

export interface FilterState {
  oaStatus: 'All' | 'OA' | 'Non-OA';
}

interface AnalyticsFiltersProps {
  filters: FilterState;
  onFilterChange: (filters: FilterState) => void;
}

export function AnalyticsFilters({ filters, onFilterChange }: AnalyticsFiltersProps) {
  const handleOAFilterChange = (status: 'All' | 'OA' | 'Non-OA') => {
    onFilterChange({ ...filters, oaStatus: status });
  };

  const handleResetFilters = () => {
    onFilterChange({ oaStatus: 'All' });
  };

  const hasActiveFilters = filters.oaStatus !== 'All';

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Filters</CardTitle>
          {hasActiveFilters && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleResetFilters}
              className="gap-2"
            >
              <FilterX className="h-4 w-4" />
              Reset Filters
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div>
            <p className="text-sm font-medium mb-2">OA Status</p>
            <div className="flex flex-wrap gap-2">
              <Badge
                variant={filters.oaStatus === 'All' ? 'default' : 'outline'}
                className="cursor-pointer"
                onClick={() => handleOAFilterChange('All')}
              >
                All Patients
              </Badge>
              <Badge
                variant={filters.oaStatus === 'OA' ? 'destructive' : 'outline'}
                className="cursor-pointer"
                onClick={() => handleOAFilterChange('OA')}
              >
                OA Only
              </Badge>
              <Badge
                variant={filters.oaStatus === 'Non-OA' ? 'default' : 'outline'}
                className="cursor-pointer bg-green-600 hover:bg-green-700"
                onClick={() => handleOAFilterChange('Non-OA')}
              >
                Non-OA Only
              </Badge>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
