import type { Metadata } from "next";
import { IBM_Plex_Sans, Rajdhani } from "next/font/google";

import "./globals.css";
import { QueryProvider } from "@/components/providers/query-provider";

const rajdhani = Rajdhani({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-rajdhani"
});

const plex = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600"],
  variable: "--font-plex"
});

export const metadata: Metadata = {
  title: "CarPartPicker",
  description: "A seed-mode car build-planning cockpit with deterministic fitment reasoning."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${rajdhani.variable} ${plex.variable}`}>
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}
