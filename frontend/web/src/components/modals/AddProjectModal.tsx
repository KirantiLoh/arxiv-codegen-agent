import { useState, type FormEvent } from "react";
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogDescription, 
  DialogFooter 
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Loader2, BookOpen, AlertCircle } from "lucide-react";

interface AddProjectModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AddProjectModal({ open, onOpenChange }: AddProjectModalProps) {
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Helper to extract just the ID if a user pastes a full URL
  const extractArxivId = (input: string): string => {
    const match = input.match(/(\d{4}\.\d{4,5})(v\d+)?/);
    return match ? match[0] : input.trim();
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    const arxivId = extractArxivId(inputValue);
    
    if (!arxivId) {
      setError("Please enter a valid ArXiv ID or URL.");
      return;
    }

    setIsLoading(true);

    try {
      // Note: Replace with your actual backend URL if not using a Vite proxy
      // e.g., `${import.meta.env.VITE_API_URL}/projects`
      const response = await fetch("/projects", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ arxiv_id: arxivId }),
      });

      if (!response.ok) {
        throw new Error(`Failed to create project: ${response.statusText}`);
      }

      // Success: Reset and close
      setInputValue("");
      onOpenChange(false);
      
      // TODO: Trigger a refetch of your projects list here
      console.log(`Successfully queued project for ArXiv ID: ${arxivId}`);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenChange = (isOpen: boolean) => {
    if (!isOpen) {
      setInputValue("");
      setError(null);
    }
    onOpenChange(isOpen);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md bg-background border-border">
        <DialogHeader>
          <DialogTitle className="text-lg font-semibold flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-primary" />
            Add ArXiv Project
          </DialogTitle>
          <DialogDescription className="text-sm text-muted-foreground">
            Enter the ArXiv ID or full URL. The backend will ingest the PDF and prepare the RAG pipeline.
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="py-2">
          <div className="space-y-4">
            <div className="space-y-2">
              <Input
                autoFocus
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="e.g., 1706.03762 or https://arxiv.org/abs/..."
                className="font-mono text-sm bg-muted/30 border-border focus-visible:ring-primary/50"
                disabled={isLoading}
              />
              {error && (
                <div className="flex items-center gap-2 text-xs text-destructive">
                  <AlertCircle className="h-3.5 w-3.5" />
                  {error}
                </div>
              )}
            </div>
          </div>

          <DialogFooter className="gap-2 sm:gap-0 mt-6">
            <Button 
              type="button" 
              variant="outline" 
              onClick={() => handleOpenChange(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button 
              type="submit" 
              disabled={!inputValue.trim() || isLoading} 
              className="gap-2 min-w-[120px]"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Processing
                </>
              ) : (
                "Create Project"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}