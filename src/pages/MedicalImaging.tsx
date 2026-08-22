import { useState } from 'react';
import { PageHeader } from '@/components/shared/PageHeader';
import { ImageUploader } from '@/components/imaging/ImageUploader';
import { AnalysisResults } from '@/components/imaging/AnalysisResults';
import { ImageViewer } from '@/components/imaging/ImageViewer';
import { ClinicalDisclaimer } from '@/components/shared/ClinicalDisclaimer';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Brain, Image as ImageIcon } from 'lucide-react';
import { UploadedImage, ImageAnalysisResult, AnalysisState } from '@/types';

export function MedicalImaging() {
  const [xrayImages, setXrayImages] = useState<UploadedImage[]>([]);
  const [mriImages, setMriImages] = useState<UploadedImage[]>([]);
  const [analysisState, setAnalysisState] = useState<AnalysisState>('ready');
  const [analysisResults, setAnalysisResults] = useState<ImageAnalysisResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [viewerOpen, setViewerOpen] = useState(false);
  const [selectedImage, setSelectedImage] = useState<UploadedImage | null>(null);

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

    // Simulate AI analysis (replace with actual API call)
    setTimeout(() => {
      // Demo analysis results
      const demoResults: ImageAnalysisResult[] = allImages.map(image => ({
        imageId: image.id,
        findings: [
          'Joint space evaluation completed',
          'Bone structure assessment performed',
          'Soft tissue analysis conducted',
        ],
        confidence: Math.floor(Math.random() * 20) + 75, // 75-95%
        abnormalRegions: image.type === 'xray' 
          ? [
              {
                region: 'Medial compartment',
                description: 'Possible joint space narrowing detected',
                severity: 'medium' as const,
              },
            ]
          : [
              {
                region: 'Meniscus',
                description: 'Potential tear or degeneration observed',
                severity: 'medium' as const,
              },
            ],
        measurements: {
          meniscusThickness: +(3 + Math.random() * 3).toFixed(1),
          jointSpaceWidth: +(4 + Math.random() * 2).toFixed(1),
        },
        oaIndicators: {
          present: Math.random() > 0.5,
          severity: ['mild', 'moderate', 'severe'][Math.floor(Math.random() * 3)] as 'mild' | 'moderate' | 'severe',
          observations: [
            'Joint space narrowing detected',
            'Osteophyte formation observed',
            'Cartilage degradation indicated',
          ],
        },
        timestamp: new Date(),
      }));

      setAnalysisResults(demoResults);
      setAnalysisState('complete');
    }, 3000);
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
        <AnalysisResults results={analysisResults} />
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
