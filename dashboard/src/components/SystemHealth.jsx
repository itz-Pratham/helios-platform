import React from 'react';

const HealthIndicator = ({ status }) => {
  const colors = {
    healthy: 'bg-green-500',
    degraded: 'bg-yellow-500',
    unhealthy: 'bg-red-500',
  };

  return (
    <span className={`inline-block w-3 h-3 rounded-full ${colors[status] || colors.unhealthy}`} />
  );
};

const SystemHealth = ({ health, isConnected }) => {
  const services = [
    { name: 'WebSocket', status: isConnected ? 'healthy' : 'unhealthy' },
    { name: 'Database', status: health?.database || 'unknown' },
    { name: 'Redis', status: health?.redis || 'unknown' },
    { name: 'Kafka', status: health?.kafka || 'unknown' },
  ];

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-bold text-gray-900 mb-4">System Health</h2>

      <div className="space-y-3">
        {services.map((service) => (
          <div
            key={service.name}
            className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
          >
            <div className="flex items-center space-x-3">
              <HealthIndicator status={service.status} />
              <span className="text-sm font-medium text-gray-700">
                {service.name}
              </span>
            </div>
            <span
              className={`text-xs font-semibold uppercase ${
                service.status === 'healthy'
                  ? 'text-green-600'
                  : service.status === 'degraded'
                  ? 'text-yellow-600'
                  : 'text-red-600'
              }`}
            >
              {service.status}
            </span>
          </div>
        ))}
      </div>

      {health?.uptime && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex justify-between items-center text-sm">
            <span className="text-gray-600">Uptime</span>
            <span className="font-medium text-gray-900">
              {Math.floor(health.uptime / 3600)}h{' '}
              {Math.floor((health.uptime % 3600) / 60)}m
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default SystemHealth;
