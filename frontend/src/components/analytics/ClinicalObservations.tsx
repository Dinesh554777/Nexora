import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Lightbulb } from 'lucide-react';
import { AnalyticsResponse } from '@/types/api';

interface ClinicalObservationsProps {
  analytics: AnalyticsResponse;
}

export function ClinicalObservations({ analytics }: ClinicalObservationsProps) {
  const observations = [
    {
      title: 'OA Prevalence',
      text: `OA cases account for ${analytics.oaPercentage}% of the analyzed dataset (${analytics.oaPatients} out of ${analytics.totalPatients} patients).`,
    },
    {
      title: 'Meniscus Thickness',
      text: `Average meniscus thickness across all patients is ${analytics.avgMeniscusThickness} mm, with a range of ${analytics.minMeniscusThickness} mm to ${analytics.maxMeniscusThickness} mm.`,
    },
    {
      title: 'Patient Distribution',
      text: `The dataset includes ${analytics.totalPatients} patients with complete knee assessments across different age groups and demographics.`,
    },
  ];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Lightbulb className="h-5 w-5 text-primary" />
          <CardTitle>Key Observations</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {observations.map((obs, index) => (
          <div key={index} className="p-3 rounded-lg bg-muted/50">
            <p className="font-semibold text-sm mb-1">{obs.title}</p>
            <p className="text-sm text-muted-foreground">{obs.text}</p>
          </div>
        ))}
        
        <div className="pt-2 border-t text-xs text-muted-foreground">
          <p>
            <strong>Note:</strong> These observations are descriptive statistics calculated from 
            the patient dataset and do not constitute clinical diagnoses or predictions.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
