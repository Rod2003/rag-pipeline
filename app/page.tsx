"use client"

import { useRef, useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

type Message = {
  role: "user" | "assistant"
  content: string
  sources?: { source_file: string; page: number }[]
}

export default function Home() {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [queryLoading, setQueryLoading] = useState(false)
  const [ingestLoading, setIngestLoading] = useState(false)
  const [ingestStatus, setIngestStatus] = useState<string | null>(null)

  const handleIngest = async () => {
    const fileInput = fileInputRef.current
    if (!fileInput?.files?.length) {
      setIngestStatus("Please select one or more PDF files.")
      return
    }
    setIngestLoading(true)
    setIngestStatus(null)
    try {
      const formData = new FormData()
      for (const file of fileInput.files) {
        formData.append("files", file)
      }
      const res = await fetch(`${API_BASE}/ingest`, {
        method: "POST",
        body: formData,
      })
      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.detail ?? "Ingest failed")
      }
      setIngestStatus(
        `Ingested ${data.chunks_created} chunks from ${data.files?.length ?? 0} file(s).`
      )
      fileInput.value = ""
    } catch (e) {
      setIngestStatus(
        e instanceof Error ? e.message : "Failed to ingest files."
      )
    } finally {
      setIngestLoading(false)
    }
  }

  const handleQuery = async () => {
    const question = input.trim()
    if (!question || queryLoading) return

    setMessages((prev) => [...prev, { role: "user", content: question }])
    setInput("")
    setQueryLoading(true)

    try {
      const res = await fetch(`${API_BASE}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      })
      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.detail ?? "Query failed")
      }
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.answer ?? "",
          sources: data.sources,
        },
      ])
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            e instanceof Error ? e.message : "Something went wrong. Please try again.",
        },
      ])
    } finally {
      setQueryLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="border-b px-6 py-4">
        <h1 className="text-xl font-semibold">RAG Pipeline</h1>
        <p className="text-sm text-muted-foreground">
          Upload PDFs and ask questions about your documents
        </p>
      </header>

      <main className="flex flex-1 flex-col gap-6 overflow-hidden p-6 md:flex-row">
        <Card className="flex h-fit flex-shrink-0 flex-col md:w-80">
          <CardHeader>
            <CardTitle>Upload PDFs</CardTitle>
            <CardDescription>
              Ingest one or more PDF files into the knowledge base
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div>
              <Label htmlFor="pdf-upload">Select PDF files</Label>
              <input
                ref={fileInputRef}
                id="pdf-upload"
                type="file"
                accept=".pdf"
                multiple
                className="mt-2 block w-full text-sm text-muted-foreground file:mr-4 file:rounded-md file:border-0 file:bg-primary file:px-4 file:py-2 file:text-sm file:font-medium file:text-primary-foreground file:hover:bg-primary/90"
              />
            </div>
            <Button
              onClick={handleIngest}
              disabled={ingestLoading}
            >
              {ingestLoading ? "Ingesting…" : "Ingest PDFs"}
            </Button>
            {ingestStatus && (
              <p
                className={cn(
                  "text-sm",
                  ingestStatus.startsWith("Ingested")
                    ? "text-muted-foreground"
                    : "text-destructive"
                )}
              >
                {ingestStatus}
              </p>
            )}
          </CardContent>
        </Card>

        <Card className="flex flex-1 flex-col overflow-hidden">
          <CardHeader>
            <CardTitle>Chat</CardTitle>
            <CardDescription>
              Ask questions about your ingested documents
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-1 flex-col gap-4 overflow-hidden">
            <ScrollArea className="flex-1 pr-4">
              <div className="flex flex-col gap-4">
                {messages.length === 0 && (
                  <p className="text-sm text-muted-foreground">
                    No messages yet. Upload PDFs first, then ask a question.
                  </p>
                )}
                {messages.map((msg, i) => (
                  <div
                    key={i}
                    className={cn(
                      "max-w-[85%] rounded-lg px-4 py-3 text-sm",
                      msg.role === "user"
                        ? "ml-auto bg-primary text-primary-foreground"
                        : "bg-muted"
                    )}
                  >
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                    {msg.role === "assistant" &&
                      msg.sources &&
                      msg.sources.length > 0 && (
                        <p className="mt-2 text-xs text-muted-foreground">
                          Sources:{" "}
                          {msg.sources
                            .map(
                              (s) =>
                                `${s.source_file ?? "?"} p.${s.page ?? "?"}`
                            )
                            .join(", ")}
                        </p>
                      )}
                  </div>
                ))}
                {queryLoading && (
                  <div className="max-w-[85%] rounded-lg bg-muted px-4 py-3 text-sm">
                    <p className="animate-pulse text-muted-foreground">
                      Thinking…
                    </p>
                  </div>
                )}
              </div>
            </ScrollArea>

            <div className="flex gap-2">
              <Textarea
                placeholder="Ask a question about your documents…"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault()
                    handleQuery()
                  }
                }}
                rows={2}
                className="min-h-0 resize-none"
                disabled={queryLoading}
              />
              <Button
                onClick={handleQuery}
                disabled={queryLoading || !input.trim()}
                className="self-end"
              >
                Send
              </Button>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
