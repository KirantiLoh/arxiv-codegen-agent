import { useEffect, useRef, useCallback } from "react";
import type { IncomingWSMessage } from "@/types";
import { useAppStore } from "@/store/useAppStore";

export function useWebSocket(url: string) {
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const reconnectAttempts = useRef(0);
    const MAX_RECONNECT_ATTEMPTS = 5;
    const BASE_RECONNECT_DELAY = 1000;

    const {
        appendToken,
        addFile,
        appendToLastAgentMessage,
        finalizeStreamingMessage,
        setPdfHighlight
    } = useAppStore();

    const connect = useCallback(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) return;

        try {
            const ws = new WebSocket(url);
            wsRef.current = ws;

            ws.onopen = () => {
                console.log("[WebSocket] Connected to Gateway");
                reconnectAttempts.current = 0;
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data) as IncomingWSMessage;

                    switch (data.type) {
                        case "AGENT_THOUGHT":
                            appendToLastAgentMessage(data.content);
                            break;

                        case "FILE_CREATED":
                            addFile(data.fileName, data.language, data.path);
                            break;

                        case "TOKEN_STREAM":
                            appendToken(data.fileName, data.token);
                            break;

                        case "PDF_HIGHLIGHT":
                            setPdfHighlight(data.page, data.boundingBox);
                            break;

                        default:
                            console.warn("[WebSocket] Unknown message type:", data);
                    }
                } catch (error) {
                    console.error("[WebSocket] Failed to parse message:", error, event.data);
                }
            };

            ws.onclose = (event) => {
                console.log(`[WebSocket] Closed. Code: ${event.code}, Reason: ${event.reason}`);
                wsRef.current = null;
                finalizeStreamingMessage();

                if (reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS) {
                    const delay = BASE_RECONNECT_DELAY * Math.pow(2, reconnectAttempts.current);
                    reconnectAttempts.current += 1;
                    console.log(`[WebSocket] Reconnecting in ${delay}ms...`);

                    reconnectTimeoutRef.current = setTimeout(() => {
                        connect();
                    }, delay);
                } else {
                    console.error("[WebSocket] Max reconnection attempts reached.");
                }
            };

            ws.onerror = (error) => {
                console.error("[WebSocket] Error:", error);
            };
        } catch (error) {
            console.error("[WebSocket] Connection failed:", error);
        }
    }, [url, appendToken, addFile, appendToLastAgentMessage, finalizeStreamingMessage, setPdfHighlight]);

    const sendMessage = useCallback((message: unknown) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify(message));
        } else {
            console.warn("[WebSocket] Cannot send message: Socket is not open.");
        }
    }, []);

    useEffect(() => {
        connect();

        return () => {
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
            if (wsRef.current) {
                wsRef.current.close(1000, "Component unmounted");
            }
        };
    }, [connect]);

    return { sendMessage, isConnected: wsRef.current?.readyState === WebSocket.OPEN };
}