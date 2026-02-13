"use client"

import { useState } from "react"

type ImportResponse = {
  repo_id: string
  status: string
}

type AnalysisResponse = {
  analysis_id: string
  status: string
}

export default function RunPanel() {
  const [repoUrl, setRepoUrl] = useState("https://github.com/org/repo")
  const [repoId, setRepoId] = useState("")
  const [analysisId, setAnalysisId] = useState("")
  const [status, setStatus] = useState("idle")

  const apiBase = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000"

  async function handleImport() {
    setStatus("importing")
    const res = await fetch(`${apiBase}/repos/import`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ repo_url: repoUrl, branch: "main" })
    })
    const data = (await res.json()) as ImportResponse
    setRepoId(data.repo_id)
    setStatus(`repo imported: ${data.repo_id}`)
  }

  async function handleAnalysis() {
    if (!repoId) return
    setStatus("analysis running")
    const res = await fetch(`${apiBase}/analysis/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ repo_id: repoId, commit_sha: "HEAD" })
    })
    const data = (await res.json()) as AnalysisResponse
    setAnalysisId(data.analysis_id)
    setStatus(`analysis started: ${data.analysis_id}`)
  }

  return (
    <div className="card">
      <h2>MVP Runner</h2>
      <p>Import a repository and trigger architecture analysis.</p>
      <div style={{ display: "grid", gap: 12 }}>
        <input className="input" value={repoUrl} onChange={(e) => setRepoUrl(e.target.value)} />
        <button className="button" onClick={handleImport}>Import Repository</button>
        <button className="button" onClick={handleAnalysis} disabled={!repoId}>Run Analysis</button>
      </div>
      <p><strong>Status:</strong> {status}</p>
      <p><strong>Repo ID:</strong> {repoId || "-"}</p>
      <p><strong>Analysis ID:</strong> {analysisId || "-"}</p>
    </div>
  )
}