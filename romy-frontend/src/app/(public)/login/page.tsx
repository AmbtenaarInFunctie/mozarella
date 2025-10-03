"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const [email, setEmail] = useState("test@example.com");
  const [password, setPassword] = useState("password123");
  const [error, setError] = useState("");
  const router = useRouter();

  const handleLogin = async (e: { preventDefault: () => void }) => {
    e.preventDefault();

    const res = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    const data = await res.json();

    if (res.ok) {
      document.cookie = `token=${data.user.token}; path=/; max-age=${
        60 * 60 * 24 * 7
      }`;
      router.refresh();
    } else {
      setError(data.message);
    }
  };

  return (
    <div className="d-flex justify-content-center align-items-center vh-100 bg-light">
      <div
        className="bg-white p-4 rounded shadow-sm"
        style={{ width: "360px" }}
      >
        {/* Logo */}
        <div className="text-center mb-4">
          <img
            src="https://www.rijksoverheid.nl/binaries/content/gallery/rijksoverheid/banner/logo-rijksoverheid.svg"
            alt="Logo"
            style={{ height: "50px" }}
          />
        </div>

        {/* Title */}
        <h6 className="fw-bold mb-3" style={{ color: "#e17000" }}>
          Vul hieronder uw gebruikersnaam en wachtwoord in
        </h6>

        {/* Form */}
        <form>
          <div className="mb-3">
            <label htmlFor="email" className="form-label fw-semibold">
              Email
            </label>
            <input
              type="text"
              className="form-control"
              id="email"
              placeholder=""
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div className="mb-3">
            <label htmlFor="password" className="form-label fw-semibold">
              Wachtwoord
            </label>
            <div className="input-group">
              <input
                type="password"
                className="form-control"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <span className="input-group-text bg-white">
                <i className="bi bi-eye"></i>
              </span>
            </div>
          </div>

          <div className="form-check mb-3">
            <input type="checkbox" className="form-check-input" id="remember" />
            <label className="form-check-label" htmlFor="remember">
              Onthoud mijn DigiD email
            </label>
          </div>

          <div className="d-flex ">
            <button
              type="submit"
              className="btn text-start w-50 fw-bold"
              style={{ backgroundColor: "white", color: "black" }}
            >
              {"<"} Vorige
            </button>

            <button
              type="submit"
              className="btn btn-warning w-50 fw-bold"
              style={{ backgroundColor: "#e17000", color: "white" }}
            >
              Inloggen {">"}
            </button>
          </div>

          <div className="mt-3 ">
            <a href="#" className="d-block small">
              Wachtwoord vergeten?
            </a>
            <a href="#" className="d-block small">
              Nog geen DigiD? Vraag uw DigiD aan
            </a>
          </div>
        </form>

        <hr className="my-4" />

        <div>
          <p className="fw-bold small mb-2">Vraag en antwoord</p>
          <ul className="list-unstyled small">
            <li>
              <a href="#">Hoe kan ik de sms-controle activeren?</a>
            </li>
            <li>
              <a href="#">Waar download ik de DigiD app?</a>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );

  return (
    <div style={{ maxWidth: "400px", margin: "auto", paddingTop: "50px" }}>
      <h1>Login</h1>
      <form onSubmit={handleLogin}>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          style={{ width: "100%", marginBottom: "10px", padding: "8px" }}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          style={{ width: "100%", marginBottom: "10px", padding: "8px" }}
        />
        <button type="submit" style={{ width: "100%", padding: "8px" }}>
          Login
        </button>
      </form>
      {error && <p style={{ color: "red" }}>{error}</p>}
    </div>
  );
}
