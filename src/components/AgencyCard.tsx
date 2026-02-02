import type { Agency } from '../types';

interface AgencyCardProps {
  agency: Agency;
  onClick: (agency: Agency) => void;
  programCount?: number;
}

// Format large numbers as currency
function formatCurrency(amount: number): string {
  if (amount >= 1_000_000_000_000) {
    return `$${(amount / 1_000_000_000_000).toFixed(1)}T`;
  }
  if (amount >= 1_000_000_000) {
    return `$${(amount / 1_000_000_000).toFixed(1)}B`;
  }
  if (amount >= 1_000_000) {
    return `$${(amount / 1_000_000).toFixed(1)}M`;
  }
  if (amount >= 1_000) {
    return `$${(amount / 1_000).toFixed(1)}K`;
  }
  return `$${amount.toFixed(0)}`;
}

export function AgencyCard({ agency, onClick, programCount }: AgencyCardProps) {
  return (
    <button
      onClick={() => onClick(agency)}
      className="w-full text-left bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow p-6 border border-gray-200 hover:border-blue-300"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            {agency.abbreviation && (
              <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-semibold rounded">
                {agency.abbreviation}
              </span>
            )}
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-1">
            {agency.agency_name}
          </h3>
          {programCount !== undefined && (
            <p className="text-sm text-gray-500">
              {programCount} loan program{programCount !== 1 ? 's' : ''}
            </p>
          )}
        </div>
        <div className="text-right">
          <p className="text-sm text-gray-500">Budget Authority</p>
          <p className="text-lg font-bold text-blue-600">
            {formatCurrency(agency.budget_authority_amount)}
          </p>
        </div>
      </div>
      <div className="mt-4 pt-4 border-t border-gray-100 grid grid-cols-2 gap-4 text-sm">
        <div>
          <p className="text-gray-500">Obligations</p>
          <p className="font-medium text-gray-900">
            {formatCurrency(agency.obligated_amount)}
          </p>
        </div>
        <div>
          <p className="text-gray-500">Outlays</p>
          <p className="font-medium text-gray-900">
            {formatCurrency(agency.outlay_amount)}
          </p>
        </div>
      </div>
      <div className="mt-3 flex items-center text-blue-600 text-sm font-medium">
        View Loan Programs
        <svg
          className="w-4 h-4 ml-1"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 5l7 7-7 7"
          />
        </svg>
      </div>
    </button>
  );
}

export default AgencyCard;
