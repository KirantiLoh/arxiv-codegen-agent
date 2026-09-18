import { Terminal } from "lucide-react";
import { AgentChat } from "./AgentChat";

interface ChatPaneProps {
  sendMessage: (message: unknown) => void;
}

export function ChatPane({ sendMessage }: ChatPaneProps) {
  return (
    <div className="flex flex-col h-full bg-background">
      {/* Pane Header */}
      <div className="h-10 flex items-center px-4 border-b border-border bg-muted/30 shrink-0">
        <Terminal className="h-4 w-4 text-muted-foreground mr-2" />
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
          Agent Terminal
        </span>
      </div>
      
      {/* Agent Chat Content */}
      <div className="flex-1 overflow-hidden">
        <AgentChat sendMessage={sendMessage} />
      </div>
    </div>
  );
}