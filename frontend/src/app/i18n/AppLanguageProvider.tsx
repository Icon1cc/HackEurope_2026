import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { loadAppSettings, type AppLanguage } from '../data/appSettings';

const AppLanguageContext = createContext<AppLanguage>('en');

function resolveCurrentLanguage(): AppLanguage {
  if (typeof window === 'undefined') {
    return 'en';
  }

  return loadAppSettings().language;
}

export function AppLanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<AppLanguage>(() => resolveCurrentLanguage());

  useEffect(() => {
    const syncLanguage = () => {
      setLanguage(resolveCurrentLanguage());
    };

    window.addEventListener('storage', syncLanguage);
    window.addEventListener('invoiceguard:settings-updated', syncLanguage);

    return () => {
      window.removeEventListener('storage', syncLanguage);
      window.removeEventListener('invoiceguard:settings-updated', syncLanguage);
    };
  }, []);

  useEffect(() => {
    if (typeof document !== 'undefined') {
      document.documentElement.lang = language;
    }
  }, [language]);

  const contextValue = useMemo(() => language, [language]);

  return <AppLanguageContext.Provider value={contextValue}>{children}</AppLanguageContext.Provider>;
}

export function useAppLanguage(): AppLanguage {
  return useContext(AppLanguageContext);
}
