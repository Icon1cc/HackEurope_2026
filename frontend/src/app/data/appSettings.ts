export const APP_SETTINGS_STORAGE_KEY = 'invoiceguard.app.settings';

export type AppLanguage = 'fr' | 'en' | 'de';

export interface AppSettings {
  profileName: string;
  profileEmail: string;
  companyName: string;
  language: AppLanguage;
}

export const DEFAULT_APP_SETTINGS: AppSettings = {
  profileName: 'Robert Quentin',
  profileEmail: 'robert@invoiceguard.ai',
  companyName: 'InvoiceGuard Labs',
  language: 'en',
};

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function sanitizeSettings(raw: unknown): AppSettings {
  if (!isObject(raw)) {
    return DEFAULT_APP_SETTINGS;
  }

  return {
    profileName:
      typeof raw.profileName === 'string' && raw.profileName.trim().length > 0
        ? raw.profileName.trim()
        : DEFAULT_APP_SETTINGS.profileName,
    profileEmail:
      typeof raw.profileEmail === 'string' && raw.profileEmail.trim().length > 0
        ? raw.profileEmail.trim()
        : DEFAULT_APP_SETTINGS.profileEmail,
    companyName:
      typeof raw.companyName === 'string' && raw.companyName.trim().length > 0
        ? raw.companyName.trim()
        : DEFAULT_APP_SETTINGS.companyName,
    language: (raw.language === 'en' || raw.language === 'de') ? raw.language : DEFAULT_APP_SETTINGS.language,
  };
}

export function loadAppSettings(): AppSettings {
  if (typeof window === 'undefined') {
    return DEFAULT_APP_SETTINGS;
  }

  try {
    const raw = window.localStorage.getItem(APP_SETTINGS_STORAGE_KEY);
    if (!raw) {
      return DEFAULT_APP_SETTINGS;
    }

    return sanitizeSettings(JSON.parse(raw));
  } catch {
    return DEFAULT_APP_SETTINGS;
  }
}

export function saveAppSettings(settings: AppSettings): AppSettings {
  const sanitized = sanitizeSettings(settings);

  if (typeof window !== 'undefined') {
    window.localStorage.setItem(APP_SETTINGS_STORAGE_KEY, JSON.stringify(sanitized));
  }

  return sanitized;
}
