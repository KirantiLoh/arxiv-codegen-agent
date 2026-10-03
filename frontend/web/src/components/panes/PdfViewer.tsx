import { useState, useCallback, useRef, useEffect } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";
import { Loader2, ZoomOut, ZoomIn } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAppStore } from "@/store/useAppStore";

// Configure PDF.js worker for Vite
// @ts-ignore
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url
).toString();

// Fixed base scale for rendering. We use CSS transform for zooming.
const BASE_SCALE = 1.2;

export function PdfViewer() {
  const pdfUrl = useAppStore((state) => state.pdf.url);
  const highlight = useAppStore((state) => state.pdf.highlight);
  
  const [pdfScale, setPdfScale] = useState<number>(BASE_SCALE);
  const [numPages, setNumPages] = useState<number | null>(null);
  const [isDocumentLoading, setIsDocumentLoading] = useState(true);
  const containerRef = useRef<HTMLDivElement>(null);

  const onDocumentLoadSuccess = useCallback(({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
    setIsDocumentLoading(false);
  }, []);

  const onDocumentLoadError = useCallback((error: Error) => {
    console.error("Failed to load PDF:", error);
    setIsDocumentLoading(false);
  }, []);

  // Auto-scroll to the highlighted page when the agent references it
  useEffect(() => {
    if (highlight && containerRef.current) {
      const pageElement = document.getElementById(`pdf-page-${highlight.page}`);
      if (pageElement) {
        pageElement.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }
  }, [highlight]);

  // Calculate the CSS scale factor relative to the base render scale
  const cssScale = pdfScale / BASE_SCALE;

  const handleZoomIn = () => setPdfScale((s) => +(Math.min(2.5, s + 0.1)).toFixed(2));
  const handleZoomOut = () => setPdfScale((s) => +(Math.max(0.5, s - 0.1)).toFixed(2));

  if (!pdfUrl) {
    return (
      <div className="flex flex-col h-full items-center justify-center p-6 text-center bg-background">
        <div className="mx-auto w-16 h-16 rounded-full bg-secondary/50 flex items-center justify-center border border-border mb-4">
          <span className="text-2xl">📄</span>
        </div>
        <h3 className="text-sm font-medium text-foreground mb-1">No PDF Loaded</h3>
        <p className="text-xs text-muted-foreground leading-relaxed max-w-xs">
          The agent will load the ArXiv paper here and highlight relevant sections.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-muted/10">
      {/* PDF Controls Header */}
      <div className="h-10 flex items-center justify-between px-4 border-b border-border bg-muted/30 shrink-0">
        <span className="text-xs font-mono text-foreground">
          {numPages ? `${numPages} Pages` : "Loading..."}
        </span>

        {isDocumentLoading ? (
          <div className="flex items-center gap-2">
            <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Loading PDF</span>
          </div>
        ) : ( 
          <div className="flex items-center gap-2">
            <Button 
              variant="ghost" 
              size="icon" 
              className="h-7 w-7 text-foreground hover:bg-accent" 
              onClick={handleZoomOut}
              disabled={pdfScale <= 0.5}
            >
              <ZoomOut className="h-3.5 w-3.5" />
            </Button>
            <span className="text-xs font-mono text-muted-foreground w-12 text-center">
              {Math.round(pdfScale * 100)}%
            </span>
            <Button 
              variant="ghost" 
              size="icon" 
              className="h-7 w-7 text-foreground hover:bg-accent" 
              onClick={handleZoomIn}
              disabled={pdfScale >= 2.5}
            >
              <ZoomIn className="h-3.5 w-3.5" />
            </Button>
          </div>
        )}
      </div>

      {/* Continuous Scroll PDF Render Area */}
      <div 
        ref={containerRef}
        className="flex-1 overflow-auto flex justify-center p-6 scrollbar-hide"
      >
        {/* 
          CSS Zoom Wrapper:
          - transform: scales the rendered pages visually without re-rendering the canvas.
          - width: 100% / cssScale: prevents the scaled pages from overlapping by adjusting the layout flow.
          - transition: adds a smooth, premium zoom animation.
        */}
        <div
          style={{
            transform: `scale(${cssScale})`,
            transformOrigin: 'top center',
            width: `${100 / cssScale}%`,
            transition: 'transform 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
          }}
          className="flex flex-col items-center space-y-4"
        >
          <Document
            file={pdfUrl}
            onLoadSuccess={onDocumentLoadSuccess}
            onLoadError={onDocumentLoadError}
            loading={
              <div className="flex items-center justify-center h-full">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            }
            className="max-w-full"
          >
            {numPages && (
              <>
                {Array.from(new Array(numPages), (el, index) => {
                  const pageNum = index + 1;
                  return (
                    <div 
                      key={`page_${pageNum}`} 
                      id={`pdf-page-${pageNum}`}
                      className="relative shadow-2xl shadow-black/50 border border-border/50 bg-white"
                    >
                      {/* Render at fixed BASE_SCALE. CSS handles the zoom. */}
                      <Page
                        pageNumber={pageNum}
                        scale={BASE_SCALE}
                        renderTextLayer={true}
                        renderAnnotationLayer={true}
                        renderMode="canvas"
                        loading={
                          <div className="flex items-center justify-center h-96 w-[600px] bg-muted/20">
                            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                          </div>
                        }
                      />
                      
                      {/* Highlight Overlay */}
                      {/* Coordinates are based on BASE_SCALE, CSS transform scales them automatically */}
                      {highlight && highlight.page === pageNum && (
                        <div
                          className="absolute bg-primary/20 border border-primary/60 pointer-events-none transition-all duration-500 ease-in-out z-10"
                          style={{
                            left: `${highlight.boundingBox[0] * BASE_SCALE}px`,
                            top: `${highlight.boundingBox[1] * BASE_SCALE}px`,
                            width: `${highlight.boundingBox[2] * BASE_SCALE}px`,
                            height: `${highlight.boundingBox[3] * BASE_SCALE}px`,
                          }}
                        >
                          <div className="absolute inset-0 bg-primary/10 animate-pulse-subtle" />
                        </div>
                      )}
                    </div>
                  );
                })}
              </>
            )}
          </Document>
        </div>
      </div>
    </div>
  );
}
