import type { Program } from '../types';

interface ProgramCardProps {
  program: Program;
  onClick: (program: Program) => void;
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

export function ProgramCard({ program, onClick }: ProgramCardProps) {
  const isDirectLoan = program.award_type === 'direct_loan';

  return (
    <button
      onClick={() => onClick(program)}
      className="w-full text-left bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow p-5 border border-gray-200 hover:border-blue-300"
    >
      <div className="flex items-start justify-between mb-3">
        <span
          className={`px-2 py-1 text-xs font-semibold rounded ${
            isDirectLoan
              ? 'bg-green-100 text-green-800'
              : 'bg-purple-100 text-purple-800'
          }`}
        >
          {isDirectLoan ? 'Direct Loan' : 'Loan Guarantee'}
        </span>
        <span className="text-xs text-gray-500 font-mono">
          {program.cfda_number}
        </span>
      </div>

      <h3 className="text-base font-semibold text-gray-900 mb-3 line-clamp-2">
        {program.cfda_title}
      </h3>

      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <p className="text-gray-500">Total Obligations</p>
          <p className="font-bold text-gray-900">
            {formatCurrency(program.total_obligation)}
          </p>
        </div>
        <div>
          <p className="text-gray-500">Face Value</p>
          <p className="font-bold text-blue-600">
            {formatCurrency(program.total_face_value)}
          </p>
        </div>
      </div>

      <div className="mt-4 flex items-center text-blue-600 text-sm font-medium">
        View Details
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

export default ProgramCard;
