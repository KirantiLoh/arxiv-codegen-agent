import { Code2, FolderTree } from "lucide-react";
import { FileTree } from "./FileTree";
import { CodeEditor } from "./CodeEditor";
import { ResizeHandle } from "../layout/ResizeHandle";
import { Panel, Group } from "react-resizable-panels";

export function IdePane() {
  return (
    <div className="flex flex-col h-full bg-background">
      {/* Pane Header */}
      <div className="h-10 flex items-center px-4 border-b border-border bg-muted/30 shrink-0">
        <Code2 className="h-4 w-4 text-muted-foreground mr-2" />
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
          Code Workspace
        </span>
      </div>
      
      {/* Inner Split: File Tree (Left) + Editor (Right) */}
      <div className="flex-1 flex overflow-hidden">
        <Group orientation="horizontal">
          {/* File Tree Sidebar */}
          <Panel collapsible defaultSize={"20"} minSize={"20"} maxSize={"35"}>
            <div className="flex flex-col h-full border-r border-border bg-muted/10">
              <div className="h-8 flex items-center px-3 border-b border-border/50 shrink-0">
                <FolderTree className="h-3.5 w-3.5 text-muted-foreground mr-2" />
                <span className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
                  Explorer
                </span>
              </div>
              <div className="flex-1 overflow-hidden">
                <FileTree />
              </div>
            </div>
          </Panel>

          <ResizeHandle className="w-1" />

          {/* Code Editor Area */}
          <Panel defaultSize={"80"} minSize={"50"}>
            <div className="h-full overflow-hidden">
              <CodeEditor />
            </div>
          </Panel>
        </Group>
      </div>
    </div>
  );
}