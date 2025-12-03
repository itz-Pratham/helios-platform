import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8001/api/v1';

export const useStats = () => {
  return useQuery({
    queryKey: ['stats'],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE_URL}/stats`);
      return response.data;
    },
    refetchInterval: 5000, // Refetch every 5 seconds
    staleTime: 4000,
  });
};

export const useHealth = () => {
  return useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE_URL}/health/detailed`);
      return response.data;
    },
    refetchInterval: 10000, // Refetch every 10 seconds
    staleTime: 9000,
  });
};
