import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { IntelligenceAPI, IntelligenceTimeline } from '../api/intelligence';
import { DataStateIndicator } from '../components/ui/DataStateIndicator';
import { LineageTooltip } from '../components/ui/LineageTooltip';
import { Newspaper, ExternalLink, Search } from 'lucide-react';
import { format } from 'date-fns';

export const NewsIntelligence = () => {
  const [symbol, setSymbol] = useState('AAPL');
  const [searchInput, setSearchInput] = useState('AAPL');
  const [data, setData] = useState<IntelligenceTimeline | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchNews = async (ticker: string) => {
    setLoading(true);
    setError('');
    try {
      const res = await IntelligenceAPI.getTimeline(ticker, undefined, 50);
      setData(res);
      setSymbol(ticker);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to fetch news timeline.');
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNews('AAPL');
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchInput.trim()) {
      fetchNews(searchInput.trim().toUpperCase());
    }
  };

  // Filter out just the news events from the timeline
  const newsEvents = data?.timeline.filter(item => item.event_type === 'NEWS_ARTICLE' || item.type === 'news') || [];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold tracking-tight mb-1">News Intelligence</h1>
          <p className="text-textMuted">Real-time NLP analysis of financial news.</p>
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
        <>
          <div className="flex items-center gap-3 mb-2">
            <h2 className="text-xl font-bold text-primary">{symbol} Feed</h2>
            <DataStateIndicator state="FRESH" />
            <LineageTooltip lineage={data.lineage} />
          </div>

          {newsEvents.length === 0 ? (
            <div className="p-8 border border-white/10 border-dashed rounded-xl text-center">
              <Newspaper size={48} className="mx-auto text-textMuted mb-4 opacity-50" />
              <h3 className="text-lg font-medium text-textMain mb-1">No News Available</h3>
              <p className="text-textMuted text-sm">There are no recent articles ingested for this symbol.</p>
              <div className="mt-4 flex justify-center">
                 <DataStateIndicator state="INSUFFICIENT_DATA" />
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {newsEvents.map((news, idx) => {
                const sentiment = news.sentiment_score || 0;
                return (
                  <Card key={idx} className="hover:border-primary/50 transition-colors">
                    <CardContent className="p-5 flex gap-4">
                      <div className="shrink-0 mt-1">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                          sentiment > 0.1 ? 'bg-accent/20 text-accent' :
                          sentiment < -0.1 ? 'bg-danger/20 text-danger' : 'bg-surfaceHighlight text-textMuted'
                        }`}>
                          <Newspaper size={20} />
                        </div>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-4">
                          <h3 className="text-lg font-semibold text-textMain leading-snug line-clamp-2">
                            {news.title || 'Untitled Article'}
                          </h3>
                          <span className="text-xs text-textMuted whitespace-nowrap shrink-0 bg-surfaceHighlight px-2 py-1 rounded">
                            {news.timestamp ? format(new Date(news.timestamp), 'MMM d, HH:mm') : 'Unknown Time'}
                          </span>
                        </div>
                        
                        <div className="mt-2 text-sm text-textMuted flex items-center gap-3">
                          <span className="font-medium text-primary">{news.source || 'Unknown Source'}</span>
                          <span className="w-1 h-1 rounded-full bg-white/20"></span>
                          <span>Sentiment: <strong className={sentiment > 0.1 ? 'text-accent' : sentiment < -0.1 ? 'text-danger' : 'text-textMain'}>{sentiment.toFixed(2)}</strong></span>
                          {news.url && (
                            <>
                              <span className="w-1 h-1 rounded-full bg-white/20"></span>
                              <a href={news.url} target="_blank" rel="noreferrer" className="flex items-center gap-1 hover:text-primary transition-colors">
                                Source <ExternalLink size={12} />
                              </a>
                            </>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </>
      )}
    </div>
  );
};
