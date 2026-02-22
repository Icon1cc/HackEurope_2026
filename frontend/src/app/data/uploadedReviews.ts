import type { ExtractionApiResponse, ExtractionDecisionAction } from '../api/extraction';
import type { AppLanguage } from './appSettings';
import type { PendingReview, PendingReviewStatus } from './pendingReviews';

export const UPLOADED_REVIEWS_STORAGE_KEY = 'invoiceguard.uploaded-reviews';
export const UPLOADED_REVIEWS_UPDATED_EVENT = 'invoiceguard:uploaded-reviews-updated';

const LANGUAGE_KEYS: AppLanguage[] = ['fr', 'en', 'de'];

export type UploadOutcome =
  | {
      kind: 'requires_review';
      review: PendingReview;
    }
  | {
      kind: 'approved';
      invoiceNumber: string;
    };

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function isLanguageReasons(value: unknown): value is Record<AppLanguage, string[]> {
  if (!isRecord(value)) {
    return false;
  }
  return LANGUAGE_KEYS.every((languageKey) => {
    const languageValue = value[languageKey];
    return Array.isArray(languageValue) && languageValue.every((entry) => typeof entry === 'string');
  });
}

function isLanguageDrafts(value: unknown): value is Record<AppLanguage, string> {
  if (!isRecord(value)) {
    return false;
  }
  return LANGUAGE_KEYS.every((languageKey) => typeof value[languageKey] === 'string');
}

function isPendingReview(value: unknown): value is PendingReview {
  if (!isRecord(value)) {
    return false;
  }

  return (
    typeof value.id === 'string'
    && typeof value.invoiceNumber === 'string'
    && typeof value.vendor === 'string'
    && typeof value.amount === 'string'
    && typeof value.date === 'string'
    && (value.status === 'pending' || value.status === 'escalated')
    && typeof value.contactEmail === 'string'
    && isLanguageReasons(value.reasons)
    && isLanguageDrafts(value.emailDraft)
  );
}

function deriveInvoiceNumber(response: ExtractionApiResponse): string {
  const candidate = response.invoice.invoice_number ?? response.extraction.invoice_number;
  if (candidate && candidate.trim().length > 0) {
    return candidate.trim();
  }
  return response.invoice.id.slice(0, 8).toUpperCase();
}

function resolveReviewStatus(
  action: ExtractionDecisionAction | undefined,
  invoiceStatus: string | null | undefined,
): PendingReviewStatus | null {
  if (action === 'approved' || invoiceStatus === 'approved') {
    return null;
  }
  if (action === 'escalate_negotiation') {
    return 'escalated';
  }
  return 'pending';
}

function formatAmount(total: number | null, currency: string | null): string {
  if (typeof total !== 'number' || Number.isNaN(total)) {
    return 'N/A';
  }

  const normalizedCurrency = (currency ?? 'USD').toUpperCase();
  try {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: normalizedCurrency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(total);
  } catch {
    return `${total.toFixed(2)} ${normalizedCurrency}`;
  }
}

function buildReasons(response: ExtractionApiResponse): string[] {
  const anomalyReasons = response.second_pass?.analysis.anomaly_flags
    .map((flag) => flag.description.trim())
    .filter((description) => description.length > 0);

  if (anomalyReasons && anomalyReasons.length > 0) {
    return anomalyReasons.slice(0, 3);
  }

  const decisionReason = response.second_pass?.decision.reason?.trim();
  if (decisionReason && decisionReason.length > 0) {
    return [decisionReason];
  }

  if (response.second_pass_error && response.second_pass_error.trim().length > 0) {
    return [response.second_pass_error.trim()];
  }

  return ['Automated extraction completed. Awaiting manual review.'];
}

function buildEmailDraft(invoiceNumber: string, vendorName: string, reasons: string[]): Record<AppLanguage, string> {
  const bulletPoints = reasons.map((reason) => `- ${reason}`).join('\n');

  return {
    en: `Hello,\n\nWe are reviewing invoice ${invoiceNumber} from ${vendorName}. Before approval, we need clarification on the following points:\n${bulletPoints}\n\nPlease confirm and share supporting details.\n\nBest regards,\nAccounts Payable Team`,
    fr: `Bonjour,\n\nNous examinons la facture ${invoiceNumber} de ${vendorName}. Avant validation, nous avons besoin d'une clarification sur les points suivants :\n${bulletPoints}\n\nMerci de confirmer et de partager les éléments justificatifs.\n\nCordialement,\nÉquipe Accounts Payable`,
    de: `Hallo,\n\nwir prüfen die Rechnung ${invoiceNumber} von ${vendorName}. Vor der Freigabe benötigen wir eine Klärung zu folgenden Punkten:\n${bulletPoints}\n\nBitte bestätigen Sie die Punkte und senden Sie die entsprechenden Nachweise.\n\nMit freundlichen Grüßen,\nTeam Kreditorenbuchhaltung`,
  };
}

function buildFallbackEmail(vendorName: string): string {
  const normalizedVendor = vendorName
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '')
    .slice(0, 40);

  if (normalizedVendor.length === 0) {
    return 'billing@vendor.com';
  }

  return `billing@${normalizedVendor}.com`;
}

function toLocalizedReasons(reasons: string[]): Record<AppLanguage, string[]> {
  return {
    fr: reasons,
    en: reasons,
    de: reasons,
  };
}

export function buildUploadOutcome(response: ExtractionApiResponse): UploadOutcome {
  const invoiceNumber = deriveInvoiceNumber(response);
  const reviewStatus = resolveReviewStatus(response.second_pass?.decision.action, response.invoice.status);

  if (reviewStatus === null) {
    return {
      kind: 'approved',
      invoiceNumber,
    };
  }

  const vendorName = (response.vendor.name || response.extraction.vendor_name || 'Unknown Vendor').trim() || 'Unknown Vendor';
  const reasons = buildReasons(response);
  const review: PendingReview = {
    id: response.invoice.id,
    invoiceNumber,
    vendor: vendorName,
    amount: formatAmount(response.extraction.total, response.extraction.currency),
    date: new Date().toISOString().slice(0, 10),
    status: reviewStatus,
    contactEmail: buildFallbackEmail(vendorName),
    reasons: toLocalizedReasons(reasons),
    emailDraft: buildEmailDraft(invoiceNumber, vendorName, reasons),
  };

  return {
    kind: 'requires_review',
    review,
  };
}

export function loadUploadedReviews(): PendingReview[] {
  if (typeof window === 'undefined') {
    return [];
  }

  try {
    const rawValue = window.localStorage.getItem(UPLOADED_REVIEWS_STORAGE_KEY);
    if (!rawValue) {
      return [];
    }
    const parsed = JSON.parse(rawValue);
    if (!Array.isArray(parsed)) {
      return [];
    }
    return parsed.filter(isPendingReview);
  } catch {
    return [];
  }
}

export function saveUploadedReview(review: PendingReview): PendingReview[] {
  const existingReviews = loadUploadedReviews();
  const nextReviews = [review, ...existingReviews.filter((existing) => existing.id !== review.id)];

  if (typeof window !== 'undefined') {
    window.localStorage.setItem(UPLOADED_REVIEWS_STORAGE_KEY, JSON.stringify(nextReviews));
    window.dispatchEvent(new Event(UPLOADED_REVIEWS_UPDATED_EVENT));
  }

  return nextReviews;
}

export function findUploadedReview(reviewId: string): PendingReview | null {
  const uploadedReview = loadUploadedReviews().find((review) => review.id === reviewId);
  return uploadedReview ?? null;
}
