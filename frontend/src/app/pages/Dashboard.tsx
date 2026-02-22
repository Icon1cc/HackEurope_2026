import { Link } from 'react-router';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
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
import { fetchInvoices, formatCurrencyValue, decimalToNumber, type InvoiceApiResponse } from '../api/backend';
import { uploadInvoiceForExtraction } from '../api/extraction';
import { isProcessedStatus, toPendingReview, type PendingReview } from '../data/reviewTypes';
import { useAppLanguage } from '../i18n/AppLanguageProvider';

const MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024;
const ACCEPTED_MIME_TYPES = new Set(['application/pdf', 'image/png', 'image/jpeg', 'image/webp']);
const ACCEPTED_EXTENSIONS = ['pdf', 'png', 'jpg', 'jpeg', 'webp'];

export default function Dashboard() {
  const language = useAppLanguage();
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [panelOpen, setPanelOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [invoices, setInvoices] = useState<InvoiceApiResponse[]>([]);
  const [invoicesLoading, setInvoicesLoading] = useState(true);
  const [invoicesError, setInvoicesError] = useState<string | null>(null);

  const copy = {
    fr: {
      title: 'Centre de contrôle',
      subtitle: 'Traitement autonome des factures en temps réel',
      totalValueProtected: 'Valeur totale protégée',
      totalValueTrend: 'vs mois dernier',
      invoicesProcessed: 'Factures traitées',
      invoicesProcessedTrend: 'actuellement en revue',
      processingVolume: 'Volume de traitement',
      processInvoice: 'Traiter une facture',
      dropInvoice: 'Dépose un PDF ici ou clique pour parcourir',
      fileFormatHint: 'Taille max: 10MB • PDF, PNG, JPG',
      uploadingLabel: 'Extraction en cours...',
      fileTooLarge: 'Le fichier dépasse 10MB.',
      invalidFileType: 'Format non supporté. Utilise PDF, PNG, JPG ou WEBP.',
      uploadErrorPrefix: 'Échec de l’extraction :',
      uploadSuccessReview: (invoiceNumber: string) => `Facture ${invoiceNumber} extraite. Revue ajoutée.`,
      uploadSuccessApproved: (invoiceNumber: string) => `Facture ${invoiceNumber} extraite et approuvée automatiquement.`,
      pendingTabLabel: 'Revues',
      openPendingReviews: 'Ouvrir les revues en attente',
      pendingReviews: 'Revues en attente',
      pendingInvoicesCount: (count: number) => `${count} factures en attente`,
      closePanel: 'Fermer le panneau',
      statusPending: 'en attente',
      statusEscalated: 'escaladé',
      loadingReviews: 'Chargement des revues...',
      noPendingReviews: 'Aucune revue en attente.',
      reviewsLoadFailed: 'Impossible de charger les revues.',
    },
    en: {
      title: 'Command Center',
      subtitle: 'Real-time autonomous invoice processing',
      totalValueProtected: 'Total Value Protected',
      totalValueTrend: 'vs last month',
      invoicesProcessed: 'Invoices Processed',
      invoicesProcessedTrend: 'currently in review',
      processingVolume: 'Processing Volume',
      processInvoice: 'Process Invoice',
      dropInvoice: 'Drop PDF invoice here or click to browse',
      fileFormatHint: 'Maximum file size: 10MB • Supports PDF, PNG, JPG',
      uploadingLabel: 'Running extraction...',
      fileTooLarge: 'The selected file exceeds 10MB.',
      invalidFileType: 'Unsupported format. Use PDF, PNG, JPG, or WEBP.',
      uploadErrorPrefix: 'Extraction failed:',
      uploadSuccessReview: (invoiceNumber: string) => `Invoice ${invoiceNumber} extracted. Review added.`,
      uploadSuccessApproved: (invoiceNumber: string) => `Invoice ${invoiceNumber} extracted and auto-approved.`,
      pendingTabLabel: 'Reviews',
      openPendingReviews: 'Open pending reviews',
      pendingReviews: 'Pending Reviews',
      pendingInvoicesCount: (count: number) => `${count} invoices pending`,
      closePanel: 'Close panel',
      statusPending: 'pending',
      statusEscalated: 'escalated',
      loadingReviews: 'Loading reviews...',
      noPendingReviews: 'No pending reviews.',
      reviewsLoadFailed: 'Failed to load reviews.',
    },
    de: {
      title: 'Kontrollzentrum',
      subtitle: 'Autonome Rechnungsverarbeitung in Echtzeit',
      totalValueProtected: 'Geschützter Gesamtwert',
      totalValueTrend: 'vs. Letzter Monat',
      invoicesProcessed: 'Verarbeitete Rechnungen',
      invoicesProcessedTrend: 'aktuell in Prüfung',
      processingVolume: 'Verarbeitungsvolumen',
      processInvoice: 'Rechnung verarbeiten',
      dropInvoice: 'PDF hier ablegen oder zum Durchsuchen klicken',
      fileFormatHint: 'Max. Größe: 10MB • PDF, PNG, JPG',
      uploadingLabel: 'Extraktion läuft...',
      fileTooLarge: 'Die ausgewählte Datei ist größer als 10MB.',
      invalidFileType: 'Nicht unterstütztes Format. Verwende PDF, PNG, JPG oder WEBP.',
      uploadErrorPrefix: 'Extraktion fehlgeschlagen:',
      uploadSuccessReview: (invoiceNumber: string) => `Rechnung ${invoiceNumber} extrahiert. Prüfung hinzugefügt.`,
      uploadSuccessApproved: (invoiceNumber: string) => `Rechnung ${invoiceNumber} extrahiert und automatisch freigegeben.`,
      pendingTabLabel: 'Prüfungen',
      openPendingReviews: 'Ausstehende Prüfungen öffnen',
      pendingReviews: 'Ausstehende Prüfungen',
      pendingInvoicesCount: (count: number) => `${count} Rechnungen ausstehend`,
      closePanel: 'Panel schließen',
      statusPending: 'ausstehend',
      statusEscalated: 'eskaliert',
      loadingReviews: 'Prüfungen werden geladen...',
      noPendingReviews: 'Keine ausstehenden Prüfungen.',
      reviewsLoadFailed: 'Prüfungen konnten nicht geladen werden.',
    },
  }[language];
  const getStatusLabel = (status: PendingReview['status']) =>
    status === 'escalated' ? copy.statusEscalated : copy.statusPending;

  const loadInvoices = useCallback(async () => {
    setInvoicesLoading(true);
    setInvoicesError(null);
    try {
      const fetchedInvoices = await fetchInvoices();
      setInvoices(fetchedInvoices);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      setInvoicesError(message);
      setInvoices([]);
    } finally {
      setInvoicesLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadInvoices();
  }, [loadInvoices]);

  const dashboardReviews = useMemo<PendingReview[]>(() => {
    return invoices
      .filter((invoice) => !isProcessedStatus(invoice.status))
      .map((invoice) => toPendingReview(invoice))
      .sort((a, b) => b.date.localeCompare(a.date));
  }, [invoices]);

  const chartData = useMemo(() => {
    const localeByLanguage: Record<typeof language, string> = {
      fr: 'fr-FR',
      en: 'en-US',
      de: 'de-DE',
    };
    const locale = localeByLanguage[language];
    const monthlyCounts = new Map<string, number>();

    for (const invoice of invoices) {
      const createdAt = new Date(invoice.created_at);
      if (Number.isNaN(createdAt.getTime())) {
        continue;
      }
      const key = `${createdAt.getFullYear()}-${String(createdAt.getMonth() + 1).padStart(2, '0')}`;
      monthlyCounts.set(key, (monthlyCounts.get(key) ?? 0) + 1);
    }

    const now = new Date();
    const points: Array<{ month: string; volume: number }> = [];
    for (let offset = 6; offset >= 0; offset -= 1) {
      const pointDate = new Date(now.getFullYear(), now.getMonth() - offset, 1);
      const key = `${pointDate.getFullYear()}-${String(pointDate.getMonth() + 1).padStart(2, '0')}`;
      points.push({
        month: pointDate.toLocaleDateString(locale, { month: 'short' }),
        volume: monthlyCounts.get(key) ?? 0,
      });
    }
    return points;
  }, [invoices, language]);

  const processedInvoices = useMemo(
    () => invoices.filter((invoice) => isProcessedStatus(invoice.status)),
    [invoices],
  );

  const rejectedInvoices = useMemo(
    () => invoices.filter((invoice) => invoice.status === 'rejected'),
    [invoices],
  );

  const totalValueProtected = useMemo(() => {
    return rejectedInvoices.reduce((sum, invoice) => sum + (decimalToNumber(invoice.total) ?? 0), 0);
  }, [rejectedInvoices]);

  const trend = useMemo(() => {
    const now = new Date();
    const currentMonthKey = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
    const previousDate = new Date(now.getFullYear(), now.getMonth() - 1, 1);
    const previousMonthKey = `${previousDate.getFullYear()}-${String(previousDate.getMonth() + 1).padStart(2, '0')}`;

    let currentMonthTotal = 0;
    let previousMonthTotal = 0;

    for (const invoice of rejectedInvoices) {
      const createdAt = new Date(invoice.created_at);
      if (Number.isNaN(createdAt.getTime())) {
        continue;
      }
      const key = `${createdAt.getFullYear()}-${String(createdAt.getMonth() + 1).padStart(2, '0')}`;
      const amount = decimalToNumber(invoice.total) ?? 0;
      if (key === currentMonthKey) {
        currentMonthTotal += amount;
      } else if (key === previousMonthKey) {
        previousMonthTotal += amount;
      }
    }

    const percentChange = previousMonthTotal > 0
      ? ((currentMonthTotal - previousMonthTotal) / previousMonthTotal) * 100
      : null;

    return { percentChange };
  }, [rejectedInvoices]);

  const primaryCurrency = rejectedInvoices.find((invoice) => invoice.currency)?.currency
    ?? invoices.find((invoice) => invoice.currency)?.currency
    ?? 'USD';

  const totalValueDisplay = formatCurrencyValue(totalValueProtected, primaryCurrency);
  const totalValueTrendDisplay = trend.percentChange === null
    ? '—'
    : `${trend.percentChange >= 0 ? '↑' : '↓'} ${Math.abs(trend.percentChange).toFixed(1)}%`;
  const totalValueTrendColor = trend.percentChange === null
    ? '#71717A'
    : (trend.percentChange >= 0 ? '#00FF94' : '#FF0055');

  const processedCount = processedInvoices.length;
  const pendingCount = dashboardReviews.length;

  const isAcceptedFile = (file: File): boolean => {
    if (ACCEPTED_MIME_TYPES.has(file.type)) {
      return true;
    }
    const extension = file.name.split('.').pop()?.toLowerCase() ?? '';
    return ACCEPTED_EXTENSIONS.includes(extension);
  };

  const openFileDialog = () => {
    if (!uploading) {
      fileInputRef.current?.click();
    }
  };

  const runUpload = async (file: File) => {
    if (file.size > MAX_UPLOAD_SIZE_BYTES) {
      setUploadSuccess(null);
      setUploadError(copy.fileTooLarge);
      return;
    }
    if (!isAcceptedFile(file)) {
      setUploadSuccess(null);
      setUploadError(copy.invalidFileType);
      return;
    }

    setUploading(true);
    setUploadError(null);
    setUploadSuccess(null);

    try {
      const response = await uploadInvoiceForExtraction(file);
      const invoiceNumber = response.invoice.invoice_number
        ?? response.extraction.invoice_number
        ?? response.invoice.id.slice(0, 8).toUpperCase();

      if (!isProcessedStatus(response.invoice.status)) {
        setPanelOpen(true);
        setUploadSuccess(copy.uploadSuccessReview(invoiceNumber));
      } else {
        setUploadSuccess(copy.uploadSuccessApproved(invoiceNumber));
      }
      await loadInvoices();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      setUploadError(`${copy.uploadErrorPrefix} ${message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile) {
      void runUpload(selectedFile);
    }
    event.target.value = '';
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile) {
      void runUpload(droppedFile);
    }
  };

  const handleUploadKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      openFileDialog();
    }
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
                  {totalValueDisplay}
                </div>
              </div>
              <div className="w-12 h-12 rounded-lg flex items-center justify-center" style={{ background: 'rgba(0, 242, 255, 0.08)', border: '1px solid rgba(0, 242, 255, 0.2)' }}>
                <ShieldIcon className="w-6 h-6 text-[#00F2FF]" />
              </div>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span style={{ color: totalValueTrendColor }}>{totalValueTrendDisplay}</span>
              <span className="text-[#71717A]">{copy.totalValueTrend}</span>
            </div>
          </div>

          <div
            className="rounded-xl p-4 sm:p-6 backdrop-blur-[20px]"
            style={{ background: 'rgba(20, 22, 25, 0.6)', border: '1px solid rgba(255, 255, 255, 0.1)', boxShadow: 'inset 0 1px 0 0 rgba(255, 255, 255, 0.1)' }}
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <div className="text-xs text-[#71717A] uppercase tracking-wider font-medium mb-2">{copy.invoicesProcessed}</div>
                <div className="text-4xl sm:text-5xl display-number text-[#00FF94]">
                  {processedCount}
                </div>
              </div>
              <div className="w-12 h-12 rounded-lg flex items-center justify-center" style={{ background: 'rgba(0, 255, 148, 0.08)', border: '1px solid rgba(0, 255, 148, 0.2)' }}>
                <Clock className="w-6 h-6 text-[#00FF94]" />
              </div>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span className="text-[#00F2FF]">{pendingCount}</span>
              <span className="text-[#71717A]">{copy.invoicesProcessedTrend}</span>
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
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.png,.jpg,.jpeg,.webp,application/pdf,image/png,image/jpeg,image/webp"
            className="hidden"
            onChange={handleFileSelect}
            disabled={uploading}
          />
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
            onClick={openFileDialog}
            onKeyDown={handleUploadKeyDown}
            role="button"
            tabIndex={0}
            aria-busy={uploading}
            className="border border-dashed rounded-xl p-8 sm:p-12 text-center transition-all cursor-pointer"
            style={
              dragActive
                ? { borderColor: '#00F2FF', background: 'rgba(0, 242, 255, 0.05)' }
                : { borderColor: 'rgba(255, 255, 255, 0.15)', background: 'rgba(6, 7, 9, 0.4)' }
            }
          >
            <Upload className="w-16 h-16 text-[#00F2FF] mx-auto mb-4" strokeWidth={1.5} />
            <p className="text-[#FAFAFA] text-base mb-2 font-medium">{uploading ? copy.uploadingLabel : copy.dropInvoice}</p>
            <p className="text-[#71717A] text-sm">{copy.fileFormatHint}</p>
          </div>
          {uploadError && (
            <p className="mt-3 text-sm text-[#FF6B8A]">{uploadError}</p>
          )}
          {uploadSuccess && (
            <p className="mt-3 text-sm text-[#00FF94]">{uploadSuccess}</p>
          )}
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
          {dashboardReviews.length}
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
              <p className="text-[11px] text-[#71717A] mt-0.5">{copy.pendingInvoicesCount(dashboardReviews.length)}</p>
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
          {invoicesLoading && (
            <div className="text-sm text-[#71717A]">{copy.loadingReviews}</div>
          )}
          {!invoicesLoading && invoicesError && (
            <div className="text-sm text-[#FF6B8A]">{copy.reviewsLoadFailed}</div>
          )}
          {!invoicesLoading && !invoicesError && dashboardReviews.length === 0 && (
            <div className="text-sm text-[#71717A]">{copy.noPendingReviews}</div>
          )}
          {!invoicesLoading && !invoicesError && dashboardReviews.map((review) => (
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
                      ? <AlertCircle className="w-3.5 h-3.5 shrink-0 text-[#FF0055]" />
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
