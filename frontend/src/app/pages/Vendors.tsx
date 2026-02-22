import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router';
import { Sidebar } from '../components/Sidebar';
import { Footer } from '../components/Footer';
import { VercelBackground } from '../components/VercelBackground';
import {
  Search,
  Download,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
} from 'lucide-react';
import { mockVendors } from '../data/mockVendors';
import { useAppLanguage } from '../i18n/AppLanguageProvider';

// Smooth color interpolation: red -> amber -> cyan -> green
function lerpHex(a: string, b: string, t: number): string {
  const p = (h: string, i: number) => parseInt(h.slice(i, i + 2), 16);
  const r = Math.round(p(a, 1) + (p(b, 1) - p(a, 1)) * t);
  const g = Math.round(p(a, 3) + (p(b, 3) - p(a, 3)) * t);
  const bv = Math.round(p(a, 5) + (p(b, 5) - p(a, 5)) * t);
  return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${bv.toString(16).padStart(2, '0')}`;
}

function getScoreColor(score: number): string {
  const s = Math.max(0, Math.min(100, score));
  if (s <= 50) return lerpHex('#FF0055', '#FFB800', s / 50);
  if (s <= 75) return lerpHex('#FFB800', '#00F2FF', (s - 50) / 25);
  return lerpHex('#00F2FF', '#00FF94', (s - 75) / 25);
}

function parseCurrency(value: string): number {
  const numericValue = Number(value.replace(/[^0-9.-]/g, ''));
  return Number.isNaN(numericValue) ? 0 : numericValue;
}

const TrustScoreBar = ({ score }: { score: number }) => {
  const color = getScoreColor(score);
  return (
    <div className="flex flex-col items-end gap-1">
      <span className="text-sm font-bold tabular-nums" style={{ color }}>
        {score}
      </span>
      <div
        className="w-14 xl:w-16 rounded-full overflow-hidden shrink-0"
        style={{ height: '3px', background: 'rgba(255,255,255,0.05)' }}
      >
        <div
          style={{
            width: `${score}%`,
            height: '100%',
            borderRadius: '9999px',
            background: color,
            opacity: 0.8,
          }}
        />
      </div>
    </div>
  );
};

const ITEMS_PER_PAGE = 10;
type VendorSortKey = 'name' | 'category' | 'paid' | 'pending' | 'rejected' | 'totalAmount' | 'trustScore';
type SortDirection = 'asc' | 'desc';

export default function Vendors() {
  const language = useAppLanguage();
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [sortConfig, setSortConfig] = useState<{ key: VendorSortKey; direction: SortDirection } | null>(null);

  const copy = {
    fr: {
      title: 'Gestion des fournisseurs',
      subtitle: 'Tous les émetteurs de factures — cliquer sur un vendor pour voir son historique',
      searchPlaceholder: 'Rechercher un vendor ou une catégorie...',
      tableVendor: 'Vendor',
      tableCategory: 'Catégorie',
      tablePaid: 'Payées',
      tablePending: 'En cours',
      tableRejected: 'Rejetées',
      tableTotal: 'Montant total',
      tableTrust: 'Trust Score',
      noResult: 'Aucun vendor ne correspond à votre recherche.',
      paginationSur: 'sur',
      paginationVendors: 'vendors',
      paginationNoResult: 'Aucun résultat',
    },
    en: {
      title: 'Vendor Management',
      subtitle: 'All invoice issuers — click on a vendor to see history',
      searchPlaceholder: 'Search a vendor or category...',
      tableVendor: 'Vendor',
      tableCategory: 'Category',
      tablePaid: 'Paid',
      tablePending: 'Pending',
      tableRejected: 'Rejected',
      tableTotal: 'Total amount',
      tableTrust: 'Trust Score',
      noResult: 'No vendor matches your search.',
      paginationSur: 'of',
      paginationVendors: 'vendors',
      paginationNoResult: 'No results',
    },
    de: {
      title: 'Lieferantenmanagement',
      subtitle: 'Alle Rechnungsaussteller — Klicken Sie auf einen Lieferanten, um den Verlauf anzuzeigen',
      searchPlaceholder: 'Lieferant oder Kategorie suchen...',
      tableVendor: 'Lieferant',
      tableCategory: 'Kategorie',
      tablePaid: 'Bezahlt',
      tablePending: 'Ausstehend',
      tableRejected: 'Abgelehnt',
      tableTotal: 'Gesamtbetrag',
      tableTrust: 'Trust Score',
      noResult: 'Kein Lieferant entspricht Ihrer Suche.',
      paginationSur: 'von',
      paginationVendors: 'Lieferanten',
      paginationNoResult: 'Keine Ergebnisse',
    },
  }[language];

  const filtered = useMemo(() => {
    return mockVendors.filter((vendor) => {
      return (
        vendor.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        vendor.category.toLowerCase().includes(searchTerm.toLowerCase())
      );
    });
  }, [searchTerm]);

  const sorted = useMemo(() => {
    if (!sortConfig) {
      return filtered;
    }

    const sortedList = [...filtered].sort((a, b) => {
      let comparison = 0;

      switch (sortConfig.key) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'category':
          comparison = a.category.localeCompare(b.category);
          break;
        case 'paid':
          comparison = a.paid - b.paid;
          break;
        case 'pending':
          comparison = a.pending - b.pending;
          break;
        case 'rejected':
          comparison = a.rejected - b.rejected;
          break;
        case 'totalAmount':
          comparison = parseCurrency(a.totalAmount) - parseCurrency(b.totalAmount);
          break;
        case 'trustScore':
          comparison = a.trustScore - b.trustScore;
          break;
      }

      return sortConfig.direction === 'asc' ? comparison : -comparison;
    });

    return sortedList;
  }, [filtered, sortConfig]);

  const totalPages = Math.ceil(sorted.length / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const paginated = sorted.slice(startIndex, startIndex + ITEMS_PER_PAGE);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
    setCurrentPage(1);
  };

  const toggleSort = (key: VendorSortKey) => {
    setCurrentPage(1);

    setSortConfig((previous) => {
      if (!previous || previous.key !== key) {
        return { key, direction: 'asc' };
      }

      if (previous.direction === 'asc') {
        return { key, direction: 'desc' };
      }

      return null;
    });
  };

  const getSortIndicator = (key: VendorSortKey): string => {
    if (!sortConfig || sortConfig.key !== key) {
      return '↕';
    }

    return sortConfig.direction === 'asc' ? '▲' : '▼';
  };

  const card: React.CSSProperties = {
    background: 'rgba(20, 22, 25, 0.6)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    boxShadow: 'inset 0 1px 0 0 rgba(255, 255, 255, 0.1)',
  };

  return (
    <div className="flex min-h-screen relative overflow-hidden">
      <VercelBackground />
      <Sidebar />

      <main className="flex-1 min-w-0 lg:ml-64 p-4 pt-20 lg:pt-8 md:p-5 xl:p-8 relative z-10">
        <div className="mb-5 xl:mb-8">
          <h1
            className="text-2xl md:text-3xl xl:text-4xl mb-1"
            style={{
              fontFamily: 'Geist Sans, Inter, sans-serif',
              fontWeight: 700,
              letterSpacing: '-0.02em',
              color: '#FAFAFA',
            }}
          >
            {copy.title}
          </h1>
          <p className="text-[#71717A] text-xs md:text-sm">{copy.subtitle}</p>
        </div>

        <div
          className="rounded-xl p-3 xl:p-4 mb-4 xl:mb-6 backdrop-blur-[20px]"
          style={card}
        >
          <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
            <div className="relative group flex-1 min-w-0">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#71717A] group-focus-within:text-[#00F2FF] transition-colors pointer-events-none" />
              <input
                type="text"
                placeholder={copy.searchPlaceholder}
                value={searchTerm}
                onChange={handleSearchChange}
                className="w-full pl-9 pr-3 py-2 xl:py-2.5 rounded-lg text-sm text-white placeholder-[#52525B] transition-all outline-none"
                style={{ background: 'rgba(6, 7, 9, 0.8)', border: '1px solid rgba(255, 255, 255, 0.1)' }}
                onFocus={(e) => { e.target.style.border = '1px solid #00F2FF'; }}
                onBlur={(e) => { e.target.style.border = '1px solid rgba(255, 255, 255, 0.1)'; }}
              />
            </div>

            <button
              className="px-3 py-2 xl:py-2.5 rounded-lg text-[#00F2FF] transition-all shrink-0 self-start sm:self-auto"
              style={{ background: 'rgba(6, 7, 9, 0.8)', border: '1px solid rgba(255, 255, 255, 0.1)' }}
              onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(0, 242, 255, 0.08)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(6, 7, 9, 0.8)'; }}
            >
              <Download className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="rounded-xl overflow-hidden backdrop-blur-[20px]" style={card}>
          <div className="overflow-x-auto">
            <table className="w-full" style={{ minWidth: '640px' }}>
              <thead style={{ background: 'rgba(6, 7, 9, 0.8)', borderColor: 'rgba(255, 255, 255, 0.1)' }}>
                <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }}>
                  <th className="px-3 xl:px-4 py-3 text-left text-xs text-[#71717A] uppercase tracking-wider font-medium">
                    <button type="button" className="inline-flex items-center gap-1" onClick={() => toggleSort('name')}>
                      <span>{copy.tableVendor}</span>
                      <span className="text-[10px] text-[#52525B]">{getSortIndicator('name')}</span>
                    </button>
                  </th>
                  <th className="hidden xl:table-cell px-3 xl:px-4 py-3 text-left text-xs text-[#71717A] uppercase tracking-wider font-medium">
                    <button type="button" className="inline-flex items-center gap-1" onClick={() => toggleSort('category')}>
                      <span>{copy.tableCategory}</span>
                      <span className="text-[10px] text-[#52525B]">{getSortIndicator('category')}</span>
                    </button>
                  </th>
                  <th className="px-3 xl:px-4 py-3 text-center text-xs text-[#00FF94] uppercase tracking-wider font-medium">
                    <button type="button" className="inline-flex items-center gap-1" onClick={() => toggleSort('paid')}>
                      <span>{copy.tablePaid}</span>
                      <span className="text-[10px] text-[#52525B]">{getSortIndicator('paid')}</span>
                    </button>
                  </th>
                  <th className="px-3 xl:px-4 py-3 text-center text-xs text-[#00F2FF] uppercase tracking-wider font-medium">
                    <button type="button" className="inline-flex items-center gap-1" onClick={() => toggleSort('pending')}>
                      <span>{copy.tablePending}</span>
                      <span className="text-[10px] text-[#52525B]">{getSortIndicator('pending')}</span>
                    </button>
                  </th>
                  <th className="px-3 xl:px-4 py-3 text-center text-xs text-[#FF0055] uppercase tracking-wider font-medium">
                    <button type="button" className="inline-flex items-center gap-1" onClick={() => toggleSort('rejected')}>
                      <span>{copy.tableRejected}</span>
                      <span className="text-[10px] text-[#52525B]">{getSortIndicator('rejected')}</span>
                    </button>
                  </th>
                  <th className="px-3 xl:px-4 py-3 text-left text-xs text-[#71717A] uppercase tracking-wider font-medium">
                    <button type="button" className="inline-flex items-center gap-1" onClick={() => toggleSort('totalAmount')}>
                      <span>{copy.tableTotal}</span>
                      <span className="text-[10px] text-[#52525B]">{getSortIndicator('totalAmount')}</span>
                    </button>
                  </th>
                  <th className="px-3 xl:px-4 py-3 text-right text-xs text-[#71717A] uppercase tracking-wider font-medium">
                    <button type="button" className="inline-flex items-center gap-1" onClick={() => toggleSort('trustScore')}>
                      <span>{copy.tableTrust}</span>
                      <span className="text-[10px] text-[#52525B]">{getSortIndicator('trustScore')}</span>
                    </button>
                  </th>
                </tr>
              </thead>

              <tbody>
                {paginated.map((vendor, index) => (
                  <tr
                    key={vendor.id}
                    className="transition-all duration-200 cursor-pointer"
                    style={{
                      borderBottom: index < paginated.length - 1
                        ? '1px solid rgba(255, 255, 255, 0.05)'
                        : 'none',
                    }}
                    onClick={() => navigate(`/vendors/${vendor.id}`)}
                    onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255, 255, 255, 0.02)'; }}
                    onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
                  >
                    <td className="px-3 xl:px-4 py-3 xl:py-4">
                      <span
                        className="text-sm text-[#FAFAFA] font-medium block truncate"
                        style={{ maxWidth: '180px' }}
                        title={vendor.name}
                      >
                        {vendor.name}
                      </span>
                    </td>

                    <td className="hidden xl:table-cell px-3 xl:px-4 py-3 xl:py-4 text-sm text-[#71717A] whitespace-nowrap">
                      {vendor.category}
                    </td>

                    <td className="px-3 xl:px-4 py-3 xl:py-4 text-center">
                      <span
                        className="inline-flex items-center justify-center min-w-[2rem] px-2 py-1 rounded-md text-xs font-semibold"
                        style={{
                          background: 'rgba(0, 255, 148, 0.06)',
                          color: '#00FF94',
                          border: '1px solid rgba(0, 255, 148, 0.2)',
                        }}
                      >
                        {vendor.paid}
                      </span>
                    </td>

                    <td className="px-3 xl:px-4 py-3 xl:py-4 text-center">
                      <span
                        className="inline-flex items-center justify-center min-w-[2rem] px-2 py-1 rounded-md text-xs font-semibold"
                        style={{
                          background: vendor.pending > 0 ? 'rgba(0, 242, 255, 0.06)' : 'transparent',
                          color: vendor.pending > 0 ? '#00F2FF' : '#52525B',
                          border: vendor.pending > 0 ? '1px solid rgba(0, 242, 255, 0.2)' : '1px solid rgba(255,255,255,0.05)',
                        }}
                      >
                        {vendor.pending}
                      </span>
                    </td>

                    <td className="px-3 xl:px-4 py-3 xl:py-4 text-center">
                      <span
                        className="inline-flex items-center justify-center min-w-[2rem] px-2 py-1 rounded-md text-xs font-semibold"
                        style={{
                          background: vendor.rejected > 0 ? 'rgba(255, 0, 85, 0.06)' : 'transparent',
                          color: vendor.rejected > 0 ? '#FF0055' : '#52525B',
                          border: vendor.rejected > 0 ? '1px solid rgba(255, 0, 85, 0.2)' : '1px solid rgba(255,255,255,0.05)',
                        }}
                      >
                        {vendor.rejected}
                      </span>
                    </td>

                    <td className="px-3 xl:px-4 py-3 xl:py-4 text-sm text-[#FAFAFA] font-semibold whitespace-nowrap">
                      {vendor.totalAmount}
                    </td>

                    <td className="px-3 xl:px-4 py-3 xl:py-4">
                      <div className="flex justify-end">
                        <TrustScoreBar score={vendor.trustScore} />
                      </div>
                    </td>
                  </tr>
                ))}

                {paginated.length === 0 && (
                  <tr>
                    <td colSpan={7} className="px-4 py-14 text-center text-[#52525B] text-sm">
                      <ShieldCheck className="w-8 h-8 mx-auto mb-3 text-[#27272A]" />
                      {copy.noResult}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <div
            className="px-3 xl:px-4 py-3 border-t flex flex-wrap items-center justify-between gap-2"
            style={{ background: 'rgba(6, 7, 9, 0.8)', borderColor: 'rgba(255, 255, 255, 0.1)' }}
          >
            <div className="text-xs text-[#71717A] shrink-0">
              {sorted.length === 0
                ? copy.paginationNoResult
                : `${startIndex + 1}-${Math.min(startIndex + ITEMS_PER_PAGE, sorted.length)} ${copy.paginationSur} ${sorted.length} ${copy.paginationVendors}`}
            </div>

            <div className="flex flex-wrap gap-1 justify-end">
              <button
                onClick={() => setCurrentPage((page) => Math.max(1, page - 1))}
                disabled={currentPage === 1}
                className="p-2 rounded-lg text-white transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                style={{ background: 'rgba(20, 22, 25, 0.6)', border: '1px solid rgba(255, 255, 255, 0.1)' }}
              >
                <ChevronLeft className="w-4 h-4" />
              </button>

              {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                <button
                  key={page}
                  onClick={() => setCurrentPage(page)}
                  className="px-3 py-2 rounded-lg text-sm transition-all"
                  style={
                    currentPage === page
                      ? { background: '#00F2FF', color: '#060709', fontWeight: 600, border: '1px solid rgba(255,255,255,0.2)' }
                      : { background: 'rgba(20, 22, 25, 0.6)', border: '1px solid rgba(255,255,255,0.1)', color: '#FAFAFA' }
                  }
                >
                  {page}
                </button>
              ))}

              <button
                onClick={() => setCurrentPage((page) => Math.min(totalPages, page + 1))}
                disabled={currentPage === totalPages || totalPages === 0}
                className="p-2 rounded-lg text-white transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                style={{ background: 'rgba(20, 22, 25, 0.6)', border: '1px solid rgba(255, 255, 255, 0.1)' }}
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        <Footer />
      </main>
    </div>
  );
}
