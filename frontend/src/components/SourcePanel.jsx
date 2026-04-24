import React from 'react'
import { FileText, Tag, Calendar } from 'lucide-react'

export default function SourcePanel({ tickets }) {
  if (!tickets || tickets.length === 0) {
    return (
      <div className="text-center py-8 bg-white rounded-xl border border-slate-200">
        <Search className="w-12 h-12 text-slate-300 mx-auto mb-3" />
        <p className="text-slate-500">No source tickets retrieved</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {tickets.map((ticket, idx) => (
        <div
          key={idx}
          className="bg-white rounded-xl border border-slate-200 p-4 hover:shadow-md transition-shadow"
        >
          <div className="flex items-start justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-100 text-blue-700 text-xs font-bold">
                {idx + 1}
              </span>
              <span className="flex items-center gap-1 text-xs text-slate-500">
                <FileText className="w-3 h-3" />
                {ticket.tweet_id || `Ticket-${idx + 1}`}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span
                className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                  ticket.is_urgent
                    ? 'bg-red-100 text-red-700'
                    : 'bg-green-100 text-green-700'
                }`}
              >
                {ticket.label || (ticket.is_urgent ? 'urgent' : 'normal')}
              </span>
              <span className="text-xs px-2 py-0.5 bg-slate-100 rounded-full text-slate-600">
                {((ticket.similarity || 0) * 100).toFixed(1)}% match
              </span>
            </div>
          </div>

          <p className="text-slate-700 text-sm leading-relaxed mb-3">
            {ticket.text}
          </p>

          {/* Additional metadata */}
          <div className="flex items-center gap-4 text-xs text-slate-400">
            {ticket.is_urgent !== undefined && (
              <span className="flex items-center gap-1">
                <Tag className="w-3 h-3" />
                {ticket.is_urgent ? 'Priority' : 'Normal'}
              </span>
            )}
            {ticket.created_at && (
              <span className="flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                {new Date(ticket.created_at).toLocaleDateString()}
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
