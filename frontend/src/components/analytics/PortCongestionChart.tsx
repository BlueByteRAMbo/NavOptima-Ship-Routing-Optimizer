import React from 'react';
import { Port } from '../../types/maritime';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, CartesianGrid } from 'recharts';

interface PortCongestionChartProps {
  ports: Port[];
}

const PortCongestionChart: React.FC<PortCongestionChartProps> = ({ ports }) => {
  const data = ports
    .map(p => ({
      name: p.name.length > 15 ? p.name.substring(0, 15) + '...' : p.name,
      fullName: p.name,
      congestion: Math.round(p.congestion * 100),
      wait: p.waiting_hours
    }))
    .sort((a, b) => b.congestion - a.congestion);

  const getColor = (level: number) => {
    if (level > 75) return '#FF4D5E'; // maritime-danger
    if (level > 40) return '#F5A623'; // maritime-warning
    return '#28D7A0'; // maritime-success
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const point = payload[0].payload;
      return (
        <div className="bg-maritime-panel border border-maritime-border p-2 rounded text-xs shadow-glow">
          <div className="text-white font-bold mb-1">{point.fullName}</div>
          <div className="text-maritime-muted">Congestion: <span className="text-white">{point.congestion}%</span></div>
          <div className="text-maritime-muted">Wait: <span className="text-white">{point.wait} hrs</span></div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="h-[280px] w-full text-xs">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 5, right: 10, left: -20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#1D3A4C" horizontal={false} opacity={0.5} />
          <XAxis type="number" domain={[0, 100]} stroke="#7893A3" tick={{ fill: '#7893A3' }} />
          <YAxis dataKey="name" type="category" stroke="#7893A3" tick={{ fill: '#7893A3' }} width={90} />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: '#102636' }} />
          <Bar dataKey="congestion" radius={[0, 4, 4, 0]}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getColor(entry.congestion)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default PortCongestionChart;
