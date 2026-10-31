import './globals.css';

// Self-hosted dyslexia-friendly fonts via @fontsource (woff2)
import '@fontsource/opendyslexic/400.css';
import '@fontsource/opendyslexic/700.css';
import '@fontsource/atkinson-hyperlegible-next/400.css';
import '@fontsource/atkinson-hyperlegible-next/700.css';

import { UserProvider } from '@/context/UserContext';
import { AccessibilityProvider } from '@/context/AccessibilityContext';

export const metadata = {
  title: 'AI Tutor — Dyslexia-Friendly Learning Assistant',
  description: 'An AI-powered learning platform designed for students with dyslexia. Upload notes, ask questions, take quizzes, and track your progress.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <UserProvider>
          <AccessibilityProvider>
            {children}
          </AccessibilityProvider>
        </UserProvider>
      </body>
    </html>
  );
}
