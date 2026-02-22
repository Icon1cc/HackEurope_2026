import { useEffect, useMemo, useRef, useState } from 'react';
import { Sidebar } from '../components/Sidebar';
import { Footer } from '../components/Footer';
import { VercelBackground } from '../components/VercelBackground';
import {
  Settings as SettingsIcon,
  User,
  CheckCircle2,
  Building2,
  Globe,
} from 'lucide-react';
import {
  loadAppSettings,
  saveAppSettings,
  type AppLanguage,
  type AppSettings,
} from '../data/appSettings';
import { useAppLanguage } from '../i18n/AppLanguageProvider';

export default function Settings() {
  const language = useAppLanguage();
  const [savedSettings, setSavedSettings] = useState<AppSettings>(() => loadAppSettings());
  const [settings, setSettings] = useState<AppSettings>(() => loadAppSettings());
  const [feedback, setFeedback] = useState<string>('');

  const copy = {
    fr: {
      title: 'Paramètres',
      subtitle: 'Configure ton profil et la langue de préférence de l\'application.',
      profileSection: 'Profil utilisateur',
      fullName: 'Nom complet',
      fullNamePlaceholder: 'Nom utilisateur',
      email: 'Email',
      emailPlaceholder: 'email@entreprise.com',
      companyName: "Nom de l'entreprise",
      companyNamePlaceholder: 'Nom de société',
      language: 'Langue de préférence',
      languageFr: 'Français',
      languageEn: 'English',
      languageDe: 'Deutsch',
      localStorageNote: 'Les préférences sont stockées localement dans le navigateur pour cette démo.',
      autoSaved: 'Paramètres sauvegardés automatiquement.',
    },
    en: {
      title: 'Settings',
      subtitle: 'Configure your profile and preferred application language.',
      profileSection: 'User profile',
      fullName: 'Full name',
      fullNamePlaceholder: 'User name',
      email: 'Email',
      emailPlaceholder: 'email@company.com',
      companyName: 'Company name',
      companyNamePlaceholder: 'Company name',
      language: 'Preferred language',
      languageFr: 'Français',
      languageEn: 'English',
      languageDe: 'Deutsch',
      localStorageNote: 'Preferences are stored locally in this browser for this demo.',
      autoSaved: 'Settings saved automatically.',
    },
    de: {
      title: 'Einstellungen',
      subtitle: 'Konfigurieren Sie Ihr Profil und die bevorzugte Anwendungssprache.',
      profileSection: 'Benutzerprofil',
      fullName: 'Vollständiger Name',
      fullNamePlaceholder: 'Benutzername',
      email: 'E-Mail',
      emailPlaceholder: 'email@unternehmen.de',
      companyName: 'Unternehmensname',
      companyNamePlaceholder: 'Unternehmensname',
      language: 'Bevorzugte Sprache',
      languageFr: 'Français',
      languageEn: 'English',
      languageDe: 'Deutsch',
      localStorageNote: 'Präferenzen werden für diese Demo lokal im Browser gespeichert.',
      autoSaved: 'Einstellungen automatisch gespeichert.',
    },
  }[language];

  const isDirty = useMemo(
    () => JSON.stringify(settings) !== JSON.stringify(savedSettings),
    [settings, savedSettings],
  );
  const hasMountedRef = useRef(false);

  const updateSetting = <K extends keyof AppSettings>(key: K, value: AppSettings[K]) => {
    setSettings((current) => ({ ...current, [key]: value }));
    setFeedback('');
  };

  useEffect(() => {
    if (!hasMountedRef.current) {
      hasMountedRef.current = true;
      return;
    }

    if (!isDirty) {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      const nextSaved = saveAppSettings(settings);
      setSettings(nextSaved);
      setSavedSettings(nextSaved);
      setFeedback(copy.autoSaved);
      window.dispatchEvent(new Event('invoiceguard:settings-updated'));
    }, 250);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [copy.autoSaved, isDirty, settings]);

  return (
    <div className="flex min-h-screen relative overflow-hidden">
      <VercelBackground />

      <Sidebar />

      <main className="flex-1 lg:ml-64 p-4 pt-20 lg:pt-8 sm:p-6 lg:p-8 relative z-10 flex flex-col items-center">
        <div className="w-full max-w-2xl">
          <div className="mb-8">
            <div>
              <h1
                className="text-3xl sm:text-4xl mb-2"
                style={{
                  fontFamily: 'Geist Sans, Inter, sans-serif',
                  fontWeight: 700,
                  letterSpacing: '-0.02em',
                  color: '#FAFAFA',
                }}
              >
                {copy.title}
              </h1>
              <p className="text-[#71717A] text-sm">{copy.subtitle}</p>
            </div>
          </div>

          <section
            className="rounded-xl p-5 sm:p-8 backdrop-blur-[20px] w-full"
            style={{
              background: 'rgba(20, 22, 25, 0.6)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              boxShadow: 'inset 0 1px 0 0 rgba(255, 255, 255, 0.1)',
            }}
          >
            <div className="flex items-center gap-2 mb-6">
              <User className="w-5 h-5 text-[#00F2FF]" />
              <h2
                className="text-lg"
                style={{ fontFamily: 'Geist Sans, Inter, sans-serif', fontWeight: 700, letterSpacing: '-0.02em' }}
              >
                {copy.profileSection}
              </h2>
            </div>

            <div className="space-y-6">
              <div>
                <label htmlFor="profile-name" className="block text-xs text-[#71717A] uppercase tracking-wider font-semibold mb-2">
                  {copy.fullName}
                </label>
                <input
                  id="profile-name"
                  type="text"
                  value={settings.profileName}
                  onChange={(event) => updateSetting('profileName', event.target.value)}
                  className="w-full px-4 py-3 rounded-lg text-sm text-white placeholder-[#52525B] outline-none transition-all"
                  style={{
                    background: 'rgba(6, 7, 9, 0.8)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                  }}
                  onFocus={(e) => { e.target.style.border = '1px solid #00F2FF'; }}
                  onBlur={(e) => { e.target.style.border = '1px solid rgba(255, 255, 255, 0.1)'; }}
                  placeholder={copy.fullNamePlaceholder}
                />
              </div>

              <div>
                <label htmlFor="profile-email" className="block text-xs text-[#71717A] uppercase tracking-wider font-semibold mb-2">
                  {copy.email}
                </label>
                <input
                  id="profile-email"
                  type="email"
                  value={settings.profileEmail}
                  onChange={(event) => updateSetting('profileEmail', event.target.value)}
                  className="w-full px-4 py-3 rounded-lg text-sm text-white placeholder-[#52525B] outline-none transition-all"
                  style={{
                    background: 'rgba(6, 7, 9, 0.8)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                  }}
                  onFocus={(e) => { e.target.style.border = '1px solid #00F2FF'; }}
                  onBlur={(e) => { e.target.style.border = '1px solid rgba(255, 255, 255, 0.1)'; }}
                  placeholder={copy.emailPlaceholder}
                />
              </div>

              <div>
                <label htmlFor="company-name" className="block text-xs text-[#71717A] uppercase tracking-wider font-semibold mb-2">
                  <span className="inline-flex items-center gap-1.5">
                    <Building2 className="w-3.5 h-3.5 text-[#00F2FF]" />
                    {copy.companyName}
                  </span>
                </label>
                <input
                  id="company-name"
                  type="text"
                  value={settings.companyName}
                  onChange={(event) => updateSetting('companyName', event.target.value)}
                  className="w-full px-4 py-3 rounded-lg text-sm text-white placeholder-[#52525B] outline-none transition-all"
                  style={{
                    background: 'rgba(6, 7, 9, 0.8)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                  }}
                  onFocus={(e) => { e.target.style.border = '1px solid #00F2FF'; }}
                  onBlur={(e) => { e.target.style.border = '1px solid rgba(255, 255, 255, 0.1)'; }}
                  placeholder={copy.companyNamePlaceholder}
                />
              </div>

              <div>
                <label htmlFor="language" className="block text-xs text-[#71717A] uppercase tracking-wider font-semibold mb-2">
                  <span className="inline-flex items-center gap-1.5">
                    <Globe className="w-3.5 h-3.5 text-[#00F2FF]" />
                    {copy.language}
                  </span>
                </label>
                <select
                  id="language"
                  value={settings.language}
                  onChange={(event) => updateSetting('language', event.target.value as AppLanguage)}
                  className="w-full px-4 py-3 rounded-lg text-sm text-white outline-none cursor-pointer transition-all appearance-none"
                  style={{
                    background: 'rgba(6, 7, 9, 0.8)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                  }}
                  onFocus={(e) => { e.target.style.border = '1px solid #00F2FF'; }}
                  onBlur={(e) => { e.target.style.border = '1px solid rgba(255, 255, 255, 0.1)'; }}
                >
                  <option value="fr">{copy.languageFr}</option>
                  <option value="en">{copy.languageEn}</option>
                  <option value="de">{copy.languageDe}</option>
                </select>
              </div>
            </div>
          </section>

          {feedback && (
            <div
              className="mt-6 rounded-lg p-3 text-sm flex items-center gap-2"
              style={{
                background: 'rgba(0, 255, 148, 0.08)',
                border: '1px solid rgba(0, 255, 148, 0.25)',
                color: '#D4FDEB',
              }}
            >
              <CheckCircle2 className="w-4 h-4 text-[#00FF94]" />
              <span>{feedback}</span>
            </div>
          )}

          <div className="mt-8 text-xs text-[#71717A] flex items-center justify-center gap-2">
            <SettingsIcon className="w-4 h-4" />
            <span>{copy.localStorageNote}</span>
          </div>
        </div>

        <div className="w-full mt-auto">
          <Footer />
        </div>
      </main>
    </div>
  );
}
