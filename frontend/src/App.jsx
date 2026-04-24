import React, { useState, useCallback } from 'react'
import axios from 'axios'
import {
  Search,
  Brain,
  Cpu,
  BarChart3,
  Clock,
  DollarSign,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Sparkles,
  Loader2
} from 'lucide-react'
import QueryInput from './components/QueryInput'
import AnswerDisplay from './components/AnswerDisplay'
import SourcePanel from './components/SourcePanel'
import ComparisonSection from './components/ComparisonSection'
import API_BASE from './config'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000
})

function App() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)

  const handleSubmit = async (userQuery, useRag = true) => {
    if (!userQuery.trim()) return

    setLoading(true)
    setError(null)
    setQuery(userQuery)

    try {
      const response = await api.post('/compare/full', {
        query: userQuery,
        use_rag: useRag,
        top_k: 5
      })
      setResults(response.data)
    } catch (err) {
      console.error('API Error:', err)
      setError(err.response?.data?.detail || 'An error occurred. Please try again.')
      setResults(null)
    } finally {
      setLoading(false)
    }
  }

  const handleClear = () => {
    setQuery('')
    setResults(null)
    setError(null)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg">
                <Brain className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  Decision Intelligence Assistant
                </h1>
                <p className="text-sm text-slate-500">
                  Compare RAG, LLM, ML, and Zero-Shot Approaches
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 text-sm text-slate-500">
              <Cpu className="w-4 h-4" />
              <span>Powered by GROQ & Weaviate</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
        {/* Query Section */}
        <div className="mb-8">
          <QueryInput
            onSubmit={handleSubmit}
            loading={loading}
            value={query}
            onChange={setQuery}
          />
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-red-800">Error</h3>
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-12">
            <Loader2 className="w-12 h-12 text-blue-500 animate-spin mb-4" />
            <p className="text-slate-600">Analyzing query and comparing models...</p>
          </div>
        )}

        {/* Results Section */}
        {results && !loading && (
          <div className="space-y-6">
            {/* Answer Display */}
            <section>
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-purple-500" />
                Generated Answers
              </h2>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <AnswerDisplay
                  title="RAG Answer"
                  subtitle="(with retrieved context)"
                  answer={results.rag.answer}
                  latency={results.rag.latency_ms}
                  cost={results.rag.cost_usd}
                  icon={<Brain className="w-5 h-5" />}
                  color="blue"
                />
                <AnswerDisplay
                  title="Pure LLM Answer"
                  subtitle="(no context)"
                  answer={results.llm_only.answer}
                  latency={results.llm_only.latency_ms}
                  cost={results.llm_only.cost_usd}
                  icon={<Cpu className="w-5 h-5" />}
                  color="purple"
                />
              </div>
            </section>

            {/* Source Panel */}
            {results.rag.retrieved_tickets && results.rag.retrieved_tickets.length > 0 && (
              <section>
                <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                  <Search className="w-5 h-5 text-green-500" />
                  Retrieved Source Tickets
                </h2>
                <SourcePanel tickets={results.rag.retrieved_tickets} />
              </section>
            )}

            {/* Comparison Section */}
            <section>
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-orange-500" />
                Four-Way Comparison
              </h2>
              <ComparisonSection
                rag={results.rag}
                llm={results.llm_only}
                ml={results.ml}
                llmPriority={results.llm_priority}
                metrics={results.aggregated_metrics}
              />
            </section>

            {/* Clear Button */}
            <div className="flex justify-center pt-4">
              <button
                onClick={handleClear}
                className="px-6 py-2 bg-slate-200 hover:bg-slate-300 text-slate-700 font-medium rounded-lg transition-colors"
              >
                Clear Results
              </button>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!results && !loading && !error && (
          <div className="text-center py-16">
            <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-blue-100 mb-6">
              <Brain className="w-12 h-12 text-blue-500" />
            </div>
            <h2 className="text-2xl font-bold text-slate-700 mb-2">Decision Intelligence Assistant</h2>
            <p className="text-slate-500 max-w-md mx-auto mb-8">
              CompareRAG, LLM, ML, and Zero-Shot predictions for customer support tickets.
              Enter your query to see how different approaches perform.
            </p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
              <div className="p-4 bg-white rounded-lg shadow-sm border border-slate-200">
                <div className="text-blue-500 mb-2">
                  <Search className="w-6 h-6" />
                </div>
                <h3 className="font-semibold text-slate-800">RAG</h3>
                <p className="text-sm text-slate-500">Context-aware with retrieval</p>
              </div>
              <div className="p-4 bg-white rounded-lg shadow-sm border border-slate-200">
                <div className="text-purple-500 mb-2">
                  <Cpu className="w-6 h-6" />
                </div>
                <h3 className="font-semibold text-slate-800">Pure LLM</h3>
                <p className="text-sm text-slate-500">General knowledge only</p>
              </div>
              <div className="p-4 bg-white rounded-lg shadow-sm border border-slate-200">
                <div className="text-green-500 mb-2">
                  <BarChart3 className="w-6 h-6" />
                </div>
                <h3 className="font-semibold text-slate-800">ML Model</h3>
                <p className="text-sm text-slate-500">Fast, low-cost predictor</p>
              </div>
              <div className="p-4 bg-white rounded-lg shadow-sm border border-slate-200">
                <div className="text-orange-500 mb-2">
                  <Sparkles className="w-6 h-6" />
                </div>
                <h3 className="font-semibold text-slate-800">Zero-Shot LLM</h3>
                <p className="text-sm text-slate-500">Direct classification</p>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-16 border-t border-slate-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
          <p className="text-center text-slate-500 text-sm">
            Decision Intelligence Assistant - Week 3 Project - AIE Bootcamp
          </p>
        </div>
      </footer>
    </div>
  )
}

export default App
