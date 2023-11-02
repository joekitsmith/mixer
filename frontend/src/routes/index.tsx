import { useRoutes } from "react-router-dom";
import { Navigate } from "react-router-dom";
import { lazyImport } from "../utils/lazyImport";

const { Tracks } = lazyImport(() => import("../features/tracks"), "Tracks");

export const routes = [
  {
    path: "/",
    element: <Navigate replace to="/tracks" />,
  },
  {
    path: "/app",
    element: <Navigate replace to="/tracks" />,
  },
  {
    path: "/tracks",
    element: <Tracks />,
  },
];

export const AppRoutes = () => {
  const element = useRoutes([...routes]);

  return <>{element}</>;
};
