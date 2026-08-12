import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { SystemAPI } from '../api/system';
import { DataStateIndicator } from '../components/ui/DataStateIndicator';
import { useAuth } from '../context/AuthContext';
import { Server, Database, PlayCircle } from 'lucide-react';

export const SystemStatus = () => {
  const { user } = useAuth();
  const [live, setLive] = useState<any>(null);
  const [ready, setReady] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [triggerLoading, setTriggerLoading] = useState(false);
  const [triggerMessage, setTriggerMessage] = useState('');

  const checkHealth = async () => {
    setLoading(true);
    try {
      const liveData = await SystemAPI.live();
      setLive(liveData);
    } catch (e) {
      setLive(null);
    }
    
    try {
      const readyData = await SystemAPI.ready();
      setReady(readyData);
    } catch (e) {
      setReady(null);
    }
    setLoading(false);
  };

  useEffect(() => {
    checkHealth();
  }, []);

  const handleTrigger = async () => {
    if (user?.role !== 'ADMIN') return;
    setTriggerLoading(true);
    setTriggerMessage('');
    try {
      const res = await SystemAPI.triggerPipeline();
      setTriggerMessage(`Pipeline triggered: ${res.run_id}`);
    } catch (err: any) {
      setTriggerMessage(err.response?.data?.message || 'Failed to trigger pipeline');
    } finally {
      setTriggerLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight mb-1">System Status</h1>
        <p className="text-textMuted">Platform health and orchestration controls.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <Server className="text-primary" size={20} /> API Liveness
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? <DataStateIndicator state="LOADING" /> : 
              live ? (
                <div className="space-y-2">
                  <DataStateIndicator state="FRESH" message="API is responding" />
                  <div className="text-sm text-textMuted mt-4 bg-surfaceHighlight p-3 rounded">
                    Version: {live.version} <br/>
                    Service: {live.service}
                  </div>
                </div>
              ) : (
                <DataStateIndicator state="FAILED" message="API is unreachable" />
              )
            }
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <Database className="text-accent" size={20} /> Database Readiness
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? <DataStateIndicator state="LOADING" /> : 
              ready ? (
                <div className="space-y-2">
                  <DataStateIndicator state="FRESH" message="Database connected" />
                  <div className="text-sm text-textMuted mt-4 bg-surfaceHighlight p-3 rounded">
                    Status: {ready.status} <br/>
                    Connection: {ready.database}
                  </div>
                </div>
              ) : (
                <DataStateIndicator state="FAILED" message="Database connection failed" />
              )
            }
          </CardContent>
        </Card>
      </div>

      {user?.role === 'ADMIN' && (
        <Card className="mt-6 border-primary/20">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <PlayCircle className="text-warning" size={20} /> Orchestration Engine
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-textMuted mb-4">
              Manually trigger the data ingestion and intelligence pipeline. This is an admin-only action.
            </p>
            <div className="flex items-center gap-4">
              <button 
                onClick={handleTrigger}
                disabled={triggerLoading || (!live || !ready)}
                className="btn-primary flex items-center gap-2"
              >
                {triggerLoading ? 'Triggering...' : 'Run Pipeline'}
              </button>
              {triggerMessage && (
                <span className={`text-sm ${triggerMessage.includes('Failed') ? 'text-danger' : 'text-accent'}`}>
                  {triggerMessage}
                </span>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
