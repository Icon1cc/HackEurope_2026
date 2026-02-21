import { useEffect, useRef, useState, useMemo } from 'react';
import { Link, useLocation, useNavigate, useParams } from 'react-router';
import { LayoutDashboard, Users, Settings, Shield, Menu, X, LogOut, ChevronUp, ChevronRight, Building2 } from 'lucide-react';
import { loadAppSettings } from '../data/appSettings';
import { useAppLanguage } from '../i18n/AppLanguageProvider';
import { pendingReviews } from '../data/pendingReviews';
import { mockVendorInvoices, mockVendors } from '../data/mockVendors';

const navItems = [
  { path: '/dashboard', labelKey: 'dashboard', icon: LayoutDashboard },
  { path: '/vendors', labelKey: 'vendors', icon: Users },
] as const;

function getInitials(name: string): string {
  const segments = name
    .trim()
    .split(/\s+/)
    .filter(Boolean);

  if (segments.length === 0) {
    return 'IG';
  }

  return segments
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join('');
}

export function Sidebar() {
  const language = useAppLanguage();
  const location = useLocation();
  const navigate = useNavigate();
  
  // Detect if we are on a review page and find the vendor
  const activeVendor = useMemo(() => {
    const reviewMatch = location.pathname.match(/\/reviews\/([^\/]+)/);
    if (!reviewMatch) return null;
    
    const reviewId = reviewMatch[1];
    
    // Check pendingReviews
    const pending = pendingReviews.find(r => r.id === reviewId);
    if (pending) {
      // Find vendor by name in pending reviews (since they use names)
      return mockVendors.find(v => v.name === pending.vendor);
    }
    
    // Check standard invoices
    const invoice = mockVendorInvoices.find(i => i.id === reviewId);
    if (invoice) {
      return mockVendors.find(v => v.id === invoice.vendorId);
    }
    
    return null;
  }, [location.pathname]);

  const [isOpen, setIsOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const userMenuRef = useRef<HTMLDivElement | null>(null);
  const copy = language === 'fr'
    ? {
        nav: { dashboard: 'Dashboard', vendors: 'Fournisseurs' },
        userMenu: { settings: 'Paramètres', signOut: 'Déconnexion' },
      }
    : {
        nav: { dashboard: 'Dashboard', vendors: 'Vendors' },
        userMenu: { settings: 'Settings', signOut: 'Sign out' },
      };
  const [user, setUser] = useState(() => {
    const settings = loadAppSettings();
    return {
      name: settings.profileName,
      email: settings.profileEmail,
      company: settings.companyName,
      initials: getInitials(settings.profileName),
    };
  });

  const toggleSidebar = () => setIsOpen(!isOpen);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setIsUserMenuOpen(false);
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsUserMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, []);

  useEffect(() => {
    const refreshUser = () => {
      const settings = loadAppSettings();
      setUser({
        name: settings.profileName,
        email: settings.profileEmail,
        company: settings.companyName,
        initials: getInitials(settings.profileName),
      });
    };

    window.addEventListener('storage', refreshUser);
    window.addEventListener('invoiceguard:settings-updated', refreshUser);

    return () => {
      window.removeEventListener('storage', refreshUser);
      window.removeEventListener('invoiceguard:settings-updated', refreshUser);
    };
  }, []);

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={toggleSidebar}
        className="lg:hidden fixed top-4 left-4 z-[60] p-2 rounded-lg backdrop-blur-md transition-all border border-white/10"
        style={{ background: 'rgba(6, 7, 9, 0.8)' }}
      >
        {isOpen ? <X className="w-6 h-6 text-[#FAFAFA]" /> : <Menu className="w-6 h-6 text-[#FAFAFA]" />}
      </button>

      {/* Backdrop */}
      {isOpen && (
        <div 
          className="lg:hidden fixed inset-0 bg-black/60 backdrop-blur-sm z-[45]"
          onClick={() => setIsOpen(false)}
        />
      )}

      <aside 
        className={`
          w-64 h-screen flex flex-col fixed left-0 top-0 backdrop-blur-[20px] z-50 transition-transform duration-300 ease-in-out
          ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
        style={{
          background: 'rgba(6, 7, 9, 0.8)',
          borderRight: '1px solid rgba(255, 255, 255, 0.1)',
        }}
      >
        {/* Logo */}
        <div 
          className="p-6 border-b"
          style={{ borderColor: 'rgba(255, 255, 255, 0.1)' }}
        >
          <Link to="/dashboard" className="flex items-center gap-3 group" onClick={() => setIsOpen(false)}>
            <Shield 
              className="w-8 h-8 text-[#00F2FF]" 
              strokeWidth={1.5}
            />
            <span 
              className="text-xl"
              style={{ 
                fontFamily: 'Geist Sans, Inter, sans-serif',
                fontWeight: 700,
                letterSpacing: '-0.02em',
                color: '#FAFAFA',
              }}
            >
              InvoiceGuard
            </span>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4">
          <ul className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path || location.pathname.startsWith(`${item.path}/`);
              
              return (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    onClick={() => setIsOpen(false)}
                    className={`
                      flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200
                      ${isActive ? 'text-[#FAFAFA]' : 'text-[#71717A] hover:text-[#FAFAFA]'}
                    `}
                    style={isActive ? {
                      background: 'rgba(0, 242, 255, 0.08)',
                      border: '1px solid rgba(0, 242, 255, 0.2)',
                    } : {
                      background: 'transparent',
                      border: '1px solid transparent',
                    }}
                    onMouseEnter={(e) => {
                      if (!isActive) {
                        e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isActive) {
                        e.currentTarget.style.background = 'transparent';
                      }
                    }}
                  >
                    <Icon className={`w-5 h-5 ${isActive ? 'text-[#00F2FF]' : ''}`} />
                    <span className="text-sm font-medium">{copy.nav[item.labelKey]}</span>
                  </Link>

                  {/* Dynamic Sub-item for Active Vendor during Review */}
                  {item.labelKey === 'vendors' && activeVendor && (
                    <ul className="mt-1 ml-4 pl-4 border-l border-white/10 space-y-1">
                      <li>
                        <Link
                          to={`/vendors/${activeVendor.id}`}
                          onClick={() => setIsOpen(false)}
                          className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-[#00F2FF] bg-[rgba(0,242,255,0.04)] border border-[rgba(0,242,255,0.15)] transition-all hover:bg-[rgba(0,242,255,0.08)]"
                        >
                          <Building2 className="w-3.5 h-3.5" />
                          <span className="font-medium truncate">{activeVendor.name}</span>
                          <ChevronRight className="w-3 h-3 ml-auto opacity-50" />
                        </Link>
                      </li>
                    </ul>
                  )}
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Footer */}
        <div 
          className="p-4 border-t"
          style={{ borderColor: 'rgba(255, 255, 255, 0.1)' }}
        >
          <div className="relative" ref={userMenuRef}>
            {isUserMenuOpen && (
              <div
                className="absolute bottom-full mb-2 left-0 right-0 rounded-lg p-2 backdrop-blur-[20px]"
                style={{
                  background: 'rgba(20, 22, 25, 0.95)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  boxShadow: '0 8px 24px rgba(0, 0, 0, 0.35)',
                }}
              >
                <button
                  type="button"
                  className="w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm text-left transition-colors"
                  style={{ color: '#FAFAFA' }}
                  onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.04)'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
                  onClick={() => {
                    setIsUserMenuOpen(false);
                    setIsOpen(false);
                    navigate('/settings');
                  }}
                >
                  <Settings className="w-4 h-4 text-[#00F2FF]" />
                  <span>{copy.userMenu.settings}</span>
                </button>
                <button
                  type="button"
                  className="w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm text-left transition-colors"
                  style={{ color: '#FAFAFA' }}
                  onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.04)'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
                  onClick={() => {
                    setIsUserMenuOpen(false);
                    setIsOpen(false);
                    navigate('/');
                  }}
                >
                  <LogOut className="w-4 h-4 text-[#FF0055]" />
                  <span>{copy.userMenu.signOut}</span>
                </button>
              </div>
            )}

            <button
              type="button"
              className="w-full flex items-center gap-3 p-2.5 rounded-lg transition-all"
              style={{
                background: 'rgba(20, 22, 25, 0.75)',
                border: '1px solid rgba(255, 255, 255, 0.12)',
              }}
              onClick={() => setIsUserMenuOpen((open) => !open)}
            >
              <div
                className="w-9 h-9 rounded-lg flex items-center justify-center text-sm font-semibold"
                style={{
                  color: '#060709',
                  background: '#00F2FF',
                }}
              >
                {user.initials}
              </div>
              <div className="flex-1 min-w-0 text-left">
                <p className="text-sm text-[#FAFAFA] font-medium truncate">{user.name}</p>
                <p className="text-xs text-[#71717A] truncate" title={user.email}>
                  {user.company} • {user.email}
                </p>
              </div>
              <ChevronUp
                className={`w-4 h-4 text-[#71717A] transition-transform ${isUserMenuOpen ? 'rotate-0' : 'rotate-180'}`}
              />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
