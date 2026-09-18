import { useEffect, useRef, useMemo } from "react";
import CodeMirror, { EditorView, type ReactCodeMirrorRef } from "@uiw/react-codemirror";
import { python } from "@codemirror/lang-python";
import { javascript } from "@codemirror/lang-javascript";
import { json } from "@codemirror/lang-json";
import { vscodeDark } from "@uiw/codemirror-theme-vscode";
import { useAppStore } from "@/store/useAppStore";
import { Code2 } from "lucide-react";

// Map language strings from backend to CodeMirror extensions
const getLanguageExtension = (language: string) => {
  switch (language.toLowerCase()) {
    case "python":
    case "py":
      return python();
    case "javascript":
    case "js":
    case "typescript":
    case "ts":
    case "jsx":
    case "tsx":
      return javascript({ jsx: true, typescript: true });
    case "json":
      return json();
    default:
      return []; // Plaintext
  }
};

export function CodeEditor() {
  const editorRef = useRef<ReactCodeMirrorRef>(null);
  
  // Select ONLY the active file's data to prevent unnecessary re-renders
  const activeFile = useAppStore((state) => state.activeFile);
  const activeFileData = useAppStore((state) => 
    state.activeFile ? state.files[state.activeFile] : null
  );

  // Keep track of the last known content length to calculate the streaming delta
  const prevContentLengthRef = useRef(0);

  const extensions = useMemo(() => {
    const base = [EditorView.lineWrapping];
    if (activeFileData?.language) {
      base.push(getLanguageExtension(activeFileData.language));
    }
    return base;
  }, [activeFileData?.language]);

  // Imperative update loop for high-performance streaming
  useEffect(() => {
    const view = editorRef.current?.view;
    if (!view || !activeFileData) return;

    const currentDocLength = view.state.doc.length;
    const newContent = activeFileData.content;

    // If the new content is longer, it's a streaming append. 
    // We only insert the delta to avoid full document re-parsing.
    if (newContent.length > currentDocLength) {
      const tokenToInsert = newContent.slice(currentDocLength);
      view.dispatch({
        changes: { from: currentDocLength, insert: tokenToInsert },
      });
    } 
    // If the file changed completely (e.g., user switched tabs), replace the whole doc
    else if (newContent !== view.state.doc.toString()) {
      view.dispatch({
        changes: { from: 0, to: currentDocLength, insert: newContent },
      });
    }

    prevContentLengthRef.current = newContent.length;
  }, [activeFileData?.content, activeFile]);

  // Auto-scroll to bottom when streaming
  useEffect(() => {
    const view = editorRef.current?.view;
    if (view && activeFileData?.content.length !== prevContentLengthRef.current) {
       // Simple auto-scroll logic for streaming
       const scrollDom = view.scrollDOM;
       scrollDom.scrollTop = scrollDom.scrollHeight;
    }
  }, [activeFileData?.content]);

  if (!activeFile || !activeFileData) {
    return (
      <div className="flex flex-col h-full items-center justify-center bg-background/50">
        <Code2 className="h-10 w-10 text-muted-foreground/30 mb-3" />
        <p className="text-sm font-mono text-muted-foreground">No file selected</p>
        <p className="text-xs text-muted-foreground/60 mt-1">
          Select a file from the explorer to view code.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-background">
      {/* File Tab Header */}
      <div className="h-9 flex items-center px-4 border-b border-border bg-muted/20 shrink-0">
        <div className="flex items-center gap-2 px-3 py-1 rounded-t-md bg-background border border-border border-b-background text-xs font-mono text-foreground">
          <span className="text-primary">●</span>
          {activeFileData.fileName}
        </div>
        <div className="ml-auto text-[10px] text-muted-foreground font-mono uppercase">
          {activeFileData.language || "plaintext"}
        </div>
      </div>

      {/* CodeMirror Editor */}
      <div className="flex-1 overflow-hidden relative">
        <CodeMirror
          ref={editorRef}
          value={activeFileData.content} // Initial value, subsequent updates handled imperatively
          height="100%"
          theme={vscodeDark}
          extensions={extensions}
          className="h-full font-mono text-sm"
          basicSetup={{
            lineNumbers: true,
            highlightActiveLineGutter: true,
            highlightSpecialChars: true,
            history: true,
            foldGutter: true,
            drawSelection: true,
            dropCursor: true,
            allowMultipleSelections: true,
            indentOnInput: true,
            syntaxHighlighting: true,
            bracketMatching: true,
            closeBrackets: true,
            autocompletion: true,
            rectangularSelection: true,
            crosshairCursor: false,
            highlightActiveLine: true,
            highlightSelectionMatches: true,
            closeBracketsKeymap: true,
            searchKeymap: true,
            foldKeymap: true,
            completionKeymap: true,
            lintKeymap: true,
          }}
        />
      </div>
    </div>
  );
}