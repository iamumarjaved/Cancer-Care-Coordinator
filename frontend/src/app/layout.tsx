import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { ClerkProvider, SignedIn, SignedOut, SignInButton, UserButton } from '@clerk/nextjs';
import './globals.css';
import { Providers } from './providers';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Cancer Care Coordinator',
  description: 'AI-powered cancer care coordination platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClerkProvider
      signInFallbackRedirectUrl="/"
      signUpFallbackRedirectUrl="/"
    >
      <html lang="en">
        <body className={inter.className}>
          <Providers>
            <div className="min-h-screen bg-gray-50 flex flex-col">
              {/* Header */}
              <header className="bg-white border-b border-gray-200">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                  <div className="flex justify-between items-center h-16">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                        <span className="text-white font-bold text-lg">C</span>
                      </div>
                      <span className="font-semibold text-lg text-gray-900">
                        Cancer Care Coordinator
                      </span>
                    </div>
                    <div className="flex items-center gap-6">
                      <SignedIn>
                        <nav className="flex gap-6">
                          <a href="/" className="text-gray-600 hover:text-gray-900">
                            Dashboard
                          </a>
                          <a href="/patients" className="text-gray-600 hover:text-gray-900">
                            Patients
                          </a>
                        </nav>
                      </SignedIn>
                      <div className="flex items-center gap-3">
                        <SignedOut>
                          <SignInButton mode="modal">
                            <button className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-md hover:bg-primary-700 transition-colors">
                              Sign In
                            </button>
                          </SignInButton>
                        </SignedOut>
                        <SignedIn>
                          <UserButton afterSignOutUrl="/" />
                        </SignedIn>
                      </div>
                    </div>
                  </div>
                </div>
              </header>

              {/* Main Content */}
              <main className="flex-grow max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
                {children}
              </main>

              {/* Footer */}
              <footer className="bg-white border-t border-gray-200 py-6">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                  <p className="text-center text-sm text-gray-500">
                    Cancer Care Coordinator - AI-Powered Treatment Support - By Umar Javed
                  </p>
                </div>
              </footer>
            </div>
          </Providers>
        </body>
      </html>
    </ClerkProvider>
  );
}
