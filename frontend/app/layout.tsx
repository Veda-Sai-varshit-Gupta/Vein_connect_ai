import type { Metadata } from "next";
import { Inter, DM_Sans } from "next/font/google";
import "./globals.css";
import RootProviders from "../components/layout/RootProviders";
import EmergencyBanner from "../components/layout/EmergencyBanner";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const dmSans = DM_Sans({
  variable: "--font-dm-sans",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "VeinConnect AI — Thalassemia Transfusion coordination platform",
  description: "AI-Powered Recurring Transfusion Coordination Platform for Thalassemia Care in India",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${dmSans.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <body className="min-h-full flex flex-col bg-zinc-50 dark:bg-zinc-950">
        <RootProviders>
          <EmergencyBanner />
          {children}
        </RootProviders>
      </body>
    </html>
  );
}
