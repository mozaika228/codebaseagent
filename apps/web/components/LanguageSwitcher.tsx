"use client"

import { useI18n } from "./I18nProvider"

export default function LanguageSwitcher() {
  const { locale, setLocale, t } = useI18n()

  return (
    <div className="lang-switcher">
      <button className={`lang-btn ${locale === "kk" ? "active" : ""}`} onClick={() => setLocale("kk")}>{t("lang.kk")}</button>
      <button className={`lang-btn ${locale === "ru" ? "active" : ""}`} onClick={() => setLocale("ru")}>{t("lang.ru")}</button>
      <button className={`lang-btn ${locale === "en" ? "active" : ""}`} onClick={() => setLocale("en")}>{t("lang.en")}</button>
    </div>
  )
}
