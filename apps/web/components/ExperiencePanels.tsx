"use client"

import { useMemo, useState } from "react"

import { useI18n } from "./I18nProvider"

type Message = { role: "user" | "assistant"; text: string }
type DocItem = { name: string; size: number }

export default function ExperiencePanels() {
  const { t } = useI18n()
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", text: "Ready. Ask about architecture, hotspots, or risk." }
  ])
  const [input, setInput] = useState("")
  const [docs, setDocs] = useState<DocItem[]>([])

  const summary = useMemo(() => {
    return {
      topModule: "apps/api/app/main.py",
      confidence: "0.87",
      risk: "low"
    }
  }, [])

  function sendMessage() {
    if (!input.trim()) return
    const userText = input.trim()
    setMessages((prev) => [
      ...prev,
      { role: "user", text: userText },
      { role: "assistant", text: `Draft answer: focus on ${summary.topModule} and test before merge.` }
    ])
    setInput("")
  }

  function onUpload(files: FileList | null) {
    if (!files) return
    const parsed = Array.from(files).map((file) => ({ name: file.name, size: file.size }))
    setDocs((prev) => [...prev, ...parsed])
  }

  return (
    <section className="card">
      <h2>{t("workspace.title")}</h2>
      <p>{t("workspace.subtitle")}</p>
      <div className="workspace-grid">
        <div className="panel">
          <h3>{t("workspace.chat")}</h3>
          <div className="chat-box">
            {messages.map((message, index) => (
              <p key={`${message.role}-${index}`} className={`msg ${message.role}`}>
                <strong>{message.role}:</strong> {message.text}
              </p>
            ))}
          </div>
          <div className="row">
            <input
              className="input"
              placeholder={t("workspace.askPlaceholder")}
              value={input}
              onChange={(e) => setInput(e.target.value)}
            />
            <button className="button" onClick={sendMessage}>{t("workspace.send")}</button>
          </div>
        </div>

        <div className="panel">
          <h3>{t("workspace.documents")}</h3>
          <input type="file" multiple onChange={(e) => onUpload(e.target.files)} />
          <ul>
            {docs.length === 0 && <li>{t("workspace.noFiles")}</li>}
            {docs.map((doc, index) => (
              <li key={`${doc.name}-${index}`}>
                <code>{doc.name}</code> ({doc.size} bytes)
              </li>
            ))}
          </ul>
        </div>

        <div className="panel">
          <h3>{t("workspace.result")}</h3>
          <p><strong>{t("workspace.topModule")}:</strong> <code>{summary.topModule}</code></p>
          <p><strong>{t("workspace.confidence")}:</strong> {summary.confidence}</p>
          <p><strong>{t("runner.risk")}:</strong> {summary.risk}</p>
        </div>

        <div className="panel">
          <h3>{t("workspace.compare")}</h3>
          <table className="compare-table">
            <thead>
              <tr>
                <th>{t("workspace.model")}</th>
                <th>{t("workspace.latency")}</th>
                <th>{t("workspace.hRisk")}</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Local (Ollama)</td>
                <td>1.8s</td>
                <td>medium</td>
              </tr>
              <tr>
                <td>Cloud baseline</td>
                <td>1.1s</td>
                <td>low</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>
  )
}
