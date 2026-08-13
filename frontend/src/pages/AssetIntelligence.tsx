import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { IntelligenceAPI } from '../api/intelligence';
import type { IntelligenceAssessment } from '../api/intelligence';
import { DataStateIndicator } from '../components/ui/DataStateIndicator';
import { LineageTooltip } from '../components/ui/LineageTooltip';

export const AssetIntelligence = () => {
  const { ticker } = useParams<{ ticker: string }>();
  const [data, setData] = useState<IntelligenceAssessment | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchAsset = async () => {
      if (!ticker) return;
      setLoading(true);
      setError('');
      try {
        const res = await IntelligenceAPI.getAssessment(ticker);
        setData(res);
      } catch (err: any) {
        setError(err.response?.data?.message || 'Failed to fetch asset intelligence.');
        setData(null);
      } finally {
        setLoading(false);
      }
    };
    fetchAsset();
  }, [ticker]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight mb-1">Asset Intelligence: {ticker}</h1>
        <p className="text-textMuted">Detailed view of predictions and risk for a specific asset.</p>
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
              <CardTitle>Prediction Output</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex justify-between items-center border-b border-white/10 pb-2">
                <span className="text-textMuted">Signal</span>
                <span className="font-bold text-lg">{data.prediction}</span>
              </div>
              <div className="flex justify-between items-center border-b border-white/10 pb-2">
                <span className="text-textMuted">Confidence</span>
                <span className="font-medium">
                  {data.prediction_probability ? `${(data.prediction_probability * 100).toFixed(1)}%` : <DataStateIndicator state="UNAVAILABLE" />}
                </span>
              </div>
              <div className="flex justify-between items-center border-b border-white/10 pb-2">
                <span className="text-textMuted">Model Metadata</span>
                <LineageTooltip lineage={data.lineage} />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Risk Profile</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex justify-between items-center border-b border-white/10 pb-2">
                <span className="text-textMuted">Classification</span>
                <span className="font-bold text-lg">{data.risk_classification}</span>
              </div>
              <div className="flex justify-between items-center border-b border-white/10 pb-2">
                <span className="text-textMuted">Methodology Version</span>
                <span className="font-medium bg-surfaceHighlight px-2 py-0.5 rounded text-sm">
                  {data.lineage.methodology_version || 'N/A'}
                </span>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};
