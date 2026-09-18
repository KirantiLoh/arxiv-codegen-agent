import { useState, useRef, type DragEvent, type ChangeEvent } from "react";
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogDescription, 
  DialogFooter 
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Upload, FileText, X } from "lucide-react";

interface UploadPdfModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function UploadPdfModal({ open, onOpenChange }: UploadPdfModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type === "application/pdf") {
      setFile(droppedFile);
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = () => {
    if (!file) return;
    
    // TODO: Implement actual upload to your FastAPI backend here
    console.log("Uploading PDF:", file.name, file.size);
    
    // Reset and close
    setFile(null);
    onOpenChange(false);
  };

  const handleCancel = () => {
    setFile(null);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md bg-background border-border">
        <DialogHeader>
          <DialogTitle className="text-lg font-semibold">Upload ArXiv PDF</DialogTitle>
          <DialogDescription className="text-sm text-muted-foreground">
            Select a paper to ingest into the RAG pipeline and generate code.
          </DialogDescription>
        </DialogHeader>
        
        <div className="py-4">
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`
              flex flex-col items-center justify-center w-full h-48 rounded-lg border-2 border-dashed cursor-pointer transition-all duration-200
              ${isDragging 
                ? "border-primary bg-primary/5 scale-[1.01]" 
                : "border-border bg-muted/20 hover:bg-muted/40 hover:border-muted-foreground/30"
              }
            `}
          >
            {file ? (
              <div className="flex items-center gap-3 px-4">
                <div className="p-2 rounded-md bg-primary/10 border border-primary/20">
                  <FileText className="h-5 w-5 text-primary" />
                </div>
                <div className="text-left flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground truncate max-w-50">
                    {file.name}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
                <Button 
                  variant="ghost" 
                  size="icon" 
                  className="h-7 w-7 text-muted-foreground hover:text-foreground" 
                  onClick={(e) => { 
                    e.stopPropagation(); 
                    setFile(null); 
                  }}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ) : (
              <>
                <div className={`p-3 rounded-full mb-3 transition-colors ${isDragging ? "bg-primary/10" : "bg-muted"}`}>
                  <Upload className={`h-5 w-5 ${isDragging ? "text-primary" : "text-muted-foreground"}`} />
                </div>
                <p className="text-sm text-muted-foreground">
                  <span className="font-semibold text-foreground">Click to upload</span> or drag and drop
                </p>
                <p className="text-xs text-muted-foreground/60 mt-1.5">PDF files only (Max 50MB)</p>
              </>
            )}
            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf"
              className="hidden"
              onChange={handleFileChange}
            />
          </div>
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button variant="outline" onClick={handleCancel}>
            Cancel
          </Button>
          <Button onClick={handleUpload} disabled={!file} className="gap-2">
            Upload & Process
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}