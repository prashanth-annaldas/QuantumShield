import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  Key,
  Radio,
  ShieldCheck,
  Flame,
  ShieldAlert,
  FileText,
  Network,
  LogOut,
  User as UserIcon,
  PanelLeftClose,
  Shield,
  AlertOctagon,
  History,
  Activity,
} from 'lucide-react';

import { useAuth } from '../hooks/useAuth';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const { user, logout } = useAuth();
  const isAnalystOrAdmin = user?.role === 'ADMIN' || user?.role === 'SECURITY_ANALYST';

  const navGroups = [
    {
      label: 'QDS WORKFLOW',
      items: [
        { to: '/create-signature', label: 'Create Signature', icon: Key },
        { to: '/teleportation', label: 'Teleportation Simulator', icon: Radio },
        { to: '/verification', label: 'Signature Verification', icon: ShieldCheck },
      ],
    },
    {
      label: 'SECURITY',
      items: [
        { to: '/attack-simulator', label: 'Attack Simulator', icon: Flame },
        { to: '/threat-detection', label: 'Threat Detection', icon: ShieldAlert },
        { to: '/threat-logs', label: 'Threat Logs', icon: FileText },
      ],
    },
    {
      label: 'OPERATIONS',
      items: [
        ...(isAnalystOrAdmin
          ? [
            { to: '/soc', label: 'Security Operations', icon: Shield },
            { to: '/incidents', label: 'Incident Center', icon: AlertOctagon },
          ]
          : []),
        { to: '/sessions/timeline', label: 'Session Timeline', icon: History },
        { to: '/audit', label: 'Security Audit', icon: FileText },
      ],
    },
    ...(isAnalystOrAdmin
      ? [
        {
          label: 'SYSTEM',
          items: [
            { to: '/monitoring', label: 'System Monitoring', icon: Activity },
            { to: '/readiness', label: 'System Readiness', icon: Network },
          ],
        },
      ]
      : []),
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 bg-slate-900/30 backdrop-blur-sm z-40 lg:hidden transition-opacity"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 w-64 bg-white border-r border-slate-200 flex flex-col z-50 transition-transform duration-300 ease-in-out ${isOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
      >
        {/* Brand Header */}
        <div className="h-16 flex items-center justify-between px-5 border-b border-slate-200">
          <h1 className="font-bold text-slate-900 text-xl">
            QuantumShield
          </h1>

          <button
            onClick={onClose}
            className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
            title="Close sidebar"
            aria-label="Close sidebar"
          >
            <PanelLeftClose className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Groups */}
        <div className="flex-1 overflow-y-auto py-4 px-3 space-y-6">
          {navGroups.map((group) => (
            <div key={group.label} className="space-y-1">
              <span className="px-3 text-[10px] font-bold text-slate-400 tracking-wider uppercase">
                {group.label}
              </span>
              <div className="mt-1 space-y-0.5">
                {group.items.map((item) => {
                  const Icon = item.icon;
                  return (
                    <NavLink
                      key={item.to}
                      to={item.to}
                      end={item.to === '/'}
                      className={({ isActive }) =>
                        `flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-semibold transition-colors ${isActive
                          ? 'bg-indigo-50 text-indigo-700 font-bold border border-indigo-100 shadow-sm'
                          : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                        }`
                      }
                    >
                      <Icon className="w-4 h-4 shrink-0" />
                      <span>{item.label}</span>
                    </NavLink>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* User Profile & Logout */}
        <div className="p-3 border-t border-slate-200 bg-slate-50/50">
          <div className="p-2.5 rounded-xl bg-white border border-slate-200 shadow-sm flex items-center justify-between">
            <div className="flex items-center gap-2.5 overflow-hidden">
              <div className="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-xs uppercase shrink-0">
                {user?.username ? user.username.slice(0, 2) : <UserIcon className="w-4 h-4" />}
              </div>
              <div className="overflow-hidden text-left">
                <p className="text-xs font-bold text-slate-800 truncate">
                  {user?.username || 'Authenticated User'}
                </p>
                <span className="text-[10px] font-semibold text-indigo-600 bg-indigo-50 px-1.5 py-0.2 rounded border border-indigo-100 uppercase inline-block">
                  {user?.role || 'USER'}
                </span>
              </div>
            </div>

            <button
              onClick={logout}
              title="Sign Out"
              className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
};
