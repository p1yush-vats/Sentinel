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
        console.log('WebSocket Connected');
      };
      
      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastMessage(data);
        } catch (e) {
          console.error("Failed to parse websocket message", e);
        }
      };
      
      ws.current.onclose = () => {
        setIsConnected(false);
        console.log('WebSocket Disconnected. Reconnecting in 3s...');
        // Auto-reconnect
        reconnectTimeout.current = setTimeout(connect, 3000);
      };
      
      ws.current.onerror = (err) => {
        console.error('WebSocket Error:', err);
        ws.current?.close();
      };
    } catch (err) {
      console.error('Failed to create WebSocket:', err);
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
