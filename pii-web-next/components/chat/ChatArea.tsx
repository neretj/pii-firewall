"use client";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Send, Trash2, RefreshCw, User, Bot, AlertTriangle, Activity } from "lucide-react";
import type { PipelineRunResponse } from "@/lib/types";

type ChatTurn = {
  id: string;
  userText: string;
  response: PipelineRunResponse;
};

interface ChatAreaProps {
  chat: ChatTurn[];
  draft: string;
  setDraft: (text: string) => void;
  sendMessage: () => void;
  loading: boolean;
  status: string;
  selectedTurnId: string | null;
  setSelectedTurnId: (id: string) => void;
  clearContext: () => void;
  chatBottomRef: React.RefObject<HTMLDivElement>;
}

export function ChatArea({
  chat,
  draft,
  setDraft,
  sendMessage,
  loading,
  status,
  selectedTurnId,
  setSelectedTurnId,
  clearContext,
  chatBottomRef,
}: ChatAreaProps) {
  return (
    <div className="flex flex-col h-[780px]">
      <div className="flex-1 overflow-y-auto px-4 py-4 bg-muted/20 scroll-smooth [scrollbar-width:thin]">
        {chat.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="max-w-sm text-center px-6 py-10">
              <div className="w-14 h-14 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center text-2xl mx-auto mb-4">
                💬
              </div>
              <h3 className="font-bold text-base mb-2">Start a conversation</h3>
              <p className="text-sm text-muted-fg leading-relaxed mb-5">
                Send a message with personal information. The privacy firewall will:
              </p>
              <ol className="text-left space-y-3">
                {[
                  "Detect and anonymize PII (names, IDs, emails…)",
                  "Generate consistent tokens across messages",
                  "Rehydrate responses with original values",
                ].map((step, i) => (
                  <li key={i} className="flex items-start gap-3 text-sm text-foreground">
                    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-primary text-primary-fg flex items-center justify-center text-[10px] font-bold mt-0.5">
                      {i + 1}
                    </span>
                    {step}
                  </li>
                ))}
              </ol>
            </div>
          </div>
        ) : (
          <div className="space-y-2.5">
            {chat.map((turn, index) => {
              const isSelected = selectedTurnId === turn.id;
              const blocked = turn.response.steps.blocked;
              return (
                <article
                  key={turn.id}
                  onClick={() => setSelectedTurnId(turn.id)}
                  className={cn(
                    "rounded-lg border p-3 cursor-pointer transition-all",
                    isSelected
                      ? "border-primary bg-primary/5 shadow-sm ring-1 ring-primary/20"
                      : "border-transparent hover:border-border hover:bg-muted/30",
                  )}
                >
                  <div className="flex items-center gap-2 mb-2.5">
                    <span className="text-[10px] font-bold uppercase tracking-widest text-muted-fg">
                      Turn {index + 1}
                    </span>
                    <span
                      className={cn(
                        "w-1.5 h-1.5 rounded-full",
                        blocked ? "bg-destructive" : "bg-emerald-500",
                      )}
                    />
                  </div>
                  <div className="ml-auto max-w-[85%] rounded-lg bg-amber-50 border border-amber-200 px-3 py-2 mb-2">
                    <span className="block text-[10px] font-bold uppercase tracking-wider text-amber-800 mb-1 flex items-center gap-1">
                      <User className="w-3 h-3" /> You
                    </span>
                    <p className="text-sm text-foreground leading-relaxed">{turn.userText}</p>
                  </div>
                  <div
                    className={cn(
                      "mr-auto max-w-[85%] rounded-lg px-3 py-2 border",
                      blocked ? "bg-red-50 border-red-200" : "bg-teal-50 border-teal-200",
                    )}
                  >
                    <span
                      className={cn(
                        "block text-[10px] font-bold uppercase tracking-wider mb-1 flex items-center gap-1",
                        blocked ? "text-red-700" : "text-teal-700",
                      )}
                    >
                      {blocked ? (
                        <><AlertTriangle className="w-3 h-3" /> Blocked</>
                      ) : (
                        <><Bot className="w-3 h-3" /> Assistant</>
                      )}
                    </span>
                    <p className="text-sm text-foreground leading-relaxed">
                      {blocked
                        ? `🚫 ${turn.response.steps.block_reason ?? "policy decision"}`
                        : turn.response.steps.rehydrated_output ||
                          turn.response.steps.llm_response ||
                          "No response"}
                    </p>
                  </div>
                </article>
              );
            })}
            <div ref={chatBottomRef} />
          </div>
        )}
      </div>

      <div className="border-t bg-card p-4 space-y-3">
        <Textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
              e.preventDefault();
              sendMessage();
            }
          }}
          placeholder="Write your message… (Ctrl+Enter to send)"
          className="min-h-[72px] max-h-[120px] text-sm resize-none"
        />
        <div className="flex items-center gap-2">
          <Button onClick={sendMessage} disabled={loading} className="flex-1">
            {loading ? (
              <><RefreshCw className="w-4 h-4 animate-spin" /> Processing…</>
            ) : (
              <><Send className="w-4 h-4" /> Send message</>
            )}
          </Button>
          <Button variant="outline" onClick={clearContext} disabled={loading} title="Clear context">
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
        <div className="flex items-center gap-2 px-3 py-2 rounded-md bg-muted/60 border text-xs text-muted-fg">
          <Activity className="w-3.5 h-3.5 flex-shrink-0" />
          <span>{status}</span>
        </div>
      </div>
    </div>
  );
}
