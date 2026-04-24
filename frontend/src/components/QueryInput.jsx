import React, { useState, useEffect } from 'react'

export default function QueryInput({ onSubmit, loading, value, onChange }) {
  const [inputValue, setInputValue] = useState(value || '')
  const [useRag, setUseRag] = useState(true)

  useEffect(() => {
    setInputValue(value || '')
  }, [value])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (inputValue.trim() && !loading) {
      onSubmit(inputValue, useRag)
    }
  }

  const exampleQueries = [
    "My order never arrived and I need a refund immediately!",
    "The app keeps crashing when I try to login",
    "How do I update my billing information?",
    "I was charged twice for my subscription, help!",
    "Service has been down for 3 hours, very frustrating"
  ]

  const handleExample = (q) => {
    setInputValue(q)
    onChange(q)
  }

  return (
    <div>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <Search className="w-5 h-5 text-slate-400" />
          </div>
          <input
            type="text"
            value={inputValue}
            onChange={(e) => {
              setInputValue(e.target.value)
              onChange(e.target.value)
            }}
            placeholder="Enter your customer support query..."
            className="w-full pl-12 pr-32 py-4 text-lg border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm bg-white"
            disabled={loading}
          />
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center gap-2">
            <button
              type="button"
              onClick={() => setUseRag(!useRag)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                useRag
                  ? 'bg-blue-100 text-blue-700 border border-blue-300'
                  : 'bg-slate-100 text-slate-600 border border-slate-300'
              }`}
              title={useRag ? "RAG enabled - will retrieve similar tickets" : "RAG disabled - LLM only"}
            >
              {useRag ? 'RAG ON' : 'LLM Only'}
            </button>
            <button
              type="submit"
              disabled={!inputValue.trim() || loading}
              className="px-6 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium rounded-lg hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Analyzing...
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  Analyze
                  <Search className="w-4 h-4" />
                </span>
              )}
            </button>
          </div>
        </div>
      </form>

      {/* Example queries */}
      <div className="flex flex-wrap gap-2 mt-4">
        <span className="text-sm text-slate-500 mr-2 py-1">Try:</span>
        {exampleQueries.map((q, i) => (
          <button
            key={i}
            onClick={() => handleExample(q)}
            disabled={loading}
            className="px-3 py-1 bg-slate-100 hover:bg-slate-200 text-slate-600 text-sm rounded-full transition-colors disabled:opacity-50"
          >
            {q.length > 50 ? q.substring(0, 50) + '...' : q}
          </button>
        ))}
      </div>
    </div>
  )
}
