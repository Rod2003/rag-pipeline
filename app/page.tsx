"use client"

import { useEffect, useRef, useState } from "react"
import ReactMarkdown from "react-markdown"
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
import { Badge } from "@/components/ui/badge"
import * as AccordionPrimitive from "@radix-ui/react-accordion"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
} from "@/components/ui/accordion"
import { ChevronRightIcon, Trash2Icon } from "lucide-react"
import { cn } from "@/lib/utils"

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

type Source = { source_file: string; page: number }

type Message = {
  role: "user" | "assistant"
  content: string
  sources?: Source[]
}

function SourcesList({ sources }: { sources: Source[] }) {
  const byFile = sources.reduce<Record<string, number[]>>((acc, s) => {
    const file = s.source_file ?? "Unknown"
    if (!acc[file]) acc[file] = []
    const page = s.page ?? 0
    if (!acc[file].includes(page)) acc[file].push(page)
    return acc
  }, {})
  Object.keys(byFile).forEach((f) => byFile[f].sort((a, b) => a - b))
  const entries = Object.entries(byFile)

  return (
    <Accordion type="single" collapsible className="w-full">
      {entries.map(([file, pages]) => (
        <AccordionItem
          key={file}
          value={file}
          className="border-0 [&[data-state=open]>*:last-child]:pb-0"
        >
          <AccordionPrimitive.Header className="flex">
            <AccordionPrimitive.Trigger className="flex flex-1 items-center gap-2 py-2 text-left outline-none hover:underline focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded [&[data-state=open]>svg]:rotate-90">
              <ChevronRightIcon className="size-3.5 shrink-0 text-muted-foreground transition-transform duration-200" />
              <span className="text-xs font-medium text-foreground/90">
                {file}
              </span>
            </AccordionPrimitive.Trigger>
          </AccordionPrimitive.Header>
          <AccordionContent className="pb-2 pt-0">
            <div className="flex flex-wrap gap-1 pl-5">
              {pages.map((p) => (
                <Badge
                  key={`${file}-${p}`}
                  variant="secondary"
                  className="text-xs"
                >
                  p.{p}
                </Badge>
              ))}
            </div>
          </AccordionContent>
        </AccordionItem>
      ))}
    </Accordion>
  )
}

export default function Home() {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [queryLoading, setQueryLoading] = useState(false)
  const [ingestLoading, setIngestLoading] = useState(false)
  const [ingestStatus, setIngestStatus] = useState<string | null>(null)
  const [ingestedFiles, setIngestedFiles] = useState<string[]>([])
  const [removingFile, setRemovingFile] = useState<string | null>(null)

  const fetchFiles = async () => {
    try {
      const res = await fetch(`${API_BASE}/files`)
      if (res.ok) {
        const data = await res.json()
        setIngestedFiles(data.files ?? [])
      }
    } catch {
      setIngestedFiles([])
    }
  }

  useEffect(() => {
    fetchFiles()
  }, [])

  const hasIngested = ingestedFiles.length > 0

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
      await fetchFiles()
      fileInput.value = ""
    } catch (e) {
      setIngestStatus(
        e instanceof Error ? e.message : "Failed to ingest files."
      )
    } finally {
      setIngestLoading(false)
    }
  }

  const handleRemoveFile = async (filename: string) => {
    setRemovingFile(filename)
    try {
      const res = await fetch(`${API_BASE}/files/${encodeURIComponent(filename)}`, {
        method: "DELETE",
      })
      if (res.ok) {
        await fetchFiles()
      }
    } finally {
      setRemovingFile(null)
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
      <header className="flex items-center justify-between gap-4 border-b px-6 py-4">
        <div>
          <h1 className="text-xl font-semibold">RAG Pipeline</h1>
          <p className="text-sm text-muted-foreground">
            Upload PDFs and ask questions about your documents
          </p>
        </div>
        {(hasIngested || messages.length > 0) && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => setMessages([])}
          >
            New Chat
          </Button>
        )}
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
            {ingestedFiles.length > 0 && (
              <div className="space-y-1">
                <span className="text-xs font-medium text-muted-foreground">
                  Ingested files
                </span>
                <ul className="space-y-1">
                  {ingestedFiles.map((file) => (
                    <li
                      key={file}
                      className="group flex items-center justify-between gap-2 rounded-md px-2 py-1.5 text-sm hover:bg-muted/50"
                    >
                      <span className="truncate text-foreground/90">{file}</span>
                      <button
                        type="button"
                        onClick={() => handleRemoveFile(file)}
                        disabled={removingFile === file}
                        className="shrink-0 rounded p-1 text-muted-foreground opacity-0 transition-opacity hover:bg-destructive/10 hover:text-destructive group-hover:opacity-100 focus:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
                        aria-label={`Remove ${file}`}
                      >
                        <Trash2Icon className="size-3.5" />
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
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
                    {msg.role === "user" ? (
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    ) : (
                      <div className="markdown-content [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5 [&_p]:my-2 [&_p:first-child]:mt-0 [&_p:last-child]:mb-0 [&_strong]:font-semibold [&_code]:rounded [&_code]:bg-muted [&_code]:px-1 [&_code]:py-0.5 [&_code]:text-xs [&_pre]:overflow-x-auto [&_pre]:rounded-md [&_pre]:bg-muted [&_pre]:p-3 [&_pre]:text-xs">
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                      </div>
                    )}
                    {msg.role === "assistant" &&
                      msg.sources &&
                      msg.sources.length > 0 && (
                        <div className="mt-3 space-y-2 border-t border-border/50 pt-3">
                          <span className="text-xs font-medium text-muted-foreground">
                            Sources
                          </span>
                          <SourcesList sources={msg.sources} />
                        </div>
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
