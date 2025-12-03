import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';

const API_BASE = 'http://localhost:8001/api/v1';

// Trigger a new reconciliation run
export function useTriggerReconciliation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ windowMinutes = 30 }) => {
      const response = await axios.post(`${API_BASE}/reconciliation/trigger`, {
        window_minutes: windowMinutes,
      });
      return response.data;
    },
    onSuccess: () => {
      // Invalidate and refetch reconciliation data
      queryClient.invalidateQueries({ queryKey: ['reconciliation'] });
    },
  });
}

// Get reconciliation summary stats
export function useReconciliationSummary(hours = 24) {
  return useQuery({
    queryKey: ['reconciliation', 'summary', hours],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE}/reconciliation/summary`, {
        params: { hours },
      });
      return response.data;
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  });
}

// Get recent reconciliation runs
export function useReconciliationRuns(limit = 10) {
  return useQuery({
    queryKey: ['reconciliation', 'runs', limit],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE}/reconciliation/runs`, {
        params: { limit },
      });
      return response.data;
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  });
}

// Get reconciliation results for a specific run
export function useReconciliationResults(runId, limit = 100) {
  return useQuery({
    queryKey: ['reconciliation', 'results', runId, limit],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE}/reconciliation/results`, {
        params: { run_id: runId, limit },
      });
      return response.data;
    },
    enabled: !!runId, // Only fetch if runId is provided
  });
}
