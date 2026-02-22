import type { AppLanguage } from './appSettings';
import type { InvoiceApiResponse } from '../api/backend';
import { formatCurrencyValue } from '../api/backend';

export type PendingReviewStatus = 'pending' | 'escalated';

export interface PendingReview {
  id: string;
  invoiceNumber: string;
  vendor: string;
  amount: string;
  date: string;
  status: PendingReviewStatus;
  contactEmail: string;
  reasons: Record<AppLanguage, string[]>;
  emailDraft: Record<AppLanguage, string>;
}

const DEFAULT_REVIEW_REASON = 'Automated review required for this invoice.';

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

export function isProcessedStatus(status: string | null | undefined): boolean {
  return status === 'approved' || status === 'paid';
}

export function toPendingReviewStatus(status: string | null | undefined): PendingReviewStatus {
  if (status === 'rejected' || status === 'overcharge') {
    return 'escalated';
  }
  return 'pending';
}

export function buildFallbackEmail(vendorName: string): string {
  const normalizedVendor = vendorName
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '')
    .slice(0, 40);

  if (normalizedVendor.length === 0) {
    return 'billing@vendor.com';
  }

  return `billing@${normalizedVendor}.com`;
}

export function extractReviewReasons(invoice: InvoiceApiResponse): string[] {
  if (Array.isArray(invoice.anomalies)) {
    const reasons = invoice.anomalies
      .map((entry) => {
        if (!isRecord(entry)) {
          return null;
        }
        const description = entry.description;
        return typeof description === 'string' && description.trim().length > 0
          ? description.trim()
          : null;
      })
      .filter((reason): reason is string => reason !== null);

    if (reasons.length > 0) {
      return reasons.slice(0, 3);
    }
  }

  const summary = invoice.claude_summary?.trim();
  if (summary && summary.length > 0) {
    return [summary];
  }

  return [DEFAULT_REVIEW_REASON];
}

function buildEmailDraft(
  invoiceNumber: string,
  vendorName: string,
  reasons: string[],
): Record<AppLanguage, string> {
  const bulletPoints = reasons.map((reason) => `- ${reason}`).join('\n');

  return {
    en: `Hello,\n\nWe are reviewing invoice ${invoiceNumber} from ${vendorName}. Before approval, we need clarification on the following points:\n${bulletPoints}\n\nPlease confirm and share supporting details.\n\nBest regards,\nAccounts Payable Team`,
    fr: `Bonjour,\n\nNous examinons la facture ${invoiceNumber} de ${vendorName}. Avant validation, nous avons besoin d'une clarification sur les points suivants :\n${bulletPoints}\n\nMerci de confirmer et de partager les éléments justificatifs.\n\nCordialement,\nÉquipe Accounts Payable`,
    de: `Hallo,\n\nwir prüfen die Rechnung ${invoiceNumber} von ${vendorName}. Vor der Freigabe benötigen wir eine Klärung zu folgenden Punkten:\n${bulletPoints}\n\nBitte bestätigen Sie die Punkte und senden Sie die entsprechenden Nachweise.\n\nMit freundlichen Grüßen,\nTeam Kreditorenbuchhaltung`,
  };
}

function withLocalizedReasons(reasons: string[]): Record<AppLanguage, string[]> {
  return {
    fr: reasons,
    en: reasons,
    de: reasons,
  };
}

export function invoiceNumberOrFallback(invoice: InvoiceApiResponse): string {
  const invoiceNumber = invoice.invoice_number?.trim();
  if (invoiceNumber && invoiceNumber.length > 0) {
    return invoiceNumber;
  }
  return invoice.id.slice(0, 8).toUpperCase();
}

export function toPendingReview(invoice: InvoiceApiResponse): PendingReview {
  const invoiceNumber = invoiceNumberOrFallback(invoice);
  const vendorName = invoice.vendor_name?.trim() || 'Unknown Vendor';
  const reasons = extractReviewReasons(invoice);

  return {
    id: invoice.id,
    invoiceNumber,
    vendor: vendorName,
    amount: formatCurrencyValue(invoice.total, invoice.currency),
    date: invoice.created_at?.slice(0, 10) ?? '',
    status: toPendingReviewStatus(invoice.status),
    contactEmail: buildFallbackEmail(vendorName),
    reasons: withLocalizedReasons(reasons),
    emailDraft: buildEmailDraft(invoiceNumber, vendorName, reasons),
  };
}
