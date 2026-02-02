import { useState, useMemo } from 'react';
import type { Agency } from '../types';
import { AgencyCard } from './AgencyCard';
import { useAgencies } from '../hooks/useAgencies';

interface AgencyListProps {
  onSelectAgency: (agency: Agency) => void;
}

export function AgencyList({ onSelectAgency }: AgencyListProps) {
  const { agencies, loading, error } = useAgencies(true);
  const [searchQuery, setSearchQuery] = useState('');

  const filteredAgencies = useMemo(() => {
    if (!searchQuery.trim()) {
      return agencies;
    }
    const query = searchQuery.toLowerCase();
    return agencies.filter(
      (agency) =>
        agency.agency_name.toLowerCase().includes(query) ||
        agency.abbreviation?.toLowerCase().includes(query)
    );
  }, [agencies, searchQuery]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <p className="mt-4 text-gray-600">Loading federal agencies...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <p className="text-red-800 font-medium">Error loading agencies</p>
        <p className="text-red-600 text-sm mt-1">{error.message}</p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Federal Agencies with Credit Programs
        </h2>
        <p className="text-gray-600">
          Select an agency to view their direct loan and loan guarantee programs
        </p>
      </div>

      <div className="mb-6">
        <div className="relative">
          <input
            type="text"
            placeholder="Search agencies by name or abbreviation..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-3 pl-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          <svg
            className="absolute left-3 top-3.5 w-5 h-5 text-gray-400"
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
      </div>

      {filteredAgencies.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-600">No agencies match your search</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredAgencies.map((agency) => (
            <AgencyCard
              key={agency.agency_id}
              agency={agency}
              onClick={onSelectAgency}
            />
          ))}
        </div>
      )}

      <div className="mt-6 text-center text-sm text-gray-500">
        Showing {filteredAgencies.length} of {agencies.length} agencies with
        credit programs
      </div>
    </div>
  );
}

export default AgencyList;
