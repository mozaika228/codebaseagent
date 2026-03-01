import "./globals.css"
import type { Metadata } from "next"
import { ReactNode } from "react"

import AppProviders from "../components/AppProviders"

export const metadata: Metadata = {
  title: "Codebase Agent",
  description: "AI agent for codebase understanding and safe refactor drafts"
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  )
}
