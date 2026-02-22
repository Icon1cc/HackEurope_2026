import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router';
import { AlertTriangle, CheckCircle2, FileText, Send, XCircle, ArrowLeft, ShieldCheck } from 'lucide-react';
import { Sidebar } from '../components/Sidebar';
import { Footer } from '../components/Footer';
import { VercelBackground } from '../components/VercelBackground';
import { pendingReviews } from '../data/pendingReviews';
import { mockVendorInvoices, mockVendors } from '../data/mockVendors';
import { useAppLanguage } from '../i18n/AppLanguageProvider';

export default function ReviewDetail() {
  const { reviewId } = useParams();
  const language = useAppLanguage();
  
  const review = useMemo(() => {
    // 1. Try to find in pendingReviews
    const pending = pendingReviews.find((item) => item.id === reviewId);
    if (pending) return { ...pending, isReview: true };

    // 2. Try to find in mockVendorInvoices
    const invoice = mockVendorInvoices.find((item) => item.id === reviewId);
    if (invoice) {
      const vendor = mockVendors.find(v => v.id === invoice.vendorId);
      return {
        id: invoice.id,
        invoiceNumber: invoice.invoiceNumber,
        vendor: vendor?.name || 'Unknown Vendor',
        amount: invoice.amount,
        date: invoice.date,
        status: invoice.status === 'flagged' ? 'pending' : (invoice.status === 'rejected' ? 'escalated' : 'paid'),
        contactEmail: `billing@${(vendor?.name || 'vendor').toLowerCase().replace(/\s+/g, '')}.com`,
        reasons: {
          fr: invoice.status === 'paid' ? ['Facture approuvée et payée.'] : 
              invoice.status === 'pending' ? ['Facture en cours de traitement.'] : 
              ['Anomalie détectée par le système.'],
          en: invoice.status === 'paid' ? ['Invoice approved and paid.'] : 
              invoice.status === 'pending' ? ['Invoice currently being processed.'] : 
              ['Anomaly detected by the system.'],
          de: invoice.status === 'paid' ? ['Rechnung genehmigt und bezahlt.'] : 
              invoice.status === 'pending' ? ['Rechnung wird zur Zeit bearbeitet.'] : 
              ['Vom System erkannte Anomalie.']
        },
        emailDraft: {
          fr: 'Brouillon non disponible pour les factures traitées.',
          en: 'Draft not available for processed invoices.',
          de: 'Entwurf für bearbeitete Rechnungen nicht verfügbar.'
        },
        isReview: false,
        rawStatus: invoice.status
      };
    }

    return null;
  }, [reviewId]);

  const [recipientEmail, setRecipientEmail] = useState('');
  const [negotiationEmail, setNegotiationEmail] = useState('');
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);

  const copy = {
    fr: {
      title: 'Facture',
      reviewTitle: 'Review',
      paidStatus: 'PAYÉE',
      backToDashboard: 'Retour au dashboard',
      previewTitle: 'Aperçu de la facture',
      invoiceNumber: 'Numéro de facture',
      date: 'Date',
      description: 'Description',
      amount: 'Montant',
      professionalServices: 'Services Professionnels',
      platformSubscription: 'Abonnement Plateforme',
      included: 'Inclus',
      totalDue: 'Total dû',
      decisionPanel: 'Panneau de décision',
      processingStatus: 'Statut du traitement',
      blockingReasons: 'Raisons du blocage',
      recipient: 'Destinataire',
      emailDraft: 'Brouillon d\'email de négociation',
      approve: 'Approuver la facture',
      reject: 'Rejeter & Envoyer Email',
      processingFinished: 'Traitement terminé',
      processingFinishedDesc: 'Cette facture a déjà été traitée par le système. Aucune action manuelle n\'est requise.',
      invoiceNotFound: 'Facture introuvable',
      invoiceNotFoundDesc: 'La facture demandée n\'existe pas ou a été supprimée.',
      approveFeedback: (num: string) => `Facture ${num} approuvée telle quelle.`,
      rejectFeedback: (num: string, email: string) => `Facture ${num} rejetée. Email de négociation prêt à l'envoi vers ${email}.`,
    },
    en: {
      title: 'Invoice',
      reviewTitle: 'Review',
      paidStatus: 'PAID',
      backToDashboard: 'Back to dashboard',
      previewTitle: 'Invoice Preview',
      invoiceNumber: 'Invoice Number',
      date: 'Date',
      description: 'Description',
      amount: 'Amount',
      professionalServices: 'Professional Services',
      platformSubscription: 'Platform Subscription',
      included: 'Included',
      totalDue: 'Total Due',
      decisionPanel: 'Decision Panel',
      processingStatus: 'Processing Status',
      blockingReasons: 'Blocking Reasons',
      recipient: 'Recipient',
      emailDraft: 'Negotiation Email Draft',
      approve: 'Approve Invoice',
      reject: 'Reject & Send Email',
      processingFinished: 'Processing Finished',
      processingFinishedDesc: 'This invoice has already been processed by the system. No manual action is required.',
      invoiceNotFound: 'Invoice not found',
      invoiceNotFoundDesc: 'The requested invoice does not exist or has been deleted.',
      approveFeedback: (num: string) => `Invoice ${num} approved as is.`,
      rejectFeedback: (num: string, email: string) => `Invoice ${num} rejected. Negotiation email ready to send to ${email}.`,
    },
    de: {
      title: 'Rechnung',
      reviewTitle: 'Prüfung',
      paidStatus: 'BEZAHLT',
      backToDashboard: 'Zurück zum Dashboard',
      previewTitle: 'Rechnungsvorschau',
      invoiceNumber: 'Rechnungsnummer',
      date: 'Datum',
      description: 'Beschreibung',
      amount: 'Betrag',
      professionalServices: 'Professionelle Dienstleistungen',
      platformSubscription: 'Plattform-Abonnement',
      included: 'Inklusive',
      totalDue: 'Gesamtbetrag',
      decisionPanel: 'Entscheidungspanel',
      processingStatus: 'Verarbeitungsstatus',
      blockingReasons: 'Gründe für die Blockierung',
      recipient: 'Empfänger',
      emailDraft: 'Entwurf Verhandlungs-E-Mail',
      approve: 'Rechnung genehmigen',
      reject: 'Ablehnen & E-Mail senden',
      processingFinished: 'Verarbeitung abgeschlossen',
      processingFinishedDesc: 'Diese Rechnung wurde bereits vom System verarbeitet. Keine manuelle Aktion erforderlich.',
      invoiceNotFound: 'Rechnung nicht gefunden',
      invoiceNotFoundDesc: 'Die angeforderte Rechnung existiert nicht oder wurde gelöscht.',
      approveFeedback: (num: string) => `Rechnung ${num} wie vorliegend genehmigt.`,
      rejectFeedback: (num: string, email: string) => `Rechnung ${num} abgelehnt. Verhandlungs-E-Mail bereit zum Versand an ${email}.`,
    }
  }[language];

  useEffect(() => {
    if (!review) {
      return;
    }

    setRecipientEmail(review.contactEmail);
    setNegotiationEmail((review.emailDraft as any)[language]);
    setActionFeedback(null);
  }, [review, language]);

  if (!review) {
    return (
      <div className="flex min-h-screen relative overflow-hidden">
        <VercelBackground />
        <Sidebar />
        <main className="flex-1 lg:ml-64 p-8 relative z-10 flex items-center justify-center">
          <div className="text-center">
            <h1
              className="text-3xl mb-4"
              style={{
                fontFamily: 'Geist Sans, Inter, sans-serif',
                fontWeight: 700,
                letterSpacing: '-0.02em',
                color: '#FAFAFA',
              }}
            >
              {copy.invoiceNotFound}
            </h1>
            <p className="text-[#71717A] mb-6">{copy.invoiceNotFoundDesc}</p>
            <Link
              to="/dashboard"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-medium transition-all"
              style={{
                background: 'rgba(0, 242, 255, 0.08)',
                border: '1px solid rgba(0, 242, 255, 0.2)',
                color: '#00F2FF',
              }}
            >
              <ArrowLeft className="w-4 h-4" />
              {copy.backToDashboard}
            </Link>
          </div>
        </main>
      </div>
    );
  }

  const handleApprove = () => {
    setActionFeedback(copy.approveFeedback(review.invoiceNumber));
  };

  const handleRejectAndSend = () => {
    setActionFeedback(copy.rejectFeedback(review.invoiceNumber, recipientEmail));
  };

  // Get reasons based on current language
  const currentReasons = (review.reasons as any)[language] || [];

  return (
    <div className="flex min-h-screen relative overflow-hidden">
      <VercelBackground />

      <Sidebar />

      <main className="flex-1 lg:ml-64 p-4 sm:p-6 lg:p-8 relative z-10">
        <div className="mb-6 pt-12 lg:pt-0 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1
                className="text-2xl sm:text-3xl lg:text-4xl"
                style={{
                  fontFamily: 'Geist Sans, Inter, sans-serif',
                  fontWeight: 700,
                  letterSpacing: '-0.02em',
                  color: '#FAFAFA',
                }}
              >
                {review.isReview ? copy.reviewTitle : copy.title} {review.invoiceNumber}
              </h1>
              {review.rawStatus === 'paid' && (
                <span className="px-2 py-1 rounded-md text-[10px] uppercase font-bold tracking-wider bg-[#00FF94]/10 text-[#00FF94] border border-[#00FF94]/20 flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3" /> {copy.paidStatus}
                </span>
              )}
            </div>
            <p className="text-[#71717A] text-xs sm:text-sm">
              {review.vendor} • {review.amount} • {review.date}
            </p>
          </div>

          <Link
            to="/dashboard"
            className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm transition-all w-full sm:w-auto"
            style={{
              background: 'rgba(20, 22, 25, 0.7)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              color: '#FAFAFA',
            }}
          >
            <ArrowLeft className="w-4 h-4" />
            {copy.backToDashboard}
          </Link>
        </div>

        <section
          className="rounded-xl overflow-hidden backdrop-blur-[20px]"
          style={{
            background: 'rgba(20, 22, 25, 0.6)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            boxShadow: 'inset 0 1px 0 0 rgba(255, 255, 255, 0.1)',
          }}
        >
          <div className="flex flex-col lg:flex-row min-h-[calc(100vh-210px)]">
            <section className="lg:flex-1 p-4 sm:p-6 lg:p-8 border-b lg:border-b-0">
              <div className="mb-5">
                <h2
                  className="text-xl sm:text-2xl mb-1"
                  style={{
                    fontFamily: 'Geist Sans, Inter, sans-serif',
                    fontWeight: 700,
                    letterSpacing: '-0.02em',
                  }}
                >
                  {copy.previewTitle}
                </h2>
                <p className="text-xs sm:text-sm text-[#71717A]">
                  {review.vendor} • {review.invoiceNumber}
                </p>
              </div>

              <div
                className="rounded-xl p-3 sm:p-6 lg:p-8 overflow-x-auto"
                style={{
                  background: 'rgba(6, 7, 9, 0.7)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                }}
              >
                <div className="min-w-[500px] sm:min-w-0 max-w-3xl mx-auto bg-white rounded-lg p-6 sm:p-10 text-left shadow-2xl">
                  <div className="border-b border-gray-300 pb-5 mb-6">
                    <h3 className="text-2xl text-gray-900 font-bold mb-2">{review.vendor}</h3>
                    <p className="text-sm text-gray-600">123 Business Street, Tech City, TC 12345</p>
                    <p className="text-sm text-gray-600">{review.contactEmail} • +1 (555) 123-4567</p>
                  </div>

                  <div className="grid grid-cols-2 gap-8 mb-8">
                    <div>
                      <div className="text-xs text-gray-500 mb-1 uppercase tracking-wider font-semibold">{copy.invoiceNumber}</div>
                      <div className="text-gray-900 font-semibold">{review.invoiceNumber}</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500 mb-1 uppercase tracking-wider font-semibold">{copy.date}</div>
                      <div className="text-gray-900 font-semibold">{review.date}</div>
                    </div>
                  </div>

                  <table className="w-full mb-8">
                    <thead>
                      <tr className="border-b-2 border-gray-300">
                        <th className="text-left py-3 text-sm text-gray-700 font-bold">{copy.description}</th>
                        <th className="text-right py-3 text-sm text-gray-700 font-bold">{copy.amount}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td className="py-3 text-gray-900">{copy.professionalServices}</td>
                        <td className="text-right text-gray-900 font-semibold">{review.amount}</td>
                      </tr>
                      <tr>
                        <td className="py-3 text-gray-900">{copy.platformSubscription}</td>
                        <td className="text-right text-gray-900 font-semibold">{copy.included}</td>
                      </tr>
                    </tbody>
                  </table>

                  <div className="border-t-2 border-gray-300 pt-6 flex justify-between items-center">
                    <span className="text-lg sm:text-xl text-gray-900 font-bold">{copy.totalDue}</span>
                    <span className="text-3xl sm:text-4xl text-gray-900 font-bold">{review.amount}</span>
                  </div>
                </div>
              </div>
            </section>

            <section
              className="lg:w-[380px] xl:w-[420px] p-4 sm:p-6 border-t lg:border-t-0 lg:border-l"
              style={{ borderColor: 'rgba(255, 255, 255, 0.1)' }}
            >
              <div className="flex items-center gap-2 mb-4">
                <FileText className="w-5 h-5 text-[#00F2FF]" />
                <h2
                  className="text-xl"
                  style={{
                    fontFamily: 'Geist Sans, Inter, sans-serif',
                    fontWeight: 700,
                    letterSpacing: '-0.02em',
                  }}
                >
                  {copy.decisionPanel}
                </h2>
              </div>

              <div
                className="rounded-lg p-4 mb-4"
                style={{
                  background: 'rgba(20, 22, 25, 0.6)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                }}
              >
                <div className="text-xs text-[#71717A] uppercase tracking-wider font-semibold mb-3">
                  {review.rawStatus === 'paid' ? copy.processingStatus : copy.blockingReasons}
                </div>
                <ul className="space-y-2">
                  {currentReasons.map((reason: string, index: number) => (
                    <li key={`${review.id}-${index}`} className="flex items-start gap-2 text-sm text-[#E4E4E7] leading-relaxed">
                      {review.rawStatus === 'paid' ? (
                        <ShieldCheck className="w-4 h-4 text-[#00FF94] mt-0.5 flex-shrink-0" />
                      ) : (
                        <AlertTriangle className="w-4 h-4 text-[#FFB800] mt-0.5 flex-shrink-0" />
                      )}
                      <span>{reason}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {review.isReview && (
                <>
                  <div
                    className="rounded-lg p-4 mb-4"
                    style={{
                      background: 'rgba(20, 22, 25, 0.6)',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                    }}
                  >
                    <label htmlFor="recipient-email" className="block text-xs text-[#71717A] uppercase tracking-wider font-semibold mb-2">
                      {copy.recipient}
                    </label>
                    <input
                      id="recipient-email"
                      type="email"
                      value={recipientEmail}
                      onChange={(event) => setRecipientEmail(event.target.value)}
                      className="w-full px-3 py-2.5 rounded-lg text-sm text-white placeholder-[#52525B] outline-none transition-all mb-3"
                      style={{
                        background: 'rgba(6, 7, 9, 0.8)',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                      }}
                    />

                    <label htmlFor="negotiation-email" className="block text-xs text-[#71717A] uppercase tracking-wider font-semibold mb-2">
                      {copy.emailDraft}
                    </label>
                    <textarea
                      id="negotiation-email"
                      value={negotiationEmail}
                      onChange={(event) => setNegotiationEmail(event.target.value)}
                      className="w-full h-48 resize-none px-3 py-2.5 rounded-lg text-sm text-white placeholder-[#52525B] outline-none transition-all"
                      style={{
                        background: 'rgba(6, 7, 9, 0.8)',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                      }}
                    />
                  </div>

                  <div className="space-y-2">
                    <button
                      type="button"
                      onClick={handleApprove}
                      className="w-full py-3 rounded-lg uppercase tracking-wider text-sm transition-all duration-200 flex items-center justify-center gap-2"
                      style={{
                        background: '#00FF94',
                        color: '#060709',
                        fontWeight: 600,
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                      }}
                    >
                      <CheckCircle2 className="w-5 h-5" />
                      <span>{copy.approve}</span>
                    </button>

                    <button
                      type="button"
                      onClick={handleRejectAndSend}
                      className="w-full py-3 rounded-lg uppercase tracking-wider text-sm transition-all duration-200 flex items-center justify-center gap-2"
                      style={{
                        background: 'transparent',
                        color: '#FF0055',
                        border: '1px solid #FF0055',
                        fontWeight: 600,
                      }}
                    >
                      <XCircle className="w-5 h-5" />
                      <Send className="w-4 h-4" />
                      <span>{copy.reject}</span>
                    </button>
                  </div>
                </>
              )}

              {!review.isReview && (
                <div 
                  className="rounded-lg p-6 text-center"
                  style={{
                    background: 'rgba(255, 255, 255, 0.03)',
                    border: '1px solid rgba(255, 255, 255, 0.05)',
                  }}
                >
                  <ShieldCheck className="w-12 h-12 text-[#00FF94] mx-auto mb-3 opacity-50" />
                  <p className="text-sm text-[#FAFAFA] font-medium mb-1">{copy.processingFinished}</p>
                  <p className="text-xs text-[#71717A]">
                    {copy.processingFinishedDesc}
                  </p>
                </div>
              )}

              {actionFeedback && (
                <div
                  className="mt-4 rounded-lg p-3 text-sm"
                  style={{
                    background: 'rgba(0, 242, 255, 0.08)',
                    border: '1px solid rgba(0, 242, 255, 0.2)',
                    color: '#E4E4E7',
                  }}
                >
                  {actionFeedback}
                </div>
              )}
            </section>
          </div>
        </section>

        <Footer />
      </main>
    </div>
  );
}
