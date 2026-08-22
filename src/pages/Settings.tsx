import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export function Settings() {
  return (
    <div className="space-y-8">
      <PageHeader
        title="Settings"
        description="Configure your KneeVision AI preferences"
      />

      <Card>
        <CardHeader>
          <CardTitle>Application Settings</CardTitle>
          <CardDescription>Settings page coming soon</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Configuration options will be available in future updates.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
