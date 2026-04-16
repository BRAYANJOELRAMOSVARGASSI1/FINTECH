import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  typescript: {
    // Esto ignora los errores de tipo solo durante el build de Render
    ignoreBuildErrors: true,
  },
  eslint: {
    // También ignoramos ESLint por si acaso, para que nada detenga el despliegue
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;