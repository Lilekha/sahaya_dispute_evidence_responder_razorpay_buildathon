import { createContext, useContext, useEffect, useMemo, useState } from 'react'

const DataContext = createContext(null)

export function DataProvider({ children }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedMerchant, setSelectedMerchant] = useState(null)

  useEffect(() => {
    let cancelled = false

    fetch('/dashboard_data.json')
      .then((res) => {
        if (!res.ok) {
          throw new Error(`Failed to load dashboard_data.json (${res.status})`)
        }
        return res.json()
      })
      .then((json) => {
        if (cancelled) return
        setData(json)
        setSelectedMerchant(
          json.merchants.find((m) => m.demo_priority === 1) ?? json.merchants[0] ?? null,
        )
        console.log(
          `dashboard_data.json loaded: ${json.merchants.length} merchants, ${json.disputes.length} disputes`,
        )
      })
      .catch((err) => {
        if (!cancelled) setError(err)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [])

  const merchantDisputes = useMemo(() => {
    if (!data || !selectedMerchant) return []
    return data.disputes.filter((d) => d.merchant_id === selectedMerchant.merchant_id)
  }, [data, selectedMerchant])

  const metrics = data?.model_metrics ?? null

  const value = {
    data,
    loading,
    error,
    selectedMerchant,
    setSelectedMerchant,
    merchantDisputes,
    metrics,
  }

  return <DataContext.Provider value={value}>{children}</DataContext.Provider>
}

export function useData() {
  const ctx = useContext(DataContext)
  if (ctx === null) {
    throw new Error('useData must be used within a DataProvider')
  }
  return ctx
}
