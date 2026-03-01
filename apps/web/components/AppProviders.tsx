"use client"

import type { ReactNode } from "react"

import { I18nProvider } from "./I18nProvider"

export default function AppProviders({ children }: { children: ReactNode }) {
  return <I18nProvider>{children}</I18nProvider>
}
