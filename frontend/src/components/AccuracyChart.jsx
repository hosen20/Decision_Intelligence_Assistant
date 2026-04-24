import React from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend
} from 'recharts'

export default function AccuracyChart({ data }) {
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-slate-200 rounded-lg shadow-lg">
          <p className="font-semibold text-slate-800 mb-1">{label}</p>
          <p style={{ color: payload[0].color }} className="text-sm font-bold">
            Accuracy: {(payload[0].value * 100).toFixed(1)}%
          </p>
        </div>
      )
    }
    return null
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 5, right: 30, left: 80, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={true} vertical={false} />
        <XAxis
          type="number"
          domain={[0, 1]}
          tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
          tick={{ fill: '#64748b' }}
        />
        <YAxis
          type="category"
          dataKey="name"
          tick={{ fill: '#64748b' }}
          width={80}
        />
        <Tooltip content={<CustomTooltip />} />
        <Bar
          dataKey="accuracy"
          name="Accuracy"
          fill="#10b981"
          radius={[0, 4, 4, 0]}
        />
      </BarChart>
    </ResponsiveContainer>
  )
}
