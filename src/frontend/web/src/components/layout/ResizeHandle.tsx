import { Separator } from "react-resizable-panels";
import { cn } from "@/lib/utils";

interface ResizeHandleProps {
  className?: string;
  orientation?: "horizontal" | "vertical"
}

export function ResizeHandle({ className, orientation = "vertical" }: ResizeHandleProps) {
  const isVertical = orientation === "vertical";
  
  return (
    <Separator
      className={cn(
        "group relative flex shrink-0 bg-transparent transition-colors",
        // Layout changes based on orientation
        isVertical 
          ? "w-2 flex-col items-center justify-center" 
          : "h-2 flex-row items-center justify-center",
        // Hover and active states
        "hover:bg-accent/5 data-resize-handle-active:bg-accent/10",
        className
      )}
    >
      {/* The visual line */}
      <div 
        className={cn(
          "bg-border transition-colors duration-200",
          // Dimensions change based on orientation
          isVertical ? "h-full w-px" : "w-full h-px",
          "group-hover:bg-primary/40 group-data-resize-handle-active:bg-primary"
        )} 
      />
    </Separator>
  );
}