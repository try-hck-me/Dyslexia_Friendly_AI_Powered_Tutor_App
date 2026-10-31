'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useUser } from '@/context/UserContext';
import {
  LayoutDashboard, Upload, MessageCircle, Heart, Brain, BarChart3,
  Settings, BookOpen, Network, LogOut, Menu, X, UserCircle
} from 'lucide-react';
import { useState, useEffect } from 'react';

const studentLinks = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/profile',   label: 'My Profile',  icon: UserCircle },
  { href: '/documents', label: 'My Documents', icon: Upload },
  { href: '/chat', label: 'Study Bot', icon: MessageCircle },
  { href: '/reader', label: 'PDF Reader', icon: BookOpen },
  { href: '/friendly', label: 'FriendlyBot', icon: Heart },
  { href: '/quiz', label: 'Quiz', icon: Brain },
  { href: '/analytics', label: 'My Progress', icon: BarChart3 },
  { href: '/graph', label: 'Knowledge Map', icon: Network },
  { href: '/settings', label: 'Settings', icon: Settings },
];

const parentLinks = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/profile',   label: 'My Profile',  icon: UserCircle },
  { href: '/analytics', label: "Child's Progress", icon: BarChart3 },
  { href: '/settings', label: 'Settings', icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { name, role, logout } = useUser();
  const [open, setOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const links = role === 'parent' ? parentLinks : studentLinks;

  // Inject responsive CSS once on client — avoids SSR/client mismatch from styled-jsx
  useEffect(() => {
    setMounted(true);
    const style = document.createElement('style');
    style.id = 'sidebar-mobile-style';
    if (!document.getElementById('sidebar-mobile-style')) {
      style.textContent = '@media (max-width: 768px) { .mobile-menu-btn { display: flex !important; } }';
      document.head.appendChild(style);
    }
  }, []);

  return (
    <>
      {/* Mobile menu button — only rendered after mount to avoid SSR/client tree mismatch */}
      {mounted && (
        <button className="btn-icon mobile-menu-btn" onClick={() => setOpen(!open)}
          style={{ position: 'fixed', top: 12, left: 12, zIndex: 200, display: 'none' }}
          aria-label="Toggle menu">
          {open ? <X size={22}/> : <Menu size={22}/>}
        </button>
      )}

      <aside className={`sidebar ${open ? 'open' : ''}`} role="navigation" aria-label="Main navigation">
        <div className="sidebar-brand">
          <h2>AI Tutor ✨</h2>
          <small>Dyslexia-Friendly Learning</small>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section">Menu</div>
          {links.map(({ href, label, icon: Icon }) => (
            <Link key={href} href={href}
              className={`nav-link ${pathname === href ? 'active' : ''}`}
              onClick={() => setOpen(false)}>
              <Icon size={18}/> {label}
            </Link>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div style={{ fontSize: 'var(--fs-sm)', marginBottom: 'var(--space-sm)', color: 'rgba(255,255,255,0.5)' }}>
            {role === 'parent' ? '👨‍👩‍👧 Parent' : '🎓 Student'}: {name || 'User'}
          </div>
          <button className="btn btn-ghost btn-sm" style={{ color: 'rgba(255,255,255,0.6)', width: '100%' }} onClick={logout}>
            <LogOut size={16}/> Sign Out
          </button>
        </div>
      </aside>

      {/* Mobile CSS injected via useEffect above — no styled-jsx needed */}
    </>
  );
}
