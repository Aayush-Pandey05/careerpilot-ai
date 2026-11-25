import type { Metadata } from 'next';
import Shell from '@/components/layout/shell';
import './globals.css';
export const metadata: Metadata = {
  title: 'CareerPilot AI — Your next move, with clarity',
  description: 'Evidence-based resume matching and thoughtful application preparation.',
};
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <Shell>{children}</Shell>
      </body>
    </html>
  );
}
