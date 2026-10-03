import { useState, useEffect, useRef } from "react";
import type { FormEvent, KeyboardEvent } from "react";
import { useAppStore } from "@/store/useAppStore";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Bot, User, Send, Terminal, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";

interface AgentChatProps {
  sendMessage: (message: unknown) => void;
}

export function AgentChat({ sendMessage }: AgentChatProps) {
  const chatHistory = useAppStore((state) => state.chatHistory);
  const isChatStreaming = useAppStore((state) => state.isChatStreaming);
  const addChatMessage = useAppStore((state) => state.addChatMessage);
  const agentThought = useAppStore((state) => state.agentThought);
  
  const [inputValue, setInputValue] = useState("");
  const [isWaitingForResponse, setIsWaitingForResponse] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [chatHistory, agentThought]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [inputValue]);

  // Reset waiting state when agent starts thinking or outputs
  useEffect(() => {
    if (agentThought || !isChatStreaming) {
      setIsWaitingForResponse(false);
    }
  }, [agentThought, isChatStreaming]);

  const submitMessage = () => {
    if (!inputValue.trim()) return;
    addChatMessage("user", inputValue);
    sendMessage({ type: "USER_PROMPT", content: inputValue });
    setInputValue("");
    setIsWaitingForResponse(true);
  };

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    submitMessage();
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submitMessage();
    }
  };

  const isInputDisabled = isWaitingForResponse || isChatStreaming;

  return (
    <div className="flex flex-col h-full w-full overflow-hidden bg-background">
      <div className="flex-1 min-h-0 overflow-hidden">
        <ScrollArea className="h-full w-full" type="auto">
          <div className="p-4 space-y-4 min-h-full">
            {chatHistory.length === 0 && !agentThought && !isWaitingForResponse && (
              <div className="flex flex-col items-center justify-center h-64 text-center opacity-50">
                <Terminal className="h-8 w-8 text-muted-foreground mb-2 mx-auto" />
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
                      "text-sm text-foreground leading-relaxed",
                      msg.role === "user" 
                        ? "bg-secondary/50 px-3 py-2 rounded-lg border border-border inline-block"
                        : "prose prose-invert prose-sm max-w-none"
                    )}
                  >
                    {msg.role === "agent" ? (
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm, remarkMath]}
                        rehypePlugins={[rehypeRaw, rehypeKatex]}
                        components={{
                          h1: ({node, ...props}) => <h1 className="text-base font-bold mt-3 mb-2 break-words" {...props} />,
                          h2: ({node, ...props}) => <h2 className="text-sm font-bold mt-3 mb-1.5 break-words" {...props} />,
                          h3: ({node, ...props}) => <h3 className="text-sm font-semibold mt-2 mb-1 break-words" {...props} />,
                          p: ({node, ...props}) => <p className="mb-2 last:mb-0 break-words whitespace-normal" {...props} />,
                          ul: ({node, ...props}) => <ul className="list-disc pl-3 mb-2 space-y-1" {...props} />,
                          ol: ({node, ...props}) => <ol className="list-decimal pl-3 mb-2 space-y-1" {...props} />,
                          li: ({node, ...props}) => <li className="pl-3 min-w-0 break-words" {...props} />,
                          strong: ({node, ...props}) => <strong className="font-semibold" {...props} />,
                          em: ({node, ...props}) => <em className="italic" {...props} />,
                          code: ({node, inline, ...props}: any) => 
                            inline ? (
                              <code className="bg-muted/50 px-1.5 py-0.5 rounded text-xs font-mono break-all" {...props} />
                            ) : (
                              <code className="block bg-muted/30 p-3 rounded text-xs font-mono my-2 overflow-x-auto whitespace-pre" {...props} />
                            ),
                          pre: ({node, ...props}) => <pre className="bg-muted/30 p-3 rounded my-2 overflow-x-auto" {...props} />,
                       
                        }}
                      >
                        {msg.content}
                      </ReactMarkdown>
                    ) : (
                      msg.content
                    )}
                    {msg.isStreaming && (
                      <span className="inline-block w-1.5 h-4 ml-0.5 bg-primary align-middle animate-pulse" />
                    )}
                  </div>
                </div>
              </div>
            ))}

            {/* Show "Sending to server..." immediately after user sends */}
            {isWaitingForResponse && !agentThought && (
              <div className="flex items-start gap-3 flex-row animate-in fade-in slide-in-from-bottom-2 duration-300">
                <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-md border bg-muted/50 border-border text-muted-foreground">
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                </div>
                <div className="flex-1 space-y-1 text-left">
                  <p className="text-[11px] font-medium text-muted-foreground/70 uppercase tracking-wider">
                    Sending...
                  </p>
                  <div className="inline-block text-sm text-muted-foreground italic leading-relaxed">
                    Sending to server...
                  </div>
                </div>
              </div>
            )}

            {/* Show agent thought when it arrives */}
            {agentThought && (
              <div className="flex items-start gap-3 flex-row animate-in fade-in slide-in-from-bottom-2 duration-300">
                <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-md border bg-muted/50 border-border text-muted-foreground">
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                </div>
                <div className="flex-1 space-y-1 text-left">
                  <p className="text-[11px] font-medium text-muted-foreground/70 uppercase tracking-wider">
                    Thinking...
                  </p>
                  <div className="inline-block text-sm text-muted-foreground italic leading-relaxed">
                    {agentThought}
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
          <ScrollBar />
        </ScrollArea>
      </div>

      <div className="shrink-0 border-t border-border bg-muted/20">
        <div className="p-3">
          <form onSubmit={handleSubmit} className="relative">
            <textarea
              ref={textareaRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={isInputDisabled ? "Waiting for response..." : "Ask the agent..."}
              rows={1}
              disabled={isInputDisabled}
              className="flex-1 w-full resize-none rounded-md border border-border bg-background px-3 py-2.5 pr-10 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50 scrollbar-hide"
              style={{ maxHeight: "120px" }}
            />
            <Button
              type="submit"
              size="icon"
              variant="ghost"
              className="absolute right-2 top-1/2 -translate-y-1/2 h-7 w-7 text-muted-foreground hover:text-foreground"
              disabled={isInputDisabled || !inputValue.trim()}
            >
              <Send className="h-4 w-4" />
            </Button>
          </form>
          <div className="flex items-center justify-between mt-1.5 px-1">
            <span className="text-[10px] text-muted-foreground/60">
              {isWaitingForResponse ? "Sending to server..." : 
               agentThought ? "Agent is thinking..." :
               isChatStreaming ? "Receiving response..." : "Ready"}
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
    </div>
  );
}
