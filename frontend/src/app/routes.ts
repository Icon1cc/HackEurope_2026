import { createBrowserRouter } from 'react-router';
import SignIn from './pages/SignIn';
import Dashboard from './pages/Dashboard';
import Vendors from './pages/Vendors';
import VendorDetail from './pages/VendorDetail';
import Settings from './pages/Settings';
import ReviewDetail from './pages/ReviewDetail';

export const router = createBrowserRouter([
  {
    path: '/',
    Component: SignIn,
  },
  {
    path: '/dashboard',
    Component: Dashboard,
  },
  {
    path: '/vendors',
    Component: Vendors,
  },
  {
    path: '/vendors/:vendorId',
    Component: VendorDetail,
  },
  {
    path: '/settings',
    Component: Settings,
  },
  {
    path: '/reviews/:reviewId',
    Component: ReviewDetail,
  },
]);
