"use client";
import { useMutation } from "@tanstack/react-query";
import { Navbar, Container, Nav, Row, Col, Button } from "react-bootstrap";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { v4 as uuid } from "uuid";
import mlClient from "@/network/ml/clients";

const postChatQuery = async (message: string) => {
  const response = await mlClient.POST("/query", {
    body: {
      query: message,
    },
    headers: {
      "Content-Type": "application/json",
    },
  });
  console.log(response);
  if (response.data) {
    return response.data;
  } else {
    return {};
  }
};

type HistoryMessage = {
  role: string;
  content: string;
  citations: any[] | null;
};

type HistoryResponse = {
  user_id: string;
  messages: HistoryMessage[];
  total_messages: number;
  status: string;
};

const getHistory = async (id: string): Promise<HistoryResponse | null> => {
  const response = await mlClient.GET("/history/{user_id}", {
    params: { path: { user_id: id } } as any,
  });
  console.log(response);
  if (response.data) {
    return response.data as HistoryResponse;
  } else {
    return null;
  }
};

export default function Home() {
  const [chats, setChats] = useState<{ id: string; messages: ChatMessage[] }[]>([]);
  const [selectedChat, setSelectedChat] = useState("");
  const [isClient, setIsClient] = useState(false);

  // Initialize chats from localStorage on client mount
  useEffect(() => {
    setIsClient(true);
    const storedChats = localStorage.getItem("chats");
    
    if (storedChats) {
      const parsedChats = JSON.parse(storedChats);
      if (parsedChats && parsedChats.length > 0) {
        setChats(parsedChats);
        setSelectedChat(parsedChats[0].id);
      } else {
        // Create initial chat if none exist
        const newId = uuid();
        const initialChat = [{ id: newId, messages: [] }];
        setChats(initialChat);
        setSelectedChat(newId);
        localStorage.setItem("chats", JSON.stringify(initialChat));
      }
    } else {
      // Create initial chat if none exist
      const newId = uuid();
      const initialChat = [{ id: newId, messages: [] }];
      setChats(initialChat);
      setSelectedChat(newId);
      localStorage.setItem("chats", JSON.stringify(initialChat));
    }
  }, []);

  // Save chats to localStorage whenever they change
  useEffect(() => {
    if (isClient && chats.length > 0) {
      localStorage.setItem("chats", JSON.stringify(chats));
    }
  }, [chats, isClient]);

  async function selectChat(id: string) {
    console.log(id);
    const currentChat = chats.find((x) => x.id === id);
    
    // Only load history if chat has no messages yet
    if ((currentChat?.messages?.length ?? 0) === 0) {
      const data = await getHistory(id);

      if (data && data.messages && Array.isArray(data.messages)) {
        // Transform history messages to ChatMessage format
        const transformedMessages = data.messages.map((msg, index) => ({
          id: Date.now() + index,
          role: msg.role,
          content: msg.content,
          citations: msg.citations || [],
        }));

        setChats((prev) =>
          prev.map((chat) =>
            chat.id === id
              ? {
                  ...chat,
                  messages: transformedMessages,
                }
              : chat
          )
        );
      }
    }
    
    setSelectedChat(id);
  }

  function createNewChat() {
    const newId = uuid();
    setChats((prev) => [{ id: newId, messages: [] }, ...prev]);
    setSelectedChat(newId);
  }

  type ChatMessage = {
    id: number;
    role: string;
    content: string;
    citations: string[];
  };

  const [input, setInput] = useState("");

  const mutation = useMutation({
    mutationFn: postChatQuery,
    onSuccess: (data: any) => {
      console.log(data);

      setChats((prev) =>
        prev.map((chat) =>
          chat.id === selectedChat
            ? {
                ...chat,
                messages: [
                  ...chat.messages,
                  {
                    id: Date.now(),
                    role: "assistant",
                    content: data.response?.content || "",
                    citations: data.response?.citations || [],
                  },
                ],
              }
            : chat
        )
      );
    },
  });

  const handleSend = () => {
    if (!input.trim()) return;
    const newMessage: ChatMessage = {
      id: Date.now(),
      role: "user",
      content: input,
      citations: [],
    };

    console.log(newMessage);
    setChats((prev) =>
      prev.map((chat) =>
        chat.id === selectedChat
          ? { ...chat, messages: [...chat.messages, newMessage] }
          : chat
      )
    );
    mutation.mutate(input);
    setInput("");
  };

  // Prevent hydration mismatch by not rendering until client-side
  if (!isClient || chats.length === 0) {
    return null;
  }

  return (
    <Row>
      <Col xs={3} className="text-center pt-5 border">
        <Button onClick={createNewChat}>New chat</Button>
        {chats.map((element) => {
          const firstUserMessage = element.messages.find(
            (msg) => msg.role === "user"
          );
          const displayText = firstUserMessage
            ? firstUserMessage.content.slice(0, 50) + 
              (firstUserMessage.content.length > 50 ? "..." : "")
            : "New Chat";
          
          return (
            <p 
              key={element.id} 
              onClick={() => selectChat(element.id)}
              className={`cursor-pointer p-2 ${
                selectedChat === element.id ? "bg-light fw-bold" : ""
              }`}
              style={{ 
                cursor: "pointer",
                textAlign: "left",
                wordBreak: "break-word"
              }}
            >
              {displayText}
            </p>
          );
        })}
      </Col>
      <Col xs={9}>
        <div
          className="d-flex flex-column vh-100 mx-auto background-red "
          style={{ maxWidth: "1000px" }}
        >
          <div className="flex-grow-1 overflow-auto p-3">
            {(chats.find((x) => x.id === selectedChat)?.messages?.length ?? 0) >
            0 ? (
              chats
                .find((x) => x.id === selectedChat)
                ?.messages?.map((chat: ChatMessage) => (
                  <motion.div
                    key={chat.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3 }}
                    className={`d-flex mb-2 ${
                      chat.role === "user"
                        ? "justify-content-end"
                        : "justify-content-start"
                    }`}
                  >
                    <div
                      className={`p-2 rounded shadow-sm text-wrap ${
                        chat.role === "user"
                          ? "bg-success text-white"
                          : "bg-white border"
                      }`}
                      style={{ maxWidth: "70%" }}
                    >
                      {chat.content}
                    </div>
                  </motion.div>
                ))
            ) : (
              <h2 className="text-center align-middle">Hoe kan ik u helpen?</h2>
            )}

            {mutation.isPending && (
              <div className="text-muted small">
                ROmy is aan het denken en schrijven...
              </div>
            )}
          </div>

          <div className="p-3 border-top bg-white d-flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="Type a message..."
              className="form-control"
            />
            <Button onClick={handleSend} className="btn btn-primary">
              Send
            </Button>
          </div>
        </div>
      </Col>
    </Row>
  );
}
