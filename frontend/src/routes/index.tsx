import { useRoutes } from "react-router-dom";
import { Navigate } from "react-router-dom";
import { lazyImport } from "../utils/lazyImport";

const { Mixer } = lazyImport(() => import("../features/mixer"), "Mixer");

export const routes = [
  {
    path: "/",
    element: <Navigate replace to="/mixer" />,
  },
  {
    path: "/app",
    element: <Navigate replace to="/mixer" />,
  },
  {
    path: "/mixer",
    element: <Mixer />,
  },
];

export const AppRoutes = () => {
  const element = useRoutes([...routes]);

  return <>{element}</>;
};
