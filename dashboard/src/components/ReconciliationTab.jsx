import { useState } from 'react';
import {
  useTriggerReconciliation,
  useReconciliationSummary,
  useReconciliationRuns,
  useReconciliationResults,
} from '../hooks/useReconciliation';

export default function ReconciliationTab() {
  const [selectedRunId, setSelectedRunId] = useState(null);
  const [windowMinutes, setWindowMinutes] = useState(30);

  const { data: summary, isLoading: summaryLoading } = useReconciliationSummary(24);
  const { data: runs, isLoading: runsLoading } = useReconciliationRuns(10);
  const { data: results } = useReconciliationResults(selectedRunId);
  const triggerMutation = useTriggerReconciliation();

  const handleTriggerReconciliation = () => {
    triggerMutation.mutate({ windowMinutes });
  };

  // Status badge component
  const StatusBadge = ({ status }) => {
    const colors = {
      consistent: 'bg-green-100 text-green-800',
      missing: 'bg-yellow-100 text-yellow-800',
      inconsistent: 'bg-red-100 text-red-800',
      duplicate: 'bg-orange-100 text-orange-800',
    };

    return (
      <span
        className={`px-2 py-1 text-xs font-medium rounded-full ${
          colors[status] || 'bg-gray-100 text-gray-800'
        }`}
      >
        {status}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header with Trigger Button */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              Event Reconciliation
            </h2>
            <p className="mt-1 text-sm text-gray-500">
              Verify event consistency across cloud sources
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Window (minutes)
              </label>
              <select
                value={windowMinutes}
                onChange={(e) => setWindowMinutes(Number(e.target.value))}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value={5}>5 minutes</option>
                <option value={15}>15 minutes</option>
                <option value={30}>30 minutes</option>
                <option value={60}>1 hour</option>
                <option value={120}>2 hours</option>
              </select>
            </div>
            <div className="flex flex-col">
              <label className="block text-sm font-medium text-gray-700 mb-1 opacity-0">
                Action
              </label>
              <button
                onClick={handleTriggerReconciliation}
                disabled={triggerMutation.isPending}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {triggerMutation.isPending ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Running...</span>
                  </>
                ) : (
                  <>
                    <svg
                      className="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                      />
                    </svg>
                    <span>Trigger Reconciliation</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {summaryLoading ? (
          <div className="col-span-5 flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : summary ? (
          <>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm font-medium text-gray-500">Total Checked</div>
              <div className="mt-1 text-3xl font-semibold text-gray-900">
                {summary.total_events_checked || 0}
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm font-medium text-gray-500">Consistent</div>
              <div className="mt-1 text-3xl font-semibold text-green-600">
                {summary.consistent || 0}
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm font-medium text-gray-500">Missing</div>
              <div className="mt-1 text-3xl font-semibold text-yellow-600">
                {summary.missing || 0}
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm font-medium text-gray-500">Inconsistent</div>
              <div className="mt-1 text-3xl font-semibold text-red-600">
                {summary.inconsistent || 0}
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm font-medium text-gray-500">Consistency</div>
              <div className="mt-1 text-3xl font-semibold text-blue-600">
                {summary.consistency_percentage?.toFixed(1) || 0}%
              </div>
            </div>
          </>
        ) : null}
      </div>

      {/* Recent Runs */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Recent Reconciliation Runs</h3>
        </div>
        <div className="overflow-x-auto">
          {runsLoading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : runs && runs.length > 0 ? (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Run ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Time Window
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total Events
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Consistent
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Issues
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {runs.map((run) => (
                  <tr key={run.run_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900 font-mono">
                        {run.run_id.slice(0, 20)}...
                      </div>
                      <div className="text-xs text-gray-500">
                        {new Date(run.created_at).toLocaleString()}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(run.window_start).toLocaleTimeString()} -{' '}
                      {new Date(run.window_end).toLocaleTimeString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {run.total_events}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600 font-medium">
                      {run.consistent}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="flex space-x-2">
                        {run.missing > 0 && (
                          <span className="text-yellow-600">M:{run.missing}</span>
                        )}
                        {run.inconsistent > 0 && (
                          <span className="text-red-600">I:{run.inconsistent}</span>
                        )}
                        {run.duplicate > 0 && (
                          <span className="text-orange-600">D:{run.duplicate}</span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-blue-600">
                      {(run.avg_consistency_score * 100).toFixed(1)}%
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        onClick={() => setSelectedRunId(run.run_id)}
                        className="text-blue-600 hover:text-blue-800 font-medium"
                      >
                        View Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="text-center py-12">
              <p className="text-gray-500">No reconciliation runs yet. Trigger one to get started!</p>
            </div>
          )}
        </div>
      </div>

      {/* Results Detail Panel */}
      {selectedRunId && results && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">
              Reconciliation Results: {selectedRunId.slice(0, 30)}...
            </h3>
            <button
              onClick={() => setSelectedRunId(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </button>
          </div>
          <div className="overflow-x-auto max-h-96 overflow-y-auto">
            {results.length > 0 ? (
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50 sticky top-0">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Event ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Sources
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Score
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Issues
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {results.map((result) => (
                    <tr key={result.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {result.event_id}
                        </div>
                        <div className="text-xs text-gray-500">{result.event_type}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <StatusBadge status={result.status} />
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-900">
                          Found: {result.found_in_sources.join(', ') || 'None'}
                        </div>
                        {result.missing_from_sources.length > 0 && (
                          <div className="text-xs text-red-600">
                            Missing: {result.missing_from_sources.join(', ')}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {result.consistency_score !== null
                            ? (result.consistency_score * 100).toFixed(0) + '%'
                            : 'N/A'}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        {result.issues && result.issues.length > 0 ? (
                          <div className="space-y-1">
                            {result.issues.map((issue, idx) => (
                              <div key={idx} className="text-xs text-gray-600">
                                {issue.description}
                              </div>
                            ))}
                          </div>
                        ) : (
                          <span className="text-xs text-gray-400">No issues</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-500">No results found for this run.</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
