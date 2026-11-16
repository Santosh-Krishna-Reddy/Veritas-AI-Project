import type { Metadata } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans, IBM_Plex_Sans_Condensed } from "next/font/google";
import "./globals.css";

// Plex Sans Condensed for headings, Plex Sans for text, Plex Mono for every number.
const plexSans = IBM_Plex_Sans({ variable: "--font-plex-sans", subsets: ["latin"], weight: ["400", "500", "600"] });
const plexCondensed = IBM_Plex_Sans_Condensed({ variable: "--font-plex-condensed", subsets: ["latin"], weight: ["500", "600"] });
const plexMono = IBM_Plex_Mono({ variable: "--font-plex-mono", subsets: ["latin"], weight: ["400", "500", "600"] });

export const metadata: Metadata = {
  title: "GridGreen — cleanest hours on the PJM grid",
  description: "Next-24-hour carbon intensity forecast for PJM, with held-out test results",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${plexSans.variable} ${plexCondensed.variable} ${plexMono.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
