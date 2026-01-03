import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

const API_BASE = 'http://localhost:8001';

export default function ReconciliationMetrics() {
  const { data: metrics, isLoading } = useQuery({
    queryKey: ['phase2-metrics'],
    queryFn: async () => {
      const { data } = await axios.get(`${API_BASE}/api/v1/phase2/metrics`);
      return data;
    },
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const { event_index, bloom_filter, reconciliation_windows } = metrics || {};

  return (
    <div className="space-y-6">
      {/* Event Index Stats */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Event Index Performance</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-6 border border-blue-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-600">Backend</p>
                <p className="mt-2 text-3xl font-bold text-blue-900">
                  {event_index?.backend?.toUpperCase() || 'N/A'}
                </p>
                <p className="mt-1 text-xs text-blue-700">
                  {event_index?.backend === 'redis' ? 'Production' : 'Fallback'}
                </p>
              </div>
              <div className="text-4xl">💾</div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-6 border border-green-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-600">Total Events</p>
                <p className="mt-2 text-3xl font-bold text-green-900">
                  {event_index?.total_events?.toLocaleString() || 0}
                </p>
                <p className="mt-1 text-xs text-green-700">Indexed</p>
              </div>
              <div className="text-4xl">📊</div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-6 border border-purple-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-purple-600">Lookup Speed</p>
                <p className="mt-2 text-3xl font-bold text-purple-900">
                  {event_index?.avg_lookup_ms?.toFixed(1) || 0}
                  <span className="text-xl ml-1">ms</span>
                </p>
                <p className="mt-1 text-xs text-purple-700">
                  {event_index?.avg_lookup_ms < 5 ? 'Excellent' : 'Good'}
                </p>
              </div>
              <div className="text-4xl">⚡</div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg p-6 border border-orange-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-orange-600">Sources</p>
                <div className="mt-2 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-orange-700">AWS:</span>
                    <span className="text-sm font-bold text-orange-900">
                      {event_index?.by_source?.aws || 0}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-orange-700">GCP:</span>
                    <span className="text-sm font-bold text-orange-900">
                      {event_index?.by_source?.gcp || 0}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-orange-700">Azure:</span>
                    <span className="text-sm font-bold text-orange-900">
                      {event_index?.by_source?.azure || 0}
                    </span>
                  </div>
                </div>
              </div>
              <div className="text-4xl">☁️</div>
            </div>
          </div>
        </div>
      </div>

      {/* Bloom Filter Stats */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Bloom Filter Efficiency</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-indigo-500">
            <p className="text-sm font-medium text-gray-600">Memory Usage</p>
            <p className="mt-2 text-2xl font-bold text-gray-900">
              {bloom_filter?.memory_mb?.toFixed(1) || 0} MB
            </p>
            <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-indigo-500 h-2 rounded-full"
                style={{
                  width: `${((bloom_filter?.memory_mb || 0) / 50) * 100}%`,
                }}
              ></div>
            </div>
            <p className="mt-1 text-xs text-gray-500">of 50 MB capacity</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-cyan-500">
            <p className="text-sm font-medium text-gray-600">Capacity</p>
            <p className="mt-2 text-2xl font-bold text-gray-900">
              {((bloom_filter?.capacity || 0) / 1000000).toFixed(1)}M
            </p>
            <p className="mt-1 text-xs text-gray-500">events max</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-teal-500">
            <p className="text-sm font-medium text-gray-600">Current Load</p>
            <p className="mt-2 text-2xl font-bold text-gray-900">
              {((bloom_filter?.current_load || 0) / 1000000).toFixed(2)}M
            </p>
            <p className="mt-1 text-xs text-gray-500">
              {(
                ((bloom_filter?.current_load || 0) / (bloom_filter?.capacity || 1)) *
                100
              ).toFixed(1)}
              % full
            </p>
          </div>

          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-rose-500">
            <p className="text-sm font-medium text-gray-600">False Positive Rate</p>
            <p className="mt-2 text-2xl font-bold text-gray-900">
              {((bloom_filter?.false_positive_rate || 0) * 100).toFixed(2)}%
            </p>
            <p className="mt-1 text-xs text-gray-500">
              {bloom_filter?.false_positive_rate < 0.01 ? 'Excellent' : 'Good'}
            </p>
          </div>
        </div>
      </div>

      {/* Reconciliation Windows */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Reconciliation Windows</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Windows</p>
                <p className="mt-2 text-3xl font-bold text-gray-900">
                  {reconciliation_windows?.active || 0}
                </p>
              </div>
              <div className="text-3xl">🪟</div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Pending Events</p>
                <p className="mt-2 text-3xl font-bold text-gray-900">
                  {reconciliation_windows?.pending_events || 0}
                </p>
              </div>
              <div className="text-3xl">⏳</div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Avg Closure Time</p>
                <p className="mt-2 text-3xl font-bold text-gray-900">
                  {reconciliation_windows?.avg_closure_sec?.toFixed(1) || 0}s
                </p>
              </div>
              <div className="text-3xl">⏱️</div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Timeout Rate</p>
                <p className="mt-2 text-3xl font-bold text-gray-900">
                  {((reconciliation_windows?.timeout_rate || 0) * 100).toFixed(1)}%
                </p>
              </div>
              <div className="text-3xl">⚠️</div>
            </div>
          </div>
        </div>
      </div>

      {/* Info Banner */}
      <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg
              className="h-5 w-5 text-blue-400"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <div className="ml-3">
            <p className="text-sm text-blue-700">
              <strong>Phase 2 Metrics:</strong> Real-time statistics updated every 5 seconds.
              Event index provides O(1) lookups for fast reconciliation.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
