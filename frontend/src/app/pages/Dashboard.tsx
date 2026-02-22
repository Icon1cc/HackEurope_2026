import { Link } from 'react-router';
import { useState } from 'react';
import {
  TrendingUp,
  Upload,
  Clock,
  Shield as ShieldIcon,
  Zap,
  AlertTriangle,
  AlertCircle,
  ChevronLeft,
  X,
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { Sidebar } from '../components/Sidebar';
import { Footer } from '../components/Footer';
import { VercelBackground } from '../components/VercelBackground';
import { pendingReviews } from '../data/pendingReviews';
import { useAppLanguage } from '../i18n/AppLanguageProvider';

const chartVolumes = [45, 52, 48, 65, 58, 70, 75];

export default function Dashboard() {
  const language = useAppLanguage();
  const [dragActive, setDragActive] = useState(false);
  const [panelOpen,  setPanelOpen]  = useState(false);
  const copy = {
    fr: {
      months: ['Janv.', 'Févr.', 'Mars', 'Avr.', 'Mai', 'Juin', 'Juil.'],
      title: 'Centre de contrôle',
      subtitle: 'Traitement autonome des factures en temps réel',
      totalValueProtected: 'Valeur totale protégée',
      totalValueTrend: 'vs mois dernier',
      humanHoursSaved: 'Heures humaines économisées',
      humanHoursTrend: "efficacité d'automatisation",
      processingVolume: 'Volume de traitement',
      processInvoice: 'Traiter une facture',
      dropInvoice: 'Dépose un PDF ici ou clique pour parcourir',
      fileFormatHint: 'Taille max: 10MB • PDF, PNG, JPG',
      pendingTabLabel: 'Revues',
      openPendingReviews: 'Ouvrir les revues en attente',
      pendingReviews: 'Revues en attente',
      pendingInvoicesCount: `${pendingReviews.length} factures en attente`,
      closePanel: 'Fermer le panneau',
      statusPending: 'en attente',
      statusEscalated: 'escaladé',
    },
    en: {
      months: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
      title: 'Command Center',
      subtitle: 'Real-time autonomous invoice processing',
      totalValueProtected: 'Total Value Protected',
      totalValueTrend: 'vs last month',
      humanHoursSaved: 'Human Hours Saved',
      humanHoursTrend: 'automation efficiency',
      processingVolume: 'Processing Volume',
      processInvoice: 'Process Invoice',
      dropInvoice: 'Drop PDF invoice here or click to browse',
      fileFormatHint: 'Maximum file size: 10MB • Supports PDF, PNG, JPG',
      pendingTabLabel: 'Reviews',
      openPendingReviews: 'Open pending reviews',
      pendingReviews: 'Pending Reviews',
      pendingInvoicesCount: `${pendingReviews.length} invoices pending`,
      closePanel: 'Close panel',
      statusPending: 'pending',
      statusEscalated: 'escalated',
    },
    de: {
      months: ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul'],
      title: 'Kontrollzentrum',
      subtitle: 'Autonome Rechnungsverarbeitung in Echtzeit',
      totalValueProtected: 'Geschützter Gesamtwert',
      totalValueTrend: 'vs. Letzter Monat',
      humanHoursSaved: 'Eingesparte Arbeitsstunden',
      humanHoursTrend: 'Automatisierungseffizienz',
      processingVolume: 'Verarbeitungsvolumen',
      processInvoice: 'Rechnung verarbeiten',
      dropInvoice: 'PDF hier ablegen oder zum Durchsuchen klicken',
      fileFormatHint: 'Max. Größe: 10MB • PDF, PNG, JPG',
      pendingTabLabel: 'Prüfungen',
      openPendingReviews: 'Ausstehende Prüfungen öffnen',
      pendingReviews: 'Ausstehende Prüfungen',
      pendingInvoicesCount: `${pendingReviews.length} Rechnungen ausstehend`,
      closePanel: 'Panel schließen',
      statusPending: 'ausstehend',
      statusEscalated: 'eskaliert',
    },
  }[language];
  const chartData = chartVolumes.map((volume, index) => ({ month: copy.months[index], volume }));
  const getStatusLabel = (status: 'pending' | 'escalated') =>
    status === 'escalated' ? copy.statusEscalated : copy.statusPending;

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true);
    else if (e.type === 'dragleave') setDragActive(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  };

  return (
    <div className="flex min-h-screen relative overflow-hidden">
      <VercelBackground />

      <Sidebar />

      {/* ── Main content ──────────────────────────────────────────────────── */}
      <main className="flex-1 min-w-0 lg:ml-64 px-4 pb-4 pt-20 lg:pt-8 sm:px-6 sm:py-6 lg:p-8 relative z-10">

        {/* Header */}
        <div className="mb-8">
          <h1
            className="text-3xl sm:text-4xl mb-2"
            style={{ fontFamily: 'Geist Sans, Inter, sans-serif', fontWeight: 700, letterSpacing: '-0.02em', color: '#FAFAFA' }}
          >
            {copy.title}
          </h1>
          <p className="text-[#71717A] text-sm">{copy.subtitle}</p>
        </div>

        {/* Metric cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
          <div
            className="rounded-xl p-4 sm:p-6 backdrop-blur-[20px]"
            style={{ background: 'rgba(20, 22, 25, 0.6)', border: '1px solid rgba(255, 255, 255, 0.1)', boxShadow: 'inset 0 1px 0 0 rgba(255, 255, 255, 0.1)' }}
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <div className="text-xs text-[#71717A] uppercase tracking-wider font-medium mb-2">{copy.totalValueProtected}</div>
                <div className="text-4xl sm:text-5xl display-number text-[#00F2FF]">
                  $2.4M
                </div>
              </div>
              <div className="w-12 h-12 rounded-lg flex items-center justify-center" style={{ background: 'rgba(0, 242, 255, 0.08)', border: '1px solid rgba(0, 242, 255, 0.2)' }}>
                <ShieldIcon className="w-6 h-6 text-[#00F2FF]" />
              </div>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span className="text-[#00FF94]">↑ 12.5%</span>
              <span className="text-[#71717A]">{copy.totalValueTrend}</span>
            </div>
          </div>

          <div
            className="rounded-xl p-4 sm:p-6 backdrop-blur-[20px]"
            style={{ background: 'rgba(20, 22, 25, 0.6)', border: '1px solid rgba(255, 255, 255, 0.1)', boxShadow: 'inset 0 1px 0 0 rgba(255, 255, 255, 0.1)' }}
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <div className="text-xs text-[#71717A] uppercase tracking-wider font-medium mb-2">{copy.humanHoursSaved}</div>
                <div className="text-4xl sm:text-5xl display-number text-[#00FF94]">
                  342
                </div>
              </div>
              <div className="w-12 h-12 rounded-lg flex items-center justify-center" style={{ background: 'rgba(0, 255, 148, 0.08)', border: '1px solid rgba(0, 255, 148, 0.2)' }}>
                <Clock className="w-6 h-6 text-[#00FF94]" />
              </div>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span className="text-[#00FF94]">↑ 28.3%</span>
              <span className="text-[#71717A]">{copy.humanHoursTrend}</span>
            </div>
          </div>
        </div>

        {/* Chart */}
        <div
          className="rounded-xl p-4 sm:p-6 mb-8 backdrop-blur-[20px]"
          style={{ background: 'rgba(20, 22, 25, 0.6)', border: '1px solid rgba(255, 255, 255, 0.1)', boxShadow: 'inset 0 1px 0 0 rgba(255, 255, 255, 0.1)' }}
        >
          <div className="flex items-center gap-3 mb-6">
            <TrendingUp className="w-5 h-5 text-[#00F2FF]" />
            <h2 className="text-lg" style={{ fontFamily: 'Geist Sans, Inter, sans-serif', fontWeight: 600, letterSpacing: '-0.02em' }}>
              {copy.processingVolume}
            </h2>
          </div>
          <div className="h-56 sm:h-64 lg:h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <XAxis dataKey="month" stroke="#71717A" style={{ fontSize: '12px' }} axisLine={{ stroke: 'rgba(255,255,255,0.1)' }} tickLine={false} />
                <YAxis stroke="#71717A" style={{ fontSize: '12px' }} axisLine={false} tickLine={false} tick={false} />
                <Tooltip
                  contentStyle={{
                    background: 'rgba(20, 22, 25, 0.95)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '8px',
                    color: '#FAFAFA',
                    backdropFilter: 'blur(20px)',
                    boxShadow: 'inset 0 1px 0 0 rgba(255, 255, 255, 0.1)',
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="volume"
                  stroke="#00F2FF"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 5, fill: '#00F2FF', stroke: '#060709', strokeWidth: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Upload zone */}
        <div
          className="rounded-xl p-4 sm:p-6 backdrop-blur-[20px]"
          style={{ background: 'rgba(20, 22, 25, 0.6)', border: '1px solid rgba(255, 255, 255, 0.1)', boxShadow: 'inset 0 1px 0 0 rgba(255, 255, 255, 0.1)' }}
        >
          <div className="flex items-center gap-3 mb-4">
            <Zap className="w-5 h-5 text-[#00F2FF]" />
            <h2 className="text-lg" style={{ fontFamily: 'Geist Sans, Inter, sans-serif', fontWeight: 600, letterSpacing: '-0.02em' }}>
              {copy.processInvoice}
            </h2>
          </div>
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className="border border-dashed rounded-xl p-8 sm:p-12 text-center transition-all cursor-pointer"
            style={
              dragActive
                ? { borderColor: '#00F2FF', background: 'rgba(0, 242, 255, 0.05)' }
                : { borderColor: 'rgba(255, 255, 255, 0.15)', background: 'rgba(6, 7, 9, 0.4)' }
            }
          >
            <Upload className="w-16 h-16 text-[#00F2FF] mx-auto mb-4" strokeWidth={1.5} />
            <p className="text-[#FAFAFA] text-base mb-2 font-medium">{copy.dropInvoice}</p>
            <p className="text-[#71717A] text-sm">{copy.fileFormatHint}</p>
          </div>
        </div>

        <Footer />
      </main>

      {/* ── Pending Reviews — deployable right panel ──────────────────────── */}

      {/* Tab trigger (visible when panel is closed) */}
      <button
        type="button"
        onClick={() => setPanelOpen(true)}
        className="fixed right-0 top-1/2 -translate-y-1/2 z-[45] flex flex-col items-center gap-3 py-8 px-4 rounded-l-2xl transition-all duration-300 group hover:bg-[rgba(0,242,255,0.05)]"
        style={{
          background: 'rgba(6, 7, 9, 0.95)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRight: 'none',
          backdropFilter: 'blur(20px)',
          boxShadow: '-8px 0 30px rgba(0, 0, 0, 0.5)',
          opacity: panelOpen ? 0 : 1,
          pointerEvents: panelOpen ? 'none' : 'auto',
          transform: panelOpen ? 'translateX(40px)' : 'translateX(0)',
        }}
        aria-label={copy.openPendingReviews}
      >
        <AlertTriangle 
          className="w-6 h-6 mb-1 text-[#00F2FF] opacity-80 group-hover:opacity-100 transition-opacity"
        />
        
        {/* Count badge */}
        <span
          className="text-sm font-bold tabular-nums w-8 h-8 rounded-full flex items-center justify-center mb-2"
          style={{ 
            background: 'rgba(0, 242, 255, 0.1)', 
            color: '#00F2FF', 
            border: '1px solid rgba(0, 242, 255, 0.3)',
          }}
        >
          {pendingReviews.length}
        </span>

        {/* Vertical Text Label */}
        <div 
          className="uppercase tracking-[0.2em] font-black text-[#FAFAFA] text-[10px] opacity-60 group-hover:opacity-100 transition-opacity"
          style={{ 
            writingMode: 'vertical-lr',
          }}
        >
          {copy.pendingTabLabel}
        </div>

        <ChevronLeft className="w-4 h-4 text-[#71717A] mt-2 group-hover:text-[#00F2FF] group-hover:-translate-x-1 transition-all" />
      </button>

      {/* Backdrop (closes panel on outside click) */}
      {panelOpen && (
        <div
          className="fixed inset-0 z-[49]"
          onClick={() => setPanelOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Panel */}
      <div
        className="fixed top-0 right-0 h-full z-[50] flex flex-col"
        style={{
          width: 'min(90vw, 340px)',
          background: 'rgba(13, 15, 18, 0.97)',
          borderLeft: '1px solid rgba(255, 255, 255, 0.1)',
          backdropFilter: 'blur(24px)',
          boxShadow: panelOpen ? '-24px 0 60px rgba(0, 0, 0, 0.5)' : 'none',
          transform: panelOpen ? 'translateX(0)' : 'translateX(100%)',
          transition: 'transform 320ms cubic-bezier(0.4, 0, 0.2, 1), box-shadow 320ms ease',
          pointerEvents: panelOpen ? 'auto' : 'none',
        }}
      >
        {/* Panel header */}
        <div
          className="flex items-center justify-between px-5 py-4 shrink-0"
          style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.08)' }}
        >
          <div className="flex items-center gap-2.5">
            <AlertTriangle className="w-4 h-4 text-[#FFB800]" />
            <div>
              <h2
                className="text-base leading-none"
                style={{ fontFamily: 'Geist Sans, Inter, sans-serif', fontWeight: 700, letterSpacing: '-0.02em', color: '#FAFAFA' }}
              >
                {copy.pendingReviews}
              </h2>
              <p className="text-[11px] text-[#71717A] mt-0.5">{copy.pendingInvoicesCount}</p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => setPanelOpen(false)}
            className="p-1.5 rounded-lg hover:bg-white/[0.06] hover:text-[#FAFAFA] text-[#71717A]"
            aria-label={copy.closePanel}
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Panel body — scrollable */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3" style={{ scrollbarWidth: 'thin', scrollbarColor: 'rgba(255,255,255,0.1) transparent' }}>
          {pendingReviews.map((review) => (
            <Link
              key={review.id}
              to={`/reviews/${review.id}`}
              className="block rounded-lg p-3.5 transition-all duration-200"
              style={{ background: 'rgba(20, 22, 25, 0.7)', border: '1px solid rgba(255, 255, 255, 0.08)' }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'rgba(0, 242, 255, 0.06)';
                e.currentTarget.style.border = '1px solid rgba(0, 242, 255, 0.2)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'rgba(20, 22, 25, 0.7)';
                e.currentTarget.style.border = '1px solid rgba(255, 255, 255, 0.08)';
              }}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  {review.status === 'escalated'
                    ? <AlertCircle   className="w-3.5 h-3.5 shrink-0 text-[#FF0055]" />
                    : <AlertTriangle className="w-3.5 h-3.5 shrink-0 text-[#FFB800]" />
                  }
                  <span
                    className="text-[10px] px-1.5 py-0.5 rounded uppercase tracking-wider font-semibold"
                    style={
                      review.status === 'escalated'
                        ? { background: 'rgba(255,0,85,0.08)', color: '#FF0055', border: '1px solid rgba(255,0,85,0.3)' }
                        : { background: 'rgba(255,184,0,0.08)', color: '#FFB800', border: '1px solid rgba(255,184,0,0.3)' }
                    }
                  >
                    {getStatusLabel(review.status)}
                  </span>
                </div>
                <span className="text-[10px] text-[#52525B] shrink-0">{review.date}</span>
              </div>

              <div className="text-sm font-semibold text-[#FAFAFA] mb-0.5">{review.vendor}</div>
              <div className="text-base font-bold display-number text-[#00F2FF] mb-2">{review.amount}</div>
              <div className="text-[11px] text-[#71717A] line-clamp-2 leading-relaxed">{review.reasons[language][0]}</div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
