import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { IntelligenceAPI, IntelligenceAssessment } from '../api/intelligence';
import { DataStateIndicator } from '../components/ui/DataStateIndicator';
import { LineageTooltip } from '../components/ui/LineageTooltip';
import { Search } from 'lucide-react';

export const Predictions = () => {
  const [symbol, setSymbol] = useState('AAPL');
  const [searchInput, setSearchInput] = useState('AAPL');
  const [data, setData] = useState<IntelligenceAssessment | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchPrediction = async (ticker: string) => {
    setLoading(true);
    setError('');
    try {
      const res = await IntelligenceAPI.getAssessment(ticker);
      setData(res);
      setSymbol(ticker);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to fetch predictions.');
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPrediction('AAPL');
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchInput.trim()) {
      fetchPrediction(searchInput.trim().toUpperCase());
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold tracking-tight mb-1">Model Predictions</h1>
          <p className="text-textMuted">Machine learning forecasts and confidence metrics.</p>
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

      {loading && <DataStateIndicator state="LOADING" />}
      
      {error && !loading && (
        <div className="p-4 bg-danger/10 text-danger rounded-lg inline-block">
          <DataStateIndicator state="FAILED" /> {error}
        </div>
      )}

      {data && !loading && (
        <Card className="max-w-3xl">
          <CardHeader>
            <CardTitle className="flex items-center gap-3">
              <span>{symbol} Forecast</span>
              <DataStateIndicator state="FRESH" />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-y-6 gap-x-8">
              <div>
                <p className="text-sm text-textMuted mb-1">Prediction Signal</p>
                <p className="text-2xl font-bold">{data.prediction}</p>
              </div>
              <div>
                <p className="text-sm text-textMuted mb-1">Confidence Score</p>
                <p className="text-2xl font-bold">
                  {data.prediction_probability !== undefined ? `${(data.prediction_probability * 100).toFixed(1)}%` : <DataStateIndicator state="UNAVAILABLE" />}
                </p>
              </div>
              
              <div className="col-span-2 border-t border-white/10 pt-4 mt-2">
                <h4 className="font-semibold mb-3">Model Provenance</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-textMuted block">Model Version</span>
                    <span>{data.lineage.model_version || 'UNKNOWN'}</span>
                  </div>
                  <div>
                    <span className="text-textMuted block">Feature Version</span>
                    <span>{data.lineage.feature_version || 'UNKNOWN'}</span>
                  </div>
                  <div>
                    <span className="text-textMuted block">Prediction Timestamp</span>
                    <span>{new Date(data.lineage.generated_at).toLocaleString()}</span>
                  </div>
                  <div>
                    <span className="text-textMuted block">Data Cutoff</span>
                    <span>{new Date(data.lineage.data_cutoff).toLocaleString()}</span>
                  </div>
                  <div>
                    <span className="text-textMuted block">Provenance ID</span>
                    <span className="font-mono text-xs text-textMuted truncate max-w-full block" title={data.lineage.provenance_id}>
                      {data.lineage.provenance_id}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
