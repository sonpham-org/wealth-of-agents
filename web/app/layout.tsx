import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Wealth of Agents - Economic Simulation",
  description: "Agent-Based Economic Simulation exploring emergent phenomena like inflation, inequality, and resource allocation",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <nav className="bg-gray-900 text-white px-6 py-4">
          <div className="max-w-7xl mx-auto flex justify-between items-center">
            <h1 className="text-2xl font-bold">🌍 Wealth of Agents</h1>
            <div className="flex gap-6">
              <a href="/" className="hover:text-blue-400">Home</a>
              <a href="/simulations" className="hover:text-blue-400">Simulations</a>
              <a href="/new" className="hover:text-blue-400">New Job</a>
            </div>
          </div>
        </nav>
        <main className="min-h-screen">
          {children}
        </main>
        <footer className="bg-gray-800 text-white text-center py-6 mt-20">
          <p>© {new Date().getFullYear()} Wealth of Agents | Agent-Based Economic Simulation</p>
        </footer>
      </body>
    </html>
  );
}
