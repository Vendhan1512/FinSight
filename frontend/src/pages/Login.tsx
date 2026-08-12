import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { AuthAPI } from '../api/auth';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Lock, User } from 'lucide-react';

export const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    
    try {
      const data = await AuthAPI.login(username, password);
      await login(data.access_token);
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || err.response?.data?.message || 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4 relative overflow-hidden">
      {/* Decorative background blur */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent/10 rounded-full blur-[120px] pointer-events-none" />
      
      <Card className="w-full max-w-md relative z-10">
        <CardHeader className="text-center flex-col gap-2 pt-8">
          <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center mb-2 mx-auto">
            <Lock className="text-primary" size={24} />
          </div>
          <CardTitle className="text-2xl">FinSight Intelligence</CardTitle>
          <p className="text-sm text-textMuted">Enter your credentials to access the dashboard</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="bg-danger/10 border border-danger/20 text-danger text-sm p-3 rounded-lg text-center">
                {error}
              </div>
            )}
            
            <div className="space-y-1">
              <label className="text-sm font-medium text-textMuted">Username</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User size={16} className="text-textMuted" />
                </div>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full bg-surface/50 border border-white/10 rounded-lg py-2 pl-10 pr-3 focus:outline-none focus:border-primary/50 text-textMain"
                  placeholder="admin, analyst, or viewer"
                  required
                />
              </div>
            </div>
            
            <div className="space-y-1">
              <label className="text-sm font-medium text-textMuted">Password</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock size={16} className="text-textMuted" />
                </div>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-surface/50 border border-white/10 rounded-lg py-2 pl-10 pr-3 focus:outline-none focus:border-primary/50 text-textMain"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>
            
            <button
              type="submit"
              disabled={isLoading}
              className="w-full btn-primary mt-6 flex justify-center items-center"
            >
              {isLoading ? 'Authenticating...' : 'Sign In'}
            </button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};
