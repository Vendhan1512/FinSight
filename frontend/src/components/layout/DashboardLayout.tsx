import React from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { 
  LayoutDashboard, 
  LineChart, 
  BrainCircuit, 
  ShieldAlert, 
  Newspaper, 
  Eye, 
  Briefcase, 
  Database, 
  Activity, 
  LogOut,
  Layers
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const DashboardLayout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { path: '/', label: 'Overview', icon: LayoutDashboard },
    { path: '/asset/AAPL', label: 'Asset Intelligence', icon: LineChart },
    { path: '/predictions', label: 'Predictions', icon: BrainCircuit },
    { path: '/risk', label: 'Risk Analysis', icon: ShieldAlert },
    { path: '/news', label: 'News Intelligence', icon: Newspaper },
    { path: '/explainability', label: 'Explainability', icon: Eye },
    { path: '/portfolio', label: 'Portfolio', icon: Briefcase },
    { path: '/data-quality', label: 'Data Quality', icon: Database },
    { path: '/models', label: 'Model Registry', icon: Layers },
    { path: '/system', label: 'System Status', icon: Activity },
  ];

  return (
    <div className="min-h-screen flex bg-background text-textMain">
      {/* Sidebar */}
      <aside className="w-64 glass-header border-r border-white/10 flex flex-col hidden md:flex">
        <div className="h-16 flex items-center px-6 border-b border-white/10">
          <div className="w-8 h-8 rounded bg-primary flex items-center justify-center font-bold mr-3">
            FS
          </div>
          <span className="text-xl font-bold tracking-tight">FinSight</span>
        </div>
        
        <nav className="flex-1 overflow-y-auto py-6 px-3 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => isActive ? "nav-item-active" : "nav-item"}
            >
              <item.icon size={20} />
              <span className="font-medium text-sm">{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-white/10">
          <div className="flex items-center gap-3 mb-4 px-2">
            <div className="w-8 h-8 rounded-full bg-surfaceHighlight flex items-center justify-center">
              {user?.username.charAt(0).toUpperCase()}
            </div>
            <div>
              <p className="text-sm font-medium">{user?.username}</p>
              <p className="text-xs text-textMuted">{user?.role}</p>
            </div>
          </div>
          <button 
            onClick={handleLogout}
            className="w-full flex items-center gap-2 text-textMuted hover:text-danger px-2 py-2 rounded-lg transition-colors text-sm font-medium"
          >
            <LogOut size={18} />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden">
        <header className="h-16 glass-header flex items-center px-8 shrink-0">
          <h2 className="text-lg font-semibold text-textMuted">Production Intelligence Dashboard</h2>
        </header>
        <div className="flex-1 overflow-y-auto p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
};
