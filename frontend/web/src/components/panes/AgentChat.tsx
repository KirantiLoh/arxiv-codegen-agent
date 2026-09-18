import { useState, useEffect, useRef } from "react";
import type { FormEvent, KeyboardEvent } from "react";
import { useAppStore } from "@/store/useAppStore";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Bot, User, Send, Terminal } from "lucide-react";
import { cn } from "@/lib/utils";

interface AgentChatProps {
  sendMessage: (message: unknown) => void;
}

export function AgentChat({ sendMessage }: AgentChatProps) {
  const chatHistory = useAppStore((state) => state.chatHistory);
  const isChatStreaming = useAppStore((state) => state.isChatStreaming);
  const addChatMessage = useAppStore((state) => state.addChatMessage);
  
  const [inputValue, setInputValue] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom when new messages arrive or stream updates
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [chatHistory, isChatStreaming]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [inputValue]);

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    // Add user message to store
    addChatMessage("user", inputValue);
    
    // Send to WebSocket gateway
    sendMessage({ type: "USER_PROMPT", content: inputValue });
    
    setInputValue("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as unknown as FormEvent<HTMLFormElement>);
    }
  };

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Chat Messages Area */}
      <ScrollArea className="flex-1">
        {/* Ref is placed on the inner div because shadcn ScrollArea doesn't forward refs to the viewport */}
        <div className="p-4" ref={scrollRef}>
          <div className="space-y-4">
            {chatHistory.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full text-center py-12 opacity-50">
                <Terminal className="h-8 w-8 text-muted-foreground mb-2" />
                <p className="text-xs text-muted-foreground">
                  Agent is ready. Ask a question about the paper.
                </p>
              </div>
            )}

            {chatHistory.map((msg) => (
              <div
                key={msg.id}
                className={cn(
                  "flex items-start gap-3",
                  msg.role === "user" ? "flex-row-reverse" : "flex-row"
                )}
              >
                {/* Avatar */}
                <div
                  className={cn(
                    "mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-md border",
                    msg.role === "agent"
                      ? "bg-primary/10 border-primary/20 text-primary"
                      : "bg-secondary border-border text-foreground"
                  )}
                >
                  {msg.role === "agent" ? (
                    <Bot className="h-4 w-4" />
                  ) : (
                    <User className="h-4 w-4" />
                  )}
                </div>

                {/* Message Content */}
                <div
                  className={cn(
                    "flex-1 space-y-1",
                    msg.role === "user" ? "text-right" : "text-left"
                  )}
                >
                  <p className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
                    {msg.role === "agent" ? "Agent" : "You"}
                  </p>
                  <div
                    className={cn(
                      "inline-block text-sm text-foreground leading-relaxed whitespace-pre-wrap wrap-break-word",
                      msg.role === "user" && "bg-secondary/50 px-3 py-2 rounded-lg border border-border"
                    )}
                  >
                    {msg.content}
                    {/* Streaming Cursor Effect */}
                    {msg.isStreaming && (
                      <span className="inline-block w-1.5 h-4 ml-0.5 bg-primary align-middle animate-pulse" />
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="p-3 border-t border-border bg-muted/20 shrink-0">
        <form onSubmit={handleSubmit} className="relative">
          <textarea
            ref={textareaRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask the agent..."
            rows={1}
            className="flex-1 w-full resize-none rounded-md border border-border bg-background px-3 py-2.5 pr-10 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50 scrollbar-hide"
            style={{ maxHeight: "120px" }}
          />
          <Button
            type="submit"
            size="icon"
            variant="ghost"
            className="absolute right-2 top-1/2 -translate-y-1/2 h-7 w-7 text-muted-foreground hover:text-foreground"
            disabled={!inputValue.trim()}
          >
            <Send className="h-4 w-4" />
          </Button>
        </form>
        <div className="flex items-center justify-between mt-1.5 px-1">
          <span className="text-[10px] text-muted-foreground/60">
            {isChatStreaming ? "Agent is thinking..." : "Ready"}
          </span>
          <div className="flex items-center gap-1 text-[10px] text-muted-foreground/60">
            <kbd className="px-1 py-0.5 rounded border border-border bg-muted text-[9px] font-mono">↵</kbd>
            <span>to send</span>
            <kbd className="px-1 py-0.5 rounded border border-border bg-muted text-[9px] font-mono ml-1">⇧↵</kbd>
            <span>for new line</span>
          </div>
        </div>
      </div>
    </div>
  );
}