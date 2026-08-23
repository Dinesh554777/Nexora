import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export interface PatientInfo {
  patientId: string;
  patientName?: string;
  age: string;
  sex: 'M' | 'F' | '';
}

interface PatientInfoFormProps {
  patientInfo: PatientInfo;
  onChange: (info: PatientInfo) => void;
}

export function PatientInfoForm({ patientInfo, onChange }: PatientInfoFormProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Patient Information</CardTitle>
        <CardDescription>Optional patient demographics for reporting</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="patientName">Patient Name (Optional)</Label>
            <Input
              id="patientName"
              type="text"
              placeholder="e.g., John Doe"
              value={patientInfo.patientName || ''}
              onChange={(e) => onChange({ ...patientInfo, patientName: e.target.value })}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="patientId">Patient ID (Optional)</Label>
            <Input
              id="patientId"
              type="text"
              placeholder="e.g., P001"
              value={patientInfo.patientId}
              onChange={(e) => onChange({ ...patientInfo, patientId: e.target.value })}
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="age">Age (Optional)</Label>
            <Input
              id="age"
              type="number"
              placeholder="e.g., 65"
              value={patientInfo.age}
              onChange={(e) => onChange({ ...patientInfo, age: e.target.value })}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="sex">Sex (Optional)</Label>
            <select
              id="sex"
              value={patientInfo.sex}
              onChange={(e) => onChange({ ...patientInfo, sex: e.target.value as 'M' | 'F' | '' })}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <option value="">Select...</option>
              <option value="M">Male</option>
              <option value="F">Female</option>
            </select>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
