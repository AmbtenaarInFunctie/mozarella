import { NextResponse } from "next/server";

export async function POST(req) {
  const { email, password } = await req.json();

  // Mock user
  const mockUser = {
    email: "test@example.com",
    password: "password123",
    name: "John Doe",
    token: "fake-jwt-token",
  };

  if (email === mockUser.email && password === mockUser.password) {
    return NextResponse.json({ user: mockUser });
  } else {
    return NextResponse.json(
      { message: "Invalid email or password" },
      { status: 401 }
    );
  }
}
