import { createContext, useContext, useState } from 'react'
import { issues as initialIssues } from '../data/issues'

const IssuesContext = createContext(null)

export function IssuesProvider({ children }) {
  const [issues, setIssues] = useState(() =>
    initialIssues.map((i) => ({ ...i, history: [...(i.history || [])] }))
  )

  function updateIssue(id, updater) {
    setIssues((prev) => prev.map((i) => (i.id === id ? { ...i, ...updater(i) } : i)))
  }

  return <IssuesContext.Provider value={{ issues, updateIssue }}>{children}</IssuesContext.Provider>
}

export function useIssues() {
  return useContext(IssuesContext)
}
