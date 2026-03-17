import React, { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";

export default function ChatBot({ queryId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const scrollRef = useRef(null);

  // Clear chat if the viewed report changes
  useEffect(() => {
    setMessages([{ role: "assistant", content: "Hi! I'm ready to answer questions about this report." }]);

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

  // Don't render anything if no report is loaded
  if (!queryId) return null;

  return (
    <>
      {/* Floating chat bubble button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-40 w-14 h-14 bg-indigo-600 hover:bg-indigo-500 rounded-full shadow-xl flex items-center justify-center transition-all hover:scale-105"
          title="Chat with this report"
        >
          <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        </button>
      )}

      {/* Chat drawer */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 z-40 w-96 h-[520px] bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl flex flex-col overflow-hidden">
          {/* Chat header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700 bg-slate-800/80">
            <span className="text-base font-semibold text-white flex items-center gap-2">
              <svg className="w-4 h-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
              Chat with Report
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={handleClear}
                className="text-xs text-slate-400 hover:text-red-400 transition-colors"
              >
                Clear
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="text-slate-400 hover:text-white transition-colors"
              >
                ✕
              </button>
            </div>
          </div>

          {/* Messages */}
          <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 space-y-3">
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[85%] rounded-2xl px-3 py-2 text-base shadow-sm ${
                  msg.role === "user"
                    ? "bg-indigo-600 text-white ml-6 rounded-tr-none"
                    : "bg-slate-800 text-slate-200 border border-slate-700 mr-6 rounded-tl-none"
                }`}>
                  {msg.role === "user" ? (
                    msg.content
                  ) : (
                    <div className="prose prose-xs prose-invert max-w-none prose-p:leading-relaxed prose-p:my-1 text-base">
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isTyping && (
              <div className="flex justify-start">
                <div className="bg-slate-800 border border-slate-700 text-slate-500 rounded-2xl rounded-tl-none px-3 py-2 mr-6 shadow-sm flex items-center gap-1">
                  <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"></span>
                  <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                  <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          <form onSubmit={handleSubmit} className="p-3 border-t border-slate-700 bg-slate-800/50">
            <div className="relative flex items-center">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={isTyping}
                placeholder="Ask about this report..."
                className="w-full pl-3 pr-10 py-2 bg-slate-800 border border-slate-700 rounded-full text-xs text-white placeholder:text-slate-500 focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 disabled:opacity-50 outline-none"
              />
              <button
                type="submit"
                disabled={!input.trim() || isTyping}
                className="absolute right-1.5 p-2.5 bg-indigo-600 text-white rounded-full hover:bg-indigo-500 disabled:bg-slate-700 disabled:text-slate-500 transition-colors"
              >
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </div>
          </form>
        </div>
      )}
    </>
  );
}
