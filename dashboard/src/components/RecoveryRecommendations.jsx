import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { useState } from 'react';

const API_BASE = 'http://localhost:8001';

export default function RecoveryRecommendations() {
  const [expandedId, setExpandedId] = useState(null);

  const { data: recommendations } = useQuery({
    queryKey: ['recommendations'],
    queryFn: async () => {
      const { data } = await axios.get(`${API_BASE}/api/v1/phase2/recommendations?limit=50`);
      return data;
    },
    refetchInterval: 5000,
  });

  const { data: criteriaWeights } = useQuery({
    queryKey: ['criteria-weights'],
    queryFn: async () => {
      const { data} = await axios.get(`${API_BASE}/api/v1/phase2/mcdm/criteria-weights`);
      return data;
    },
  });

  return (
    <div className="space-y-6">
      {/* MCDM Criteria Weights */}
      <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg p-6 border border-indigo-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          MCDM Decision Criteria (TOPSIS)
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {criteriaWeights?.weights && Object.entries(criteriaWeights.weights).map(([key, value]) => (
            <div key={key} className="bg-white rounded-lg p-4 shadow">
              <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">
                {key.replace(/_/g, ' ')}
              </p>
              <p className="text-2xl font-bold text-indigo-600">{(value * 100).toFixed(0)}%</p>
              <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-indigo-500 h-2 rounded-full"
                  style={{ width: `${value * 100}%` }}
                ></div>
              </div>
            </div>
          ))}
        </div>
        <p className="mt-4 text-xs text-gray-600">
          Method: <strong>{criteriaWeights?.method}</strong> | Last Updated:{' '}
          {criteriaWeights?.last_updated && new Date(criteriaWeights.last_updated).toLocaleString()}
        </p>
      </div>

      {/* Recommendations Feed */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Recovery Action Recommendations</h3>
          <p className="text-sm text-gray-500">
            AI-driven MCDM analysis for optimal recovery actions
          </p>
        </div>

        {!recommendations || recommendations.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">💡</div>
            <p className="text-lg font-medium text-gray-900">No Recommendations</p>
            <p className="text-sm text-gray-500 mt-2">
              System is healthy. Recommendations will appear when issues are detected.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {recommendations.map((rec, idx) => (
              <div key={idx} className="p-6">
                {/* Recommendation Header */}
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <span className="text-xs text-gray-500">
                        {new Date(rec.timestamp).toLocaleString()}
                      </span>
                      <span
                        className={`px-2 py-1 text-xs font-semibold rounded-full ${
                          rec.issue?.severity === 'critical'
                            ? 'bg-red-100 text-red-800'
                            : rec.issue?.severity === 'high'
                            ? 'bg-orange-100 text-orange-800'
                            : 'bg-yellow-100 text-yellow-800'
                        }`}
                      >
                        {rec.issue?.severity?.toUpperCase()}
                      </span>
                    </div>

                    <h4 className="text-base font-semibold text-gray-900 mb-2">
                      {rec.issue?.description}
                    </h4>

                    {/* Recommended Action */}
                    <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-r">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <p className="text-sm font-medium text-blue-900">
                            Recommended Action: {rec.recommended_action?.name?.replace(/_/g, ' ')}
                          </p>
                          <p className="text-sm text-blue-700 mt-1">
                            {rec.recommended_action?.description}
                          </p>

                          <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-3">
                            <div>
                              <p className="text-xs text-blue-600">TOPSIS Score</p>
                              <p className="text-lg font-bold text-blue-900">
                                {rec.recommended_action?.topsis_score?.toFixed(2)}
                              </p>
                            </div>
                            <div>
                              <p className="text-xs text-blue-600">Est. MTTR</p>
                              <p className="text-lg font-bold text-blue-900">
                                {rec.recommended_action?.estimated_mttr_sec}s
                              </p>
                            </div>
                            <div>
                              <p className="text-xs text-blue-600">QoS Impact</p>
                              <p className="text-lg font-bold text-blue-900">
                                {(rec.recommended_action?.qos_impact * 100)?.toFixed(0)}%
                              </p>
                            </div>
                            <div>
                              <p className="text-xs text-blue-600">Success Rate</p>
                              <p className="text-lg font-bold text-blue-900">
                                {(rec.recommended_action?.success_rate * 100)?.toFixed(0)}%
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Status Badge */}
                    <div className="mt-4 flex items-center space-x-2">
                      <span className="px-3 py-1 bg-yellow-100 text-yellow-800 text-xs font-medium rounded-full">
                        ⏳ {rec.status?.replace(/_/g, ' ').toUpperCase()}
                      </span>
                      <span className="text-xs text-gray-500">
                        Awaiting manual approval or automated execution
                      </span>
                    </div>

                    {/* Decision Matrix (Expandable) */}
                    {rec.decision_matrix && (
                      <div className="mt-4">
                        <button
                          onClick={() =>
                            setExpandedId(expandedId === idx ? null : idx)
                          }
                          className="text-sm text-blue-600 hover:text-blue-800 font-medium flex items-center space-x-1"
                        >
                          <span>{expandedId === idx ? '▼' : '▶'}</span>
                          <span>View Decision Matrix</span>
                        </button>

                        {expandedId === idx && (
                          <div className="mt-3 bg-gray-50 p-4 rounded border border-gray-200">
                            <h5 className="text-sm font-semibold text-gray-900 mb-2">
                              MCDM Decision Matrix
                            </h5>

                            <div className="overflow-x-auto">
                              <table className="min-w-full text-xs">
                                <thead>
                                  <tr className="border-b border-gray-300">
                                    <th className="text-left py-2 px-2">Action</th>
                                    {rec.decision_matrix.criteria?.map((criterion) => (
                                      <th key={criterion} className="text-left py-2 px-2">
                                        {criterion.toUpperCase()}
                                      </th>
                                    ))}
                                    <th className="text-left py-2 px-2 font-bold">Final Score</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {rec.decision_matrix.candidates?.map((candidate, i) => (
                                    <tr
                                      key={i}
                                      className={`border-b border-gray-200 ${
                                        candidate.action === rec.recommended_action?.name
                                          ? 'bg-green-50 font-semibold'
                                          : ''
                                      }`}
                                    >
                                      <td className="py-2 px-2">
                                        {candidate.action?.replace(/_/g, ' ')}
                                      </td>
                                      {candidate.scores?.map((score, j) => (
                                        <td key={j} className="py-2 px-2">
                                          {score.toFixed(2)}
                                        </td>
                                      ))}
                                      <td className="py-2 px-2 font-bold">
                                        {candidate.final_score?.toFixed(2) || 'N/A'}
                                      </td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>

                            <div className="mt-3 text-xs text-gray-600">
                              <strong>Weights:</strong>{' '}
                              {rec.decision_matrix.criteria?.map((c, i) => (
                                <span key={c}>
                                  {c}={rec.decision_matrix.weights?.[i]?.toFixed(1)}
                                  {i < rec.decision_matrix.criteria.length - 1 ? ', ' : ''}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Info */}
      <div className="bg-indigo-50 border-l-4 border-indigo-500 p-4 rounded">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-indigo-400" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <div className="ml-3">
            <p className="text-sm text-indigo-700">
              <strong>Recovery Recommendations:</strong> Uses TOPSIS (Multi-Criteria Decision
              Making) from research paper "AI-Driven Self-Healing Cloud Systems". Actions are
              analyzed and ranked automatically based on MTTR, QoS impact, success rate, and cost.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
