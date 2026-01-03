import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

const API_BASE = 'http://localhost:8001';

export default function MissingEvents() {
  const { data: reliability } = useQuery({
    queryKey: ['source-reliability'],
    queryFn: async () => {
      const { data } = await axios.get(`${API_BASE}/api/v1/phase2/source-reliability`);
      return data;
    },
  });

  const { data: missingEvents } = useQuery({
    queryKey: ['missing-events'],
    queryFn: async () => {
      const { data } = await axios.get(`${API_BASE}/api/v1/phase2/missing-events?hours=6`);
      return data;
    },
    refetchInterval: 5000,
  });

  const getReliabilityColor = (percentage) => {
    if (percentage >= 99) return 'text-green-600';
    if (percentage >= 97) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="space-y-6">
      {/* Source Reliability Cards */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Source Reliability (Last 24h)</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {reliability?.map((source) => (
            <div
              key={source.source}
              className="bg-white rounded-lg shadow-lg p-6 border-t-4"
              style={{
                borderColor:
                  source.reliability_percentage >= 99
                    ? '#10b981'
                    : source.reliability_percentage >= 97
                    ? '#f59e0b'
                    : '#ef4444',
              }}
            >
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-lg font-bold text-gray-900 uppercase">
                  {source.source}
                </h4>
                <div className="text-3xl">
                  {source.source === 'aws' && '🟠'}
                  {source.source === 'gcp' && '🔵'}
                  {source.source === 'azure' && '🔷'}
                </div>
              </div>

              <div className="mb-4">
                <div className="flex items-baseline justify-between">
                  <span className="text-sm text-gray-600">Reliability</span>
                  <span
                    className={`text-3xl font-bold ${getReliabilityColor(
                      source.reliability_percentage
                    )}`}
                  >
                    {source.reliability_percentage.toFixed(1)}%
                  </span>
                </div>
                <div className="mt-2 w-full bg-gray-200 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full ${
                      source.reliability_percentage >= 99
                        ? 'bg-green-500'
                        : source.reliability_percentage >= 97
                        ? 'bg-yellow-500'
                        : 'bg-red-500'
                    }`}
                    style={{ width: `${source.reliability_percentage}%` }}
                  ></div>
                </div>
              </div>

              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">On Time</span>
                  <span className="font-medium text-green-600">
                    {source.events_on_time.toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Delayed</span>
                  <span className="font-medium text-yellow-600">
                    {source.events_delayed.toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Missing</span>
                  <span className="font-medium text-red-600">
                    {source.events_missing.toLocaleString()}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Missing Events Table */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Missing Events (Last 6 Hours)</h3>
          <p className="text-sm text-gray-500">Events not received from all expected sources</p>
        </div>

        {!missingEvents || missingEvents.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">✅</div>
            <p className="text-lg font-medium text-gray-900">No Missing Events</p>
            <p className="text-sm text-gray-500 mt-2">
              All events received from all sources. System is healthy!
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Event ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Expected Sources
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Received From
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Missing From
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    First Seen
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {missingEvents.map((event, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900 font-mono">
                        {event.event_id}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex space-x-1">
                        {event.expected_sources.map((src) => (
                          <span
                            key={src}
                            className="px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded"
                          >
                            {src}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex space-x-1">
                        {event.received_sources.map((src) => (
                          <span
                            key={src}
                            className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded"
                          >
                            ✓ {src}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex space-x-1">
                        {event.missing_sources.map((src) => (
                          <span
                            key={src}
                            className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded"
                          >
                            ✗ {src}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(event.first_seen).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 text-xs font-semibold rounded-full ${
                          event.status === 'missing'
                            ? 'bg-red-100 text-red-800'
                            : event.status === 'delayed'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-green-100 text-green-800'
                        }`}
                      >
                        {event.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <div className="ml-3">
            <p className="text-sm text-yellow-700">
              <strong>Missing Event Detection:</strong> Uses Bloom filters for space-efficient
              tracking. Events shown here were detected but not received from all expected cloud sources.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
