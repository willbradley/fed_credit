import React from 'react';

interface LayoutProps {
  children: React.ReactNode;
  onHomeClick?: () => void;
}

export function Layout({ children, onHomeClick }: LayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-blue-900 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <button
              onClick={onHomeClick}
              className="flex items-center gap-3 hover:opacity-80 transition-opacity"
            >
              <svg
                className="w-8 h-8"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
                />
              </svg>
              <div>
                <h1 className="text-xl font-bold">Federal Credit Programs</h1>
                <p className="text-xs text-blue-200">
                  Direct Loans & Loan Guarantees
                </p>
              </div>
            </button>
            <nav className="flex items-center gap-4">
              <a
                href="https://www.usaspending.gov"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-200 hover:text-white transition-colors"
              >
                Data Source: USAspending.gov
              </a>
            </nav>
          </div>
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
      <footer className="bg-gray-800 text-gray-400 py-6 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-sm">
          <p>
            Data sourced from{' '}
            <a
              href="https://api.usaspending.gov"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 hover:text-blue-300"
            >
              USAspending.gov API
            </a>
          </p>
          <p className="mt-1">
            Federal Credit Supplement data from OMB Budget Documents
          </p>
        </div>
      </footer>
    </div>
  );
}

export default Layout;
