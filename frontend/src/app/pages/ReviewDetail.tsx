import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router';
import { AlertTriangle, CheckCircle2, FileText, Send, XCircle, ArrowLeft, ShieldCheck, CreditCard, Building2 } from 'lucide-react';
import { Sidebar } from '../components/Sidebar';
import { Footer } from '../components/Footer';
import { VercelBackground } from '../components/VercelBackground';
import {
  approveInvoice,
  decimalToNumber,
  dispatchInvoicesUpdatedEvent,
  fetchInvoiceById,
  fetchPaymentsByInvoice,
  fetchPaymentConfirmation,
  fetchVendorById,
  formatCurrencyValue,
  updateInvoice,
  type InvoiceApiResponse,
  type PaymentApiResponse,
  type PaymentConfirmationApiResponse,
} from '../api/backend';
import {
  buildFallbackEmail,
  extractDecisionReasonSummary,
  extractReviewReasons,
  invoiceNumberOrFallback,
  isProcessedStatus,
} from '../data/reviewTypes';
import { useAppLanguage } from '../i18n/AppLanguageProvider';

interface LineItemView {
  description: string;
  quantity: string;
  unitPrice: string;
  amount: string;
}

function formatQuantity(value: string | number | null | undefined): string {
  const n = decimalToNumber(value);
  if (n === null) return '';
  return Number.isInteger(n) ? String(n) : n.toFixed(2).replace(/\.?0+$/, '');
}

interface ReviewViewModel {
  id: string;
  invoiceNumber: string;
  vendor: string;
  amount: string;
  date: string;
  contactEmail: string;
  reasons: {
    fr: string[];
    en: string[];
    de: string[];
  };
  emailDraft: {
    fr: string;
    en: string;
    de: string;
  };
  isReview: boolean;
  rawStatus: string;
  decisionState: 'approved' | 'rejected';
  decisionSummary: string | null;
  vendorAddress: string;
  lineItems: LineItemView[];
  subtotal: string;
  tax: string | null;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function toLineItems(invoice: InvoiceApiResponse): LineItemView[] {
  if (invoice.items.length > 0) {
    return invoice.items.map((item) => ({
      description: item.description || 'Line item',
      quantity: formatQuantity(item.quantity),
      unitPrice: formatCurrencyValue(item.unit_price, invoice.currency),
      amount: formatCurrencyValue(item.total_price, invoice.currency),
    }));
  }

  if (isRecord(invoice.extracted_data) && Array.isArray(invoice.extracted_data.line_items)) {
    const extractedItems = invoice.extracted_data.line_items
      .map((item) => {
        if (!isRecord(item)) {
          return null;
        }
        const description = typeof item.description === 'string' && item.description.trim().length > 0
          ? item.description.trim()
          : 'Line item';
        const totalPrice = typeof item.total_price === 'number' || typeof item.total_price === 'string'
          ? item.total_price
          : null;
        const unitPrice = typeof item.unit_price === 'number' || typeof item.unit_price === 'string'
          ? item.unit_price
          : null;
        const qty = typeof item.quantity === 'number' || typeof item.quantity === 'string'
          ? item.quantity
          : null;
        return {
          description,
          quantity: formatQuantity(qty),
          unitPrice: formatCurrencyValue(unitPrice, invoice.currency),
          amount: formatCurrencyValue(totalPrice, invoice.currency),
        };
      })
      .filter((item): item is LineItemView => item !== null);

    if (extractedItems.length > 0) {
      return extractedItems;
    }
  }

  return [
    {
      description: 'Line item',
      quantity: '',
      unitPrice: '',
      amount: formatCurrencyValue(invoice.total, invoice.currency),
    },
  ];
}

function buildEmailDraft(invoiceNumber: string, vendorName: string, reasons: string[]): ReviewViewModel['emailDraft'] {
  const bulletPoints = reasons.map((reason) => `- ${reason}`).join('\n');
  return {
    en: `Hello,\n\nWe are reviewing invoice ${invoiceNumber} from ${vendorName}. Before approval, we need clarification on the following points:\n${bulletPoints}\n\nPlease confirm and share supporting details.\n\nBest regards,\nAccounts Payable Team`,
    fr: `Bonjour,\n\nNous examinons la facture ${invoiceNumber} de ${vendorName}. Avant validation, nous avons besoin d'une clarification sur les points suivants :\n${bulletPoints}\n\nMerci de confirmer et de partager les éléments justificatifs.\n\nCordialement,\nÉquipe Accounts Payable`,
    de: `Hallo,\n\nwir prüfen die Rechnung ${invoiceNumber} von ${vendorName}. Vor der Freigabe benötigen wir eine Klärung zu folgenden Punkten:\n${bulletPoints}\n\nBitte bestätigen Sie die Punkte und senden Sie die entsprechenden Nachweise.\n\nMit freundlichen Grüßen,\nTeam Kreditorenbuchhaltung`,
  };
}

function toLocalizedReasons(reasons: string[]): ReviewViewModel['reasons'] {
  return {
    fr: reasons,
    en: reasons,
    de: reasons,
  };
}

function buildManualDecisionSummary(
  action: 'approved' | 'rejected',
  reasons: string[],
  recipientEmail?: string,
): string {
  const normalizedReasons = reasons
    .map((reason) => reason.trim())
    .filter((reason) => reason.length > 0)
    .slice(0, 3);
  const reasonSuffix = normalizedReasons.length > 0 ? ` ${normalizedReasons.join(' ')}` : '';

  if (action === 'approved') {
    return `Approved after human review.${reasonSuffix}`;
  }

  const recipientSuffix = recipientEmail?.trim() ? ` Negotiation note prepared for ${recipientEmail.trim()}.` : '';
  return `Rejected after human review due to unresolved concerns.${reasonSuffix}${recipientSuffix}`;
}

function toReviewViewModel(invoice: InvoiceApiResponse): ReviewViewModel {
  const invoiceNumber = invoiceNumberOrFallback(invoice);
  const vendorName = invoice.vendor_name?.trim() || 'Unknown Vendor';
  const reasons = extractReviewReasons(invoice);
  const normalizedStatus = invoice.status?.trim().toLowerCase() ?? '';
  const isReview = !isProcessedStatus(normalizedStatus);
  const decisionSummary = isReview ? null : extractDecisionReasonSummary(invoice);
  const decisionState = normalizedStatus === 'rejected' ? 'rejected' : 'approved';

  return {
    id: invoice.id,
    invoiceNumber,
    vendor: vendorName,
    amount: formatCurrencyValue(invoice.total, invoice.currency),
    date: invoice.created_at?.slice(0, 10) ?? '',
    contactEmail: buildFallbackEmail(vendorName),
    reasons: toLocalizedReasons(reasons),
    emailDraft: isReview
      ? (invoice.negotiation_email
          ? { en: invoice.negotiation_email, fr: invoice.negotiation_email, de: invoice.negotiation_email }
          : buildEmailDraft(invoiceNumber, vendorName, reasons))
      : {
          en: 'Draft not available for processed invoices.',
          fr: 'Brouillon non disponible pour les factures traitées.',
          de: 'Entwurf für bearbeitete Rechnungen nicht verfügbar.',
        },
    isReview,
    rawStatus: normalizedStatus,
    decisionState,
    decisionSummary,
    vendorAddress: invoice.vendor_address?.trim() || 'Address unavailable',
    lineItems: toLineItems(invoice),
    subtotal: formatCurrencyValue(invoice.subtotal ?? invoice.total, invoice.currency),
    tax: decimalToNumber(invoice.tax) ? formatCurrencyValue(invoice.tax, invoice.currency) : null,
  };
}

export default function ReviewDetail() {
  const { reviewId } = useParams();
  const language = useAppLanguage();
  const [invoice, setInvoice] = useState<InvoiceApiResponse | null>(null);
  const [invoiceLoading, setInvoiceLoading] = useState(true);
  const [invoiceError, setInvoiceError] = useState<string | null>(null);
  const review = useMemo(() => (invoice ? toReviewViewModel(invoice) : null), [invoice]);

  useEffect(() => {
    if (!reviewId) {
      setInvoice(null);
      setInvoiceLoading(false);
      setInvoiceError('Missing invoice id');
      return;
    }

    let cancelled = false;
    const loadInvoice = async () => {
      setInvoiceLoading(true);
      setInvoiceError(null);
      try {
        const fetchedInvoice = await fetchInvoiceById(reviewId);
        if (!cancelled) {
          setInvoice(fetchedInvoice);
        }
      } catch (error) {
        if (!cancelled) {
          const message = error instanceof Error ? error.message : 'Unknown error';
          setInvoiceError(message);
          setInvoice(null);
        }
      } finally {
        if (!cancelled) {
          setInvoiceLoading(false);
        }
      }
    };

    void loadInvoice();
    return () => {
      cancelled = true;
    };
  }, [reviewId]);

  const [paymentConfirmation, setPaymentConfirmation] = useState<PaymentConfirmationApiResponse | null>(null);
  const [paymentRecord, setPaymentRecord] = useState<PaymentApiResponse | null>(null);
  const [vendorIban, setVendorIban] = useState<string | null>(null);

  useEffect(() => {
    if (!invoice || (invoice.status !== 'paid' && invoice.status !== 'approved')) {
      setPaymentConfirmation(null);
      setPaymentRecord(null);
      setVendorIban(null);
      return;
    }

    let cancelled = false;
    const loadPaymentData = async () => {
      try {
        const payments = await fetchPaymentsByInvoice(invoice.id);
        if (cancelled) return;

        const latestPayment = [...payments].sort(
          (a, b) => new Date(b.initiated_at).getTime() - new Date(a.initiated_at).getTime(),
        )[0] ?? null;
        setPaymentRecord(latestPayment);

        if (invoice.vendor_id) {
          try {
            const vendor = await fetchVendorById(invoice.vendor_id);
            if (!cancelled) {
              setVendorIban(vendor.registered_iban ?? null);
            }
          } catch {
            if (!cancelled) {
              setVendorIban(null);
            }
          }
        } else {
          setVendorIban(null);
        }

        if (!latestPayment || latestPayment.status !== 'confirmed') {
          setPaymentConfirmation(null);
          return;
        }

        const confirmation = await fetchPaymentConfirmation(latestPayment.id);
        if (!cancelled) setPaymentConfirmation(confirmation);
      } catch {
        if (!cancelled) {
          setPaymentConfirmation(null);
          setPaymentRecord(null);
          setVendorIban(null);
        }
      }
    };

    void loadPaymentData();
    return () => { cancelled = true; };
  }, [invoice]);

  const [recipientEmail, setRecipientEmail] = useState('');
  const [negotiationEmail, setNegotiationEmail] = useState('');
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);
  const [decisionSubmitting, setDecisionSubmitting] = useState(false);

  const copy = {
    fr: {
      title: 'Facture',
      reviewTitle: 'Review',
      approvedStatus: 'APPROUVÉE',
      rejectedStatus: 'REJETÉE',
      backToDashboard: 'Retour au dashboard',
      previewTitle: 'Aperçu de la facture',
      invoiceNumber: 'Numéro de facture',
      date: 'Date',
      description: 'Description',
      quantity: 'Qté',
      unitPrice: 'Prix unitaire',
      amount: 'Total',
      professionalServices: 'Services Professionnels',
      platformSubscription: 'Abonnement Plateforme',
      included: 'Inclus',
      subtotal: 'Sous-total',
      tax: 'TVA',
      totalDue: 'Total dû',
      decisionPanel: 'Panneau de décision',
      processingStatus: 'Statut du traitement',
      blockingReasons: 'Raisons du blocage',
      reasoningSection: 'Résumé du raisonnement',
      recipient: 'Destinataire',
      emailDraft: 'Brouillon d\'email de négociation',
      approve: 'Approuver la facture',
      reject: 'Rejeter & Envoyer Email',
      savingDecision: 'Enregistrement...',
      processingFinished: 'Traitement terminé',
      processingFinishedDesc: 'Cette facture a déjà été traitée par le système. Aucune action manuelle n\'est requise.',
      processingApprovedDesc: 'Décision finale: facture approuvée.',
      processingRejectedDesc: 'Décision finale: facture rejetée.',
      invoiceNotFound: 'Facture introuvable',
      invoiceNotFoundDesc: 'La facture demandée n\'existe pas ou a été supprimée.',
      invoiceLoading: 'Chargement de la facture...',
      reasoningFallbackApproved: 'Facture approuvée après revue manuelle.',
      reasoningFallbackRejected: 'Facture rejetée après revue manuelle.',
      approveFeedback: (num: string) => `Facture ${num} approuvée telle quelle.`,
      rejectFeedback: (num: string, email: string) => `Facture ${num} rejetée. Email de négociation prêt à l'envoi vers ${email}.`,
      decisionUpdateError: (message: string) => `Échec de la mise à jour de la décision: ${message}`,
      paymentConfirmation: 'Confirmation de paiement',
      vendorIban: 'IBAN du fournisseur',
      transferId: 'ID du transfert',
      paymentAmount: 'Montant',
      paymentStatus: 'Statut',
      confirmedAt: 'Confirmé le',
      statusConfirmed: 'Confirmé',
      statusInitiated: 'Initié',
      statusPending: 'En attente',
      statusFailed: 'Échoué',
      statusUnknown: 'Inconnu',
      noIban: 'IBAN non renseigné',
      paymentNotFound: 'Aucun enregistrement de paiement lié à cette facture.',
    },
    en: {
      title: 'Invoice',
      reviewTitle: 'Review',
      approvedStatus: 'APPROVED',
      rejectedStatus: 'REJECTED',
      backToDashboard: 'Back to dashboard',
      previewTitle: 'Invoice Preview',
      invoiceNumber: 'Invoice Number',
      date: 'Date',
      description: 'Description',
      quantity: 'Qty',
      unitPrice: 'Unit Price',
      amount: 'Total',
      professionalServices: 'Professional Services',
      platformSubscription: 'Platform Subscription',
      included: 'Included',
      subtotal: 'Subtotal',
      tax: 'VAT',
      totalDue: 'Total Due',
      decisionPanel: 'Decision Panel',
      processingStatus: 'Processing Status',
      blockingReasons: 'Blocking Reasons',
      reasoningSection: 'Reasoning Summary',
      recipient: 'Recipient',
      emailDraft: 'Negotiation Email Draft',
      approve: 'Approve Invoice',
      reject: 'Reject & Send Email',
      savingDecision: 'Saving...',
      processingFinished: 'Processing Finished',
      processingFinishedDesc: 'This invoice has already been processed by the system. No manual action is required.',
      processingApprovedDesc: 'Final decision: invoice approved.',
      processingRejectedDesc: 'Final decision: invoice rejected.',
      invoiceNotFound: 'Invoice not found',
      invoiceNotFoundDesc: 'The requested invoice does not exist or has been deleted.',
      invoiceLoading: 'Loading invoice...',
      reasoningFallbackApproved: 'Invoice approved after manual review.',
      reasoningFallbackRejected: 'Invoice rejected after manual review.',
      approveFeedback: (num: string) => `Invoice ${num} approved as is.`,
      rejectFeedback: (num: string, email: string) => `Invoice ${num} rejected. Negotiation email ready to send to ${email}.`,
      decisionUpdateError: (message: string) => `Failed to update decision: ${message}`,
      paymentConfirmation: 'Payment Confirmation',
      vendorIban: 'Vendor IBAN',
      transferId: 'Transfer ID',
      paymentAmount: 'Amount',
      paymentStatus: 'Status',
      confirmedAt: 'Confirmed at',
      statusConfirmed: 'Confirmed',
      statusInitiated: 'Initiated',
      statusPending: 'Pending',
      statusFailed: 'Failed',
      statusUnknown: 'Unknown',
      noIban: 'IBAN not provided',
      paymentNotFound: 'No payment record is linked to this invoice.',
    },
    de: {
      title: 'Rechnung',
      reviewTitle: 'Prüfung',
      approvedStatus: 'GENEHMIGT',
      rejectedStatus: 'ABGELEHNT',
      backToDashboard: 'Zurück zum Dashboard',
      previewTitle: 'Rechnungsvorschau',
      invoiceNumber: 'Rechnungsnummer',
      date: 'Datum',
      description: 'Beschreibung',
      quantity: 'Menge',
      unitPrice: 'Stückpreis',
      amount: 'Total',
      professionalServices: 'Professionelle Dienstleistungen',
      platformSubscription: 'Plattform-Abonnement',
      included: 'Inklusive',
      subtotal: 'Zwischensumme',
      tax: 'MwSt.',
      totalDue: 'Gesamtbetrag',
      decisionPanel: 'Entscheidungspanel',
      processingStatus: 'Verarbeitungsstatus',
      blockingReasons: 'Gründe für die Blockierung',
      reasoningSection: 'Begründung',
      recipient: 'Empfänger',
      emailDraft: 'Entwurf Verhandlungs-E-Mail',
      approve: 'Rechnung genehmigen',
      reject: 'Ablehnen & E-Mail senden',
      savingDecision: 'Wird gespeichert...',
      processingFinished: 'Verarbeitung abgeschlossen',
      processingFinishedDesc: 'Diese Rechnung wurde bereits vom System verarbeitet. Keine manuelle Aktion erforderlich.',
      processingApprovedDesc: 'Finale Entscheidung: Rechnung genehmigt.',
      processingRejectedDesc: 'Finale Entscheidung: Rechnung abgelehnt.',
      invoiceNotFound: 'Rechnung nicht gefunden',
      invoiceNotFoundDesc: 'Die angeforderte Rechnung existiert nicht oder wurde gelöscht.',
      invoiceLoading: 'Rechnung wird geladen...',
      reasoningFallbackApproved: 'Rechnung nach manueller Prüfung genehmigt.',
      reasoningFallbackRejected: 'Rechnung nach manueller Prüfung abgelehnt.',
      approveFeedback: (num: string) => `Rechnung ${num} wie vorliegend genehmigt.`,
      rejectFeedback: (num: string, email: string) => `Rechnung ${num} abgelehnt. Verhandlungs-E-Mail bereit zum Versand an ${email}.`,
      decisionUpdateError: (message: string) => `Entscheidung konnte nicht aktualisiert werden: ${message}`,
      paymentConfirmation: 'Zahlungsbestätigung',
      vendorIban: 'IBAN des Lieferanten',
      transferId: 'Transfer-ID',
      paymentAmount: 'Betrag',
      paymentStatus: 'Status',
      confirmedAt: 'Bestätigt am',
      statusConfirmed: 'Bestätigt',
      statusInitiated: 'Gestartet',
      statusPending: 'Ausstehend',
      statusFailed: 'Fehlgeschlagen',
      statusUnknown: 'Unbekannt',
      noIban: 'IBAN nicht angegeben',
      paymentNotFound: 'Kein Zahlungseintrag mit dieser Rechnung verknüpft.',
    }
  }[language];

  useEffect(() => {
    if (!review) {
      return;
    }

    setRecipientEmail(review.contactEmail);
    setNegotiationEmail(review.emailDraft[language]);
  }, [review, language]);

  useEffect(() => {
    setActionFeedback(null);
  }, [reviewId]);

  if (invoiceLoading) {
    return (
      <div className="flex min-h-screen relative overflow-hidden">
        <VercelBackground />
        <Sidebar />
        <main className="flex-1 lg:ml-64 p-8 relative z-10 flex items-center justify-center">
          <div className="text-center">
            <p className="text-[#71717A]">{copy.invoiceLoading}</p>
          </div>
        </main>
      </div>
    );
  }

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
            <p className="text-[#71717A] mb-6">{invoiceError ?? copy.invoiceNotFoundDesc}</p>
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

  const currentReasons = review.reasons[language] || [];
  const decisionSummary = (review.decisionSummary?.trim() || (
    review.decisionState === 'rejected'
      ? copy.reasoningFallbackRejected
      : copy.reasoningFallbackApproved
  ));
  const paymentStatusValue = (
    paymentConfirmation?.stripe_confirmation.status
    ?? paymentRecord?.status
    ?? ''
  ).toLowerCase();
  const paymentStatusLabel = (() => {
    if (paymentStatusValue === 'confirmed' || paymentStatusValue === 'paid') {
      return copy.statusConfirmed;
    }
    if (paymentStatusValue === 'initiated') {
      return copy.statusInitiated;
    }
    if (paymentStatusValue === 'pending') {
      return copy.statusPending;
    }
    if (paymentStatusValue === 'failed' || paymentStatusValue === 'canceled') {
      return copy.statusFailed;
    }
    if (paymentStatusValue.length > 0) {
      return paymentStatusValue.toUpperCase();
    }
    return copy.statusUnknown;
  })();
  const paymentStatusColor = (() => {
    if (paymentStatusValue === 'confirmed' || paymentStatusValue === 'paid') {
      return '#00FF94';
    }
    if (paymentStatusValue === 'initiated') {
      return '#00F2FF';
    }
    if (paymentStatusValue === 'pending') {
      return '#FFB800';
    }
    if (paymentStatusValue === 'failed' || paymentStatusValue === 'canceled') {
      return '#FF0055';
    }
    return '#71717A';
  })();
  const paymentAmountValue = paymentConfirmation
    ? formatCurrencyValue(
        paymentConfirmation.stripe_confirmation.amount,
        paymentConfirmation.stripe_confirmation.currency,
      )
    : (paymentRecord ? formatCurrencyValue(paymentRecord.amount, paymentRecord.currency) : '—');
  const paymentConfirmedAt = paymentConfirmation?.stripe_confirmation.confirmed_at ?? paymentRecord?.confirmed_at ?? null;
  const paymentTransferId = paymentConfirmation?.stripe_confirmation.transfer_id ?? paymentRecord?.stripe_payout_id ?? '—';
  const extractedInvoiceIban = (() => {
    if (!invoice || !isRecord(invoice.extracted_data)) {
      return null;
    }
    const raw = invoice.extracted_data.vendor_iban;
    return typeof raw === 'string' && raw.trim().length > 0 ? raw.trim() : null;
  })();
  const displayedIban = paymentConfirmation?.iban_vendor ?? vendorIban ?? extractedInvoiceIban;

  const handleApprove = async () => {
    if (decisionSubmitting) {
      return;
    }

    setDecisionSubmitting(true);
    setActionFeedback(null);
    try {
      await approveInvoice(review.id);
      const updatedInvoice = await updateInvoice(review.id, {
        claude_summary: buildManualDecisionSummary('approved', currentReasons),
        auto_approved: false,
      });
      setInvoice(updatedInvoice);
      dispatchInvoicesUpdatedEvent();
      setActionFeedback(copy.approveFeedback(review.invoiceNumber));
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      setActionFeedback(copy.decisionUpdateError(message));
    } finally {
      setDecisionSubmitting(false);
    }
  };

  const handleRejectAndSend = async () => {
    if (decisionSubmitting) {
      return;
    }

    setDecisionSubmitting(true);
    setActionFeedback(null);
    try {
      const updatedInvoice = await updateInvoice(review.id, {
        status: 'rejected',
        claude_summary: buildManualDecisionSummary('rejected', currentReasons, recipientEmail),
        negotiation_email: negotiationEmail,
        auto_approved: false,
      });
      setInvoice(updatedInvoice);
      dispatchInvoicesUpdatedEvent();
      setActionFeedback(copy.rejectFeedback(review.invoiceNumber, recipientEmail));
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      setActionFeedback(copy.decisionUpdateError(message));
    } finally {
      setDecisionSubmitting(false);
    }
  };

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
              {isProcessedStatus(review.rawStatus) && (
                <span
                  className="px-2 py-1 rounded-md text-[10px] uppercase font-bold tracking-wider flex items-center gap-1"
                  style={review.decisionState === 'rejected'
                    ? {
                        background: 'rgba(255, 0, 85, 0.1)',
                        color: '#FF0055',
                        border: '1px solid rgba(255, 0, 85, 0.25)',
                      }
                    : {
                        background: 'rgba(0, 255, 148, 0.1)',
                        color: '#00FF94',
                        border: '1px solid rgba(0, 255, 148, 0.25)',
                      }}
                >
                  {review.decisionState === 'rejected'
                    ? <XCircle className="w-3 h-3" />
                    : <ShieldCheck className="w-3 h-3" />}
                  {review.decisionState === 'rejected' ? copy.rejectedStatus : copy.approvedStatus}
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
                    <p className="text-sm text-gray-600">{review.vendorAddress}</p>
                    <p className="text-sm text-gray-600">{review.contactEmail}</p>
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
                        <th className="text-right py-3 text-sm text-gray-700 font-bold">{copy.quantity}</th>
                        <th className="text-right py-3 text-sm text-gray-700 font-bold">{copy.unitPrice}</th>
                        <th className="text-right py-3 text-sm text-gray-700 font-bold">{copy.amount}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {review.lineItems.map((lineItem, index) => (
                        <tr key={`${review.id}-${index}`}>
                          <td className="py-3 text-gray-900">{lineItem.description}</td>
                          <td className="text-right text-gray-900">{lineItem.quantity}</td>
                          <td className="text-right text-gray-900">{lineItem.unitPrice}</td>
                          <td className="text-right text-gray-900 font-semibold">{lineItem.amount}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>

                  <div className="border-t border-gray-200 pt-4 space-y-2">
                    <div className="flex justify-between text-sm text-gray-600">
                      <span>{copy.subtotal}</span>
                      <span>{review.subtotal}</span>
                    </div>
                    {review.tax && (
                      <div className="flex justify-between text-sm text-gray-600">
                        <span>{copy.tax}</span>
                        <span>{review.tax}</span>
                      </div>
                    )}
                    <div className="border-t-2 border-gray-300 pt-4 flex justify-between items-center">
                      <span className="text-lg sm:text-xl text-gray-900 font-bold">{copy.totalDue}</span>
                      <span className="text-3xl sm:text-4xl text-gray-900 font-bold">{review.amount}</span>
                    </div>
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
                {review.isReview ? (
                  <>
                    <div className="text-xs text-[#71717A] uppercase tracking-wider font-semibold mb-3">
                      {copy.blockingReasons}
                    </div>
                    <ul className="space-y-2">
                      {currentReasons.map((reason: string, index: number) => (
                        <li key={`${review.id}-${index}`} className="flex items-start gap-2 text-sm text-[#E4E4E7] leading-relaxed">
                          <AlertTriangle className="w-4 h-4 text-[#FFB800] mt-0.5 flex-shrink-0" />
                          <span>{reason}</span>
                        </li>
                      ))}
                    </ul>
                  </>
                ) : (
                  <>
                    <div className="text-xs text-[#71717A] uppercase tracking-wider font-semibold mb-3">
                      {copy.processingStatus}
                    </div>
                    <div className="flex items-start gap-2 text-sm text-[#E4E4E7] leading-relaxed">
                      {review.decisionState === 'rejected' ? (
                        <XCircle className="w-4 h-4 text-[#FF0055] mt-0.5 flex-shrink-0" />
                      ) : (
                        <ShieldCheck className="w-4 h-4 text-[#00FF94] mt-0.5 flex-shrink-0" />
                      )}
                      <span>{review.decisionState === 'rejected' ? copy.processingRejectedDesc : copy.processingApprovedDesc}</span>
                    </div>
                  </>
                )}
              </div>

              {!review.isReview && (
                <div
                  className="rounded-lg p-4 mb-4"
                  style={{
                    background: 'rgba(20, 22, 25, 0.6)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                  }}
                >
                  <div className="text-xs text-[#71717A] uppercase tracking-wider font-semibold mb-3">
                    {copy.reasoningSection}
                  </div>
                  <p className="text-sm text-[#E4E4E7] leading-relaxed">
                    {decisionSummary}
                  </p>
                </div>
              )}

              {!review.isReview && (review.rawStatus === 'approved' || review.rawStatus === 'paid') && (
                <div
                  className="rounded-lg p-4 mb-4"
                  style={{
                    background: 'rgba(0, 255, 148, 0.04)',
                    border: '1px solid rgba(0, 255, 148, 0.15)',
                  }}
                >
                  <div className="flex items-center gap-2 mb-3">
                    <CreditCard className="w-4 h-4 text-[#00FF94]" />
                    <div className="text-xs text-[#00FF94] uppercase tracking-wider font-semibold">
                      {copy.paymentConfirmation}
                    </div>
                  </div>

                  {(paymentRecord || paymentConfirmation || displayedIban) ? (
                    <div className="space-y-2.5">
                      <div className="flex items-start gap-2">
                        <Building2 className="w-3.5 h-3.5 text-[#71717A] mt-0.5 flex-shrink-0" />
                        <div className="min-w-0">
                          <div className="text-[10px] text-[#71717A] uppercase tracking-wider">{copy.vendorIban}</div>
                          <div className="text-sm text-[#E4E4E7] font-mono break-all">
                            {displayedIban || copy.noIban}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-start gap-2">
                        <CreditCard className="w-3.5 h-3.5 text-[#71717A] mt-0.5 flex-shrink-0" />
                        <div className="min-w-0">
                          <div className="text-[10px] text-[#71717A] uppercase tracking-wider">{copy.transferId}</div>
                          <div className="text-sm text-[#E4E4E7] font-mono break-all">
                            {paymentTransferId}
                          </div>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <div className="text-[10px] text-[#71717A] uppercase tracking-wider">{copy.paymentAmount}</div>
                          <div className="text-sm text-[#E4E4E7] font-semibold">
                            {paymentAmountValue}
                          </div>
                        </div>
                        <div>
                          <div className="text-[10px] text-[#71717A] uppercase tracking-wider">{copy.paymentStatus}</div>
                          <div className="flex items-center gap-1">
                            <span
                              className="inline-block w-1.5 h-1.5 rounded-full"
                              style={{ background: paymentStatusColor }}
                            />
                            <span
                              className="text-sm font-medium"
                              style={{ color: paymentStatusColor }}
                            >
                              {paymentStatusLabel}
                            </span>
                          </div>
                        </div>
                      </div>

                      {paymentConfirmedAt && (
                        <div>
                          <div className="text-[10px] text-[#71717A] uppercase tracking-wider">{copy.confirmedAt}</div>
                          <div className="text-sm text-[#E4E4E7]">
                            {new Date(paymentConfirmedAt).toLocaleString()}
                          </div>
                        </div>
                      )}

                      {!paymentRecord && (
                        <p className="text-xs text-[#71717A]">{copy.paymentNotFound}</p>
                      )}
                    </div>
                  ) : (
                    <p className="text-sm text-[#71717A]">{copy.paymentNotFound}</p>
                  )}
                </div>
              )}

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
                      disabled={decisionSubmitting}
                      className="w-full py-3 rounded-lg uppercase tracking-wider text-sm transition-all duration-200 flex items-center justify-center gap-2"
                      style={{
                        background: '#00FF94',
                        color: '#060709',
                        fontWeight: 600,
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                        opacity: decisionSubmitting ? 0.75 : 1,
                      }}
                    >
                      <CheckCircle2 className="w-5 h-5" />
                      <span>{decisionSubmitting ? copy.savingDecision : copy.approve}</span>
                    </button>

                    <button
                      type="button"
                      onClick={handleRejectAndSend}
                      disabled={decisionSubmitting}
                      className="w-full py-3 rounded-lg uppercase tracking-wider text-sm transition-all duration-200 flex items-center justify-center gap-2"
                      style={{
                        background: 'transparent',
                        color: '#FF0055',
                        border: '1px solid #FF0055',
                        fontWeight: 600,
                        opacity: decisionSubmitting ? 0.75 : 1,
                      }}
                    >
                      <XCircle className="w-5 h-5" />
                      <Send className="w-4 h-4" />
                      <span>{decisionSubmitting ? copy.savingDecision : copy.reject}</span>
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
                  {review.decisionState === 'rejected' ? (
                    <XCircle className="w-12 h-12 text-[#FF0055] mx-auto mb-3 opacity-50" />
                  ) : (
                    <ShieldCheck className="w-12 h-12 text-[#00FF94] mx-auto mb-3 opacity-50" />
                  )}
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
