import { NextRequest, NextResponse } from "next/server";

const BASE_URL = process.env.PII_API_BASE_URL || "http://127.0.0.1:8080";

export async function POST(req: NextRequest) {
  try {
    const payload = await req.json();
    const response = await fetch(`${BASE_URL}/api/forget`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      cache: "no-store",
    });

    const text = await response.text();
    if (!response.ok) {
      return NextResponse.json(
        { error: `Upstream ${response.status}`, detail: text },
        { status: response.status },
      );
    }

    return new NextResponse(text, {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  } catch (err) {
    return NextResponse.json(
      { error: "Proxy error", detail: String(err) },
      { status: 500 },
    );
  }
}
