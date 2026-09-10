import React from 'react';
import { PanelLeft } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

interface NavbarProps {
  onToggleSidebar: () => void;
  isSidebarOpen?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ onToggleSidebar, isSidebarOpen }) => {
  const { user } = useAuth();

  return (
    <header className="h-16 bg-white border-b border-slate-200 sticky top-0 z-30 flex items-center justify-between px-4 sm:px-6 lg:px-8">
      <div className="flex items-center gap-3">
        {!isSidebarOpen && (
          <button
            onClick={onToggleSidebar}
            className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors flex items-center gap-2"
            title="Open sidebar"
            aria-label="Open sidebar"
          >
            <PanelLeft className="w-5 h-5 text-slate-700" />
          </button>
        )}
      </div>

      <div className="flex items-center gap-3">
        {/* User Role Tag */}
        {user && (
          <div className="hidden sm:flex items-center gap-2 pl-3 border-l border-slate-200">
            <div className="text-right">
              <span className="text-xs font-bold text-slate-800 block leading-tight">
                {user.username}
              </span>
              <span className="text-[10px] font-semibold text-indigo-600 uppercase">
                {user.role}
              </span>
            </div>
          </div>
        )}
      </div>
    </header>
  );
};
