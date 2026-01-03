import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

const API_BASE = 'http://localhost:8001';

export default function AnomalyAlerts() {
  const { data: modelStatus } = useQuery({
    queryKey: ['model-status'],
    queryFn: async () => {
      const { data } = await axios.get(`${API_BASE}/api/v1/phase2/anomaly/model-status`);
      return data;
    },
  });

  const { data: alerts } = useQuery({
    queryKey: ['anomaly-alerts'],
    queryFn: async () => {
      const { data } = await axios.get(`${API_BASE}/api/v1/phase2/anomaly/recent?limit=50`);
      return data;
    },
    refetchInterval: 3000,
  });

  const getSeverityColor = (severity) => {
    const colors = {
      critical: 'bg-red-100 text-red-800 border-red-300',
      high: 'bg-orange-100 text-orange-800 border-orange-300',
      medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      low: 'bg-green-100 text-green-800 border-green-300',
    };
    return colors[severity] || 'bg-gray-100 text-gray-800 border-gray-300';
  };

  return (
    <div className="space-y-6">
      {/* Model Status Card */}
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-6 border border-purple-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">ML Model Status</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-600">Model Type</p>
            <div className="mt-2 flex items-center space-x-2">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                modelStatus?.model_type === 'lstm'
                  ? 'bg-green-100 text-green-800'
                  : 'bg-yellow-100 text-yellow-800'
              }`}>
                {modelStatus?.model_type?.toUpperCase() || 'N/A'}
              </span>
            </div>
          </div>
          <div>
            <p className="text-sm text-gray-600">Window Size</p>
            <p className="mt-2 text-2xl font-bold text-gray-900">
              {modelStatus?.window_size || 0} min
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Threshold</p>
            <p className="mt-2 text-2xl font-bold text-gray-900">
              {(modelStatus?.threshold * 100)?.toFixed(0) || 0}%
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Features</p>
            <p className="mt-2 text-2xl font-bold text-gray-900">
              {modelStatus?.feature_count || 0}
            </p>
          </div>
        </div>

        {modelStatus?.model_type === 'ewma_fallback' && (
          <div className="mt-4 bg-yellow-50 border-l-4 border-yellow-400 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-yellow-700">
                  <strong>Fallback Mode:</strong> LSTM model unavailable. Using statistical EWMA detector.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Alerts Feed */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Recent Anomaly Alerts</h3>
          <p className="text-sm text-gray-500">Real-time anomaly detection feed</p>
        </div>

        <div className="p-6">
          {!alerts || alerts.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">✅</div>
              <p className="text-lg font-medium text-gray-900">No Anomalies Detected</p>
              <p className="text-sm text-gray-500 mt-2">
                System is operating normally. Alerts will appear here when anomalies are detected.
              </p>
            </div>
          ) : (
            <div className="space-y-4 max-h-96 overflow-y-auto">
              {alerts.map((alert, idx) => (
                <div
                  key={idx}
                  className={`border-l-4 p-4 rounded-r-lg ${getSeverityColor(alert.severity)}`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <span className={`px-2 py-1 text-xs font-bold rounded ${
                          alert.severity === 'critical' ? 'bg-red-600 text-white' :
                          alert.severity === 'high' ? 'bg-orange-600 text-white' :
                          alert.severity === 'medium' ? 'bg-yellow-600 text-white' :
                          'bg-green-600 text-white'
                        }`}>
                          {alert.severity.toUpperCase()}
                        </span>
                        <span className="text-xs font-medium text-gray-500">
                          {new Date(alert.timestamp).toLocaleString()}
                        </span>
                        <span className="text-xs px-2 py-1 bg-gray-200 rounded">
                          {alert.model_type}
                        </span>
                      </div>

                      <p className="mt-2 text-sm font-medium text-gray-900">
                        {alert.message}
                      </p>

                      <div className="mt-2 flex items-center space-x-4 text-xs text-gray-600">
                        <span>Metric: <strong>{alert.metric_name}</strong></span>
                        <span>Confidence: <strong>{(alert.confidence * 100).toFixed(1)}%</strong></span>
                        {alert.expected_value !== null && (
                          <span>Expected: <strong>{alert.expected_value.toFixed(2)}</strong></span>
                        )}
                        <span>Actual: <strong>{alert.actual_value.toFixed(2)}</strong></span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Info */}
      <div className="bg-purple-50 border-l-4 border-purple-500 p-4 rounded">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-purple-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <p className="text-sm text-purple-700">
              <strong>Anomaly Detection:</strong> LSTM model trained on Kaggle with 100% test accuracy.
              Auto-falls back to EWMA statistical detector if model unavailable.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
