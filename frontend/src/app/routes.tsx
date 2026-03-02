import { createBrowserRouter } from "react-router";
import Dashboard from "./pages/Dashboard";
import ReviewDetail from "./pages/ReviewDetail";
import Settings from "./pages/Settings";
import SignIn from "./pages/SignIn";
import VendorDetail from "./pages/VendorDetail";
import Vendors from "./pages/Vendors";
// import { ProtectedRoute } from './auth/ProtectedRoute';

export const router = createBrowserRouter([
  {
    path: "/",
    element: <SignIn />,
  },
  {
    path: "/dashboard",
    element: <Dashboard />,
  },
  {
    path: "/vendors",
    element: <Vendors />,
  },
  {
    path: "/vendors/:vendorId",
    element: <VendorDetail />,
  }
  
  
  ,

  
  {
    path: "/settings",
    element: <Settings />,
  },
  {
    path: "/reviews/:reviewId",
    element: <ReviewDetail />,
  },
]);
