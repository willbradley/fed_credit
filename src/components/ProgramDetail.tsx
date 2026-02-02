import { useState } from 'react';
import type { Program, Agency, CreditSupplementProgram } from '../types';
import { useProgramStats } from '../hooks/useProgramStats';
import { StatisticsPanel } from './StatisticsPanel';
import { TrendChart } from './TrendChart';
import creditSupplementData from '../data/creditSupplement.json';

interface ProgramDetailProps {
  program: Program;
  agency: Agency;
  onBack: () => void;
}

type TabType = 'overview' | 'trends' | 'awards';

export function ProgramDetail({ program, agency, onBack }: ProgramDetailProps) {
  const { stats, awards, loading } = useProgramStats(program.cfda_number);
  const [activeTab, setActiveTab] = useState<TabType>('overview');

  // Find supplement data if available
  const supplementData = (creditSupplementData.programs as CreditSupplementProgram[]).find(
    (p) => p.cfda_number === program.cfda_number
  );

  const isDirectLoan = program.award_type === 'direct_loan';

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
        Back to Programs
      </button>

      {/* Program Header */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <span
                className={`px-3 py-1 text-sm font-semibold rounded-full ${
                  isDirectLoan
                    ? 'bg-green-100 text-green-800'
                    : 'bg-purple-100 text-purple-800'
                }`}
              >
                {isDirectLoan ? 'Direct Loan' : 'Loan Guarantee'}
              </span>
              <span className="text-sm text-gray-500 font-mono">
                CFDA {program.cfda_number}
              </span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              {program.cfda_title}
            </h1>
            <p className="text-gray-600">
              <span className="font-medium">{agency.agency_name}</span>
              {agency.abbreviation && (
                <span className="text-gray-400 ml-1">({agency.abbreviation})</span>
              )}
            </p>
          </div>
          <a
            href={`https://www.usaspending.gov/search/?hash=4c54c09eb69b3a5e22bdae540e64a6fc&filters={"timePeriodFY":["2024","2023","2022","2021"],"awardType":["07","08"],"selectedCFDA":[{"program_number":"${program.cfda_number}"}]}`}
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
          >
            View on USAspending
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
              />
            </svg>
          </a>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex gap-8">
          <button
            onClick={() => setActiveTab('overview')}
            className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'overview'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('trends')}
            className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'trends'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Trends
          </button>
          <button
            onClick={() => setActiveTab('awards')}
            className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'awards'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Recent Awards
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <StatisticsPanel
          stats={stats}
          supplementData={supplementData}
          loading={loading}
        />
      )}

      {activeTab === 'trends' && (
        <div className="space-y-6">
          <TrendChart
            data={stats?.fiscal_year_data || []}
            title="Fiscal Year Trends"
            chartType="line"
          />
          <TrendChart
            data={stats?.fiscal_year_data || []}
            title="Annual Comparison"
            chartType="bar"
          />
        </div>
      )}

      {activeTab === 'awards' && (
        <div className="bg-white rounded-lg shadow">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">
              Recent Awards
            </h3>
            <p className="text-sm text-gray-500">
              Top awards by amount (FY 2020-2024)
            </p>
          </div>
          {loading ? (
            <div className="p-8 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-gray-500">Loading awards...</p>
            </div>
          ) : awards.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              No award data available
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Recipient
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Award ID
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      Amount
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      Outlays
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Start Date
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {awards.slice(0, 20).map((award, index) => (
                    <tr key={award.Award_ID || index} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm text-gray-900 max-w-xs truncate">
                        {award.Recipient_Name || 'N/A'}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600 font-mono">
                        {award.Award_ID || 'N/A'}
                      </td>
                      <td className="px-4 py-3 text-sm text-right text-gray-900">
                        ${(award.Award_Amount || 0).toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-sm text-right text-gray-600">
                        ${(award.Total_Outlays || 0).toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {award.Start_Date || 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {awards.length > 20 && (
            <div className="p-4 border-t border-gray-200 text-center text-sm text-gray-500">
              Showing 20 of {awards.length} awards
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default ProgramDetail;
