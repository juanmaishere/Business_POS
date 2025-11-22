import { useEffect, useRef, useState } from "react";

export default function useWebSocket(room = "general") {
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const wsRef = useRef(null);

  useEffect(() => {
    const host = window.location.hostname;
    const url = `ws://${host}:8000/ws/${room}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setMessages((prev) => [...prev, data]);
      } catch (e) {
        console.warn("WS non-json:", event.data);
      }
    };
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);

    return () => ws.close();
  }, [room]);

  const send = (obj) => {
    if (wsRef.current && wsRef.current.readyState === 1) {
      wsRef.current.send(JSON.stringify(obj));
    }
  };

  return { connected, messages, send };
}
