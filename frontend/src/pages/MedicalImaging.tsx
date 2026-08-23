import { useState } from 'react';
import { PageHeader } from '@/components/shared/PageHeader';
import { ImageUploader } from '@/components/imaging/ImageUploader';
import { AnalysisResults } from '@/components/imaging/AnalysisResults';
import { ImageViewer } from '@/components/imaging/ImageViewer';
import { ClinicalDisclaimer } from '@/components/shared/ClinicalDisclaimer';
import { PatientInfoForm, PatientInfo } from '@/components/implant/PatientInfoForm';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Brain, Image as ImageIcon } from 'lucide-react';
import { UploadedImage, ImageAnalysisResult, AnalysisState } from '@/types';
import { apiService } from '@/services/api';

export function MedicalImaging() {
  const [xrayImages, setXrayImages] = useState<UploadedImage[]>([]);
  const [mriImages, setMriImages] = useState<UploadedImage[]>([]);
  const [analysisState, setAnalysisState] = useState<AnalysisState>('ready');
  const [analysisResults, setAnalysisResults] = useState<ImageAnalysisResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [viewerOpen, setViewerOpen] = useState(false);
  const [selectedImage, setSelectedImage] = useState<UploadedImage | null>(null);
  const [patientInfo, setPatientInfo] = useState<PatientInfo>({
    patientId: '',
    age: '',
    sex: '',
  });

  const handleXrayUpload = (image: UploadedImage) => {
    setXrayImages(prev => [...prev, image]);
    setError(null);
  };

  const handleMriUpload = (image: UploadedImage) => {
    setMriImages(prev => [...prev, image]);
    setError(null);
  };

  const handleRemoveXray = (imageId: string) => {
    setXrayImages(prev => prev.filter(img => img.id !== imageId));
  };

  const handleRemoveMri = (imageId: string) => {
    setMriImages(prev => prev.filter(img => img.id !== imageId));
  };

  const handleViewImage = (image: UploadedImage) => {
    setSelectedImage(image);
    setViewerOpen(true);
  };

  const handleAnalyze = async () => {
    const allImages = [...xrayImages, ...mriImages];
    if (allImages.length === 0) {
      setError('Please upload at least one image before analyzing.');
      return;
    }

    setAnalysisState('processing');
    setError(null);

    try {
      const realResults: ImageAnalysisResult[] = await Promise.all(
        allImages.map(async (image) => {
          const formData = new FormData();
          formData.append('file', image.file);

          const response = await apiService.segmentImage(formData);
          const metrics = response.metrics ?? {};
          const probabilityMean = typeof metrics.probability_mean === 'number'
            ? Number(metrics.probability_mean)
            : undefined;
          const maskAreaPixels = typeof metrics.mask_area_pixels === 'number'
            ? Number(metrics.mask_area_pixels)
            : undefined;
          const maskFraction = typeof metrics.mask_fraction === 'number'
            ? Number(metrics.mask_fraction)
            : undefined;
          const threshold = typeof metrics.threshold === 'number'
            ? Number(metrics.threshold)
            : undefined;

          const normalizeBase64 = (value?: string) => {
            if (!value) {
              return undefined;
            }
            return value.startsWith('data:image') ? value : `data:image/png;base64,${value}`;
          };

          const findings = [
            'The uploaded knee image was processed successfully by the Nexora AI segmentation pipeline.',
          ];

          if (typeof probabilityMean === 'number') {
            findings.push(`Probability Mean: ${probabilityMean.toFixed(4)}`);
          }
          if (typeof maskAreaPixels === 'number') {
            findings.push(`Segmented region area: ${maskAreaPixels.toLocaleString()} pixels`);
          }
          if (typeof maskFraction === 'number') {
            findings.push(`Mask fraction: ${(maskFraction * 100).toFixed(2)}%`);
          }

          return {
            imageId: image.id,
            filename: response.filename,
            findings,
            confidence: typeof probabilityMean === 'number'
              ? Math.max(0, Math.min(100, Math.round(probabilityMean * 100)))
              : 95,
            abnormalRegions: [],
            originalImageBase64: image.preview,
            maskImageBase64: normalizeBase64(response.mask_image_base64),
            overlayImageBase64: normalizeBase64(response.overlay_image_base64),
            technicalMetrics: {
              probabilityMean,
              maskAreaPixels,
              maskFraction,
              threshold,
            },
            timestamp: new Date(),
          };
        })
      );

      setAnalysisResults(realResults);
      setAnalysisState('complete');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Analysis failed unexpectedly.';
      setError(message);
      setAnalysisState('failed');
      setAnalysisResults([]);
    }
  };

  const handleClear = () => {
    setXrayImages([]);
    setMriImages([]);
    setAnalysisResults([]);
    setAnalysisState('ready');
    setError(null);
  };

  const totalImages = xrayImages.length + mriImages.length;

  return (
    <div className="space-y-8">
      <PageHeader
        title="Medical Imaging"
        description="AI-assisted knee image analysis for X-rays and MRI scans"
      />

      {/* Analysis Status */}
      {analysisState === 'processing' && (
        <Card className="border-primary/20 bg-primary/5">
          <CardContent className="p-6">
            <div className="flex flex-col items-center justify-center space-y-4">
              <Loader2 className="h-12 w-12 animate-spin text-primary" />
              <div className="text-center">
                <p className="text-lg font-semibold">Analyzing Medical Images...</p>
                <p className="text-sm text-muted-foreground mt-1">
                  AI is processing your images. This may take a moment.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {analysisState === 'complete' && (
        <Alert className="border-green-200 bg-green-50 dark:bg-green-950">
          <Brain className="h-5 w-5 text-green-600" />
          <AlertDescription className="text-green-800 dark:text-green-200">
            Analysis complete! {analysisResults.length} image{analysisResults.length !== 1 ? 's' : ''} analyzed successfully.
          </AlertDescription>
        </Alert>
      )}

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Upload Sections */}
      <PatientInfoForm
        patientInfo={patientInfo}
        onChange={setPatientInfo}
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <ImageUploader
          type="xray"
          onUpload={handleXrayUpload}
          onRemove={handleRemoveXray}
          uploadedImages={xrayImages}
          maxImages={3}
        />

        <ImageUploader
          type="mri"
          onUpload={handleMriUpload}
          onRemove={handleRemoveMri}
          uploadedImages={mriImages}
          maxImages={3}
        />
      </div>

      {/* Image Gallery */}
      {totalImages > 0 && (
        <Card>
          <CardContent className="p-6">
            <h3 className="text-lg font-semibold mb-4">Uploaded Images ({totalImages})</h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
              {[...xrayImages, ...mriImages].map(image => (
                <div
                  key={image.id}
                  className="relative group cursor-pointer"
                  onClick={() => handleViewImage(image)}
                >
                  <div className="aspect-square rounded-lg overflow-hidden border-2 border-muted hover:border-primary transition-colors">
                    <img
                      src={image.preview}
                      alt={`${image.type} preview`}
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center rounded-lg">
                    <ImageIcon className="h-8 w-8 text-white" />
                  </div>
                  <p className="text-xs text-center mt-1 text-muted-foreground truncate">
                    {image.type === 'xray' ? 'X-Ray' : 'MRI'}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Action Buttons */}
      <div className="flex gap-3">
        <Button
          onClick={handleAnalyze}
          disabled={totalImages === 0 || analysisState === 'processing'}
          className="flex-1 gap-2"
        >
          {analysisState === 'processing' ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <Brain className="h-4 w-4" />
              Analyze Images
            </>
          )}
        </Button>
        <Button
          variant="outline"
          onClick={handleClear}
          disabled={analysisState === 'processing'}
        >
          Clear All
        </Button>
      </div>

      {/* Analysis Results */}
      {analysisState === 'complete' && analysisResults.length > 0 && (
        <AnalysisResults
          results={analysisResults}
          uploadedImages={[...xrayImages, ...mriImages]}
          patientInfo={patientInfo}
        />
      )}

      <ClinicalDisclaimer />

      {/* Image Viewer */}
      {selectedImage && (
        <ImageViewer
          isOpen={viewerOpen}
          onClose={() => setViewerOpen(false)}
          imageUrl={selectedImage.preview}
          imageTitle={`${selectedImage.type === 'xray' ? 'X-Ray' : 'MRI'} Image`}
          metadata={{
            fileName: selectedImage.file.name,
            fileSize: `${(selectedImage.file.size / 1024 / 1024).toFixed(2)} MB`,
            fileType: selectedImage.file.type.split('/')[1].toUpperCase(),
            uploadedAt: new Date(selectedImage.uploadedAt).toLocaleString(),
          }}
        />
      )}
    </div>
  );
}
