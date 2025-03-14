import { useState, useEffect, useRef } from 'react';
import './App.css';

// Update Message interface to handle complex content from tool use
interface Message {
  role: 'user' | 'assistant';
  content: string | any; // Can be string or complex object with tool data
}

interface Conversation {
  id: string;
  message_count: number;
}

function App() {
  const [input, setInput] = useState<string>('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [useTools, setUseTools] = useState<boolean>(true); // Default to using tools
  const [toolUsed, setToolUsed] = useState<boolean>(false);
  const [lastToolUsed, setLastToolUsed] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Fetch conversations on component mount
  useEffect(() => {
    fetchConversations();
  }, []);

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchConversations = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/conversations');
      const data = await response.json();
      setConversations(data);
    } catch (error) {
      console.error('Error fetching conversations:', error);
    }
  };

  const loadConversation = async (id: string) => {
    try {
      const response = await fetch(`http://localhost:5000/api/conversations/${id}`);
      const data = await response.json();
      setMessages(data.history);
      setConversationId(id);
    } catch (error) {
      console.error('Error loading conversation:', error);
    }
  };

  const handleSend = async () => {
    if (!input.trim()) return;
    
    // Make sure messages is an array before spreading
    const currentMessages = Array.isArray(messages) ? messages : [];
    
    // Add user message to UI immediately
    const userMessage: Message = { role: 'user', content: input };
    setMessages([...currentMessages, userMessage]);
    setInput('');
    setLoading(true);
    setLastToolUsed(null); // Reset tool info
    
    try {
      const response = await fetch('http://localhost:5000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: input,
          conversation_id: conversationId,
          use_tools: useTools
        }),
      });
      
      const data = await response.json();
      
      if (data.error) {
        console.error('Error from server:', data.error);
        setMessages([...currentMessages, userMessage, {
          role: 'assistant',
          content: `Error: ${data.error}`
        }]);
        return;
      }
      
      // Check if tool was used
      if (data.tool_used && data.tool_name) {
        setLastToolUsed(data.tool_name);
        console.log(`Tool used: ${data.tool_name}`);
      }
      
      // Update with full conversation history from server
      if (Array.isArray(data.history)) {
        setMessages(data.history);
      } else {
        console.error('History from server is not an array:', data.history);
      }
      
      setConversationId(data.conversation_id);
      
      // Refresh conversation list
      fetchConversations();
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages([...currentMessages, userMessage, {
        role: 'assistant',
        content: `Error: Could not connect to the server. Please try again.`
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const startNewConversation = () => {
    setConversationId(null);
    setMessages([]);
  };

  // Function to render message content properly with safety checks
  const renderMessageContent = (msg: Message) => {
    if (!msg || msg.content === undefined) {
      return <div className="message-content">Error: Invalid message</div>;
    }
    
    // If content is a string, render it directly
    if (typeof msg.content === 'string') {
      return <div className="message-content">{msg.content}</div>;
    }
    
    // If content is an array (for tool use)
    if (Array.isArray(msg.content)) {
      return (
        <div className="message-content">
          {msg.content.map((item, idx) => {
            if (!item) return <div key={idx}>Invalid item</div>;
            
            if (item.type === 'tool_use') {
              // Render tool use block
              return (
                <div key={idx} className="tool-use">
                  <div className="tool-badge">Using Tool: {item.name}</div>
                  <pre>{JSON.stringify(item.input || {}, null, 2)}</pre>
                </div>
              );
            } else if (item.type === 'text') {
              // Render text content
              return <div key={idx}>{item.text}</div>;
            } else {
              // Fallback for other content types
              return <div key={idx}>{JSON.stringify(item)}</div>;
            }
          })}
        </div>
      );
    }
    
    // Fallback for any other content format
    return <div className="message-content">{JSON.stringify(msg.content)}</div>;
  };

  return (
    <div className="app">
      <div className="sidebar">
        <h2>Conversations</h2>
        <button onClick={startNewConversation} className="new-chat-btn">
          New Conversation
        </button>
        
        {/* Add tool use toggle */}
        <div className="tool-toggle">
          <label>
            <input
              type="checkbox"
              checked={useTools}
              onChange={() => setUseTools(!useTools)}
            />
            Enable DaVinci Resolve Tools
          </label>
        </div>
        
        <div className="conversation-list">
          {Array.isArray(conversations) && conversations.map((conv) => (
            <div 
              key={conv.id} 
              className={`conversation-item ${conv.id === conversationId ? 'active' : ''}`}
              onClick={() => loadConversation(conv.id)}
            >
              Conversation {conv.id.substring(0, 6)}... 
              <span className="message-count">({conv.message_count} messages)</span>
            </div>
          ))}
        </div>
      </div>
      
      <div className="chat-container">
        <div className="messages">
          {!Array.isArray(messages) || messages.length === 0 ? (
            <div className="empty-state">
              <h2>Claude AI Assistant</h2>
              <p>Send a message to start a conversation</p>
              {useTools && (
                <div className="tools-enabled-notice">
                  <p>DaVinci Resolve tools are enabled</p>
                  <p className="tools-hint">Try asking about your DaVinci Resolve project</p>
                </div>
              )}
            </div>
          ) : (
            messages.map((msg, index) => (
              <div key={index} className={`message ${msg?.role || 'unknown'}`}>
                {/* Show tool use badge for tool-related messages */}
                {msg.content && typeof msg.content === 'string' && 
                 msg.content.includes("I'll use the") && (
                  <div className="tool-badge">
                    <span className="tool-icon">🛠️</span> Using DaVinci Resolve Tool
                  </div>
                )}
                {renderMessageContent(msg)}
              </div>
            ))
          )}
          {loading && (
            <div className="message assistant">
              <div className="message-content">
                <div className="loading-indicator">
                  <span>●</span><span>●</span><span>●</span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        
        <div className="input-area">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={useTools ? "Ask about DaVinci Resolve or anything else..." : "Type a message..."}
            rows={3}
          />
          <button onClick={handleSend} disabled={loading || !input.trim()}>
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
