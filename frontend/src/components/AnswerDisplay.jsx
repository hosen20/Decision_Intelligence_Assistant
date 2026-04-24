import React from 'react'
import { Clock, DollarSign, CheckCircle, XCircle } from 'lucide-react'

export default function AnswerDisplay({ title, subtitle, answer, latency, cost, icon, color }) {
  const colorClasses = {
    blue: 'bg-blue-50 border-blue-200 text-blue-900',
    purple: 'bg-purple-50 border-purple-200 text-purple-900',
    green: 'bg-green-50 border-green-200 text-green-900',
    orange: 'bg-orange-50 border-orange-200 text-orange-900',
  }

  const metricColors = {
    blue: 'text-blue-600',
    purple: 'text-purple-600',
    green: 'text-green-600',
    orange: 'text-orange-600',
  }

  return (
    <div className={`rounded-xl border-2 ${colorClasses[color]} p-6 bg-white shadow-sm`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-bold flex items-center gap-2">
            {icon}
            {title}
          </h3>
          <p className="text-sm opacity-75">{subtitle}</p>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-1" title="Latency">
            <Clock className="w-4 h-4" />
            <span className="font-medium">{latency.toFixed(1)}ms</span>
          </div>
          <div className="flex items-center gap-1" title="Cost">
            <DollarSign className="w-4 h-4" />
            <span className="font-medium">${cost.toFixed(6)}</span>
          </div>
        </div>
      </div>

      {/* Answer */}
      <div className="prose prose-sm max-w-none">
        <p className="whitespace-pre-wrap leading-relaxed">{answer}</p>
      </div>

      {/* Simplicity - latency and cost can be visually compared easily */}
      <div className="mt-4 pt-4 border-t border-current opacity-20">
        <div className="flex justify-between text-sm">
          <span>Efficient: {latency < 1000 ? '✓' : '⚠'}</span>
          <span>Cost-effective: {cost < 0.01 ? '✓' : '⚠'}</span>
        </div>
      </div>
    </div>
  )
}
