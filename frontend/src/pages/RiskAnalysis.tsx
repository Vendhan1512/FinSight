import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { IntelligenceAPI } from '../api/intelligence';
import type { IntelligenceAssessment } from '../api/intelligence';
import { DataStateIndicator } from '../components/ui/DataStateIndicator';
import { LineageTooltip } from '../components/ui/LineageTooltip';
import { Search } from 'lucide-react';

export const RiskAnalysis = () => {
  const [symbol, setSymbol] = useState('AAPL');
  const [searchInput, setSearchInput] = useState('AAPL');
  const [data, setData] = useState<IntelligenceAssessment | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchRisk = async (ticker: string) => {
    setLoading(true);
    setError('');
    try {
      const res = await IntelligenceAPI.getAssessment(ticker);
      setData(res);
      setSymbol(ticker);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to fetch risk analysis.');
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRisk('AAPL');
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchInput.trim()) {
      fetchRisk(searchInput.trim().toUpperCase());
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold tracking-tight mb-1">Risk Analysis</h1>
          <p className="text-textMuted">Volatility, VaR, CVaR, and Drawdown metrics.</p>
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
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-3">
                <span>{symbol} Core Risk</span>
                <DataStateIndicator state="FRESH" />
                <LineageTooltip lineage={data.lineage} />
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center border-b border-white/10 pb-2">
                  <span className="text-textMuted">Risk Classification</span>
                  <span className={`font-bold text-lg ${
                    data.risk_classification === 'HIGH' ? 'text-danger' :
                    data.risk_classification === 'MODERATE' ? 'text-warning' : 'text-accent'
                  }`}>{data.risk_classification}</span>
                </div>
                <div className="flex justify-between items-center border-b border-white/10 pb-2">
                  <span className="text-textMuted">Methodology</span>
                  <span className="font-medium text-sm bg-surfaceHighlight px-2 py-1 rounded">
                    {data.lineage.methodology_version || 'UNKNOWN'}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Advanced Metrics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center border-b border-white/10 pb-2">
                  <span className="text-textMuted">Value at Risk (95%)</span>
                  <DataStateIndicator state="UNAVAILABLE" />
                </div>
                <div className="flex justify-between items-center border-b border-white/10 pb-2">
                  <span className="text-textMuted">Conditional VaR (95%)</span>
                  <DataStateIndicator state="UNAVAILABLE" />
                </div>
                <div className="flex justify-between items-center border-b border-white/10 pb-2">
                  <span className="text-textMuted">Max Drawdown</span>
                  <DataStateIndicator state="UNAVAILABLE" />
                </div>
                <div className="flex justify-between items-center border-b border-white/10 pb-2">
                  <span className="text-textMuted">Beta</span>
                  <DataStateIndicator state="UNAVAILABLE" />
                </div>
              </div>
              <p className="text-xs text-textMuted mt-4 italic">
                Advanced quantitative metrics are currently unavailable due to missing API exposure in Phase 7.2.
              </p>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};
