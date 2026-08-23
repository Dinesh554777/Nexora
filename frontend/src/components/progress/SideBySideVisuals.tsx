import { ImageAnalysisResult, UploadedImage } from '@/types';
import { Sparkles, Layers, Image as ImageIcon } from 'lucide-react';

interface SideBySideVisualsProps {
  previousResult: ImageAnalysisResult;
  currentResult: ImageAnalysisResult;
  previousImage?: UploadedImage;
  currentImage?: UploadedImage;
  previousDate?: string;
  currentDate?: string;
}

export function SideBySideVisuals({
  previousResult,
  currentResult,
  previousImage,
  currentImage,
  previousDate,
  currentDate,
}: SideBySideVisualsProps) {
  const prevOriginal = previousResult.originalImageBase64 || previousImage?.preview;
  const currOriginal = currentResult.originalImageBase64 || currentImage?.preview;

  const prevMask = previousResult.maskImageBase64;
  const currMask = currentResult.maskImageBase64;

  const prevOverlay = previousResult.overlayImageBase64;
  const currOverlay = currentResult.overlayImageBase64;

  return (
    <div className="space-y-6">
      {/* 1. Original Images Side by Side */}
      <div className="rounded-xl border bg-card p-4 shadow-sm space-y-3">
        <h4 className="text-xs uppercase font-bold text-primary tracking-wider flex items-center gap-1.5">
          <ImageIcon className="h-4 w-4" />
          1. Original Knee X-Rays Side by Side
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Previous Original */}
          <div className="border rounded-lg overflow-hidden bg-muted/10 text-center">
            <div className="bg-slate-900 text-white text-xs font-semibold py-1.5 px-3 flex justify-between items-center">
              <span>PREVIOUS SCAN</span>
              <span className="text-[11px] text-slate-300">{previousDate || 'Baseline'}</span>
            </div>
            <div className="h-56 bg-black flex items-center justify-center p-2">
              {prevOriginal ? (
                <img
                  src={prevOriginal}
                  alt="Previous Original Knee X-Ray"
                  className="max-h-52 max-w-full object-contain"
                />
              ) : (
                <span className="text-xs text-muted-foreground">Image not available</span>
              )}
            </div>
            <div className="p-2 border-t text-xs text-muted-foreground truncate">
              {previousResult.filename || previousImage?.file.name || 'previous_xray.png'}
            </div>
          </div>

          {/* Current Original */}
          <div className="border rounded-lg overflow-hidden bg-muted/10 text-center">
            <div className="bg-primary text-primary-foreground text-xs font-semibold py-1.5 px-3 flex justify-between items-center">
              <span>CURRENT SCAN</span>
              <span className="text-[11px] text-primary-foreground/80">{currentDate || 'Follow-up'}</span>
            </div>
            <div className="h-56 bg-black flex items-center justify-center p-2">
              {currOriginal ? (
                <img
                  src={currOriginal}
                  alt="Current Original Knee X-Ray"
                  className="max-h-52 max-w-full object-contain"
                />
              ) : (
                <span className="text-xs text-muted-foreground">Image not available</span>
              )}
            </div>
            <div className="p-2 border-t text-xs text-muted-foreground truncate">
              {currentResult.filename || currentImage?.file.name || 'current_xray.png'}
            </div>
          </div>
        </div>
      </div>

      {/* 2. AI Segmentation Masks Side by Side */}
      <div className="rounded-xl border bg-card p-4 shadow-sm space-y-3">
        <h4 className="text-xs uppercase font-bold text-primary tracking-wider flex items-center gap-1.5">
          <Layers className="h-4 w-4" />
          2. AI Segmentation Masks Side by Side
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Previous Mask */}
          <div className="border rounded-lg overflow-hidden bg-muted/10 text-center">
            <div className="bg-slate-800 text-white text-xs font-semibold py-1.5 px-3 flex justify-between items-center">
              <span>PREVIOUS AI MASK</span>
              <span className="text-[11px] text-slate-300">U-Net Output</span>
            </div>
            <div className="h-56 bg-black flex items-center justify-center p-2">
              {prevMask ? (
                <img
                  src={prevMask}
                  alt="Previous AI Segmentation Mask"
                  className="max-h-52 max-w-full object-contain"
                />
              ) : (
                <span className="text-xs text-muted-foreground">Mask not available</span>
              )}
            </div>
            <div className="p-2 border-t text-xs text-muted-foreground">
              Segmented Area: {previousResult.technicalMetrics?.maskAreaPixels?.toLocaleString() ?? 'N/A'} px
            </div>
          </div>

          {/* Current Mask */}
          <div className="border rounded-lg overflow-hidden bg-muted/10 text-center">
            <div className="bg-primary/90 text-primary-foreground text-xs font-semibold py-1.5 px-3 flex justify-between items-center">
              <span>CURRENT AI MASK</span>
              <span className="text-[11px] text-primary-foreground/80">U-Net Output</span>
            </div>
            <div className="h-56 bg-black flex items-center justify-center p-2">
              {currMask ? (
                <img
                  src={currMask}
                  alt="Current AI Segmentation Mask"
                  className="max-h-52 max-w-full object-contain"
                />
              ) : (
                <span className="text-xs text-muted-foreground">Mask not available</span>
              )}
            </div>
            <div className="p-2 border-t text-xs text-muted-foreground">
              Segmented Area: {currentResult.technicalMetrics?.maskAreaPixels?.toLocaleString() ?? 'N/A'} px
            </div>
          </div>
        </div>
      </div>

      {/* 3. AI Overlay Visualizations Side by Side */}
      <div className="rounded-xl border bg-card p-4 shadow-sm space-y-3">
        <h4 className="text-xs uppercase font-bold text-primary tracking-wider flex items-center gap-1.5">
          <Sparkles className="h-4 w-4" />
          3. AI Overlay Visualizations Side by Side
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Previous Overlay */}
          <div className="border rounded-lg overflow-hidden bg-muted/10 text-center">
            <div className="bg-slate-800 text-white text-xs font-semibold py-1.5 px-3 flex justify-between items-center">
              <span>PREVIOUS AI OVERLAY</span>
              <span className="text-[11px] text-slate-300">Composite Map</span>
            </div>
            <div className="h-56 bg-black flex items-center justify-center p-2">
              {prevOverlay ? (
                <img
                  src={prevOverlay}
                  alt="Previous AI Overlay Visualization"
                  className="max-h-52 max-w-full object-contain"
                />
              ) : (
                <span className="text-xs text-muted-foreground">Overlay not available</span>
              )}
            </div>
            <div className="p-2 border-t text-xs text-muted-foreground">
              Coverage: {typeof previousResult.technicalMetrics?.maskFraction === 'number' ? `${(previousResult.technicalMetrics.maskFraction * 100).toFixed(2)}%` : 'N/A'}
            </div>
          </div>

          {/* Current Overlay */}
          <div className="border rounded-lg overflow-hidden bg-muted/10 text-center">
            <div className="bg-primary/90 text-primary-foreground text-xs font-semibold py-1.5 px-3 flex justify-between items-center">
              <span>CURRENT AI OVERLAY</span>
              <span className="text-[11px] text-primary-foreground/80">Composite Map</span>
            </div>
            <div className="h-56 bg-black flex items-center justify-center p-2">
              {currOverlay ? (
                <img
                  src={currOverlay}
                  alt="Current AI Overlay Visualization"
                  className="max-h-52 max-w-full object-contain"
                />
              ) : (
                <span className="text-xs text-muted-foreground">Overlay not available</span>
              )}
            </div>
            <div className="p-2 border-t text-xs text-muted-foreground">
              Coverage: {typeof currentResult.technicalMetrics?.maskFraction === 'number' ? `${(currentResult.technicalMetrics.maskFraction * 100).toFixed(2)}%` : 'N/A'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

