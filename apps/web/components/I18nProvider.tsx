"use client"

import { createContext, ReactNode, useContext, useEffect, useMemo, useState } from "react"

import { Locale, translations } from "../i18n/translations"

type I18nContextType = {
  locale: Locale
  setLocale: (locale: Locale) => void
  t: (key: string) => string
}

const STORAGE_KEY = "codebase-agent-locale"

const I18nContext = createContext<I18nContextType | null>(null)

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState<Locale>("en")

  useEffect(() => {
    const saved = window.localStorage.getItem(STORAGE_KEY)
    if (saved === "en" || saved === "ru" || saved === "kk") {
      setLocale(saved)
      return
    }
    const nav = navigator.language.toLowerCase()
    if (nav.startsWith("ru")) setLocale("ru")
    if (nav.startsWith("kk")) setLocale("kk")
  }, [])

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, locale)
  }, [locale])

  const value = useMemo<I18nContextType>(() => ({
    locale,
    setLocale,
    t: (key: string) => translations[locale][key] ?? translations.en[key] ?? key
  }), [locale])

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export function useI18n(): I18nContextType {
  const context = useContext(I18nContext)
  if (!context) {
    throw new Error("useI18n must be used inside I18nProvider")
  }
  return context
}
