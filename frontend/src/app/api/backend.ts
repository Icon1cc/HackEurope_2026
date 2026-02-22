export interface VendorApiResponse {
  id: string;
  name: string;
  category: string | null;
  email: string | null;
  registered_iban: string | null;
  known_iban_changes: Array<Record<string, unknown>> | null;
  avg_invoice_amount: string | number | null;
  invoice_count: number;
  trust_score: string | number;
  auto_approve_threshold: number;
  vendor_address: string | null;
  created_at: string;
}

export interface InvoiceItemApiResponse {
  id: string;
  invoice_id: string;
  description: string;
  quantity: string | number | null;
  unit_price: string | number | null;
  total_price: string | number | null;
  unit: string | null;
  created_at: string;
}

export interface InvoiceApiResponse {
  id: string;
  vendor_id: string | null;
  client_id: string | null;
  invoice_number: string | null;
  due_date: string | null;
  vendor_name: string | null;
  vendor_address: string | null;
  client_name: string | null;
  client_address: string | null;
  subtotal: string | number | null;
  tax: string | number | null;
  total: string | number | null;
  currency: string | null;
  raw_file_url: string | null;
  extracted_data: Record<string, unknown> | null;
  anomalies: Array<Record<string, unknown>> | null;
  market_benchmarks: Record<string, unknown> | null;
  confidence_score: number | null;
  status: string;
  claude_summary: string | null;
  negotiation_email: string | null;
  auto_approved: boolean;
  items: InvoiceItemApiResponse[];
  created_at: string;
  updated_at: string;
}

export interface PaymentApiResponse {
  id: string;
  invoice_id: string;
  stripe_payout_id: string | null;
  amount: string | number;
  currency: string;
  status: string;
  initiated_at: string;
  confirmed_at: string | null;
}

export interface StripeConfirmationApiResponse {
  transfer_id: string | null;
  payment_id: string;
  amount: string | number;
  currency: string;
  status: string;
  initiated_at: string;
  confirmed_at: string | null;
}

export interface PaymentConfirmationApiResponse {
  iban_vendor: string | null;
  stripe_confirmation: StripeConfirmationApiResponse;
}

export interface InvoiceUpdateApiRequest {
  extracted_data?: Record<string, unknown> | null;
  anomalies?: Array<Record<string, unknown>> | null;
  market_benchmarks?: Record<string, unknown> | null;
  confidence_score?: number | null;
  status?: string | null;
  claude_summary?: string | null;
  negotiation_email?: string | null;
  auto_approved?: boolean | null;
}

const DEFAULT_API_BASE_URL = 'http://127.0.0.1:8000';
const DEFAULT_API_VERSION = 'v1';
export const INVOICES_UPDATED_EVENT = 'invoiceguard:invoices-updated';
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

function buildApiUrl(path: string, query: URLSearchParams | null = null): string {
  const baseUrl = normalizeBaseUrl(env.VITE_API_BASE_URL);
  const apiVersion = normalizeApiVersion(env.VITE_API_VERSION);
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  const url = new URL(`${baseUrl}/api/${apiVersion}${normalizedPath}`);
  if (query) {
    url.search = query.toString();
  }
  return url.toString();
}

function getStoredAccessToken(): string | null {
  try {
    const raw = localStorage.getItem('invoiceguard.auth.tokens');
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return parsed.access_token ?? null;
  } catch {
    return null;
  }
}

function authHeaders(): Record<string, string> {
  const token = getStoredAccessToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
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

async function getErrorMessage(response: Response, fallback: string): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    return getErrorMessageFromDetail(payload.detail) ?? fallback;
  } catch {
    return fallback;
  }
}

async function requestJson<T>(path: string, query: URLSearchParams | null = null): Promise<T> {
  const endpoint = buildApiUrl(path, query);

  let response: Response;
  try {
    response = await fetch(endpoint, { method: 'GET', headers: authHeaders() });
  } catch {
    throw new Error(`Network error while requesting ${path}`);
  }

  if (!response.ok) {
    throw new Error(await getErrorMessage(response, `Request failed (${response.status})`));
  }

  return (await response.json()) as T;
}

async function requestJsonWithBody<TResponse>(
  path: string,
  method: 'PATCH',
  body: unknown,
): Promise<TResponse> {
  const endpoint = buildApiUrl(path);

  let response: Response;
  try {
    response = await fetch(endpoint, {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...authHeaders(),
      },
      body: JSON.stringify(body),
    });
  } catch {
    throw new Error(`Network error while requesting ${path}`);
  }

  if (!response.ok) {
    throw new Error(await getErrorMessage(response, `Request failed (${response.status})`));
  }

  return (await response.json()) as TResponse;
}

export function dispatchInvoicesUpdatedEvent(): void {
  window.dispatchEvent(new Event(INVOICES_UPDATED_EVENT));
}

export function decimalToNumber(value: string | number | null | undefined): number | null {
  if (value === null || value === undefined) {
    return null;
  }
  if (typeof value === 'number') {
    return Number.isFinite(value) ? value : null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function normalizeCurrency(rawCurrency: string | null | undefined): string {
  const currency = (rawCurrency ?? 'USD').trim().toUpperCase();
  if (currency === '$') return 'USD';
  if (currency === '€') return 'EUR';
  if (currency === '£') return 'GBP';
  if (currency.length === 3) return currency;
  return 'USD';
}

export function formatCurrencyValue(
  amount: string | number | null | undefined,
  currency: string | null | undefined,
): string {
  const numeric = decimalToNumber(amount);
  if (numeric === null) {
    return 'N/A';
  }
  const normalizedCurrency = normalizeCurrency(currency);
  try {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: normalizedCurrency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(numeric);
  } catch {
    return `${numeric.toFixed(2)} ${normalizedCurrency}`;
  }
}

export function trustScoreToPercent(rawTrustScore: string | number): number {
  const numericScore = decimalToNumber(rawTrustScore);
  if (numericScore === null) {
    return 0;
  }
  const normalized = numericScore <= 1 ? numericScore * 100 : numericScore;
  return Math.max(0, Math.min(100, Math.round(normalized)));
}

export async function fetchVendors(limit = 500): Promise<VendorApiResponse[]> {
  const query = new URLSearchParams();
  query.set('skip', '0');
  query.set('limit', String(limit));
  return requestJson<VendorApiResponse[]>('/vendors/', query);
}

export async function fetchVendorById(vendorId: string): Promise<VendorApiResponse> {
  return requestJson<VendorApiResponse>(`/vendors/${vendorId}`);
}

export async function fetchInvoices(limit = 1000): Promise<InvoiceApiResponse[]> {
  const query = new URLSearchParams();
  query.set('skip', '0');
  query.set('limit', String(limit));
  return requestJson<InvoiceApiResponse[]>('/invoices/', query);
}

export async function fetchInvoiceById(invoiceId: string): Promise<InvoiceApiResponse> {
  return requestJson<InvoiceApiResponse>(`/invoices/${invoiceId}`);
}

export async function updateInvoice(
  invoiceId: string,
  payload: InvoiceUpdateApiRequest,
): Promise<InvoiceApiResponse> {
  return requestJsonWithBody<InvoiceApiResponse>(`/invoices/${invoiceId}`, 'PATCH', payload);
}

export async function fetchPaymentsByInvoice(invoiceId: string): Promise<PaymentApiResponse[]> {
  return requestJson<PaymentApiResponse[]>(`/payments/invoice/${invoiceId}`);
}

export async function fetchPaymentConfirmation(paymentId: string): Promise<PaymentConfirmationApiResponse> {
  return requestJson<PaymentConfirmationApiResponse>(`/payments/${paymentId}/confirmation`);
}
