"use client";
import { useMutation } from "@tanstack/react-query";
import { Navbar, Container, Nav, Row, Col, Button } from "react-bootstrap";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { v4 as uuid } from "uuid";
import mlClient from "@/network/ml/clients";

const fetchAIResponse = async (message: string) => {
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

const getHistory = async (id: string) => {
  const response = await mlClient.GET("/history/{user_id}", {
    params: { path: { user_id: id! } },
  });
  console.log(response);
  if (response.data) {
    return response.data;
  } else {
    return {};
  }
};

export default function Home() {
  const existingIds = JSON.parse(localStorage.getItem("existingIds") || "[]");

  const initialChats =
    existingIds && existingIds.length > 0
      ? existingIds.map((id: string) => ({ id, messages: [] }))
      : [
          {
            id: uuid(),
            messages: [],
          },
        ];

  const [chats, setChats] =
    useState<{ id: string; messages: ChatMessage[] }[]>(initialChats);
  const [selectedChat, setSelectedChat] = useState(initialChats[0].id);

  async function selectChat(id: string) {
    console.log(id);
    if ((chats.find((x) => x.id === id)?.messages?.length ?? 0) < 0) {
      const data = getHistory(id);

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
                    content: data.response.content,
                    citations: data.response.citations,
                  },
                ],
              }
            : chat
        )
      );

      setSelectedChat(element.id);
    }
  }

  function createNewChat() {
    const newId = uuid();
    setChats((prev) => [{ id: newId, messages: [] }, ...prev]);

    const existingIds = JSON.parse(localStorage.getItem("existingIds") || "[]");
    existingIds.push(newId);
    localStorage.setItem("existingIds", JSON.stringify(existingIds));

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
    mutationFn: fetchAIResponse,
    onSuccess: (data) => {
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
                    content: data.response.content,
                    citations: data.response.citations,
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
    setSelectedChat(element.id);
    mutation.mutate(input);
    setInput("");
  };

  return (
    <Row>
      <Col xs={3} className="text-center pt-5 border">
        <Button onClick={createNewChat}>New chat</Button>
        {chats.map((element) => (
          <p key={element.id} onClick={() => selectChat(element.id)}>
            {element.id}
          </p>
        ))}
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
