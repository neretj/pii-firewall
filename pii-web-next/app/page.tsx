"use client";

import { useMemo, useState, useRef, useEffect } from "react";
import type { PipelineForm, PipelineRequest, PipelineRunResponse } from "../lib/types";
import type { ApiPath } from "@/lib/constants";
import { SESSION_KEY, INITIAL_FORM } from "@/lib/constants";
import { PasswordGate } from "@/components/chat/PasswordGate";
import { AppHeader } from "@/components/chat/AppHeader";
import { ConfigSidebar } from "@/components/chat/ConfigSidebar";
import { ChatArea } from "@/components/chat/ChatArea";
import { TraceSidebar } from "@/components/chat/TraceSidebar";
import { DebugPanel } from "@/components/chat/DebugPanel";

type ChatTurn = {
  id: string;
  userText: string;
  response: PipelineRunResponse;
};

// --- MAIN APP ORCHESTRATOR ---
function App() {
  const [form, setForm] = useState<PipelineForm>(INITIAL_FORM);
  const [draft, setDraft] = useState(
    "Ana García, ID 12345678A, is 43 years old and has hypertension. What do you recommend?",
  );
  const [chat, setChat] = useState<ChatTurn[]>([]);
  const [selectedTurnId, setSelectedTurnId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("Ready — choose a scenario or write your own message");
  const [output, setOutput] = useState("{}");
  const chatBottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat]);

  const onChange = (key: keyof PipelineForm, value: string) =>
    setForm((prev) => ({ ...prev, [key]: value } as PipelineForm));

  const selectedTurn = useMemo(
    () =>
      selectedTurnId
        ? chat.find((t) => t.id === selectedTurnId) ?? null
        : chat.at(-1) ?? null,
    [chat, selectedTurnId],
  );

  const continuity = useMemo(() => {
    const stats: Record<string, { original: string; turns: number[] }> = {};
    for (const [idx, turn] of chat.entries()) {
      for (const [token, original] of Object.entries(turn.response.steps.mapping)) {
        if (!stats[token]) stats[token] = { original, turns: [] };
        if (!stats[token].turns.includes(idx + 1)) stats[token].turns.push(idx + 1);
      }
    }
    const rows = Object.entries(stats)
      .map(([token, data]) => ({ token, original: data.original, turns: data.turns }))
      .sort((a, b) => a.token.localeCompare(b.token));
    return { rows, repeated: rows.filter((r) => r.turns.length > 1).length, total: rows.length };
  }, [chat]);

  const toApiRequest = (input: PipelineForm): PipelineRequest => ({
    ...input,
    language: input.language === "auto" ? null : input.language,
  });

  const callApi = async (path: ApiPath, body: PipelineRequest) => {
    setLoading(true);
    setStatus(`Processing ${path}…`);
    try {
      const res = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const text = await res.text();
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${text}`);
      return text;
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async () => {
    const content = draft.trim();
    if (!content) { setStatus("Write a message before sending"); return; }
    const payload: PipelineRequest = toApiRequest({ ...form, text: content });
    const t0 = Date.now();
    try {
      const text = await callApi("/api/run", payload);
      const elapsed = Date.now() - t0;
      const data = JSON.parse(text) as PipelineRunResponse;
      const turn: ChatTurn = { id: data.trace.trace_id, userText: content, response: data };
      setChat((prev) => [...prev, turn]);
      setSelectedTurnId(turn.id);
      setOutput(JSON.stringify(data, null, 2));
      setDraft("");
      const hint = elapsed < 200 ? " (fast response, possible cache)" : "";
      setStatus(
        data.steps.blocked
          ? `Blocked by policy: ${data.steps.block_reason ?? "policy decision"}`
          : `Completed in ${elapsed}ms${hint}`,
      );
    } catch (err) {
      setStatus(`Error: ${String(err)}`);
      setOutput(String(err));
    }
  };

  const clearContext = async () => {
    try {
      const payload: PipelineRequest = toApiRequest({ ...form, text: "_" });
      const text = await callApi("/api/forget", payload);
      const result = JSON.parse(text);
      setChat([]);
      setSelectedTurnId(null);
      setOutput("{}");
      setStatus(`Context cleared — ${result.removed} mappings removed`);
    } catch (err) {
      setStatus(`Error clearing: ${String(err)}`);
    }
  };

  return (
    <div className="min-h-screen bg-muted/40 p-5 font-sans">
      <AppHeader />

      <div className="rounded-xl border bg-card shadow-sm overflow-hidden">
        <div className="grid" style={{ gridTemplateColumns: "272px minmax(0,1fr) 320px" }}>
          <ConfigSidebar 
            form={form} 
            onChange={onChange} 
            continuity={continuity} 
            loading={loading} 
            setDraft={setDraft} 
          />

          <ChatArea 
            chat={chat} 
            draft={draft} 
            setDraft={setDraft} 
            sendMessage={sendMessage} 
            loading={loading} 
            status={status} 
            selectedTurnId={selectedTurnId} 
            setSelectedTurnId={setSelectedTurnId} 
            clearContext={clearContext} 
            chatBottomRef={chatBottomRef} 
          />

          <TraceSidebar 
            selectedTurn={selectedTurn} 
            continuity={continuity} 
          />
        </div>
      </div>

      <DebugPanel output={output} />
    </div>
  );
}

// --- ENTRY POINT ---
export default function Page() {
  const [unlocked, setUnlocked] = useState(false);

  useEffect(() => {
    if (sessionStorage.getItem(SESSION_KEY) === "1") {
      setUnlocked(true);
    }
  }, []);

  if (!unlocked) return <PasswordGate onUnlock={() => setUnlocked(true)} />;
  return <App />;
}
