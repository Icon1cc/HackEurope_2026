import { useState } from 'react';
import { useNavigate } from 'react-router';
import { Mail, Lock } from 'lucide-react';
import { VercelBackground } from '../components/VercelBackground';
import { Footer } from '../components/Footer';
import { useAppLanguage } from '../i18n/AppLanguageProvider';

export default function SignIn() {
  const language = useAppLanguage();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const copy = {
    fr: {
      tagline: 'Protection IA autonome pour la comptabilité fournisseurs',
      email: 'Email',
      emailPlaceholder: 'vous@entreprise.com',
      password: 'Mot de passe',
      forgotPassword: 'Mot de passe oublié ?',
      signIn: 'Se connecter',
      noAccount: "Vous n'avez pas de compte ?",
      requestAccess: "Demander l'accès",
    },
    en: {
      tagline: 'Autonomous AI Protection for Accounts Payable',
      email: 'Email',
      emailPlaceholder: 'you@company.com',
      password: 'Password',
      forgotPassword: 'Forgot password?',
      signIn: 'Sign In',
      noAccount: "Don't have an account?",
      requestAccess: 'Request Access',
    },
    de: {
      tagline: 'Autonomer KI-Schutz für die Kreditorenbuchhaltung',
      email: 'E-Mail',
      emailPlaceholder: 'sie@unternehmen.de',
      password: 'Passwort',
      forgotPassword: 'Passwort vergessen?',
      signIn: 'Anmelden',
      noAccount: 'Sie haben noch keinen Account?',
      requestAccess: 'Zugang anfordern',
    },
  }[language];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden">
      <VercelBackground />

      {/* Sign in card - glass floating plate */}
      <div className="relative z-10 w-full max-w-[440px] px-6">
        <div 
          className="rounded-xl p-12 backdrop-blur-[20px] relative overflow-hidden"
          style={{
            background: 'rgba(20, 22, 25, 0.6)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            boxShadow: 'inset 0 1px 0 0 rgba(255, 255, 255, 0.1)',
          }}
        >
          {/* Logo with pulse animation */}
          <div className="text-center mb-12">
            <div className="inline-flex items-center justify-center mb-8 relative">
              {/* Pulsing rings */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div 
                  className="absolute w-28 h-28 rounded-full animate-ping"
                  style={{
                    border: '1px solid #00F2FF',
                    opacity: 0.2,
                    animationDuration: '3s'
                  }}
                />
              </div>

              {/* Logo image */}
              <div className="relative">
                <img 
                  src="/logo.svg" 
                  alt="InvoiceGuard Logo" 
                  className="w-24 h-auto relative z-10"
                  style={{
                    animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite'
                  }}
                />
              </div>
            </div>

            <h1 
              className="text-4xl mb-2"
              style={{ 
                fontFamily: 'Geist Sans, Inter, sans-serif',
                fontWeight: 700,
                letterSpacing: '-0.02em',
                color: '#FAFAFA',
              }}
            >
              InvoiceGuard
            </h1>
            <p className="text-[#71717A] text-sm">
              {copy.tagline}
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Email field */}
            <div>
              <label htmlFor="email" className="block text-sm mb-2 text-[#FAFAFA] font-medium">
                {copy.email}
              </label>
              <div className="relative group">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#71717A] group-focus-within:text-[#00F2FF] transition-colors" />
                <input
                  type="email"
                  id="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder={copy.emailPlaceholder}
                  className="w-full pl-12 pr-4 py-3.5 rounded-lg text-white placeholder-[#52525B] transition-all outline-none"
                  style={{
                    background: 'rgba(6, 7, 9, 0.8)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                  }}
                  onFocus={(e) => {
                    e.target.style.border = '1px solid #00F2FF';
                  }}
                  onBlur={(e) => {
                    e.target.style.border = '1px solid rgba(255, 255, 255, 0.1)';
                  }}
                  required
                />
              </div>
            </div>

            {/* Password field */}
            <div>
              <label htmlFor="password" className="block text-sm mb-2 text-[#FAFAFA] font-medium">
                {copy.password}
              </label>
              <div className="relative group">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#71717A] group-focus-within:text-[#00F2FF] transition-colors" />
                <input
                  type="password"
                  id="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-12 pr-4 py-3.5 rounded-lg text-white placeholder-[#52525B] transition-all outline-none"
                  style={{
                    background: 'rgba(6, 7, 9, 0.8)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                  }}
                  onFocus={(e) => {
                    e.target.style.border = '1px solid #00F2FF';
                  }}
                  onBlur={(e) => {
                    e.target.style.border = '1px solid rgba(255, 255, 255, 0.1)';
                  }}
                  required
                />
              </div>
            </div>

            {/* Forgot password */}
            <div className="text-right">
              <button 
                type="button" 
                className="text-sm text-[#00F2FF] hover:text-[#33F5FF] transition-colors"
              >
                {copy.forgotPassword}
              </button>
            </div>

            {/* Submit button */}
            <button
              type="submit"
              className="w-full py-3.5 rounded-lg uppercase tracking-wider text-sm transition-all duration-200 relative overflow-hidden"
              style={{
                background: '#00F2FF',
                color: '#060709',
                fontWeight: 600,
                border: '1px solid rgba(255, 255, 255, 0.2)',
                boxShadow: 'inset 0 1px 0 0 rgba(255, 255, 255, 0.2)',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'scale(1.02)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'scale(1)';
              }}
            >
              <span className="relative z-10">{copy.signIn}</span>
            </button>
          </form>

          {/* Sign up link */}
          <div className="mt-8 text-center text-sm text-[#71717A]">
            {copy.noAccount}{' '}
            <button className="text-[#00F2FF] hover:text-[#33F5FF] transition-colors font-medium">
              {copy.requestAccess}
            </button>
          </div>
        </div>
      </div>

      {/* CSS animations */}
      <style>{`
        @keyframes scan {
          0% { transform: translateY(-20px); opacity: 0; }
          10% { opacity: 1; }
          90% { opacity: 1; }
          100% { transform: translateY(100px); opacity: 0; }
        }
      `}</style>

      <div className="absolute bottom-0 left-0 right-0">
        <Footer />
      </div>
    </div>
  );
}
