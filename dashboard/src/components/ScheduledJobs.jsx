import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

const API_BASE = 'http://localhost:8001';

export default function ScheduledJobs() {
  const { data: jobs, isLoading } = useQuery({
    queryKey: ['scheduled-jobs'],
    queryFn: async () => {
      const { data } = await axios.get(`${API_BASE}/api/v1/phase2/scheduler/jobs`);
      return data;
    },
    refetchInterval: 5000,
  });

  const getStatusColor = (status) => {
    const colors = {
      running: 'bg-green-100 text-green-800',
      paused: 'bg-red-100 text-red-800',
      idle: 'bg-gray-100 text-gray-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getNextRunCountdown = (nextRun) => {
    if (!nextRun) return 'N/A';
    const diff = new Date(nextRun) - new Date();
    if (diff < 0) return 'Overdue';

    const minutes = Math.floor(diff / 60000);
    const seconds = Math.floor((diff % 60000) / 1000);

    if (minutes > 60) {
      const hours = Math.floor(minutes / 60);
      return `${hours}h ${minutes % 60}m`;
    }
    if (minutes > 0) {
      return `${minutes}m ${seconds}s`;
    }
    return `${seconds}s`;
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Jobs</p>
              <p className="mt-2 text-3xl font-bold text-gray-900">{jobs?.length || 0}</p>
            </div>
            <div className="text-4xl">📅</div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Running</p>
              <p className="mt-2 text-3xl font-bold text-green-600">
                {jobs?.filter((j) => j.status === 'running').length || 0}
              </p>
            </div>
            <div className="text-4xl">▶️</div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Paused</p>
              <p className="mt-2 text-3xl font-bold text-red-600">
                {jobs?.filter((j) => j.status === 'paused').length || 0}
              </p>
            </div>
            <div className="text-4xl">⏸️</div>
          </div>
        </div>
      </div>

      {/* Jobs Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Scheduled Reconciliation Jobs</h3>
          <p className="text-sm text-gray-500">Automated jobs running on APScheduler</p>
        </div>

        {!jobs || jobs.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">⏸️</div>
            <p className="text-lg font-medium text-gray-900">No Jobs Running</p>
            <p className="text-sm text-gray-500 mt-2">
              Scheduler not started. Jobs will appear when scheduler is running.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Job Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Schedule
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Next Run
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Countdown
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last Run
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {jobs.map((job) => (
                  <tr key={job.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900">{job.name}</div>
                      <div className="text-xs text-gray-500 font-mono">{job.id}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <code className="text-xs bg-gray-100 px-2 py-1 rounded">{job.schedule}</code>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {job.next_run
                        ? new Date(job.next_run).toLocaleString()
                        : 'Not scheduled'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-mono text-blue-600">
                        {getNextRunCountdown(job.next_run)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(
                          job.status
                        )}`}
                      >
                        {job.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {job.last_run ? (
                        <div>
                          <div className="flex items-center space-x-2">
                            <span
                              className={`w-2 h-2 rounded-full ${
                                job.last_run.status === 'success'
                                  ? 'bg-green-500'
                                  : 'bg-red-500'
                              }`}
                            ></span>
                            <span>{job.last_run.status}</span>
                          </div>
                          <div className="text-xs text-gray-400">
                            {job.last_run.duration_sec?.toFixed(2)}s
                          </div>
                        </div>
                      ) : (
                        <span className="text-gray-400">No runs yet</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <div className="ml-3">
            <p className="text-sm text-blue-700">
              <strong>Scheduled Jobs:</strong> 7 automated reconciliation tasks (incremental every
              5min, full hourly, daily deep at 2AM, anomaly detection every 1min, cleanup at 3AM, health check every 1min, metrics aggregation every 5min).
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
