import React, { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";

export default function ChatBot({ queryId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef(null);

  // Clear chat if the viewed report changes
  useEffect(() => {
    setMessages([{ role: "assistant", content: "Hi! I'm ready to answer questions about this report." }]);
    
    // Optionally fetch history
    if (queryId) {
      fetch(`http://localhost:8000/api/chat/${queryId}/history`)
        .then(res => res.json())
        .then(data => {
          if (data && data.length > 0) {
            setMessages(data);
          }
        })
        .catch(console.error);
    }
  }, [queryId]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || !queryId || isTyping) return;

    const userMessage = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsTyping(true);

    try {
      const response = await fetch(`http://localhost:8000/api/chat/${queryId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage.content }),
      });

      if (!response.ok) throw new Error("Network response was not ok");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      let assistantMsg = { role: "assistant", content: "" };
      setMessages((prev) => [...prev, assistantMsg]);

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n\n").filter(Boolean);

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.substring(6));
              if (data.chunk) {
                assistantMsg.content += data.chunk;
                setMessages((prev) => [
                  ...prev.slice(0, -1),
                  { ...assistantMsg }
                ]);
              } else if (data.error) {
                 assistantMsg.content += `\n**Error:** ${data.error}`;
                 setMessages((prev) => [
                  ...prev.slice(0, -1),
                  { ...assistantMsg }
                ]);
              }
            } catch (e) {
              console.error("Error parsing chat chunk", e, line);
            }
          }
        }
      }
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, I encountered an error. Please try again." }
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleClear = async () => {
    if (!queryId) return;
    try {
      await fetch(`http://localhost:8000/api/chat/${queryId}/history`, { method: "DELETE" });
      setMessages([{ role: "assistant", content: "Chat history cleared. What else would you like to know?" }]);
    } catch (err) {
      console.error(err);
    }
  };

  if (!queryId) {
    return (
      <div className="glass h-full flex items-center justify-center p-6 text-center text-text-secondary border-t border-border">
        <p>Generate a report first to enable chat.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-bg-surface border-t border-border mt-4 max-h-[400px]">
      <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-bg-surface/50">
        <h3 className="text-sm font-semibold flex items-center gap-2">
          <svg className="w-4 h-4 text-accent-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
          Chat with Report
        </h3>
        <button onClick={handleClear} className="text-xs text-text-tertiary hover:text-state-error pb-1">Clear</button>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[85%] rounded-2xl px-4 py-2 text-sm shadow-sm ${
              msg.role === "user" 
                ? "bg-accent-primary text-white ml-8 rounded-tr-none" 
                : "bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-700 mr-8 rounded-tl-none"
            }`}>
              {msg.role === "user" ? (
                msg.content
              ) : (
                <div className="prose prose-sm dark:prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-slate-900 prose-pre:p-2">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
              )}
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-500 rounded-2xl rounded-tl-none px-4 py-3 mr-8 shadow-sm flex items-center gap-1">
              <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"></span>
              <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
              <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
            </div>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="p-3 border-t border-border bg-white dark:bg-slate-900">
        <div className="relative flex items-center">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isTyping}
            placeholder="Ask a question grounded in this report..."
            className="w-full pl-4 pr-12 py-2.5 bg-slate-100 dark:bg-slate-800 border-none rounded-full text-sm focus:ring-1 focus:ring-accent-primary disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!input.trim() || isTyping}
            className="absolute right-1.5 p-1.5 bg-accent-primary text-white rounded-full hover:bg-accent-secondary disabled:bg-slate-300 dark:disabled:bg-slate-700 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
      </form>
    </div>
  );
}
