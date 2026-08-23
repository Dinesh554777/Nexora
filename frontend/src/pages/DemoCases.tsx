import { useEffect, useState } from 'react';
import { PageHeader } from '@/components/shared/PageHeader';
import { ErrorRetry } from '@/components/shared/ErrorRetry';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  User,
  Scan,
  Activity,
  Ruler,
  Layers,
  Wrench,
  FlaskConical,
  ShieldAlert,
} from 'lucide-react';
import { apiService } from '@/services/api';
import { DemoCaseCard, DemoReport } from '@/types/api';

// ── Demo banner ───────────────────────────────────────────────────────────────

function DemoBanner() {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-amber-300 bg-amber-50 p-4 dark:border-amber-700 dark:bg-amber-950">
      <ShieldAlert className="h-5 w-5 flex-shrink-0 text-amber-600 dark:text-amber-400" />
      <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
        <span className="font-bold">DEMO — NOT FOR CLINICAL USE.</span>{' '}
        All cases shown here are synthetic demonstration data only. This system is a
        research/demo decision-support prototype and does not provide a medical diagnosis.
      </p>
    </div>
  );
}

// ── Case selector card ────────────────────────────────────────────────────────

interface CaseSelectorCardProps {
  card: DemoCaseCard;
  selected: boolean;
  onClick: () => void;
}

function CaseSelectorCard({ card, selected, onClick }: CaseSelectorCardProps) {
  const isOA = card.case_type === 'OA';
  return (
    <button
      onClick={onClick}
      className={[
        'w-full text-left rounded-xl border-2 p-5 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-primary',
        selected
          ? 'border-primary bg-primary/5 shadow-md'
          : 'border-border bg-card hover:border-primary/50 hover:shadow-sm',
      ].join(' ')}
      aria-pressed={selected}
    >
      {/* Header row */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {isOA ? (
            <AlertTriangle className="h-5 w-5 text-destructive flex-shrink-0" />
          ) : (
            <CheckCircle2 className="h-5 w-5 text-green-600 flex-shrink-0" />
          )}
          <span className="font-semibold text-base">{card.label}</span>
        </div>
        <Badge variant={isOA ? 'destructive' : 'success'}>
          {isOA ? 'OA' : 'Non-OA'}
        </Badge>
      </div>

      {/* Detail rows */}
      <div className="space-y-1 text-sm text-muted-foreground">
        <p>
          <span className="font-medium text-foreground">ID:</span> {card.patient_id}
        </p>
        <p>
          <span className="font-medium text-foreground">Age / Sex:</span>{' '}
          {card.age} · {card.sex}
        </p>
        <p>
          <span className="font-medium text-foreground">Knee:</span>{' '}
          {card.affected_knee}
        </p>
        <p>
          <span className="font-medium text-foreground">Severity:</span>{' '}
          {card.severity}
        </p>
        <p>
          <span className="font-medium text-foreground">Confidence:</span>{' '}
          {(card.confidence * 100).toFixed(0)}%
        </p>
      </div>

      <div className="mt-3">
        <Badge variant="outline" className="text-xs">DEMO DATA</Badge>
      </div>
    </button>
  );
}

// ── Collapsible section ───────────────────────────────────────────────────────

interface SectionProps {
  title: string;
  icon: React.ReactNode;
  defaultOpen?: boolean;
  children: React.ReactNode;
}

function ReportSection({ title, icon, defaultOpen = true, children }: SectionProps) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <Card>
      <CardHeader
        className="cursor-pointer select-none py-4"
        onClick={() => setOpen(o => !o)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {icon}
            <CardTitle className="text-base">{title}</CardTitle>
          </div>
          {open ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
        </div>
      </CardHeader>
      {open && <CardContent>{children}</CardContent>}
    </Card>
  );
}

// ── Full report view ──────────────────────────────────────────────────────────

interface ReportViewProps {
  report: DemoReport;
}

function ReportView({ report }: ReportViewProps) {
  const isOA = report.assessment.classification === 'OA';
  const confidencePct = (report.assessment.confidence * 100).toFixed(0);
  const maskPct = report.segmentation.mask_fraction != null
    ? (report.segmentation.mask_fraction * 100).toFixed(1)
    : null;

  return (
    <div className="space-y-4">
      {/* Report header */}
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="outline" className="font-mono text-xs">
          {report.report_id}
        </Badge>
        <Badge variant="destructive" className="text-xs font-bold">
          DEMO — NOT FOR CLINICAL USE
        </Badge>
        {isOA ? (
          <Badge variant="destructive">OA Suspected</Badge>
        ) : (
          <Badge variant="success">No OA Features</Badge>
        )}
      </div>

      {/* 1 — Patient information */}
      <ReportSection
        title="Patient Information"
        icon={<User className="h-4 w-4 text-muted-foreground" />}
      >
        <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm sm:grid-cols-3">
          {[
            ['Patient ID', report.patient.patient_id],
            ['Name', report.patient.name],
            ['Age', `${report.patient.age} years`],
            ['Sex', report.patient.sex],
            ['Affected Knee', report.patient.affected_knee],
            ['Scan Type', report.scan.scan_type],
            ['Scan Date', report.scan.scan_date],
          ].map(([label, value]) => (
            <div key={label}>
              <dt className="text-muted-foreground">{label}</dt>
              <dd className="font-medium">{value}</dd>
            </div>
          ))}
        </dl>
      </ReportSection>

      {/* 2 — AI OA assessment */}
      <ReportSection
        title="AI OA Assessment"
        icon={<Activity className="h-4 w-4 text-muted-foreground" />}
      >
        <div className="space-y-4">
          <div className="flex flex-wrap gap-3">
            <div className="flex-1 min-w-[120px] rounded-lg border bg-muted/40 p-4 text-center">
              <p className="text-xs text-muted-foreground mb-1">Classification</p>
              <p className={`text-xl font-bold ${isOA ? 'text-destructive' : 'text-green-600'}`}>
                {isOA ? 'OA' : 'Non-OA'}
              </p>
            </div>
            <div className="flex-1 min-w-[120px] rounded-lg border bg-muted/40 p-4 text-center">
              <p className="text-xs text-muted-foreground mb-1">Confidence</p>
              <p className="text-xl font-bold">{confidencePct}%</p>
            </div>
            <div className="flex-1 min-w-[120px] rounded-lg border bg-muted/40 p-4 text-center">
              <p className="text-xs text-muted-foreground mb-1">Severity</p>
              <p className="text-xl font-bold">{report.assessment.severity}</p>
            </div>
          </div>

          {/* Confidence bar */}
          <div>
            <div className="flex justify-between text-xs text-muted-foreground mb-1">
              <span>Confidence</span>
              <span>{confidencePct}%</span>
            </div>
            <div className="h-2 rounded-full bg-muted overflow-hidden">
              <div
                className={`h-full rounded-full ${isOA ? 'bg-destructive' : 'bg-green-500'}`}
                style={{ width: `${confidencePct}%` }}
              />
            </div>
          </div>

          <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-200">
            <strong>Source:</strong> {report.assessment.source} ·{' '}
            <strong>Model:</strong> {report.assessment.model_version ?? 'N/A'}<br />
            {report.assessment.clinical_warning}
          </div>
        </div>
      </ReportSection>

      {/* 3 — Segmentation */}
      <ReportSection
        title="Segmentation Result"
        icon={<Scan className="h-4 w-4 text-muted-foreground" />}
      >
        <div className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
          {[
            ['Mask Area', report.segmentation.mask_area_pixels != null ? `${report.segmentation.mask_area_pixels.toLocaleString()} px` : 'N/A'],
            ['Mask Fraction', maskPct != null ? `${maskPct}%` : 'N/A'],
            ['Probability Mean', report.segmentation.probability_mean != null ? report.segmentation.probability_mean.toFixed(3) : 'N/A'],
            ['Threshold', report.segmentation.threshold.toFixed(2)],
          ].map(([label, value]) => (
            <div key={label} className="rounded-lg border bg-muted/40 p-3 text-center">
              <p className="text-xs text-muted-foreground mb-1">{label}</p>
              <p className="font-semibold">{value}</p>
            </div>
          ))}
        </div>
        <p className="mt-3 text-xs text-muted-foreground">
          Source: {report.segmentation.source} · Model: {report.segmentation.model_name}
        </p>
      </ReportSection>

      {/* 4 — Measurements */}
      <ReportSection
        title="Quantitative Measurements"
        icon={<Ruler className="h-4 w-4 text-muted-foreground" />}
      >
        {Object.keys(report.measurements).length === 0 ? (
          <p className="text-sm text-muted-foreground">No measurements available.</p>
        ) : (
          <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
            {Object.entries(report.measurements).map(([key, value]) => {
              const label = key
                .replace(/_mm$/, '')
                .replace(/_/g, ' ')
                .replace(/\b\w/g, c => c.toUpperCase());
              return (
                <div key={key} className="rounded-lg border bg-muted/40 p-3 text-center">
                  <p className="text-xs text-muted-foreground mb-1">{label}</p>
                  <p className="font-semibold">{typeof value === 'number' ? value.toFixed(1) : value} mm</p>
                </div>
              );
            })}
          </div>
        )}
      </ReportSection>

      {/* 5 — Imaging findings */}
      <ReportSection
        title="Imaging Findings"
        icon={<Layers className="h-4 w-4 text-muted-foreground" />}
      >
        {report.findings.length === 0 ? (
          <p className="text-sm text-muted-foreground">No findings recorded.</p>
        ) : (
          <ul className="space-y-2">
            {report.findings.map((finding, i) => (
              <li key={i} className="flex items-start gap-2 text-sm">
                <span className="mt-1 h-2 w-2 flex-shrink-0 rounded-full bg-primary" />
                {finding}
              </li>
            ))}
          </ul>
        )}
      </ReportSection>

      {/* 6 — Implant assessment */}
      <ReportSection
        title="Implant Assessment"
        icon={<Wrench className="h-4 w-4 text-muted-foreground" />}
      >
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Badge variant={report.implant_assessment.required ? 'destructive' : 'success'}>
              {report.implant_assessment.required ? 'Implant Assessment Required' : 'Not Required'}
            </Badge>
            <span className="text-sm text-muted-foreground">{report.implant_assessment.status}</span>
          </div>

          {report.implant_assessment.recommendation && (
            <>
              <div>
                <p className="text-sm font-semibold mb-2">Best Match</p>
                <ImplantCard rec={report.implant_assessment.recommendation} highlight />
              </div>

              {report.implant_assessment.alternatives.length > 0 && (
                <div>
                  <p className="text-sm font-semibold mb-2">Alternatives</p>
                  <div className="space-y-2">
                    {report.implant_assessment.alternatives.map(alt => (
                      <ImplantCard key={alt.implantId} rec={alt} />
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          <p className="text-xs text-muted-foreground">{report.implant_assessment.note}</p>
        </div>
      </ReportSection>

      {/* 7 — Pipeline provenance */}
      <ReportSection
        title="Pipeline Stages"
        icon={<FlaskConical className="h-4 w-4 text-muted-foreground" />}
        defaultOpen={false}
      >
        <ol className="flex flex-wrap gap-2">
          {report.pipeline_stages.map((stage, i) => (
            <li key={stage} className="flex items-center gap-1 text-xs">
              <span className="rounded-full bg-primary/10 px-2 py-0.5 font-medium text-primary">
                {i + 1}. {stage.replace(/_/g, ' ')}
              </span>
              {i < report.pipeline_stages.length - 1 && (
                <span className="text-muted-foreground">→</span>
              )}
            </li>
          ))}
        </ol>
        <p className="mt-3 text-xs text-muted-foreground">
          Generated: {new Date(report.generated_at).toLocaleString()} ·
          Version: {report.report_version}
        </p>
      </ReportSection>
    </div>
  );
}

// ── Implant card helper ───────────────────────────────────────────────────────

interface ImplantCardProps {
  rec: {
    implantId: string;
    implantName: string;
    size: string;
    matchScore: number;
    confidence: number;
    measurementDifference: number;
    rank: number;
  };
  highlight?: boolean;
}

function ImplantCard({ rec, highlight }: ImplantCardProps) {
  return (
    <div className={`rounded-lg border p-3 text-sm ${highlight ? 'border-primary bg-primary/5' : 'bg-muted/30'}`}>
      <div className="flex items-center justify-between mb-1">
        <span className="font-medium">{rec.implantName}</span>
        <Badge variant={highlight ? 'default' : 'secondary'}>
          Rank {rec.rank}
        </Badge>
      </div>
      <div className="grid grid-cols-3 gap-2 text-xs text-muted-foreground mt-2">
        <span><strong className="text-foreground">Size:</strong> {rec.size}</span>
        <span><strong className="text-foreground">Match:</strong> {rec.matchScore.toFixed(1)}%</span>
        <span><strong className="text-foreground">Conf:</strong> {rec.confidence.toFixed(1)}%</span>
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export function DemoCases() {
  const [loadingList, setLoadingList] = useState(true);
  const [listError, setListError] = useState<string | null>(null);
  const [cases, setCases] = useState<DemoCaseCard[]>([]);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loadingReport, setLoadingReport] = useState(false);
  const [reportError, setReportError] = useState<string | null>(null);
  const [report, setReport] = useState<DemoReport | null>(null);

  // Load case list on mount
  const fetchCases = async () => {
    try {
      setLoadingList(true);
      setListError(null);
      const data = await apiService.getDemoCases();
      setCases(data.cases);
    } catch (err) {
      setListError(err instanceof Error ? err.message : 'Failed to load demo cases');
    } finally {
      setLoadingList(false);
    }
  };

  useEffect(() => { fetchCases(); }, []);

  // Load report when a case is selected
  const selectCase = async (caseId: string) => {
    if (caseId === selectedId) return;
    setSelectedId(caseId);
    setReport(null);
    setReportError(null);
    setLoadingReport(true);
    try {
      const data = await apiService.getDemoCase(caseId);
      setReport(data);
    } catch (err) {
      setReportError(err instanceof Error ? err.message : 'Failed to load demo report');
    } finally {
      setLoadingReport(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Demo Cases"
        description="Synthetic patient cases for jury demonstration — OA and Non-OA workflows"
      />

      <DemoBanner />

      {/* Case selector */}
      {loadingList ? (
        <div className="grid gap-4 md:grid-cols-2">
          {[1, 2].map(i => (
            <Card key={i}><CardContent className="p-6"><Skeleton className="h-40 w-full" /></CardContent></Card>
          ))}
        </div>
      ) : listError ? (
        <ErrorRetry
          title="Failed to load demo cases"
          message={listError}
          onRetry={fetchCases}
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {cases.map(c => (
            <CaseSelectorCard
              key={c.case_id}
              card={c}
              selected={selectedId === c.case_id}
              onClick={() => selectCase(c.case_id)}
            />
          ))}
        </div>
      )}

      {/* Report panel */}
      {selectedId && (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-semibold">Full Report</h2>
            <Badge variant="outline" className="font-mono">{selectedId}</Badge>
          </div>

          {loadingReport ? (
            <div className="space-y-3">
              {[1, 2, 3].map(i => (
                <Card key={i}><CardContent className="p-6"><Skeleton className="h-24 w-full" /></CardContent></Card>
              ))}
            </div>
          ) : reportError ? (
            <Card>
              <CardContent className="p-6">
                <p className="text-sm text-destructive">{reportError}</p>
              </CardContent>
            </Card>
          ) : report ? (
            <ReportView report={report} />
          ) : null}
        </div>
      )}

      {/* Prompt when nothing is selected */}
      {!selectedId && !loadingList && !listError && (
        <Card>
          <CardContent className="p-8 text-center text-muted-foreground">
            <FlaskConical className="mx-auto mb-3 h-10 w-10 opacity-40" />
            <p className="text-sm">Select a demo case above to view the full synthetic patient report.</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
