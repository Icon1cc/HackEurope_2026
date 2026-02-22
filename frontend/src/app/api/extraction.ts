export interface ExtractionLineItem {
  description: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  unit: string | null;
}

export interface InvoiceExtractionPayload {
  invoice_number: string | null;
  due_date: string | null;
  vendor_name: string | null;
  vendor_iban: string | null;
  vendor_address: string | null;
  client_name: string | null;
  client_address: string | null;
  line_items: ExtractionLineItem[];
  subtotal: number | null;
  tax: number | null;
  total: number | null;
  currency: string | null;
}

export interface ExtractionAnomalyFlag {
  anomaly_type: string;
  severity: 'low' | 'medium' | 'high';
  affected_field: string;
  description: string;
  confidence: number;
}

export interface ExtractionAnalysis {
  anomaly_flags: ExtractionAnomalyFlag[];
  summary: string;
}

export type ExtractionDecisionAction = 'approved' | 'human_review' | 'escalate_negotiation';

export interface ExtractionDecision {
  action: ExtractionDecisionAction;
  reason: string;
}

export interface ExtractionSecondPass {
  analysis: ExtractionAnalysis;
  decision: ExtractionDecision;
  confidence_score: number;
}

export interface ExtractionInvoice {
  id: string;
  vendor_id: string | null;
  invoice_number: string | null;
  status: string;
  confidence_score: number | null;
}

export interface ExtractionVendor {
  id: string;
  name: string;
  registered_iban: string | null;
  vendor_address: string | null;
}

export interface ExtractionApiResponse {
  vendor: ExtractionVendor;
  invoice: ExtractionInvoice;
  extraction: InvoiceExtractionPayload;
  vendor_context: unknown;
  second_pass: ExtractionSecondPass | null;
  second_pass_error: string | null;
}

const DEFAULT_API_BASE_URL = 'http://127.0.0.1:8000';
const DEFAULT_API_VERSION = 'v1';

const env = (import.meta as ImportMeta & { env?: Record<string, string | undefined> }).env ?? {};

function normalizeBaseUrl(rawUrl: string | undefined): string {
  const candidate = rawUrl?.trim();
  if (!candidate) {
    return DEFAULT_API_BASE_URL;
  }
  return candidate.replace(/\/+$/, '');
}

function normalizeApiVersion(rawVersion: string | undefined): string {
  const candidate = rawVersion?.trim();
  const version = candidate && candidate.length > 0 ? candidate : DEFAULT_API_VERSION;
  return version.replace(/^\/+|\/+$/g, '');
}

function getExtractionEndpoint(): string {
  const baseUrl = normalizeBaseUrl(env.VITE_API_BASE_URL);
  const apiVersion = normalizeApiVersion(env.VITE_API_VERSION);
  return `${baseUrl}/api/${apiVersion}/extraction/`;
}

function getErrorMessageFromDetail(detail: unknown): string | null {
  if (typeof detail === 'string' && detail.trim().length > 0) {
    return detail.trim();
  }
  if (!Array.isArray(detail)) {
    return null;
  }

  const messages = detail
    .map((entry) => {
      if (typeof entry !== 'object' || entry === null) {
        return null;
      }
      const message = (entry as { msg?: unknown }).msg;
      return typeof message === 'string' && message.trim().length > 0 ? message.trim() : null;
    })
    .filter((message): message is string => message !== null);

  return messages.length > 0 ? messages.join('; ') : null;
}

async function getErrorMessage(response: Response): Promise<string> {
  const fallback = `Extraction request failed (${response.status})`;
  try {
    const payload = (await response.json()) as { detail?: unknown };
    return getErrorMessageFromDetail(payload.detail) ?? fallback;
  } catch {
    return fallback;
  }
}

function getStoredAccessToken(): string | null {
  try {
    const raw = localStorage.getItem('invoiceguard.auth.tokens');
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return parsed?.access_token ?? null;
  } catch {
    return null;
  }
}

export async function uploadInvoiceForExtraction(file: File): Promise<ExtractionApiResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const token = getStoredAccessToken();
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  let response: Response;
  try {
    response = await fetch(getExtractionEndpoint(), {
      method: 'POST',
      headers,
      body: formData,
    });
  } catch {
    throw new Error('Network error while contacting extraction API');
  }

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  return (await response.json()) as ExtractionApiResponse;
}
