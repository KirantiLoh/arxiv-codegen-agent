import { useEffect, useRef, useState } from "react";
import type { IncomingWSMessage } from "@/types";
import { useAppStore } from "@/store/useAppStore";

export function useWebSocket(url: string) {
    const wsRef = useRef<WebSocket | null>(null);
    const [isConnected, setIsConnected] = useState(false);
    const reconnectAttempts = useRef(0);
    const maxReconnectAttempts = 5;

    useEffect(() => {
        if (!url) {
            console.warn("[WebSocket] No URL provided");
            return;
        }

        let isMounted = true;

        const connect = () => {
            if (!isMounted) return;

            console.log("[WebSocket] Connecting to:", url);
            const ws = new WebSocket(url);
            wsRef.current = ws;

            ws.onopen = () => {
                if (isMounted) {
                    console.log("[WebSocket] Connected successfully");
                    setIsConnected(true);
                    reconnectAttempts.current = 0;
                }
            };

            ws.onmessage = (event) => {
                if (!isMounted) return;
                try {
                    const data = JSON.parse(event.data) as IncomingWSMessage;
                    const actions = useAppStore.getState();

                    switch (data.type) {
                        case "AGENT_OUTPUT":
                            actions.appendToLastAgentMessage(data.content);
                            actions.setAgentThought("");
                            // Finalize streaming when we receive AGENT_OUTPUT
                            // This re-enables the input field
                            actions.finalizeStreamingMessage();
                            break;
                        case "AGENT_THOUGHT":
                            actions.setAgentThought(data.content);
                            break;
                        case "FILE_CREATED":
                            actions.addFile(data.fileName, data.language, data.path);
                            break;
                        case "TOKEN_STREAM":
                            actions.appendToken(data.fileName, data.token);
                            break;
                        default:
                            console.warn("[WebSocket] Unknown message type:", data);
                    }
                } catch (error) {
                    console.error("[WebSocket] Failed to parse message:", error);
                }
            };

            ws.onclose = (event) => {
                if (isMounted) {
                    console.log(`[WebSocket] Closed. Code: ${event.code}`);
                    setIsConnected(false);
                    wsRef.current = null;
                    useAppStore.getState().finalizeStreamingMessage();
                    useAppStore.getState().setAgentThought("");

                    if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
                        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 10000);
                        reconnectAttempts.current += 1;
                        console.log(`[WebSocket] Reconnecting in ${delay}ms...`);
                        setTimeout(connect, delay);
                    }
                }
            };

            ws.onerror = (error) => {
                console.error("[WebSocket] Error:", error);
            };
        };

        connect();

        return () => {
            isMounted = false;
            if (wsRef.current) {
                console.log("[WebSocket] Cleanup: Closing socket");
                wsRef.current.close(1000, "Component unmounting");
                wsRef.current = null;
            }
        };
    }, [url]);

    const sendMessage = (message: unknown) => {
        const socket = wsRef.current;
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify(message));
        } else {
            console.warn(`[WebSocket] Cannot send. Socket state: ${
                !socket ? "NULL (not initialized or closed)" : 
                socket.readyState === WebSocket.CONNECTING ? "CONNECTING" :
                socket.readyState === WebSocket.CLOSING ? "CLOSING" : "CLOSED"
            }`);
        }
    };

    return { sendMessage, isConnected };
}
