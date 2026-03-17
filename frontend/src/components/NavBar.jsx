import { Link, useLocation } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';

const NAV_LINKS = [
  { to: '/research', label: 'Research',  icon: '🔬' },
  { to: '/history',  label: 'History',   icon: '📋' },
  { to: '/upload',   label: 'Upload',    icon: '📄' },
  { to: '/settings', label: 'Settings',  icon: '⚙️' },
];

function SunIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
      fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="5"/>
      <line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/>
      <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
      <line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>
      <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
      fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
    </svg>
  );
}

export default function NavBar() {
  const { pathname } = useLocation();
  const { theme, toggleTheme } = useTheme();

  return (
    <nav
      className="h-14 border-b flex items-center px-6 gap-6 sticky top-0 z-50 transition-colors duration-300"
      style={{ backgroundColor: 'var(--bg-nav)', borderColor: 'var(--border-color)' }}
    >
      {/* Logo */}
      <Link to="/" className="flex items-center gap-2.5 font-bold shrink-0" style={{ color: 'var(--text-primary)' }}>
        <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white shadow">
          <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24"
            fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
            <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
          </svg>
        </div>
        <span className="hidden sm:block text-sm tracking-tight">Personal Research Assistant</span>
      </Link>

      {/* Nav links */}
      <div className="flex items-center gap-1 ml-auto sm:ml-4">
        {NAV_LINKS.map(link => {
          const active = pathname.startsWith(link.to);
          return (
            <Link
              key={link.to}
              to={link.to}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                active
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'hover:bg-[var(--bg-hover)]'
              }`}
              style={!active ? { color: 'var(--text-secondary)' } : {}}
            >
              <span className="sm:hidden">{link.icon}</span>
              <span className="hidden sm:inline">{link.label}</span>
            </Link>
          );
        })}

        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          aria-label="Toggle theme"
          className="ml-2 p-2 rounded-lg transition-all hover:bg-[var(--bg-hover)]"
          style={{ color: 'var(--text-secondary)' }}
          title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {theme === 'dark' ? <SunIcon /> : <MoonIcon />}
        </button>
      </div>
    </nav>
  );
}
