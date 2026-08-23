import { useCallback, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Upload, X, Image as ImageIcon } from 'lucide-react';
import { UploadedImage } from '@/types';

interface ImageUploaderProps {
  type: 'xray' | 'mri';
  onUpload: (image: UploadedImage) => void;
  onRemove: (imageId: string) => void;
  uploadedImages: UploadedImage[];
  maxImages?: number;
}

const ACCEPTED_FORMATS = ['image/png', 'image/jpeg', 'image/jpg'];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export function ImageUploader({ type, onUpload, onRemove, uploadedImages, maxImages = 3 }: ImageUploaderProps) {
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validateFile = (file: File): string | null => {
    if (!ACCEPTED_FORMATS.includes(file.type)) {
      return 'Unsupported file format. Please upload PNG or JPEG images.';
    }
    if (file.size > MAX_FILE_SIZE) {
      return 'File size exceeds 10MB limit.';
    }
    return null;
  };

  const handleFile = useCallback((file: File) => {
    setError(null);
    
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const uploadedImage: UploadedImage = {
        id: `${type}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        file,
        preview: e.target?.result as string,
        type,
        uploadedAt: new Date(),
      };
      onUpload(uploadedImage);
    };
    reader.readAsDataURL(file);
  }, [type, onUpload]);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (uploadedImages.length >= maxImages) {
      setError(`Maximum ${maxImages} images allowed.`);
      return;
    }

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    
    if (uploadedImages.length >= maxImages) {
      setError(`Maximum ${maxImages} images allowed.`);
      return;
    }

    if (e.target.files && e.target.files.length > 0) {
      handleFile(e.target.files[0]);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const title = type === 'xray' ? 'X-Ray Upload' : 'MRI Upload';
  const description = type === 'xray' 
    ? 'Upload knee X-ray images for AI-assisted analysis'
    : 'Upload knee MRI scans for AI-assisted analysis';

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {uploadedImages.length < maxImages && (
          <div
            className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragActive 
                ? 'border-primary bg-primary/5' 
                : 'border-muted-foreground/25 hover:border-primary/50'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              type="file"
              id={`file-upload-${type}`}
              className="hidden"
              accept={ACCEPTED_FORMATS.join(',')}
              onChange={handleChange}
            />
            <div className="flex flex-col items-center gap-2">
              <Upload className="h-10 w-10 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">
                  Drag and drop your {type === 'xray' ? 'X-ray' : 'MRI'} image here
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  or click to browse files
                </p>
              </div>
              <Button 
                type="button"
                variant="outline" 
                size="sm"
                onClick={() => document.getElementById(`file-upload-${type}`)?.click()}
                className="mt-2"
              >
                Browse Files
              </Button>
              <p className="text-xs text-muted-foreground mt-2">
                PNG, JPG, JPEG • Max 10MB • Up to {maxImages} images
              </p>
            </div>
          </div>
        )}

        {uploadedImages.length > 0 && (
          <div className="space-y-3">
            <p className="text-sm font-medium">Uploaded Images ({uploadedImages.length}/{maxImages})</p>
            {uploadedImages.map((image) => (
              <div key={image.id} className="flex items-center gap-3 p-3 border rounded-lg bg-muted/30">
                <div className="flex-shrink-0">
                  <img 
                    src={image.preview} 
                    alt={`${type} preview`}
                    className="h-16 w-16 object-cover rounded border"
                  />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{image.file.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {formatFileSize(image.file.size)} • {image.file.type.split('/')[1].toUpperCase()}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(image.uploadedAt).toLocaleString()}
                  </p>
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={() => onRemove(image.id)}
                  className="flex-shrink-0"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        )}

        {uploadedImages.length === 0 && (
          <div className="text-center py-4 text-muted-foreground">
            <ImageIcon className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No images uploaded yet</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
