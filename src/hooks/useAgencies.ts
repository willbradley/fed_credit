import { useState, useEffect } from 'react';
import type { Agency } from '../types';
import { getAgencies, getAgenciesWithLoanPrograms } from '../services/usaspending';

interface UseAgenciesResult {
  agencies: Agency[];
  loading: boolean;
  error: Error | null;
  refetch: () => void;
}

export function useAgencies(onlyWithLoanPrograms: boolean = false): UseAgenciesResult {
  const [agencies, setAgencies] = useState<Agency[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchAgencies = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = onlyWithLoanPrograms
        ? await getAgenciesWithLoanPrograms()
        : await getAgencies();
      setAgencies(data);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch agencies'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgencies();
  }, [onlyWithLoanPrograms]);

  return {
    agencies,
    loading,
    error,
    refetch: fetchAgencies,
  };
}

export default useAgencies;
