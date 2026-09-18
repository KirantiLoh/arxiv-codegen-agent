import { useState, useCallback } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight, Loader2 } from "lucide-react";
import { useAppStore } from "@/store/useAppStore";

// Configure PDF.js worker for Vite
// @ts-ignore
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url
).toString();

// Adjust this scale for PDF readability (1.5 is usually a good balance)
const PDF_SCALE = 1.5;

export function PdfViewer() {
  const pdfUrl = useAppStore((state) => state.pdf.url);
  const currentPage = useAppStore((state) => state.pdf.currentPage);
  const highlight = useAppStore((state) => state.pdf.highlight);
  const setPdfPage = useAppStore((state) => state.setPdfPage);

  const [numPages, setNumPages] = useState<number | null>(null);
  const [isDocumentLoading, setIsDocumentLoading] = useState(false);

  const onDocumentLoadSuccess = useCallback(({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
    setIsDocumentLoading(false);
  }, []);

  const onDocumentLoadStart = useCallback(() => {
    setIsDocumentLoading(true);
  }, []);

  const goToPrevPage = () => {
    if (currentPage > 1) setPdfPage(currentPage - 1);
  };

  const goToNextPage = () => {
    if (currentPage < (numPages || 1)) setPdfPage(currentPage + 1);
  };

  // If no PDF is loaded yet, show a placeholder
  if (!pdfUrl) {
    return (
      <div className="flex flex-col h-full items-center justify-center p-6 text-center bg-background">
        <div className="mx-auto w-16 h-16 rounded-full bg-secondary/50 flex items-center justify-center border border-border mb-4">
          <span className="text-2xl">📄</span>
        </div>
        <h3 className="text-sm font-medium text-foreground mb-1">No PDF Loaded</h3>
        <p className="text-xs text-muted-foreground leading-relaxed max-w-xs">
          Upload an ArXiv PDF to begin. The agent will analyze the paper and highlight relevant sections here.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-muted/10">
      {/* PDF Controls Header */}
      <div className="h-10 flex items-center justify-between px-4 border-b border-border bg-muted/30 shrink-0">
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={goToPrevPage}
            disabled={currentPage <= 1}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          
          <span className="text-xs font-mono text-foreground min-w-20 text-center">
            {currentPage} / {numPages ?? "—"}
          </span>
          
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={goToNextPage}
            disabled={currentPage >= (numPages || 1)}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>

        {isDocumentLoading && (
          <div className="flex items-center gap-2">
            <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Rendering</span>
          </div>
        )}
      </div>

      {/* PDF Render Area */}
      <div className="flex-1 overflow-auto flex justify-center p-6 scrollbar-hide">
        <Document
          file={pdfUrl}
          onLoadSuccess={onDocumentLoadSuccess}
          onLoadStart={onDocumentLoadStart}
          loading={
            <div className="flex items-center justify-center h-full">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          }
          className="max-w-full shadow-2xl shadow-black/50 border border-border/50"
        >
          <div className="relative inline-block">
            <Page
              pageNumber={currentPage}
              scale={PDF_SCALE}
              renderTextLayer={true}
              renderAnnotationLayer={true}
              className="bg-white" // PDFs are typically white; keeps text readable
            />
            
            {/* Highlight Overlay */}
            {highlight && highlight.page === currentPage && (
              <div
                className="absolute bg-primary/20 border border-primary/60 pointer-events-none transition-all duration-500 ease-in-out z-10"
                style={{
                  // Assuming top-left origin coordinates from backend.
                  // If your backend uses standard PDF bottom-left origin, change 'top' to:
                  // top: `${(pageHeight - highlight.boundingBox[1] - highlight.boundingBox[3]) * PDF_SCALE}px`
                  left: `${highlight.boundingBox[0] * PDF_SCALE}px`,
                  top: `${highlight.boundingBox[1] * PDF_SCALE}px`,
                  width: `${highlight.boundingBox[2] * PDF_SCALE}px`,
                  height: `${highlight.boundingBox[3] * PDF_SCALE}px`,
                }}
              >
                {/* Subtle pulse effect to draw attention to the highlight */}
                <div className="absolute inset-0 bg-primary/10 animate-pulse-subtle" />
              </div>
            )}
          </div>
        </Document>
      </div>
    </div>
  );
}