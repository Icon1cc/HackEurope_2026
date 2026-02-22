import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router';
import { Sidebar } from '../components/Sidebar';
import { VercelBackground } from '../components/VercelBackground';
import { Search, Download, Eye, ChevronLeft, ChevronRight } from 'lucide-react';
import {
  INVOICES_UPDATED_EVENT,
  decimalToNumber,
  fetchInvoices,
  fetchVendors,
  formatCurrencyValue,
  trustScoreToPercent,
  type InvoiceApiResponse,
  type VendorApiResponse,
} from '../api/backend';
import { isProcessedStatus } from '../data/reviewTypes';

interface InvoiceRow {
  id: string;
  date: string;
  invoiceNumber: string;
  vendor: string;
  amount: string;
  amountValue: number;
  status: 'paid' | 'pending' | 'flagged' | 'rejected';
  trustScore: string;
  trustScoreValue: number;
  spendTrend: number[];
}

type HistorySortKey = 'date' | 'invoiceNumber' | 'vendor' | 'amount' | 'trustScore' | 'status';
type SortDirection = 'asc' | 'desc';

const STATUS_BASE_SCORE: Record<InvoiceRow['status'], number> = {
  paid: 90,
  pending: 68,
  flagged: 44,
  rejected: 30,
};

const MiniSparkline = ({ data }: { data: number[] }) => {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const width = 60;
  const height = 20;
  const points = data
    .map((value, index) => {
      const x = (index / (data.length - 1)) * width;
      const y = height - ((value - min) / range) * height;
      return `${x},${y}`;
    })
    .join(' ');

  return (
    <svg width={width} height={height} className="inline-block">
      <polyline
        points={points}
        fill="none"
        stroke="#00F2FF"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        style={{ filter: 'drop-shadow(0 0 2px rgba(0, 242, 255, 0.5))' }}
      />
    </svg>
  );
};

function toTrustGrade(score: number): string {
  if (score >= 95) return 'A+';
  if (score >= 85) return 'A';
  if (score >= 75) return 'A-';
  if (score >= 65) return 'B';
  if (score >= 50) return 'C';
  return 'D';
}

function trustScoreRank(score: string): number {
  switch (score) {
    case 'A+':
      return 6;
    case 'A':
      return 5;
    case 'A-':
      return 4;
    case 'B':
      return 3;
    case 'C':
      return 2;
    case 'D':
      return 1;
    default:
      return 0;
  }
}

function toStatus(status: string | null | undefined): InvoiceRow['status'] {
  const normalized = status?.trim().toLowerCase() ?? '';
  if (normalized === 'rejected' || normalized === 'overcharge') {
    return 'rejected';
  }
  if (normalized === 'flagged') {
    return 'flagged';
  }
  if (isProcessedStatus(normalized)) {
    return 'paid';
  }
  return 'pending';
}

function clampScore(value: number): number {
  return Math.max(0, Math.min(100, Math.round(value)));
}

function getFallbackScore(invoice: InvoiceApiResponse, status: InvoiceRow['status']): number {
  const numericId = Number(invoice.id.replace(/\D/g, ''));
  const variance = Number.isNaN(numericId) ? 0 : (numericId % 7) - 3;
  return clampScore(STATUS_BASE_SCORE[status] + variance);
}

function getVendorKey(invoice: InvoiceApiResponse): string {
  if (invoice.vendor_id) {
    return `id:${invoice.vendor_id}`;
  }
  if (invoice.vendor_name?.trim()) {
    return `name:${invoice.vendor_name.trim().toLowerCase()}`;
  }
  return 'unknown';
}

function buildSpendTrendMap(invoices: InvoiceApiResponse[]): Map<string, number[]> {
  const sorted = [...invoices].sort((a, b) => a.created_at.localeCompare(b.created_at));
  const trendMap = new Map<string, number[]>();

  for (const invoice of sorted) {
    const key = getVendorKey(invoice);
    const amount = decimalToNumber(invoice.total) ?? 0;
    const series = trendMap.get(key);
    if (series) {
      series.push(amount);
    } else {
      trendMap.set(key, [amount]);
    }
  }

  return trendMap;
}

function buildInvoiceRows(invoices: InvoiceApiResponse[], vendors: VendorApiResponse[]): InvoiceRow[] {
  const vendorsById = new Map(vendors.map((vendor) => [vendor.id, vendor]));
  const trendMap = buildSpendTrendMap(invoices);

  return invoices.map((invoice) => {
    const vendor = invoice.vendor_id ? vendorsById.get(invoice.vendor_id) : undefined;
    const status = toStatus(invoice.status);
    const amountValue = decimalToNumber(invoice.total) ?? 0;
    const vendorScore = vendor ? trustScoreToPercent(vendor.trust_score) : null;
    const computedScore = typeof invoice.confidence_score === 'number'
      ? clampScore(invoice.confidence_score)
      : getFallbackScore(invoice, status);
    const trustScoreValue = vendorScore ?? computedScore;
    const trend = trendMap.get(getVendorKey(invoice)) ?? [amountValue];
    const spendTrend = (trend.length < 2 ? [amountValue, amountValue] : trend).slice(-5);

    return {
      id: invoice.id,
      date: invoice.created_at?.slice(0, 10) ?? '',
      invoiceNumber: invoice.invoice_number?.trim() || invoice.id.slice(0, 8).toUpperCase(),
      vendor: vendor?.name || invoice.vendor_name?.trim() || 'Unknown Vendor',
      amountValue,
      amount: formatCurrencyValue(invoice.total, invoice.currency),
      status,
      trustScore: toTrustGrade(trustScoreValue),
      trustScoreValue,
      spendTrend,
    };
  });
}

export default function History() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [sortConfig, setSortConfig] = useState<{ key: HistorySortKey; direction: SortDirection } | null>(null);
  const [invoices, setInvoices] = useState<InvoiceRow[]>([]);
  const [invoicesLoading, setInvoicesLoading] = useState(true);
  const [invoicesError, setInvoicesError] = useState<string | null>(null);
  const itemsPerPage = 8;

  const loadHistory = useCallback(async () => {
    setInvoicesLoading(true);
    setInvoicesError(null);
    try {
      const [fetchedInvoices, fetchedVendors] = await Promise.all([fetchInvoices(), fetchVendors()]);
      setInvoices(buildInvoiceRows(fetchedInvoices, fetchedVendors));
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      setInvoicesError(message);
      setInvoices([]);
    } finally {
      setInvoicesLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadHistory();
  }, [loadHistory]);

  useEffect(() => {
    const handleInvoicesUpdated = () => {
      void loadHistory();
    };

    window.addEventListener(INVOICES_UPDATED_EVENT, handleInvoicesUpdated);
    return () => {
      window.removeEventListener(INVOICES_UPDATED_EVENT, handleInvoicesUpdated);
    };
  }, [loadHistory]);

  const getTrustScoreStyles = (score: string) => {
    if (score.startsWith('A')) {
      return { color: '#00FF94', border: '#00FF94' };
    }

    if (score.startsWith('B')) {
      return { color: '#00F2FF', border: '#00F2FF' };
    }

    if (score.startsWith('C')) {
      return { color: '#FFB800', border: '#FFB800' };
    }

    return { color: '#FF0055', border: '#FF0055' };
  };

  const getStatusStyles = (status: string) => {
    switch (status) {
      case 'paid':
        return { color: '#00FF94', border: '#00FF94' };
      case 'pending':
        return { color: '#00F2FF', border: '#00F2FF' };
      case 'flagged':
        return { color: '#FFB800', border: '#FFB800' };
      case 'rejected':
        return { color: '#FF0055', border: '#FF0055' };
      default:
        return { color: '#71717A', border: '#71717A' };
    }
  };

  const filteredInvoices = useMemo(() => {
    const query = searchTerm.toLowerCase();
    return invoices.filter((invoice) => {
      return (
        invoice.invoiceNumber.toLowerCase().includes(query) ||
        invoice.vendor.toLowerCase().includes(query)
      );
    });
  }, [invoices, searchTerm]);

  const sortedInvoices = useMemo(() => {
    if (!sortConfig) {
      return filteredInvoices;
    }

    const sorted = [...filteredInvoices].sort((a, b) => {
      let comparison = 0;

      switch (sortConfig.key) {
        case 'date':
          comparison = a.date.localeCompare(b.date);
          break;
        case 'invoiceNumber':
          comparison = a.invoiceNumber.localeCompare(b.invoiceNumber);
          break;
        case 'vendor':
          comparison = a.vendor.localeCompare(b.vendor);
          break;
        case 'amount':
          comparison = a.amountValue - b.amountValue;
          break;
        case 'trustScore':
          comparison = trustScoreRank(a.trustScore) - trustScoreRank(b.trustScore);
          break;
        case 'status':
          comparison = a.status.localeCompare(b.status);
          break;
      }

      return sortConfig.direction === 'asc' ? comparison : -comparison;
    });

    return sorted;
  }, [filteredInvoices, sortConfig]);

  useEffect(() => {
    const maxPage = Math.max(1, Math.ceil(sortedInvoices.length / itemsPerPage));
    if (currentPage > maxPage) {
      setCurrentPage(maxPage);
    }
  }, [currentPage, sortedInvoices.length]);

  const totalPages = Math.ceil(sortedInvoices.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedInvoices = sortedInvoices.slice(startIndex, startIndex + itemsPerPage);

  const toggleSort = (key: HistorySortKey) => {
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

  const getSortIndicator = (key: HistorySortKey): string => {
    if (!sortConfig || sortConfig.key !== key) {
      return '↕';
    }

    return sortConfig.direction === 'asc' ? '▲' : '▼';
  };

  return (
    <div className="flex min-h-screen relative overflow-hidden">
      <VercelBackground />

      <Sidebar />

      <main className="flex-1 ml-64 p-8 relative z-10">
        <div className="mb-8">
          <h1
            className="text-4xl mb-2"
            style={{
              fontFamily: 'Geist Sans, Inter, sans-serif',
              fontWeight: 700,
              letterSpacing: '-0.02em',
              color: '#FAFAFA',
            }}
          >
            Vendor Trust Directory
          </h1>
          <p className="text-[#71717A] text-sm">Complete invoice history with trust analytics</p>
        </div>

        <div
          className="rounded-xl p-3 xl:p-4 mb-4 xl:mb-6 backdrop-blur-[20px]"
          style={{
            background: 'rgba(20, 22, 25, 0.6)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            boxShadow: 'inset 0 1px 0 0 rgba(255, 255, 255, 0.1)',
          }}
        >
          <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
            <div className="relative group flex-1 min-w-0">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#71717A] group-focus-within:text-[#00F2FF] transition-colors pointer-events-none" />
              <input
                type="text"
                placeholder="Search invoices or vendors..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setCurrentPage(1);
                }}
                className="w-full pl-9 pr-3 py-2 xl:py-2.5 rounded-lg text-sm text-white placeholder-[#52525B] transition-all outline-none"
                style={{
                  background: 'rgba(6, 7, 9, 0.8)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                }}
                onFocus={(e) => {
                  e.target.style.border = '1px solid #00F2FF';
                }}
                onBlur={(e) => {
                  e.target.style.border = '1px solid rgba(255, 255, 255, 0.1)';
                }}
              />
            </div>

            <button
              className="px-3 py-2 xl:py-2.5 rounded-lg text-[#00F2FF] transition-all shrink-0 self-start sm:self-auto"
              style={{
                background: 'rgba(6, 7, 9, 0.8)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'rgba(0, 242, 255, 0.08)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'rgba(6, 7, 9, 0.8)';
              }}
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
            <table className="w-full" style={{ minWidth: '860px' }}>
              <thead
                style={{
                  background: 'rgba(6, 7, 9, 0.8)',
                  borderColor: 'rgba(255, 255, 255, 0.1)',
                }}
              >
                <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }}>
                  <th className="px-4 py-3 text-left text-xs text-[#71717A] uppercase tracking-wider font-medium">
                    <button type="button" className="inline-flex items-center gap-1" onClick={() => toggleSort('date')}>
                      <span>Date</span>
                      <span className="text-[10px] text-[#52525B]">{getSortIndicator('date')}</span>
                    </button>
                  </th>
                  <th className="px-4 py-3 text-left text-xs text-[#71717A] uppercase tracking-wider font-medium">
                    <button type="button" className="inline-flex items-center gap-1" onClick={() => toggleSort('invoiceNumber')}>
                      <span>Invoice #</span>
                      <span className="text-[10px] text-[#52525B]">{getSortIndicator('invoiceNumber')}</span>
                    </button>
                  </th>
                  <th className="px-4 py-3 text-left text-xs text-[#71717A] uppercase tracking-wider font-medium">
                    <button type="button" className="inline-flex items-center gap-1" onClick={() => toggleSort('vendor')}>
                      <span>Vendor</span>
                      <span className="text-[10px] text-[#52525B]">{getSortIndicator('vendor')}</span>
                    </button>
                  </th>
                  <th className="px-4 py-3 text-left text-xs text-[#71717A] uppercase tracking-wider font-medium">
                    <button type="button" className="inline-flex items-center gap-1" onClick={() => toggleSort('amount')}>
                      <span>Amount</span>
                      <span className="text-[10px] text-[#52525B]">{getSortIndicator('amount')}</span>
                    </button>
                  </th>
                  <th className="px-4 py-3 text-left text-xs text-[#71717A] uppercase tracking-wider font-medium">
                    <button type="button" className="inline-flex items-center gap-1" onClick={() => toggleSort('trustScore')}>
                      <span>Trust Score</span>
                      <span className="text-[10px] text-[#52525B]">{getSortIndicator('trustScore')}</span>
                    </button>
                  </th>
                  <th className="px-4 py-3 text-left text-xs text-[#71717A] uppercase tracking-wider font-medium">Trend</th>
                  <th className="px-4 py-3 text-left text-xs text-[#71717A] uppercase tracking-wider font-medium">
                    <button type="button" className="inline-flex items-center gap-1" onClick={() => toggleSort('status')}>
                      <span>Status</span>
                      <span className="text-[10px] text-[#52525B]">{getSortIndicator('status')}</span>
                    </button>
                  </th>
                  <th className="px-4 py-3 text-left text-xs text-[#71717A] uppercase tracking-wider font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {invoicesLoading && (
                  <tr>
                    <td colSpan={8} className="px-4 py-14 text-center text-[#71717A] text-sm">
                      Loading invoice history...
                    </td>
                  </tr>
                )}

                {!invoicesLoading && invoicesError && (
                  <tr>
                    <td colSpan={8} className="px-4 py-14 text-center text-[#FF6B8A] text-sm">
                      Failed to load invoice history.
                    </td>
                  </tr>
                )}

                {!invoicesLoading && !invoicesError && paginatedInvoices.map((invoice, index) => {
                  const statusStyles = getStatusStyles(invoice.status);
                  const trustStyles = getTrustScoreStyles(invoice.trustScore);
                  return (
                    <tr
                      key={invoice.id}
                      className="transition-all duration-200 cursor-pointer"
                      style={{ borderBottom: index < paginatedInvoices.length - 1 ? '1px solid rgba(255, 255, 255, 0.05)' : 'none' }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.background = 'rgba(255, 255, 255, 0.02)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.background = 'transparent';
                      }}
                    >
                      <td className="px-4 py-4 text-sm text-[#71717A]">{invoice.date}</td>
                      <td className="px-4 py-4">
                        <span className="text-sm text-[#00F2FF] font-medium">{invoice.invoiceNumber}</span>
                      </td>
                      <td className="px-4 py-4 text-sm text-[#FAFAFA]">{invoice.vendor}</td>
                      <td className="px-4 py-4 text-sm text-[#FAFAFA] font-semibold display-number">{invoice.amount}</td>
                      <td className="px-4 py-4">
                        <span
                          className="px-2.5 py-1 rounded-md text-xs font-semibold inline-block"
                          style={{
                            background: 'rgba(20, 22, 25, 0.8)',
                            color: trustStyles.color,
                            border: `1px solid ${trustStyles.border}`,
                          }}
                        >
                          {invoice.trustScore}
                        </span>
                      </td>
                      <td className="px-4 py-4">
                        <MiniSparkline data={invoice.spendTrend} />
                      </td>
                      <td className="px-4 py-4">
                        <span
                          className="px-2.5 py-1 rounded-md text-xs uppercase tracking-wider font-medium inline-block"
                          style={{
                            background: 'rgba(20, 22, 25, 0.8)',
                            color: statusStyles.color,
                            border: `1px solid ${statusStyles.border}`,
                          }}
                        >
                          {invoice.status}
                        </span>
                      </td>
                      <td className="px-4 py-4">
                        <button
                          className="p-2 text-[#00F2FF] rounded-lg transition-all"
                          onClick={() => navigate(`/reviews/${invoice.id}`)}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.background = 'rgba(0, 242, 255, 0.08)';
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.background = 'transparent';
                          }}
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })}

                {!invoicesLoading && !invoicesError && paginatedInvoices.length === 0 && (
                  <tr>
                    <td colSpan={8} className="px-4 py-14 text-center text-[#52525B] text-sm">
                      No invoices found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <div
            className="px-4 py-3 border-t flex items-center justify-between"
            style={{
              background: 'rgba(6, 7, 9, 0.8)',
              borderColor: 'rgba(255, 255, 255, 0.1)',
            }}
          >
            <div className="text-xs text-[#71717A]">
              {sortedInvoices.length === 0
                ? 'No results'
                : `Showing ${startIndex + 1}-${Math.min(startIndex + itemsPerPage, sortedInvoices.length)} of ${sortedInvoices.length}`}
            </div>

            <div className="flex gap-1">
              <button
                onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
                className="p-2 rounded-lg text-white transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                style={{
                  background: 'rgba(20, 22, 25, 0.6)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                }}
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
                      ? {
                          background: '#00F2FF',
                          color: '#060709',
                          fontWeight: 600,
                          border: '1px solid rgba(255, 255, 255, 0.2)',
                        }
                      : {
                          background: 'rgba(20, 22, 25, 0.6)',
                          border: '1px solid rgba(255, 255, 255, 0.1)',
                          color: '#FAFAFA',
                        }
                  }
                >
                  {page}
                </button>
              ))}

              <button
                onClick={() => setCurrentPage((prev) => Math.min(totalPages, prev + 1))}
                disabled={currentPage === totalPages || totalPages === 0}
                className="p-2 rounded-lg text-white transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                style={{
                  background: 'rgba(20, 22, 25, 0.6)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                }}
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
