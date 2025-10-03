"use client";
import { useMutation } from "@tanstack/react-query";
import { Navbar, Container, Nav, Row, Col, Button } from "react-bootstrap";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { v4 as uuid } from "uuid";
// Simulated API call (replace with your real backend)
async function fetchAIResponse(message: string): Promise<{ reply: string }> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ reply: `🤖 AI says: ${message.split("").reverse().join("")}` });
    }, 500);
  });
}

function getCookie(cname: string) {
  const name = cname + "=";
  const ca = document.cookie.split(";");
  for (let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) == " ") {
      c = c.substring(1);
    }
    if (c.indexOf(name) == 0) {
      return c.substring(name.length, c.length);
    }
  }
  return null;
}

function getAllChats() {
  return JSON.parse(getCookie("chats") ?? "[]");
}

export default function Home() {
  const [selectedChat, setSelectedChat] = useState("");

  async function createNewChat() {
    const newUuid = uuid();
    const x = getCookie("chats");
    const updatedChats = [newUuid, ...getAllChats()];

    document.cookie = `chats=${JSON.stringify(updatedChats)}; path=/; max-age=${
      60 * 60 * 24 * 7
    }`;

    setSelectedChat(newUuid);
  }

  const [messages, setMessages] = useState<
    { id: number; role: string; content: string }[]
  >([]);
  const [input, setInput] = useState("");

  const mutation = useMutation({
    mutationFn: fetchAIResponse,
    onSuccess: (data: { reply: string }) => {
      setMessages((prev) => [
        ...prev,
        { id: Date.now(), role: "assistant", content: data.reply },
      ]);
    },
  });

  function getMessagesFromChat(uuid: string) {
    return JSON.parse(getCookie(`chat-${uuid}`) ?? "[]");
  }

  useEffect(() => {
    document.cookie = `chat-${selectedChat}=${JSON.stringify(
      messages
    )}; path=/; max-age=${60 * 60 * 24 * 7}`;
  }, [messages]);

  useEffect(() => {
    setMessages(getMessagesFromChat(selectedChat));
  }, [selectedChat]);

  const handleSend = () => {
    if (!input.trim()) return;
    const newMessage = { id: Date.now(), role: "user", content: input };
    setMessages((prev) => [...prev, newMessage]);
    mutation.mutate(input);
    setInput("");
  };

  return (
    <Row>
      <Col xs={3} className="text-center pt-5 border">
        <Button onClick={createNewChat}>New chat</Button>
        {getAllChats().map((element: string) => {
          return (
            getMessagesFromChat(element).length > 0 && (
              <p key={element} onClick={() => setSelectedChat(element)}>
                {element}
              </p>
            )
          );
        })}
      </Col>
      <Col xs={9}>
        <div
          className="d-flex flex-column vh-100 mx-auto background-red "
          style={{ maxWidth: "1000px" }}
        >
          <div className="flex-grow-1 overflow-auto p-3">
            {messages.length > 0 ? (
              messages.map((msg) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                  className={`d-flex mb-2 ${
                    msg.role === "user"
                      ? "justify-content-end"
                      : "justify-content-start"
                  }`}
                >
                  <div
                    className={`p-2 rounded shadow-sm text-wrap ${
                      msg.role === "user"
                        ? "bg-success text-white"
                        : "bg-white border"
                    }`}
                    style={{ maxWidth: "70%" }}
                  >
                    {msg.content}
                  </div>
                </motion.div>
              ))
            ) : (
              <h2 className="text-center align-middle">Hoe kan ik u helpen?</h2>
            )}

            {mutation.isPending && (
              <div className="text-muted small">AI is typing...</div>
            )}
          </div>

          {/* Input */}
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

  return <div></div>;

  // return (
  //   <div>
  //     {/* Header */}
  //     <Navbar bg="dark" variant="dark" expand="lg">
  //       <Container>
  //         <Navbar.Brand href="#home">MyLandingPage</Navbar.Brand>
  //         <Navbar.Toggle aria-controls="basic-navbar-nav" />
  //         <Navbar.Collapse id="basic-navbar-nav">
  //           <Nav className="ms-auto">
  //             <Nav.Link href="#home">Home</Nav.Link>
  //             <Nav.Link href="#features">Features</Nav.Link>
  //             <Nav.Link href="#contact">Contact</Nav.Link>
  //           </Nav>
  //         </Navbar.Collapse>
  //       </Container>
  //     </Navbar>

  //     {/* Main Content */}
  //     <Container className="flex-grow-1 d-flex flex-column justify-content-center my-5">
  //       <Row className="text-center mb-4">
  //         <Col>
  //           <h1>Welcome to Our Landing Page</h1>
  //           <p>Discover the features and benefits of our product.</p>
  //           <Button variant="primary">Get Started</Button>
  //         </Col>
  //       </Row>
  //       <Row>
  //         <Col md={4} className="mb-3">
  //           <div className="p-4 border rounded h-100">
  //             <h3>Feature One</h3>
  //             <p>Explain the first feature of your product here.</p>
  //           </div>
  //         </Col>
  //         <Col md={4} className="mb-3">
  //           <div className="p-4 border rounded h-100">
  //             <h3>Feature Two</h3>
  //             <p>Explain the second feature of your product here.</p>
  //           </div>
  //         </Col>
  //         <Col md={4} className="mb-3">
  //           <div className="p-4 border rounded h-100">
  //             <h3>Feature Three</h3>
  //             <p>Explain the third feature of your product here.</p>
  //           </div>
  //         </Col>
  //       </Row>
  //     </Container>

  //     {/* Footer */}
  //     <footer className="bg-dark text-white text-center py-4">
  //       <Container>
  //         <p>&copy; 2025 MyLandingPage. All rights reserved.</p>
  //       </Container>
  //     </footer>
  //   </div>
  // );
}
