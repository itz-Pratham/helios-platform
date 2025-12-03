import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

const COLORS = {
  aws: '#FF9900',
  gcp: '#4285F4',
  azure: '#0078D4',
  direct: '#34D399',
};

const CloudPieChart = ({ eventsBySource }) => {
  if (!eventsBySource || Object.keys(eventsBySource).length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">
          Event Distribution by Source
        </h2>
        <div className="flex items-center justify-center h-64 text-gray-400">
          <p className="text-sm">No data available</p>
        </div>
      </div>
    );
  }

  const data = Object.entries(eventsBySource).map(([name, value]) => ({
    name: name.toUpperCase(),
    value,
  }));

  const total = data.reduce((sum, item) => sum + item.value, 0);

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-bold text-gray-900 mb-4">
        Event Distribution by Source
      </h2>

      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percent }) =>
              `${name} ${(percent * 100).toFixed(0)}%`
            }
            outerRadius={100}
            fill="#8884d8"
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={COLORS[entry.name.toLowerCase()] || '#999'}
              />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>

      <div className="mt-4 grid grid-cols-2 gap-4">
        {data.map((item) => (
          <div
            key={item.name}
            className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
          >
            <div className="flex items-center">
              <div
                className="w-3 h-3 rounded-full mr-2"
                style={{
                  backgroundColor: COLORS[item.name.toLowerCase()] || '#999',
                }}
              />
              <span className="text-sm font-medium text-gray-700">
                {item.name}
              </span>
            </div>
            <span className="text-sm font-bold text-gray-900">
              {item.value.toLocaleString()}
            </span>
          </div>
        ))}
      </div>

      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="flex justify-between items-center">
          <span className="text-sm font-medium text-gray-600">Total Events</span>
          <span className="text-lg font-bold text-gray-900">
            {total.toLocaleString()}
          </span>
        </div>
      </div>
    </div>
  );
};

export default CloudPieChart;
