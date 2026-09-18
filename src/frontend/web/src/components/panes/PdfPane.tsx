import { FileText } from "lucide-react";
import { PdfViewer } from "./PdfViewer";

export function PdfPane() {
  return (
    <div className="flex flex-col h-full bg-background">
      {/* Pane Header */}
      <div className="h-10 flex items-center px-4 border-b border-border bg-muted/30 shrink-0">
        <FileText className="h-4 w-4 text-muted-foreground mr-2" />
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
          Paper PDF
        </span>
      </div>
      
      {/* PDF Viewer Content */}
      <div className="flex-1 overflow-hidden">
        <PdfViewer />
      </div>
    </div>
  );
}