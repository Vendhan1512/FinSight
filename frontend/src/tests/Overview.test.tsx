import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { Overview } from '../pages/Overview';
import { IntelligenceAPI } from '../api/intelligence';
import '@testing-library/jest-dom';

// Mock the API wrapper
vi.mock('../api/intelligence', () => ({
  IntelligenceAPI: {
    getAssessment: vi.fn(),
  },
}));

describe('Overview Page Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', async () => {
    // Make the mock promise unresolved immediately to capture loading state
    vi.mocked(IntelligenceAPI.getAssessment).mockImplementation(() => new Promise(() => {}));
    
    render(<Overview />);
    
    expect(screen.getByText(/Loading.../i)).toBeInTheDocument();
  });

  it('renders successful data correctly', async () => {
    const mockData = {
      assessment_id: '123',
      entity_id: 'AAPL',
      assessment_time: new Date().toISOString(),
      risk_classification: 'MODERATE',
      prediction: 'OUTPERFORM',
      prediction_probability: 0.85,
      news_sentiment_summary: { score: 0.5 },
      lineage: {
        provenance_id: 'abc',
        data_cutoff: new Date().toISOString(), // fresh
        generated_at: new Date().toISOString(),
      }
    };

    vi.mocked(IntelligenceAPI.getAssessment).mockResolvedValue(mockData as any);
    
    render(<Overview />);
    
    await waitFor(() => {
      expect(screen.getByText('OUTPERFORM')).toBeInTheDocument();
      expect(screen.getByText('85.0%')).toBeInTheDocument();
      expect(screen.getByText('MODERATE')).toBeInTheDocument();
      expect(screen.getByText('Fresh')).toBeInTheDocument();
    });
  });

  it('renders stale data warning when cutoff is old', async () => {
    const oldDate = new Date();
    oldDate.setDate(oldDate.getDate() - 3); // 3 days old

    const mockData = {
      assessment_id: '123',
      entity_id: 'AAPL',
      assessment_time: new Date().toISOString(),
      risk_classification: 'MODERATE',
      prediction: 'OUTPERFORM',
      news_sentiment_summary: { score: 0 },
      lineage: {
        provenance_id: 'abc',
        data_cutoff: oldDate.toISOString(), // stale
        generated_at: oldDate.toISOString(),
      }
    };

    vi.mocked(IntelligenceAPI.getAssessment).mockResolvedValue(mockData as any);
    
    render(<Overview />);
    
    await waitFor(() => {
      expect(screen.getByText('Stale Data')).toBeInTheDocument();
    });
  });

  it('renders API error state', async () => {
    vi.mocked(IntelligenceAPI.getAssessment).mockRejectedValue({
      response: { data: { message: 'Internal Server Error' } }
    });
    
    render(<Overview />);
    
    await waitFor(() => {
      expect(screen.getByText('Internal Server Error')).toBeInTheDocument();
      expect(screen.getByText('Failed')).toBeInTheDocument();
    });
  });

  it('renders INSUFFICIENT_DATA when missing fields (news sentiment)', async () => {
    const mockData = {
      assessment_id: '123',
      entity_id: 'AAPL',
      assessment_time: new Date().toISOString(),
      risk_classification: 'MODERATE',
      prediction: 'OUTPERFORM',
      news_sentiment_summary: {}, // missing score
      lineage: {
        provenance_id: 'abc',
        data_cutoff: new Date().toISOString(),
        generated_at: new Date().toISOString(),
      }
    };

    vi.mocked(IntelligenceAPI.getAssessment).mockResolvedValue(mockData as any);
    
    render(<Overview />);
    
    await waitFor(() => {
      expect(screen.getByText('Insufficient Data')).toBeInTheDocument();
      expect(screen.getByText('No recent news')).toBeInTheDocument();
    });
  });
});
