import { createFileRoute, Link } from '@tanstack/react-router';
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowLeft, FileText, Plus } from 'lucide-react';
import { useState } from 'react';
import { UploadPdfModal } from '@/components/modals/UploadPdfModal';

export const Route = createFileRoute('/projects/')({
  component: Projects,
});

// TODO: Replace with actual data fetching from your backend
const mockProjects = [
  { id: 'proj_001', name: 'Attention Is All You Need', date: '2023-10-15', abstract: 'The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...' },
  { id: 'proj_002', name: 'Deep Residual Learning (ResNet)', date: '2023-11-02', abstract: 'Deeper neural networks are more difficult to train. We present a residual learning framework...' },
];

function Projects() {
  
  const [isUploadOpen, setIsUploadOpen] = useState(false);

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Projects</h1>
          <p className="text-sm text-muted-foreground mt-1">Select a paper to open the IDE workspace.</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={() => setIsUploadOpen(true)} className="gap-2">
            <Plus className="h-4 w-4" />
            Upload PDF
          </Button>
        <Button variant="ghost" size="sm">
          <Link to="/" className="gap-2 flex items-center">
            <ArrowLeft className="h-4 w-4" />
            Home
          </Link>
        </Button>
        </div>
      </div>
      
      <div className="grid gap-4">
        {mockProjects.map((project) => (
          <Button key={project.id} variant="ghost" className="h-auto p-0 hover:bg-transparent">
            <Link
              to="/projects/$id"
              params={{ id: project.id }}
              className="block w-full text-left"
            >
              <Card className="group hover:border-primary/50 hover:bg-accent/30 transition-all duration-200 border-border bg-card/50">
                <CardHeader className="p-5">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start gap-3">
                      <div className="mt-1 p-2 rounded-md bg-secondary border border-border">
                        <FileText className="h-4 w-4 text-muted-foreground" />
                      </div>
                      <div>
                        <CardTitle className="text-base font-medium group-hover:text-primary transition-colors">
                          {project.name}
                        </CardTitle>
                        <CardDescription className="mt-1.5 line-clamp-1 truncate max-w-prose">
                          {project.abstract}
                        </CardDescription>
                      </div>
                    </div>
                    <span className="text-xs text-muted-foreground font-mono whitespace-nowrap mt-1">
                      {project.date}
                    </span>
                  </div>
                </CardHeader>
              </Card>
            </Link>
          </Button>
        ))}
      </div>

      <UploadPdfModal open={isUploadOpen} onOpenChange={setIsUploadOpen} />
    </div>
  );
}