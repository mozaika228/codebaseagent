"use client"

import ExperiencePanels from "../components/ExperiencePanels"
import LanguageSwitcher from "../components/LanguageSwitcher"
import RunPanel from "../components/RunPanel"
import { useI18n } from "../components/I18nProvider"

export default function HomePage() {
  const { t } = useI18n()

  return (
    <main className="container stack">
      <section className="card">
        <div className="hero-head">
          <h1>{t("app.title")}</h1>
          <LanguageSwitcher />
        </div>
        <p>{t("app.subtitle")}</p>
        <ul>
          <li>{t("hero.item1")}</li>
          <li>{t("hero.item2")}</li>
          <li>{t("hero.item3")}</li>
          <li>{t("hero.item4")}</li>
        </ul>
      </section>
      <section className="grid">
        <RunPanel />
        <ExperiencePanels />
      </section>
    </main>
  )
}
