import { createFileRoute, Link } from '@tanstack/react-router';
import { Button } from '@/components/ui/button';
import { ArrowRight } from 'lucide-react';

export const Route = createFileRoute('/')({
  component: Index,
});

function Index() {
  return (
    <div className="relative flex flex-col items-center justify-center min-h-screen p-8 max-w-3xl mx-auto text-center overflow-hidden">
      
      {/* 1. The Grid Pattern Background */}
      <div 
        className="absolute inset-0 bg-background pointer-events-none"
        style={{
          backgroundImage: `
            linear-gradient(to right, rgba(255, 255, 255, 0.04) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255, 255, 255, 0.04) 1px, transparent 1px)
          `,
          backgroundSize: '32px 32px',
          // Fades the grid out towards the bottom and edges, keeping it sharp at the top center
          maskImage: 'radial-gradient(ellipse 80% 80% at 50% 0%, #000 40%, transparent 100%)',
          WebkitMaskImage: 'radial-gradient(ellipse 80% 80% at 50% 0%, #000 40%, transparent 100%)',
        }}
      />

      {/* 2. Subtle Ambient Glow behind the text */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-150 h-75 bg-primary/5 blur-[120px] rounded-full pointer-events-none" />

      {/* 3. Main Content (z-10 to sit above the grid) */}
      <div className="relative z-10 flex flex-col items-center">
        <div className="inline-flex items-center rounded-full border border-border px-3 py-1 text-sm text-muted-foreground mb-6 bg-secondary/50 backdrop-blur-sm">
          <span className="mr-2 h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
          Sub-100ms RAG Pipeline Active
        </div>

        <h1 className="text-4xl md:text-5xl font-bold tracking-tight mb-4 bg-linear-to-b from-foreground to-foreground/70 bg-clip-text text-transparent">
          ArXiv Code Reproducer
        </h1>
        
        <p className="text-lg text-muted-foreground mb-10 leading-relaxed max-w-xl">
          An AI-Native Academic IDE. Ingest ArXiv PDFs and reproduce code instantly 
          using our Parent-Child Hybrid RAG pipeline.
        </p>
        
        <Button size="lg" className="gap-2 shadow-lg shadow-primary/10">
          <Link to="/projects" className="gap-2 flex items-center">
            Enter Workspace
            <ArrowRight className="h-4 w-4" />
          </Link>
        </Button>
      </div>
    </div>
  );
}