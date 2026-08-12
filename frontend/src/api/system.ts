import { api } from './client';
import axios from 'axios';

// Directly hit the health endpoints without the v1 prefix since they are at root
const rootApi = axios.create({
  baseURL: 'http://localhost:8000',
});

export const SystemAPI = {
  live: async () => {
    const res = await rootApi.get('/live');
    return res.data;
  },
  
  ready: async () => {
    const res = await rootApi.get('/ready');
    return res.data;
  },

  triggerPipeline: async (backfillDate?: string) => {
    const params = backfillDate ? { backfill_date: backfillDate } : {};
    const res = await api.post('/system/pipeline/trigger', null, { params });
    return res.data;
  }
};
