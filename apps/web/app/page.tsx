import ExperiencePanels from "../components/ExperiencePanels"
import RunPanel from "../components/RunPanel"

export default function HomePage() {
  return (
    <main className="container stack">
      <section className="card">
        <h1>Codebase Agent</h1>
        <p>
          Analyze repository architecture, compare model answers, and generate safe draft PRs with test gates.
        </p>
        <ul>
          <li>Architect summary + hotspots</li>
          <li>RAG-style chat and doc ingestion workspace</li>
          <li>Scoped refactor proposal and run trace</li>
          <li>Patch + test-gated PR draft</li>
        </ul>
      </section>
      <section className="grid">
        <RunPanel />
        <ExperiencePanels />
      </section>
    </main>
  )
}
