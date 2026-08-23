import { Badge } from '@/components/ui/badge';
import { Layers, ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';
import { ImageAnalysisResult, MetricDifference } from '@/types';

interface MetricComparisonTableProps {
  previousResult: ImageAnalysisResult;
  currentResult: ImageAnalysisResult;
}

export function computeMetricDifferences(
  previousResult: ImageAnalysisResult,
  currentResult: ImageAnalysisResult
): MetricDifference[] {
  const prevMetrics = previousResult.technicalMetrics || {};
  const currMetrics = currentResult.technicalMetrics || {};

  const differences: MetricDifference[] = [];

  // 1. Mask Area (pixels)
  const prevArea = prevMetrics.maskAreaPixels;
  const currArea = currMetrics.maskAreaPixels;
  if (typeof prevArea === 'number' && typeof currArea === 'number') {
    const diff = currArea - prevArea;
    let diffStr = 'No change';
    let diffType: MetricDifference['differenceType'] = 'neutral';
    if (diff > 0) {
      diffStr = `+${diff.toLocaleString()} pixels`;
      diffType = 'positive';
    } else if (diff < 0) {
      diffStr = `${diff.toLocaleString()} pixels`;
      diffType = 'negative';
    }
    differences.push({
      metricName: 'Mask Area (pixels)',
      previousValue: prevArea,
      currentValue: currArea,
      previousFormatted: `${prevArea.toLocaleString()} pixels`,
      currentFormatted: `${currArea.toLocaleString()} pixels`,
      differenceFormatted: diffStr,
      differenceType: diffType,
    });
  } else {
    differences.push({
      metricName: 'Mask Area (pixels)',
      previousValue: prevArea,
      currentValue: currArea,
      previousFormatted: typeof prevArea === 'number' ? `${prevArea.toLocaleString()} pixels` : 'N/A',
      currentFormatted: typeof currArea === 'number' ? `${currArea.toLocaleString()} pixels` : 'N/A',
      differenceFormatted: 'Unavailable',
      differenceType: 'unavailable',
    });
  }

  // 2. Mask Fraction (%)
  const prevFraction = prevMetrics.maskFraction;
  const currFraction = currMetrics.maskFraction;
  if (typeof prevFraction === 'number' && typeof currFraction === 'number') {
    const diffPct = (currFraction - prevFraction) * 100;
    let diffStr = 'No change';
    let diffType: MetricDifference['differenceType'] = 'neutral';
    if (Math.abs(diffPct) < 0.001) {
      diffStr = 'No change';
      diffType = 'neutral';
    } else if (diffPct > 0) {
      diffStr = `+${diffPct.toFixed(2)} percentage points`;
      diffType = 'positive';
    } else {
      diffStr = `${diffPct.toFixed(2)} percentage points`;
      diffType = 'negative';
    }
    differences.push({
      metricName: 'Mask Fraction (coverage)',
      previousValue: prevFraction,
      currentValue: currFraction,
      previousFormatted: `${(prevFraction * 100).toFixed(2)}%`,
      currentFormatted: `${(currFraction * 100).toFixed(2)}%`,
      differenceFormatted: diffStr,
      differenceType: diffType,
    });
  } else {
    differences.push({
      metricName: 'Mask Fraction (coverage)',
      previousValue: prevFraction,
      currentValue: currFraction,
      previousFormatted: typeof prevFraction === 'number' ? `${(prevFraction * 100).toFixed(2)}%` : 'N/A',
      currentFormatted: typeof currFraction === 'number' ? `${(currFraction * 100).toFixed(2)}%` : 'N/A',
      differenceFormatted: 'Unavailable',
      differenceType: 'unavailable',
    });
  }

  // 3. Probability Mean
  const prevProb = prevMetrics.probabilityMean;
  const currProb = currMetrics.probabilityMean;
  if (typeof prevProb === 'number' && typeof currProb === 'number') {
    const diff = currProb - prevProb;
    let diffStr = 'No change';
    let diffType: MetricDifference['differenceType'] = 'neutral';
    if (Math.abs(diff) < 0.0001) {
      diffStr = 'No change';
      diffType = 'neutral';
    } else if (diff > 0) {
      diffStr = `+${diff.toFixed(4)}`;
      diffType = 'positive';
    } else {
      diffStr = `${diff.toFixed(4)}`;
      diffType = 'negative';
    }
    differences.push({
      metricName: 'Probability Mean (confidence)',
      previousValue: prevProb,
      currentValue: currProb,
      previousFormatted: prevProb.toFixed(4),
      currentFormatted: currProb.toFixed(4),
      differenceFormatted: diffStr,
      differenceType: diffType,
    });
  } else {
    differences.push({
      metricName: 'Probability Mean (confidence)',
      previousValue: prevProb,
      currentValue: currProb,
      previousFormatted: typeof prevProb === 'number' ? prevProb.toFixed(4) : 'N/A',
      currentFormatted: typeof currProb === 'number' ? currProb.toFixed(4) : 'N/A',
      differenceFormatted: 'Unavailable',
      differenceType: 'unavailable',
    });
  }

  // 4. Threshold
  const prevThresh = prevMetrics.threshold;
  const currThresh = currMetrics.threshold;
  if (typeof prevThresh === 'number' && typeof currThresh === 'number') {
    const diff = currThresh - prevThresh;
    let diffStr = 'No change';
    let diffType: MetricDifference['differenceType'] = 'neutral';
    if (Math.abs(diff) > 0.001) {
      diffStr = diff > 0 ? `+${diff.toFixed(2)}` : `${diff.toFixed(2)}`;
      diffType = diff > 0 ? 'positive' : 'negative';
    }
    differences.push({
      metricName: 'Threshold (binarization cutoff)',
      previousValue: prevThresh,
      currentValue: currThresh,
      previousFormatted: prevThresh.toFixed(2),
      currentFormatted: currThresh.toFixed(2),
      differenceFormatted: diffStr,
      differenceType: diffType,
    });
  } else {
    differences.push({
      metricName: 'Threshold (binarization cutoff)',
      previousValue: prevThresh,
      currentValue: currThresh,
      previousFormatted: typeof prevThresh === 'number' ? prevThresh.toFixed(2) : '0.50',
      currentFormatted: typeof currThresh === 'number' ? currThresh.toFixed(2) : '0.50',
      differenceFormatted: 'No change',
      differenceType: 'neutral',
    });
  }

  return differences;
}

export function MetricComparisonTable({
  previousResult,
  currentResult,
}: MetricComparisonTableProps) {
  const differences = computeMetricDifferences(previousResult, currentResult);

  return (
    <div className="rounded-xl border bg-card overflow-hidden shadow-sm">
      <div className="bg-muted/20 px-4 py-3 border-b flex items-center gap-2">
        <Layers className="h-4 w-4 text-primary" />
        <h4 className="text-sm font-semibold text-foreground">
          Real AI Segmentation Metric Comparison
        </h4>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs sm:text-sm">
          <thead>
            <tr className="border-b bg-muted/10 text-muted-foreground font-semibold">
              <th className="py-3 px-4">Metric</th>
              <th className="py-3 px-4 text-right">Previous Scan</th>
              <th className="py-3 px-4 text-right">Current Scan</th>
              <th className="py-3 px-4 text-right">Difference (Current - Previous)</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {differences.map((diff, index) => (
              <tr key={index} className="hover:bg-muted/5 transition-colors">
                <td className="py-3 px-4 font-medium text-foreground">
                  {diff.metricName}
                </td>
                <td className="py-3 px-4 text-right font-mono text-muted-foreground">
                  {diff.previousFormatted}
                </td>
                <td className="py-3 px-4 text-right font-mono font-semibold text-foreground">
                  {diff.currentFormatted}
                </td>
                <td className="py-3 px-4 text-right">
                  <div className="flex items-center justify-end gap-1.5 font-mono font-semibold">
                    {diff.differenceType === 'positive' && (
                      <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200 gap-1 font-mono">
                        <ArrowUpRight className="h-3 w-3" />
                        {diff.differenceFormatted}
                      </Badge>
                    )}
                    {diff.differenceType === 'negative' && (
                      <Badge variant="outline" className="bg-slate-100 text-slate-700 border-slate-300 gap-1 font-mono">
                        <ArrowDownRight className="h-3 w-3" />
                        {diff.differenceFormatted}
                      </Badge>
                    )}
                    {diff.differenceType === 'neutral' && (
                      <Badge variant="outline" className="bg-muted text-muted-foreground border-muted-foreground/30 gap-1 font-mono">
                        <Minus className="h-3 w-3" />
                        No change
                      </Badge>
                    )}
                    {diff.differenceType === 'unavailable' && (
                      <span className="text-xs text-muted-foreground">Unavailable</span>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

