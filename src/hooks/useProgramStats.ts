import { useState, useEffect } from 'react';
import type { ProgramStatistics, FiscalYearData, Award } from '../types';
import { getProgramAwards, getProgramTimeSeries } from '../services/usaspending';

interface UseProgramStatsResult {
  stats: ProgramStatistics | null;
  awards: Award[];
  loading: boolean;
  error: Error | null;
  refetch: () => void;
}

export function useProgramStats(cfdaNumber: string | null): UseProgramStatsResult {
  const [stats, setStats] = useState<ProgramStatistics | null>(null);
  const [awards, setAwards] = useState<Award[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchStats = async () => {
    if (!cfdaNumber) {
      setStats(null);
      setAwards([]);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      // Fetch awards and time series data in parallel
      const [awardsResponse, timeSeries] = await Promise.all([
        getProgramAwards(cfdaNumber),
        getProgramTimeSeries(cfdaNumber),
      ]);

      // Transform awards response
      const transformedAwards: Award[] = awardsResponse.results.map((award: Record<string, unknown>) => ({
        Award_ID: (award['Award ID'] as string) || '',
        Recipient_Name: (award['Recipient Name'] as string) || '',
        Start_Date: (award['Start Date'] as string) || '',
        End_Date: (award['End Date'] as string) || '',
        Award_Amount: (award['Award Amount'] as number) || 0,
        Total_Outlays: (award['Total Outlays'] as number) || 0,
        description: (award['description'] as string) || '',
        def_codes: (award['def_codes'] as string[]) || [],
        awarding_agency: (award['awarding_agency'] as string) || '',
        awarding_sub_agency: (award['awarding_sub_agency'] as string) || '',
        Award_Type: (award['Award Type'] as string) || '',
        recipient_id: (award['recipient_id'] as string) || '',
        prime_award_recipient_id: (award['prime_award_recipient_id'] as string) || '',
        generated_internal_id: (award['generated_internal_id'] as string) || '',
      }));

      // Calculate aggregate statistics
      const totalDisbursements = transformedAwards.reduce(
        (sum, a) => sum + (a.Total_Outlays || 0),
        0
      );
      const totalFaceValue = transformedAwards.reduce(
        (sum, a) => sum + (a.Award_Amount || 0),
        0
      );

      // Transform time series to fiscal year data
      const fiscalYearData: FiscalYearData[] = timeSeries.map((ts) => ({
        fiscal_year: ts.fiscal_year,
        disbursements: ts.amount,
        face_value: ts.amount,
        subsidy_cost: 0, // Not available from API
        new_loans: 0,
      }));

      setStats({
        cfda_number: cfdaNumber,
        cfda_title: transformedAwards[0]?.description || '',
        total_disbursements: totalDisbursements,
        total_face_value: totalFaceValue,
        total_subsidy_cost: 0, // Would come from Federal Credit Supplement
        award_count: awardsResponse.page_metadata?.total || transformedAwards.length,
        fiscal_year_data: fiscalYearData,
      });

      setAwards(transformedAwards);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch program statistics'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, [cfdaNumber]);

  return {
    stats,
    awards,
    loading,
    error,
    refetch: fetchStats,
  };
}

export default useProgramStats;
