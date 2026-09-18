import { useAppStore } from "@/store/useAppStore";
import { ScrollArea } from "@/components/ui/scroll-area";
import { FileCode, FileJson, FileText, FileType } from "lucide-react";
import { cn } from "@/lib/utils";

const getFileIcon = (fileName: string) => {
  const ext = fileName.split(".").pop()?.toLowerCase();
  switch (ext) {
    case "py":
      return <FileCode className="h-4 w-4 text-blue-400" />;
    case "js":
    case "jsx":
    case "ts":
    case "tsx":
      return <FileCode className="h-4 w-4 text-yellow-400" />;
    case "json":
      return <FileJson className="h-4 w-4 text-green-400" />;
    default:
      return <FileText className="h-4 w-4 text-muted-foreground" />;
  }
};

export function FileTree() {
  const files = useAppStore((state) => state.files);
  const activeFile = useAppStore((state) => state.activeFile);
  const setActiveFile = useAppStore((state) => state.setActiveFile);

  const fileEntries = Object.values(files);

  if (fileEntries.length === 0) {
    return (
      <div className="flex flex-col h-full items-center justify-center p-4 text-center">
        <FileType className="h-8 w-8 text-muted-foreground/50 mb-2" />
        <p className="text-xs text-muted-foreground">
          No files generated yet.
        </p>
        <p className="text-[10px] text-muted-foreground/60 mt-1">
          Agent will create files here.
        </p>
      </div>
    );
  }

  return (
    <ScrollArea className="h-full">
      <div className="flex flex-col p-2 space-y-0.5">
        {fileEntries.map((file) => {
          const isActive = activeFile === file.fileName;
          return (
            <button
              key={file.fileName}
              onClick={() => setActiveFile(file.fileName)}
              className={cn(
                "group flex items-center w-full px-2 py-1.5 rounded-md text-xs transition-all duration-150",
                "hover:bg-accent/50 hover:text-foreground",
                isActive 
                  ? "bg-accent text-foreground font-medium" 
                  : "text-muted-foreground"
              )}
            >
              <span className="mr-2 shrink-0">
                {getFileIcon(file.fileName)}
              </span>
              <span className="truncate font-mono">
                {file.fileName}
              </span>
            </button>
          );
        })}
      </div>
    </ScrollArea>
  );
}