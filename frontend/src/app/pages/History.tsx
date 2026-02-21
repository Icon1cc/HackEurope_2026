import { useMemo, useState } from 'react';
import { Sidebar } from '../components/Sidebar';
import { VercelBackground } from '../components/VercelBackground';
import { Search, Download, Eye, ChevronLeft, ChevronRight } from 'lucide-react';

interface Invoice {
  id: string;
  date: string;
  invoiceNumber: string;
  vendor: string;
  amount: string;
  status: 'paid' | 'pending' | 'flagged' | 'rejected';
  trustScore: string;
  spendTrend: number[];
}

type HistorySortKey = 'date' | 'invoiceNumber' | 'vendor' | 'amount' | 'trustScore' | 'status';
type SortDirection = 'asc' | 'desc';

const mockInvoices: Invoice[] = [
  { id: '1', date: '2026-02-20', invoiceNumber: 'INV-2345', vendor: 'Acme Corp', amount: '$5,234.00', status: 'paid', trustScore: 'A+', spendTrend: [45, 48, 50, 52, 53] },
  { id: '2', date: '2026-02-19', invoiceNumber: 'INV-2344', vendor: 'TechSupply Inc', amount: '$12,450.00', status: 'flagged', trustScore: 'B', spendTrend: [85, 88, 90, 95, 124] },
  { id: '3', date: '2026-02-19', invoiceNumber: 'INV-2343', vendor: 'Office Depot', amount: '$892.50', status: 'paid', trustScore: 'A', spendTrend: [8, 9, 8, 9, 9] },
  { id: '4', date: '2026-02-18', invoiceNumber: 'INV-2342', vendor: 'Cloud Services Ltd', amount: '$3,200.00', status: 'pending', trustScore: 'A', spendTrend: [30, 31, 32, 32, 32] },
  { id: '5', date: '2026-02-18', invoiceNumber: 'INV-2341', vendor: 'Marketing Pro', amount: '$7,890.00', status: 'paid', trustScore: 'A-', spendTrend: [70, 72, 75, 78, 79] },
  { id: '6', date: '2026-02-17', invoiceNumber: 'INV-2340', vendor: 'Shipping Express', amount: '$425.00', status: 'rejected', trustScore: 'C', spendTrend: [5, 4, 3, 4, 4] },
  { id: '7', date: '2026-02-17', invoiceNumber: 'INV-2339', vendor: 'Legal Advisors', amount: '$15,000.00', status: 'paid', trustScore: 'A+', spendTrend: [150, 150, 150, 150, 150] },
  { id: '8', date: '2026-02-16', invoiceNumber: 'INV-2338', vendor: 'IT Solutions', amount: '$9,500.00', status: 'pending', trustScore: 'A', spendTrend: [88, 90, 92, 93, 95] },
];

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

function parseCurrency(value: string): number {
  const numericValue = Number(value.replace(/[^0-9.-]/g, ''));
  return Number.isNaN(numericValue) ? 0 : numericValue;
}

function trustScoreRank(score: string): number {
  switch (score) {
    case 'A+':
      return 5;
    case 'A':
      return 4;
    case 'A-':
      return 3;
    case 'B':
      return 2;
    case 'C':
      return 1;
    default:
      return 0;
  }
}

export default function History() {
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [sortConfig, setSortConfig] = useState<{ key: HistorySortKey; direction: SortDirection } | null>(null);
  const itemsPerPage = 8;

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
    return mockInvoices.filter((invoice) => {
      return (
        invoice.invoiceNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
        invoice.vendor.toLowerCase().includes(searchTerm.toLowerCase())
      );
    });
  }, [searchTerm]);

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
          comparison = parseCurrency(a.amount) - parseCurrency(b.amount);
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
                {paginatedInvoices.map((invoice, index) => {
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
              Showing {startIndex + 1}-{Math.min(startIndex + itemsPerPage, sortedInvoices.length)} of {sortedInvoices.length}
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
                disabled={currentPage === totalPages}
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
