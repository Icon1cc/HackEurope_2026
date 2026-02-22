import { RouterProvider } from 'react-router';
import { router } from './routes';
import { AppLanguageProvider } from './i18n/AppLanguageProvider';
import { AuthProvider } from './auth/AuthContext';

export default function App() {
  return (
    <AppLanguageProvider>
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    </AppLanguageProvider>
  );
}
