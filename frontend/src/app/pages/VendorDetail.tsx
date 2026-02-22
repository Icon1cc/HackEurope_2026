import { useMemo, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router';
import { Sidebar } from '../components/Sidebar';
import { VercelBackground } from '../components/VercelBackground';
import {
  ArrowLeft,
  Building2,
  Search,
  Download,
  ChevronLeft,
  ChevronRight,
  FileText,
  CheckCircle,
  Clock,
  XCircle,
} from 'lucide-react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { mockVendors, mockVendorInvoices } from '../data/mockVendors';
import type { VendorInvoice } from '../data/mockVendors';
import { useAppLanguage } from '../i18n/AppLanguageProvider';

const ITEMS_PER_PAGE = 8;
type InvoiceSortKey = 'date' | 'invoiceNumber' | 'amount' | 'status';
type SortDirection = 'asc' | 'desc';

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

function getInvoiceScore(invoice: VendorInvoice): number {
  const baseScoreByStatus: Record<VendorInvoice['status'], number> = {
    paid: 92,
    pending: 66,
    flagged: 44,
    rejected: 28,
  };
  const numericId = Number(invoice.id.replace(/\D/g, ''));
  const variance = Number.isNaN(numericId) ? 0 : (numericId % 7) - 3;
  const score = baseScoreByStatus[invoice.status] + variance;
  return Math.max(0, Math.min(100, score));
}

const getStatusStyles = (status: VendorInvoice['status']) => {
  switch (status) {
    case 'paid':
      return { color: '#00FF94', border: 'rgba(0, 255, 148, 0.3)', bg: 'rgba(0, 255, 148, 0.06)' };
    case 'pending':
      return { color: '#00F2FF', border: 'rgba(0, 242, 255, 0.3)', bg: 'rgba(0, 242, 255, 0.06)' };
    case 'flagged':
      return { color: '#FFB800', border: 'rgba(255, 184, 0, 0.3)', bg: 'rgba(255, 184, 0, 0.06)' };
    case 'rejected':
      return { color: '#FF0055', border: 'rgba(255, 0, 85, 0.3)', bg: 'rgba(255, 0, 85, 0.06)' };
  }
};

export default function VendorDetail() {
  const language = useAppLanguage();
  const { vendorId } = useParams<{ vendorId: string }>();
  const navigate = useNavigate();

  const vendor = mockVendors.find((v) => v.id === vendorId);
  const allInvoices = mockVendorInvoices.filter((i) => i.vendorId === vendorId);

  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [sortConfig, setSortConfig] = useState<{ key: InvoiceSortKey; direction: SortDirection } | null>(null);

  const copy = {
    fr: {
      notFound: 'Vendor introuvable.',
      backToVendors: 'Retour aux vendors',
      vendors: 'Vendors',
      totalInvoices: 'Total factures',
      paid: 'Payées',
      processing: 'En cours',
      rejected: 'Rejetées',
      searchPlaceholder: 'Rechercher par numéro de facture...',
      tableDate: 'Date',
      tableInvoice: 'Facture #',
      tableAmount: 'Montant',
      tableStatus: 'Statut',
      chartTitle: 'Score des factures dans le temps',
      chartSubtitle: 'Évolution du score de confiance pour chaque facture',
      chartLatest: 'Dernière facture',
      chartAverage: 'Moyenne',
      chartTooltipScore: 'Score facture',
      noResult: 'Aucune facture ne correspond à votre recherche.',
      paginationSur: 'sur',
      paginationInvoices: 'factures',
      paginationNoResult: 'Aucun résultat',
    },
    en: {
      notFound: 'Vendor not found.',
      backToVendors: 'Back to vendors',
      vendors: 'Vendors',
      totalInvoices: 'Total invoices',
      paid: 'Paid',
      processing: 'Pending',
      rejected: 'Rejected',
      searchPlaceholder: 'Search by invoice number...',
      tableDate: 'Date',
      tableInvoice: 'Invoice #',
      tableAmount: 'Amount',
      tableStatus: 'Status',
      chartTitle: 'Invoice score over time',
      chartSubtitle: 'Trust score trend across vendor invoices',
      chartLatest: 'Latest invoice',
      chartAverage: 'Average',
      chartTooltipScore: 'Invoice score',
      noResult: 'No invoice matches your search.',
      paginationSur: 'of',
      paginationInvoices: 'invoices',
      paginationNoResult: 'No results',
    },
    de: {
      notFound: 'Lieferant nicht gefunden.',
      backToVendors: 'Zurück zu Lieferanten',
      vendors: 'Lieferanten',
      totalInvoices: 'Gesamt Rechnungen',
      paid: 'Bezahlt',
      processing: 'Ausstehend',
      rejected: 'Abgelehnt',
      searchPlaceholder: 'Suche nach Rechnungsnummer...',
      tableDate: 'Datum',
      tableInvoice: 'Rechnung #',
      tableAmount: 'Betrag',
      tableStatus: 'Status',
      chartTitle: 'Rechnungs-Score im Zeitverlauf',
      chartSubtitle: 'Trend des Vertrauens-Scores über Lieferantenrechnungen',
      chartLatest: 'Letzte Rechnung',
      chartAverage: 'Durchschnitt',
      chartTooltipScore: 'Rechnungs-Score',
      noResult: 'Keine Rechnung entspricht Ihrer Suche.',
      paginationSur: 'von',
      paginationInvoices: 'Rechnungen',
      paginationNoResult: 'Keine Ergebnisse',
    },
  }[language];

  const scoreTrendData = useMemo(() => {
    return [...allInvoices]
      .sort((a, b) => a.date.localeCompare(b.date))
      .map((invoice) => ({
        date: invoice.date,
        invoiceNumber: invoice.invoiceNumber,
        score: getInvoiceScore(invoice),
      }));
  }, [allInvoices]);

  const filtered = useMemo(() => {
    return allInvoices.filter((invoice) => {
      return invoice.invoiceNumber.toLowerCase().includes(searchTerm.toLowerCase());
    });
  }, [allInvoices, searchTerm]);

  const sorted = useMemo(() => {
    if (!sortConfig) {
      return filtered;
    }

    const sortedList = [...filtered].sort((a, b) => {
      let comparison = 0;

      switch (sortConfig.key) {
        case 'date':
          comparison = a.date.localeCompare(b.date);
          break;
        case 'invoiceNumber':
          comparison = a.invoiceNumber.localeCompare(b.invoiceNumber);
          break;
        case 'amount':
          comparison = parseCurrency(a.amount) - parseCurrency(b.amount);
          break;
        case 'status':
          comparison = a.status.localeCompare(b.status);
          break;
      }

      return sortConfig.direction === 'asc' ? comparison : -comparison;
    });

    return sortedList;
  }, [filtered, sortConfig]);

  if (!vendor) {
    return (
      <div className="flex min-h-screen relative overflow-hidden">
        <VercelBackground />
        <Sidebar />
        <main className="flex-1 lg:ml-64 p-8 relative z-10 flex items-center justify-center">
          <div className="text-center">
            <p className="text-[#71717A] mb-4">{copy.notFound}</p>
            <button
              onClick={() => navigate('/vendors')}
              className="px-4 py-2 rounded-lg text-sm text-[#00F2FF] transition-all"
              style={{ background: 'rgba(0, 242, 255, 0.08)', border: '1px solid rgba(0, 242, 255, 0.2)' }}
            >
              {copy.backToVendors}
            </button>
          </div>
        </main>
      </div>
    );
  }

  const scoreColor = getScoreColor(vendor.trustScore);
  const lineGradientId = `invoice-score-line-gradient-${vendor.id}`;
  const glowGradientId = `invoice-score-glow-gradient-${vendor.id}`;
  const latestInvoiceScore = scoreTrendData.at(-1)?.score ?? vendor.trustScore;
  const averageInvoiceScore = scoreTrendData.length === 0
    ? 0
    : Math.round(scoreTrendData.reduce((sum, point) => sum + point.score, 0) / scoreTrendData.length);

  const totalPages = Math.ceil(sorted.length / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const paginated = sorted.slice(startIndex, startIndex + ITEMS_PER_PAGE);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
    setCurrentPage(1);
  };

  const toggleSort = (key: InvoiceSortKey) => {
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

  const getSortIndicator = (key: InvoiceSortKey): string => {
    if (!sortConfig || sortConfig.key !== key) {
      return '↕';
    }

    return sortConfig.direction === 'asc' ? '▲' : '▼';
  };

  const formatTrendDate = (value: string): string => {
    const date = new Date(`${value}T00:00:00`);
    if (Number.isNaN(date.getTime())) {
      return value;
    }

    return language === 'fr'
      ? date.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' })
      : date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <div className="flex min-h-screen relative overflow-hidden">
      <VercelBackground />
      <Sidebar />

      <main className="flex-1 lg:ml-64 p-4 pt-20 lg:pt-8 sm:px-6 sm:py-6 lg:p-8 relative z-10">
        <div className="flex items-center gap-2 mb-6 text-sm">
          <button
            onClick={() => navigate('/vendors')}
            className="flex items-center gap-1.5 text-[#71717A] hover:text-[#FAFAFA] transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            {copy.vendors}
          </button>
          <span className="text-[#3F3F46]">/</span>
          <span className="text-[#FAFAFA]">{vendor.name}</span>
        </div>

        <div
          className="rounded-xl p-6 mb-6 backdrop-blur-[20px]"
          style={{
            background: 'rgba(20, 22, 25, 0.6)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            boxShadow: 'inset 0 1px 0 0 rgba(255, 255, 255, 0.1)',
          }}
        >
          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-6">
            <div className="flex items-center gap-4">
              <div
                className="w-14 h-14 rounded-xl flex items-center justify-center shrink-0"
                style={{ background: `${scoreColor}12`, border: `1px solid ${scoreColor}35` }}
              >
                <Building2 className="w-7 h-7" style={{ color: scoreColor }} />
              </div>
              <div>
                <h1
                  className="text-2xl sm:text-3xl mb-0.5"
                  style={{
                    fontFamily: 'Geist Sans, Inter, sans-serif',
                    fontWeight: 700,
                    letterSpacing: '-0.02em',
                    color: '#FAFAFA',
                  }}
                >
                  {vendor.name}
                </h1>
                <p className="text-[#71717A] text-sm">{vendor.category}</p>
              </div>
            </div>

            <div className="flex flex-col items-end gap-2">
              <span className="text-xs text-[#71717A] uppercase tracking-wider">Trust Score</span>
              <span
                className="text-4xl font-bold tabular-nums"
                style={{ fontFamily: 'Geist Sans, Inter, sans-serif', color: scoreColor }}
              >
                {vendor.trustScore}
              </span>
              <div className="w-24 rounded-full overflow-hidden" style={{ height: '4px', background: 'rgba(255,255,255,0.05)' }}>
                <div
                  style={{
                    width: `${vendor.trustScore}%`,
                    height: '100%',
                    borderRadius: '9999px',
                    background: scoreColor,
                    opacity: 0.8,
                  }}
                />
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-5" style={{ borderTop: '1px solid rgba(255,255,255,0.07)' }}>
            {[
              { icon: FileText, label: copy.totalInvoices, value: vendor.paid + vendor.pending + vendor.rejected, color: '#FAFAFA' },
              { icon: CheckCircle, label: copy.paid, value: vendor.paid, color: '#00FF94' },
              { icon: Clock, label: copy.processing, value: vendor.pending, color: '#00F2FF' },
              { icon: XCircle, label: copy.rejected, value: vendor.rejected, color: '#FF0055' },
            ].map(({ icon: Icon, label, value, color }) => (
              <div key={label} className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0" style={{ background: `${color}10`, border: `1px solid ${color}30` }}>
                  <Icon className="w-4 h-4" style={{ color }} />
                </div>
                <div>
                  <p className="text-[10px] text-[#71717A] mb-0.5 uppercase tracking-wider">{label}</p>
                  <p className="text-lg font-bold" style={{ color, fontFamily: 'Geist Sans, Inter, sans-serif' }}>
                    {value}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div
          className="rounded-xl p-4 sm:p-6 mb-6 backdrop-blur-[20px]"
          style={{
            background: 'rgba(20, 22, 25, 0.6)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            boxShadow: 'inset 0 1px 0 0 rgba(255, 255, 255, 0.1)',
          }}
        >
          <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4 mb-5">
            <div>
              <h2
                className="text-lg sm:text-xl"
                style={{
                  fontFamily: 'Geist Sans, Inter, sans-serif',
                  fontWeight: 600,
                  letterSpacing: '-0.02em',
                  color: '#FAFAFA',
                }}
              >
                {copy.chartTitle}
              </h2>
              <p className="text-xs sm:text-sm text-[#71717A] mt-1">{copy.chartSubtitle}</p>
            </div>

            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span
                className="px-2.5 py-1 rounded-md"
                style={{ background: 'rgba(0, 242, 255, 0.08)', border: '1px solid rgba(0, 242, 255, 0.25)', color: '#00F2FF' }}
              >
                {copy.chartLatest}: <strong className="font-semibold">{latestInvoiceScore}/100</strong>
              </span>
              <span
                className="px-2.5 py-1 rounded-md"
                style={{ background: 'rgba(0, 255, 148, 0.08)', border: '1px solid rgba(0, 255, 148, 0.25)', color: '#00FF94' }}
              >
                {copy.chartAverage}: <strong className="font-semibold">{averageInvoiceScore}/100</strong>
              </span>
            </div>
          </div>

          <div className="h-56 sm:h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={scoreTrendData} margin={{ top: 8, right: 16, left: 0, bottom: 4 }}>
                <defs>
                  <linearGradient id={lineGradientId} x1="0" y1="1" x2="0" y2="0">
                    <stop offset="0%" stopColor="#FF0055" />
                    <stop offset="35%" stopColor="#FFB800" />
                    <stop offset="70%" stopColor="#00F2FF" />
                    <stop offset="100%" stopColor="#00FF94" />
                  </linearGradient>
                  <linearGradient id={glowGradientId} x1="0" y1="1" x2="0" y2="0">
                    <stop offset="0%" stopColor="rgba(255, 0, 85, 0.24)" />
                    <stop offset="35%" stopColor="rgba(255, 184, 0, 0.2)" />
                    <stop offset="70%" stopColor="rgba(0, 242, 255, 0.2)" />
                    <stop offset="100%" stopColor="rgba(0, 255, 148, 0.24)" />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
                <XAxis
                  dataKey="date"
                  tickFormatter={formatTrendDate}
                  stroke="#71717A"
                  tickLine={false}
                  axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
                  style={{ fontSize: '12px' }}
                />
                <YAxis
                  domain={[0, 100]}
                  ticks={[0, 25, 50, 75, 100]}
                  stroke="#71717A"
                  tickLine={false}
                  axisLine={false}
                  style={{ fontSize: '12px' }}
                />
                <Tooltip
                  labelFormatter={(label) => formatTrendDate(String(label))}
                  formatter={(value: number | string) => [`${value}/100`, copy.chartTooltipScore]}
                  contentStyle={{
                    background: 'rgba(20, 22, 25, 0.95)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '8px',
                    color: '#FAFAFA',
                    backdropFilter: 'blur(20px)',
                    boxShadow: 'inset 0 1px 0 0 rgba(255, 255, 255, 0.1)',
                  }}
                  labelStyle={{ color: '#FAFAFA' }}
                  itemStyle={{ color: '#00F2FF' }}
                />
                <Line
                  type="monotone"
                  dataKey="score"
                  stroke={`url(#${glowGradientId})`}
                  strokeWidth={8}
                  dot={false}
                  activeDot={false}
                  isAnimationActive={false}
                />
                <Line
                  type="monotone"
                  dataKey="score"
                  stroke={`url(#${lineGradientId})`}
                  strokeWidth={2}
                  dot={{ r: 3, fill: '#00F2FF', stroke: '#060709', strokeWidth: 1.5 }}
                  activeDot={{ r: 5, fill: '#00FF94', stroke: '#060709', strokeWidth: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div
          className="rounded-xl p-4 mb-6 backdrop-blur-[20px]"
          style={{
            background: 'rgba(20, 22, 25, 0.6)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            boxShadow: 'inset 0 1px 0 0 rgba(255, 255, 255, 0.1)',
          }}
        >
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="md:col-span-2 relative group">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#71717A] group-focus-within:text-[#00F2FF] transition-colors" />
              <input
                type="text"
                placeholder={copy.searchPlaceholder}
                value={searchTerm}
                onChange={handleSearchChange}
                className="w-full pl-10 pr-3 py-2.5 rounded-lg text-sm text-white placeholder-[#52525B] transition-all outline-none"
                style={{ background: 'rgba(6, 7, 9, 0.8)', border: '1px solid rgba(255, 255, 255, 0.1)' }}
                onFocus={(e) => { e.target.style.border = '1px solid #00F2FF'; }}
                onBlur={(e) => { e.target.style.border = '1px solid rgba(255, 255, 255, 0.1)'; }}
              />
            </div>
            <button
              className="px-3 py-2.5 rounded-lg text-[#00F2FF] transition-all justify-self-start md:justify-self-stretch md:w-full"
              style={{ background: 'rgba(6, 7, 9, 0.8)', border: '1px solid rgba(255, 255, 255, 0.1)' }}
              onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(0, 242, 255, 0.08)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(6, 7, 9, 0.8)'; }}
            >
              <Download className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div
          className="rounded-xl overflow-hidden backdrop-blur-[20px]"
          style={{
            background: 'rgba(20, 22, 25, 0.6)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            boxShadow: 'inset 0 1px 0 0 rgba(255, 255, 255, 0.1)',
          }}
        >
          <div className="overflow-x-auto">
            <table className="w-full" style={{ minWidth: '680px' }}>
              <thead style={{ background: 'rgba(6, 7, 9, 0.8)', borderColor: 'rgba(255, 255, 255, 0.1)' }}>
                <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }}>
                  <th className="px-4 py-3 text-left text-xs text-[#71717A] uppercase tracking-wider font-medium">
                    <button type="button" className="inline-flex items-center gap-1" onClick={() => toggleSort('date')}>
                      <span>{copy.tableDate}</span>
                      <span className="text-[10px] text-[#52525B]">{getSortIndicator('date')}</span>
                    </button>
                  </th>
                  <th className="px-4 py-3 text-left text-xs text-[#71717A] uppercase tracking-wider font-medium">
                    <button type="button" className="inline-flex items-center gap-1" onClick={() => toggleSort('invoiceNumber')}>
                      <span>{copy.tableInvoice}</span>
                      <span className="text-[10px] text-[#52525B]">{getSortIndicator('invoiceNumber')}</span>
                    </button>
                  </th>
                  <th className="px-4 py-3 text-left text-xs text-[#71717A] uppercase tracking-wider font-medium">
                    <button type="button" className="inline-flex items-center gap-1" onClick={() => toggleSort('amount')}>
                      <span>{copy.tableAmount}</span>
                      <span className="text-[10px] text-[#52525B]">{getSortIndicator('amount')}</span>
                    </button>
                  </th>
                  <th className="px-4 py-3 text-left text-xs text-[#71717A] uppercase tracking-wider font-medium">
                    <button type="button" className="inline-flex items-center gap-1" onClick={() => toggleSort('status')}>
                      <span>{copy.tableStatus}</span>
                      <span className="text-[10px] text-[#52525B]">{getSortIndicator('status')}</span>
                    </button>
                  </th>
                </tr>
              </thead>
              <tbody>
                {paginated.map((invoice, index) => {
                  const statusStyles = getStatusStyles(invoice.status);
                  return (
                    <tr
                      key={invoice.id}
                      className="transition-all duration-200"
                      style={{
                        borderBottom: index < paginated.length - 1 ? '1px solid rgba(255, 255, 255, 0.05)' : 'none',
                      }}
                      onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255, 255, 255, 0.02)'; }}
                      onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
                    >
                      <td className="px-4 py-4 text-sm text-[#71717A]">{invoice.date}</td>
                      <td className="px-4 py-4">
                        <Link
                          to={`/reviews/${invoice.id}`}
                          className="text-sm text-[#00F2FF] font-medium hover:underline decoration-[#00F2FF]/40 underline-offset-4 transition-all"
                        >
                          {invoice.invoiceNumber}
                        </Link>
                      </td>
                      <td className="px-4 py-4 text-sm text-[#FAFAFA] font-semibold">{invoice.amount}</td>
                      <td className="px-4 py-4">
                        <span
                          className="px-2.5 py-1 rounded-md text-xs uppercase tracking-wider font-medium inline-block"
                          style={{
                            background: statusStyles.bg,
                            color: statusStyles.color,
                            border: `1px solid ${statusStyles.border}`,
                          }}
                        >
                          {invoice.status}
                        </span>
                      </td>
                    </tr>
                  );
                })}

                {paginated.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-4 py-16 text-center text-[#52525B] text-sm">
                      {copy.noResult}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <div
            className="px-4 py-3 border-t flex items-center justify-between"
            style={{ background: 'rgba(6, 7, 9, 0.8)', borderColor: 'rgba(255, 255, 255, 0.1)' }}
          >
            <div className="text-xs text-[#71717A]">
              {sorted.length === 0
                ? copy.paginationNoResult
                : `${startIndex + 1}-${Math.min(startIndex + ITEMS_PER_PAGE, sorted.length)} ${copy.paginationSur} ${sorted.length} ${copy.paginationInvoices}`}
            </div>

            {totalPages > 1 && (
              <div className="flex gap-1">
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
                        : { background: 'rgba(20, 22, 25, 0.6)', border: '1px solid rgba(255, 255, 255, 0.1)', color: '#FAFAFA' }
                    }
                  >
                    {page}
                  </button>
                ))}

                <button
                  onClick={() => setCurrentPage((page) => Math.min(totalPages, page + 1))}
                  disabled={currentPage === totalPages}
                  className="p-2 rounded-lg text-white transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                  style={{ background: 'rgba(20, 22, 25, 0.6)', border: '1px solid rgba(255, 255, 255, 0.1)' }}
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
