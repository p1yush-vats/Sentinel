import { useState, useEffect, useRef } from 'react';

export default function useWebSocket(url) {
  const [lastMessage, setLastMessage] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const ws = useRef(null);
  const reconnectTimeout = useRef(null);

  const connect = () => {
    try {
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        setIsConnected(true);
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastMessage(data);
        } catch (e) {
          // Silently drop malformed messages
        }
      };

      ws.current.onclose = () => {
        setIsConnected(false);
        // Auto-reconnect after 3 seconds
        reconnectTimeout.current = setTimeout(connect, 3000);
      };

      ws.current.onerror = () => {
        ws.current?.close();
      };
    } catch (err) {
      // Connection failed — reconnect will retry
    }
  };

  useEffect(() => {
    connect();

    return () => {
      clearTimeout(reconnectTimeout.current);
      if (ws.current) {
        ws.current.onclose = null; // Prevent reconnect loop on unmount
        ws.current.close();
      }
    };
  }, [url]);

  return { lastMessage, isConnected };
}
