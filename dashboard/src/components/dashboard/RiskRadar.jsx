import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer } from 'recharts'

export default function RiskRadar({ data }) {
  const chartData = data || [
    { subject: 'Idle Time',   value: 0 },
    { subject: 'Paste Events',value: 0 },
    { subject: 'Mouse Jigg.', value: 0 },
    { subject: 'Burst Typing',value: 0 },
    { subject: 'Off Hours',   value: 0 },
    { subject: 'Anomalies',   value: 0 },
  ]

  return (
    <div className="card p-5">
      <h3 className="section-title mb-4">Risk Distribution</h3>
      <ResponsiveContainer width="100%" height={220}>
        <RadarChart data={chartData}>
          <PolarGrid stroke="#162848" />
          <PolarAngleAxis dataKey="subject" tick={{ fill: '#64748b', fontSize: 10, fontFamily: 'IBM Plex Mono' }} />
          <Radar dataKey="value" stroke="#22d3ee" fill="#22d3ee" fillOpacity={0.1} strokeWidth={1.5} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}
