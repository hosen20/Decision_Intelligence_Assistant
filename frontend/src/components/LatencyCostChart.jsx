import React from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  LineChart, Line, ComposedChart, Area
} from 'recharts'

export default function LatencyCostChart({ data }) {
  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-slate-200 rounded-lg shadow-lg">
          <p className="font-semibold text-slate-800 mb-2">{label}</p>
          {payload.map((entry, index) => (
            <p key={index} style={{ color: entry.color }} className="text-sm">
              {entry.name}: {entry.name === 'Cost' ? `$${entry.value.toFixed(6)}` : `${entry.value.toFixed(1)}ms`}
            </p>
          ))}
        </div>
      )
    }
    return null
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <ComposedChart
        data={data}
        margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey="name" tick={{ fill: '#64748b' }} />
        <YAxis
          yAxisId="left"
          orientation="left"
          tick={{ fill: '#64748b' }}
          label={{ value: 'Latency (ms)', angle: -90, position: 'insideLeft', fill: '#64748b' }}
        />
        <YAxis
          yAxisId="right"
          orientation="right"
          tick={{ fill: '#64748b' }}
          label={{ value: 'Cost ($)', angle: 90, position: 'insideRight', fill: '#64748b' }}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend />
        <Bar
          yAxisId="left"
          dataKey="latency"
          name="Latency"
          fill="#3b82f6"
          radius={[4, 4, 0, 0]}
          barSize={30}
        />
        <Line
          yAxisId="right"
          type="monotone"
          dataKey="cost"
          name="Cost"
          stroke="#ef4444"
          strokeWidth={3}
          dot={{ fill: '#ef4444', r: 5 }}
          activeDot={{ r: 7 }}
        />
      </ComposedChart>
    </ResponsiveContainer>
  )
}
