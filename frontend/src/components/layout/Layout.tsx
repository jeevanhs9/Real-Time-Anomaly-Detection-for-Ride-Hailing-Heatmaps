import React from 'react'
import Header from './Header'

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="app-shell">
      <Header />
      <main className="dashboard-main">
        {children}
      </main>
    </div>
  )
}
