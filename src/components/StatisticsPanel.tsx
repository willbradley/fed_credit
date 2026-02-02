import type { ProgramStatistics, CreditSupplementProgram } from '../types';

interface StatisticsPanelProps {
  stats: ProgramStatistics | null;
  supplementData?: CreditSupplementProgram | null;
  loading?: boolean;
}

// Format large numbers as currency
function formatCurrency(amount: number): string {
  if (amount >= 1_000_000_000_000) {
    return `$${(amount / 1_000_000_000_000).toFixed(2)}T`;
  }
  if (amount >= 1_000_000_000) {
    return `$${(amount / 1_000_000_000).toFixed(2)}B`;
  }
  if (amount >= 1_000_000) {
    return `$${(amount / 1_000_000).toFixed(2)}M`;
  }
  if (amount >= 1_000) {
    return `$${(amount / 1_000).toFixed(2)}K`;
  }
  return `$${amount.toFixed(0)}`;
}

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(2)}%`;
}

export function StatisticsPanel({ stats, supplementData, loading }: StatisticsPanelProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-2 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i}>
                <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
                <div className="h-8 bg-gray-200 rounded w-3/4"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="bg-gray-50 rounded-lg p-6 text-center text-gray-500">
        No statistics available
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Primary Statistics */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Program Statistics
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div>
            <p className="text-sm text-gray-500">Total Disbursements</p>
            <p className="text-2xl font-bold text-blue-600">
              {formatCurrency(stats.total_disbursements)}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Face Value</p>
            <p className="text-2xl font-bold text-green-600">
              {formatCurrency(stats.total_face_value)}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Subsidy Cost</p>
            <p className="text-2xl font-bold text-purple-600">
              {stats.total_subsidy_cost > 0
                ? formatCurrency(stats.total_subsidy_cost)
                : 'N/A'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Award Count</p>
            <p className="text-2xl font-bold text-gray-900">
              {stats.award_count.toLocaleString()}
            </p>
          </div>
        </div>
      </div>

      {/* Loan Characteristics from Federal Credit Supplement */}
      {supplementData && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Loan Characteristics
            <span className="ml-2 text-xs font-normal text-gray-500">
              (Federal Credit Supplement)
            </span>
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div>
              <p className="text-sm text-gray-500">Subsidy Rate</p>
              <p className="text-xl font-bold text-orange-600">
                {formatPercent(supplementData.subsidy_rate)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Default Rate</p>
              <p className="text-xl font-bold text-red-600">
                {formatPercent(supplementData.default_rate)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Avg. Maturity</p>
              <p className="text-xl font-bold text-gray-900">
                {supplementData.average_maturity_years} years
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Grace Period</p>
              <p className="text-xl font-bold text-gray-900">
                {supplementData.grace_period_months} months
              </p>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t border-gray-100">
            <p className="text-sm text-gray-500">Interest Rate Type</p>
            <p className="text-base font-medium text-gray-900 capitalize">
              {supplementData.interest_rate_type}
            </p>
          </div>
        </div>
      )}

      {/* Cohort Summary Table */}
      {supplementData && supplementData.cohort_data.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Cohort Data
          </h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Cohort Year
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Obligations
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Disbursements
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Unpaid Principal
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Subsidy Cost
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {supplementData.cohort_data.map((cohort) => (
                  <tr key={cohort.cohort_year} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">
                      FY {cohort.cohort_year}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-gray-600">
                      {formatCurrency(cohort.obligations)}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-gray-600">
                      {formatCurrency(cohort.disbursements)}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-gray-600">
                      {formatCurrency(cohort.unpaid_principal)}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-gray-600">
                      {formatCurrency(cohort.subsidy_cost)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default StatisticsPanel;
