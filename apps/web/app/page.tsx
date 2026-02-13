import RunPanel from "../components/RunPanel"

export default function HomePage() {
  return (
    <main className="container grid">
      <section className="card">
        <h1>Codebase Agent</h1>
        <p>
          Analyze repository architecture, propose low-risk refactors,
          and draft pull requests with guardrails.
        </p>
        <ul>
          <li>Architect summary + hotspots</li>
          <li>Scoped refactor proposal</li>
          <li>Patch + test-gated PR draft</li>
        </ul>
      </section>
      <RunPanel />
    </main>
  )
}