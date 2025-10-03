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
      resolve({ reply: `ROmy: ${message.split("").reverse().join("")}` });
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
      <input type="checkbox" className="show-hide-trigger" />
      <Col xs={12} className="bg-white pt-3 vh-100 vw-100 show-hide-panel" id="chatHistory">
        <h2>Antwoorden op jouw eerdere vragen</h2>
        <ol>
          {getAllChats().map((element: string) => {
            return (
              getMessagesFromChat(element).length > 0 && (
                <li key={element} onClick={() => setSelectedChat(element)}>
                  {element}
                </li>
              )
            );
          })}
        </ol>
        <Button onClick={createNewChat}>Stel een nieuwe vraag</Button>
      </Col>
      <Col xs={12}>
        <div
          className="d-flex flex-column vh-100 vw-100 mx-auto chat-canvas"
          style={{ maxWidth: "100%" }}
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
                      ? "justify-content-start"
                      : "justify-content-start"
                  }`}
                >
                  <div
                    className={`rounded border-0 p-3 romy-chat fs-5 ${
                      msg.role === "user"
                        ? "bg-success"
                        : "bg-white border"
                    }`}
                    style={{ maxWidth: "70%" }}
                  >
                    {msg.content}
                  </div>
                </motion.div>
              ))
            ) : (
              <h2>Hoi, hoe kan ik je helpen?</h2>
            )}

            {mutation.isPending && (
              <div className="text-muted small">ROmy schrijft…</div>
            )}
          </div>

          {/* Input */}
          <div className="p-3 bg-white d-flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="Waar kan ik je mee helpen?"
              className="border-2 form-control fs-5 p-3"
            />
            <Button onClick={handleSend} className="btn fs-5 btn-primary">
              Stel je vraag
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