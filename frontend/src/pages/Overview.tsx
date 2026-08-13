import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { IntelligenceAPI } from '../api/intelligence';
import type { IntelligenceAssessment } from '../api/intelligence';
import { DataStateIndicator } from '../components/ui/DataStateIndicator';
import { LineageTooltip } from '../components/ui/LineageTooltip';
import { TrendingUp, AlertTriangle, ShieldCheck, Clock, Search } from 'lucide-react';

export const Overview = () => {
  const [symbol, setSymbol] = useState('AAPL');
  const [searchInput, setSearchInput] = useState('AAPL');
  const [data, setData] = useState<IntelligenceAssessment | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchOverview = async (ticker: string) => {
    setLoading(true);
    setError('');
    try {
      const res = await IntelligenceAPI.getAssessment(ticker);
      setData(res);
      setSymbol(ticker);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to fetch intelligence overview.');
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview('AAPL');
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchInput.trim()) {
      fetchOverview(searchInput.trim().toUpperCase());
    }
  };

  const isDataStale = data ? (new Date().getTime() - new Date(data.lineage.data_cutoff).getTime()) > 86400000 : false;

  return (
    <div className="space-y-6">
      {/* Header & Search */}
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold tracking-tight mb-1">Overview Intelligence</h1>
          <p className="text-textMuted">High-level insights across ML, Risk, and NLP pipelines.</p>
        </div>
        
        <form onSubmit={handleSearch} className="relative w-64">
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="w-full bg-surface/80 border border-white/10 rounded-lg py-2 pl-4 pr-10 focus:outline-none focus:border-primary/50 text-textMain uppercase"
            placeholder="Search Symbol..."
          />
          <button type="submit" className="absolute right-2 top-1/2 -translate-y-1/2 text-textMuted hover:text-primary">
            <Search size={18} />
          </button>
        </form>
      </div>

      {loading && (
        <div className="flex items-center gap-3 p-4 bg-surfaceHighlight border border-white/10 rounded-lg w-fit">
          <DataStateIndicator state="LOADING" />
          <span className="text-sm text-textMuted">Fetching latest intelligence...</span>
        </div>
      )}

      {error && !loading && (
        <div className="flex items-center gap-3 p-4 bg-danger/10 border border-danger/20 rounded-lg text-danger">
          <DataStateIndicator state="FAILED" />
          <span className="text-sm">{error}</span>
        </div>
      )}

      {data && !loading && (
        <>
          <div className="flex items-center gap-3 mb-2">
            <h2 className="text-2xl font-bold text-primary">{symbol}</h2>
            {isDataStale ? (
              <DataStateIndicator state="STALE" message={`Data cutoff: ${new Date(data.lineage.data_cutoff).toLocaleString()}`} />
            ) : (
              <DataStateIndicator state="FRESH" />
            )}
            <LineageTooltip lineage={data.lineage} />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            {/* Prediction Card */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-textMuted flex items-center gap-2">
                  <TrendingUp size={16} /> Latest Prediction
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold mb-2">
                  {data.prediction}
                </div>
                {data.prediction_probability !== undefined && (
                  <div className="text-sm text-textMuted flex justify-between items-center bg-surfaceHighlight rounded px-3 py-1.5">
                    <span>Confidence</span>
                    <span className="font-semibold text-textMain">{(data.prediction_probability * 100).toFixed(1)}%</span>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Risk Card */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-textMuted flex items-center gap-2">
                  <ShieldCheck size={16} /> Risk Classification
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold mb-2">
                  {data.risk_classification}
                </div>
                <div className="text-sm text-textMuted bg-surfaceHighlight rounded px-3 py-1.5 inline-block">
                  Methodology: {data.lineage.methodology_version || 'Unknown'}
                </div>
              </CardContent>
            </Card>

            {/* News Card */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-textMuted flex items-center gap-2">
                  <AlertTriangle size={16} /> News Sentiment
                </CardTitle>
              </CardHeader>
              <CardContent>
                {data.news_sentiment_summary.score !== undefined ? (
                  <>
                    <div className="text-3xl font-bold mb-2">
                      {data.news_sentiment_summary.score > 0.1 ? 'POSITIVE' : data.news_sentiment_summary.score < -0.1 ? 'NEGATIVE' : 'NEUTRAL'}
                    </div>
                    <div className="text-sm text-textMuted flex justify-between items-center bg-surfaceHighlight rounded px-3 py-1.5">
                      <span>Polarity Score</span>
                      <span className="font-semibold text-textMain">{data.news_sentiment_summary.score.toFixed(3)}</span>
                    </div>
                  </>
                ) : (
                  <div className="flex items-center gap-2 mt-2">
                    <DataStateIndicator state="INSUFFICIENT_DATA" />
                    <span className="text-sm text-textMuted">No recent news</span>
                  </div>
                )}
              </CardContent>
            </Card>

          </div>
        </>
      )}
    </div>
  );
};
