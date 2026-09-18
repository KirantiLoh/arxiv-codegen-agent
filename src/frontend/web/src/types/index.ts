export type WSMessageType = "AGENT_THOUGHT" | "FILE_CREATED" | "TOKEN_STREAM" | "PDF_HIGHLIGHT";

export interface WSMessage {
    type: WSMessageType;
}

export interface AgentThoughtMessage extends WSMessage {
    type: "AGENT_THOUGHT";
    content: string;
}

export interface FileCreatedMessage extends WSMessage {
    type: "FILE_CREATED";
    fileName: string;
    language: string;
    path: string;
}

export interface TokenStreamMessage extends WSMessage {
    type: "TOKEN_STREAM";
    fileName: string;
    token: string;
}

export interface PdfHighlightMessage extends WSMessage {
    type: "PDF_HIGHLIGHT";
    page: number;
    boundingBox: [number, number, number, number]; // [x, y, width, height]
}

export type IncomingWSMessage =
    | AgentThoughtMessage
    | FileCreatedMessage
    | TokenStreamMessage
    | PdfHighlightMessage;

export interface FileData {
    fileName: string;
    path: string;
    language: string;
    content: string;
}

export interface ChatMessage {
    id: string;
    role: "user" | "agent";
    content: string;
    isStreaming: boolean;
    timestamp: number;
}

export interface PdfState {
    url: string | null;
    currentPage: number;
    highlight: {
        page: number;
        boundingBox: [number, number, number, number];
    } | null;
}