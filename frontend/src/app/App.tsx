import { RouterProvider } from 'react-router';
import { router } from './routes';
import { AppLanguageProvider } from './i18n/AppLanguageProvider';

export default function App() {
  return (
    <AppLanguageProvider>
      <RouterProvider router={router} />
    </AppLanguageProvider>
  );
}
