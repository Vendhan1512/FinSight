import { api } from './client';

export interface LineageMetadata {
  provenance_id: string;
  model_version?: string;
  feature_version?: string;
  methodology_version?: string;
  data_cutoff: string;
  generated_at: string;
}

export interface IntelligenceAssessment {
  assessment_id: string;
  entity_id: string;
  assessment_time: string;
  risk_classification: string;
  prediction: string;
  prediction_probability?: number;
  news_sentiment_summary: {
    score?: number;
    label?: string;
  };
  lineage: LineageMetadata;
}

export interface TimelineEvent {
  event: string;
  [key: string]: any;
}

export interface IntelligenceTimeline {
  entity_id: string;
  data_cutoff_time: string;
  timeline: TimelineEvent[];
  lineage: LineageMetadata;
}

export const IntelligenceAPI = {
  getAssessment: async (entityId: string, cutoff?: string): Promise<IntelligenceAssessment> => {
    const params = cutoff ? { cutoff } : {};
    const res = await api.get(`/intelligence/${entityId}`, { params });
    return res.data;
  },
  
  getTimeline: async (entityId: string, cutoff?: string, limit: number = 20): Promise<IntelligenceTimeline> => {
    const params = { limit, ...(cutoff ? { cutoff } : {}) };
    const res = await api.get(`/intelligence/${entityId}/timeline`, { params });
    return res.data;
  }
};
