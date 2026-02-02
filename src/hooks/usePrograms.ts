import { useState, useEffect } from 'react';
import type { Program } from '../types';
import {
  getProgramsByAgency,
  getDirectLoanPrograms,
  getLoanGuaranteePrograms,
  getAllLoanPrograms,
} from '../services/usaspending';

interface UseProgramsResult {
  programs: Program[];
  loading: boolean;
  error: Error | null;
  refetch: () => void;
}

export function usePrograms(agencyName?: string): UseProgramsResult {
  const [programs, setPrograms] = useState<Program[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchPrograms = async () => {
    setLoading(true);
    setError(null);
    try {
      if (agencyName) {
        // Fetch both direct loans and loan guarantees separately to classify them
        const [directLoans, loanGuarantees] = await Promise.all([
          getDirectLoanPrograms(agencyName),
          getLoanGuaranteePrograms(agencyName),
        ]);

        // Merge and deduplicate by CFDA number
        const programMap = new Map<string, Program>();

        directLoans.forEach((p) => {
          programMap.set(p.cfda_number, { ...p, award_type: 'direct_loan' });
        });

        loanGuarantees.forEach((p) => {
          const existing = programMap.get(p.cfda_number);
          if (existing) {
            // Program has both types, mark based on larger amount
            if (p.total_obligation > existing.total_obligation) {
              programMap.set(p.cfda_number, { ...p, award_type: 'loan_guarantee' });
            }
          } else {
            programMap.set(p.cfda_number, { ...p, award_type: 'loan_guarantee' });
          }
        });

        setPrograms(Array.from(programMap.values()));
      } else {
        const data = await getAllLoanPrograms();
        setPrograms(data);
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch programs'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPrograms();
  }, [agencyName]);

  return {
    programs,
    loading,
    error,
    refetch: fetchPrograms,
  };
}

// Hook to get all programs for an agency (simpler version)
export function useAgencyPrograms(agencyName: string | null): UseProgramsResult {
  const [programs, setPrograms] = useState<Program[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchPrograms = async () => {
    if (!agencyName) {
      setPrograms([]);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await getProgramsByAgency(agencyName);
      setPrograms(data);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch programs'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPrograms();
  }, [agencyName]);

  return {
    programs,
    loading,
    error,
    refetch: fetchPrograms,
  };
}

export default usePrograms;
