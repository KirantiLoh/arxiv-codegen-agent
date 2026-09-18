import { createFileRoute, Link } from '@tanstack/react-router';
import { Panel, Group } from 'react-resizable-panels';
import { ResizeHandle } from '@/components/layout/ResizeHandle';
import { PdfPane } from '@/components/panes/PdfPane';
import { IdePane } from '@/components/panes/IdePane';
import { ChatPane } from '@/components/panes/ChatPane';
import { useWebSocket } from '@/hooks/useWebSocket';
import { ChevronLeft, Wifi, WifiOff } from 'lucide-react';

export const Route = createFileRoute('/projects/$id')({
  component: ProjectWorkspace,
});

function ProjectWorkspace() {
  const { id } = Route.useParams();
  
  // Initialize WebSocket connection (Step 2 hook)
  // In production, this URL will come from your environment variables
  const { sendMessage, isConnected } = useWebSocket(`ws://localhost:8080/ws?project_id=${id}`);

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden bg-background">
      {/* Top Bar */}
      <header className="h-12 border-b border-border flex items-center px-4 bg-background/80 backdrop-blur-md z-10 shrink-0">
        <Link to="/projects" className='mr-4 hover:text-zinc-400'>
          <ChevronLeft />
        </Link>
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
          Project
        </span>
        <span className="ml-2 text-sm font-semibold font-mono text-foreground">
          {id}
        </span>
        
        <div className="ml-auto h-full flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            {isConnected ? (
              <>
                <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                <Wifi className="h-3.5 w-3.5 text-emerald-500" />
                <span className="text-xs text-muted-foreground">Gateway Connected</span>
              </>
            ) : (
              <>
                <div className="h-1.5 w-1.5 rounded-full bg-red-500" />
                <WifiOff className="h-3.5 w-3.5 text-red-500" />
                <span className="text-xs text-red-400">Disconnected</span>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Main 3-Pane Workspace */}
      <main className="flex-1 overflow-hidden relative">
        <Group orientation="horizontal" className='h-full'>
          <Panel defaultSize={"50"} minSize={"30"} maxSize={"80"}>
            <Group orientation='vertical'>

              {/* Top Pane: PDF Viewer (70%) */}
              <Panel defaultSize={"70"} minSize={"15"} maxSize={"80"}>
                <PdfPane />
              </Panel>

              <ResizeHandle orientation='horizontal' />

              {/* Bottom Pane: Agent Chat (30%) */}
              <Panel collapsible defaultSize={"30"} minSize={"15"} maxSize={"40"}>
                <ChatPane sendMessage={sendMessage} />
              </Panel>
            </Group>
          </Panel>

          <ResizeHandle />


          {/* Right Pane: Code IDE (50%) */}
          <Panel defaultSize={"50"} minSize={"30"} maxSize={"80"}>
            <IdePane />
          </Panel>

        </Group>
      </main>
    </div>
  );
}