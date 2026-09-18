import { create } from "zustand";
import type { FileData, ChatMessage, PdfState } from "@/types";

interface AppState {
    // File System State
    files: Record<string, FileData>;
    activeFile: string | null;

    // Chat State
    chatHistory: ChatMessage[];
    isChatStreaming: boolean;

    // PDF State
    pdf: PdfState;

    // Actions
    setActiveFile: (fileName: string) => void;
    addFile: (fileName: string, language: string, path: string) => void;
    appendToken: (fileName: string, token: string) => void;

    addChatMessage: (role: "user" | "agent", content: string) => void;
    appendToLastAgentMessage: (content: string) => void;
    finalizeStreamingMessage: () => void;

    setPdfUrl: (url: string) => void;
    setPdfPage: (page: number) => void;
    setPdfHighlight: (page: number, boundingBox: [number, number, number, number] | null) => void;
    clearPdfHighlight: () => void;
}

export const useAppStore = create<AppState>((set, _) => ({
    files: {},
    activeFile: null,
    chatHistory: [],
    isChatStreaming: false,
    pdf: {
        url: null,
        currentPage: 1,
        highlight: null,
    },

    setActiveFile: (fileName) => set({ activeFile: fileName }),

    addFile: (fileName, language, path) =>
        set((state) => ({
            files: {
                ...state.files,
                [fileName]: { fileName, path, language, content: "" },
            },
            activeFile: state.activeFile || fileName,
        })),

    appendToken: (fileName, token) =>
        set((state) => {
            const existingFile = state.files[fileName];
            // Handle race condition where TOKEN_STREAM arrives before FILE_CREATED
            const file = existingFile || { fileName, path: fileName, language: "plaintext", content: "" };

            return {
                files: {
                    ...state.files,
                    [fileName]: {
                        ...file,
                        content: file.content + token,
                    },
                },
                activeFile: state.activeFile || fileName,
            };
        }),

    addChatMessage: (role, content) =>
        set((state) => ({
            chatHistory: [
                ...state.chatHistory,
                {
                    id: crypto.randomUUID(),
                    role,
                    content,
                    isStreaming: role === "agent",
                    timestamp: Date.now(),
                },
            ],
            isChatStreaming: role === "agent",
        })),

    appendToLastAgentMessage: (content) =>
        set((state) => {
            const history = [...state.chatHistory];
            const lastIndex = history.length - 1;

            if (lastIndex >= 0 && history[lastIndex].role === "agent") {
                history[lastIndex] = {
                    ...history[lastIndex],
                    content: history[lastIndex].content + content,
                };
            } else {
                history.push({
                    id: crypto.randomUUID(),
                    role: "agent",
                    content,
                    isStreaming: true,
                    timestamp: Date.now(),
                });
            }

            return { chatHistory: history, isChatStreaming: true };
        }),

    finalizeStreamingMessage: () =>
        set((state) => {
            const history = [...state.chatHistory];
            const lastIndex = history.length - 1;
            if (lastIndex >= 0 && history[lastIndex].isStreaming) {
                history[lastIndex] = { ...history[lastIndex], isStreaming: false };
            }
            return { chatHistory: history, isChatStreaming: false };
        }),

    setPdfUrl: (url) => set((state) => ({ pdf: { ...state.pdf, url } })),

    setPdfPage: (page) => set((state) => ({ pdf: { ...state.pdf, currentPage: page } })),

    setPdfHighlight: (page, boundingBox) =>
        set((state) => ({
            pdf: {
                ...state.pdf,
                currentPage: page,
                highlight: boundingBox ? { page, boundingBox } : null,
            },
        })),

    clearPdfHighlight: () =>
        set((state) => ({
            pdf: { ...state.pdf, highlight: null },
        })),
}));