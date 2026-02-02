import { useState, useMemo } from 'react';
import type { Agency, Program } from '../types';
import { ProgramCard } from './ProgramCard';
import { usePrograms } from '../hooks/usePrograms';

interface ProgramListProps {
  agency: Agency;
  onSelectProgram: (program: Program) => void;
  onBack: () => void;
}

type FilterType = 'all' | 'direct_loan' | 'loan_guarantee';

export function ProgramList({ agency, onSelectProgram, onBack }: ProgramListProps) {
  const { programs, loading, error } = usePrograms(agency.agency_name);
  const [filter, setFilter] = useState<FilterType>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredPrograms = useMemo(() => {
    let result = programs;

    // Filter by type
    if (filter !== 'all') {
      result = result.filter((p) => p.award_type === filter);
    }

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (p) =>
          p.cfda_title.toLowerCase().includes(query) ||
          p.cfda_number.toLowerCase().includes(query)
      );
    }

    return result;
  }, [programs, filter, searchQuery]);

  const directLoanCount = programs.filter(
    (p) => p.award_type === 'direct_loan'
  ).length;
  const guaranteeCount = programs.filter(
    (p) => p.award_type === 'loan_guarantee'
  ).length;

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <p className="mt-4 text-gray-600">Loading loan programs...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <p className="text-red-800 font-medium">Error loading programs</p>
        <p className="text-red-600 text-sm mt-1">{error.message}</p>
        <button
          onClick={onBack}
          className="mt-4 text-blue-600 hover:text-blue-800"
        >
          Go back to agencies
        </button>
      </div>
    );
  }

  return (
    <div>
      <button
        onClick={onBack}
        className="flex items-center text-blue-600 hover:text-blue-800 mb-4"
      >
        <svg
          className="w-5 h-5 mr-1"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 19l-7-7 7-7"
          />
        </svg>
        Back to Agencies
      </button>

      <div className="bg-blue-50 rounded-lg p-4 mb-6">
        <div className="flex items-center gap-2 mb-1">
          {agency.abbreviation && (
            <span className="px-2 py-1 bg-blue-200 text-blue-800 text-xs font-semibold rounded">
              {agency.abbreviation}
            </span>
          )}
        </div>
        <h2 className="text-2xl font-bold text-gray-900">{agency.agency_name}</h2>
        <p className="text-gray-600 mt-1">
          {programs.length} loan program{programs.length !== 1 ? 's' : ''} (
          {directLoanCount} direct loan{directLoanCount !== 1 ? 's' : ''},{' '}
          {guaranteeCount} guarantee{guaranteeCount !== 1 ? 's' : ''})
        </p>
      </div>

      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="relative flex-1">
          <input
            type="text"
            placeholder="Search programs..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 pl-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          <svg
            className="absolute left-3 top-2.5 w-5 h-5 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => setFilter('all')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              filter === 'all'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            All
          </button>
          <button
            onClick={() => setFilter('direct_loan')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              filter === 'direct_loan'
                ? 'bg-green-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Direct Loans
          </button>
          <button
            onClick={() => setFilter('loan_guarantee')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              filter === 'loan_guarantee'
                ? 'bg-purple-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Guarantees
          </button>
        </div>
      </div>

      {filteredPrograms.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-600">
            {programs.length === 0
              ? 'No loan programs found for this agency'
              : 'No programs match your filters'}
          </p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredPrograms.map((program) => (
            <ProgramCard
              key={program.cfda_number}
              program={program}
              onClick={onSelectProgram}
            />
          ))}
        </div>
      )}

      <div className="mt-6 text-center text-sm text-gray-500">
        Showing {filteredPrograms.length} of {programs.length} programs
      </div>
    </div>
  );
}

export default ProgramList;
