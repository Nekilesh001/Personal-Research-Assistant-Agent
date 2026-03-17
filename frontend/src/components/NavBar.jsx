import { Link, useLocation } from 'react-router-dom';

const NAV_LINKS = [
  { to: '/research', label: 'Research', icon: '🔬' },
  { to: '/history', label: 'History', icon: '📋' },
  { to: '/upload', label: 'Upload', icon: '📄' },
  { to: '/settings', label: 'Settings', icon: '⚙️' },
];

export default function NavBar() {
  const { pathname } = useLocation();

  return (
    <nav className="h-14 border-b border-slate-800 flex items-center px-6 gap-8 bg-slate-900 sticky top-0 z-50">
      <Link to="/" className="flex items-center gap-2.5 font-bold text-white shrink-0">
        <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-sm shadow">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
          </svg>
        </div>
        <span className="hidden sm:block text-sm tracking-tight">Personal Research Assistant</span>
      </Link>

      <div className="flex items-center gap-1 ml-auto sm:ml-4">
        {NAV_LINKS.map(link => (
          <Link
            key={link.to}
            to={link.to}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              pathname.startsWith(link.to)
                ? 'bg-indigo-600 text-white'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            <span className="sm:hidden">{link.icon}</span>
            <span className="hidden sm:inline">{link.label}</span>
          </Link>
        ))}
      </div>
    </nav>
  );
}
