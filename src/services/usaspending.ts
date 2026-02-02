import type {
  AgencyListResponse,
  SpendingByCategoryResponse,
  SpendingByAwardResponse,
  SearchFilters,
  Agency,
  Program,
} from '../types';

const BASE_URL = 'https://api.usaspending.gov/api/v2';

// Simple in-memory cache
const cache = new Map<string, { data: unknown; timestamp: number }>();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

function getCached<T>(key: string): T | null {
  const entry = cache.get(key);
  if (entry && Date.now() - entry.timestamp < CACHE_TTL) {
    return entry.data as T;
  }
  return null;
}

function setCache(key: string, data: unknown): void {
  cache.set(key, { data, timestamp: Date.now() });
}

async function fetchWithCache<T>(
  url: string,
  options?: RequestInit
): Promise<T> {
  const cacheKey = `${url}:${JSON.stringify(options?.body || '')}`;
  const cached = getCached<T>(cacheKey);
  if (cached) {
    return cached;
  }

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();
  setCache(cacheKey, data);
  return data;
}

// Get all top-tier federal agencies
export async function getAgencies(): Promise<Agency[]> {
  const response = await fetchWithCache<AgencyListResponse>(
    `${BASE_URL}/references/toptier_agencies/`
  );
  return response.results;
}

// Get loan programs by agency using spending by category (CFDA)
export async function getProgramsByAgency(
  agencyName: string,
  fiscalYearStart: number = 2020,
  fiscalYearEnd: number = 2024
): Promise<Program[]> {
  const filters: SearchFilters = {
    award_type_codes: ['07', '08'], // Direct loans and loan guarantees
    agencies: [
      {
        type: 'awarding',
        tier: 'toptier',
        name: agencyName,
      },
    ],
    time_period: [
      {
        start_date: `${fiscalYearStart}-10-01`,
        end_date: `${fiscalYearEnd}-09-30`,
      },
    ],
  };

  const response = await fetchWithCache<SpendingByCategoryResponse>(
    `${BASE_URL}/search/spending_by_category/cfda/`,
    {
      method: 'POST',
      body: JSON.stringify({
        filters,
        category: 'cfda',
        limit: 100,
        page: 1,
      }),
    }
  );

  // Transform to Program type
  return response.results.map((result) => ({
    id: result.code,
    cfda_number: result.code,
    cfda_title: result.name,
    agency_name: agencyName,
    award_type: 'direct_loan' as const, // Will be refined with additional API call
    total_obligation: result.amount,
    total_face_value: result.amount, // Face value needs separate calculation
    transaction_count: 0,
  }));
}

// Get all loan programs across all agencies
export async function getAllLoanPrograms(
  fiscalYearStart: number = 2020,
  fiscalYearEnd: number = 2024
): Promise<Program[]> {
  const filters: SearchFilters = {
    award_type_codes: ['07', '08'],
    time_period: [
      {
        start_date: `${fiscalYearStart}-10-01`,
        end_date: `${fiscalYearEnd}-09-30`,
      },
    ],
  };

  const response = await fetchWithCache<SpendingByCategoryResponse>(
    `${BASE_URL}/search/spending_by_category/cfda/`,
    {
      method: 'POST',
      body: JSON.stringify({
        filters,
        category: 'cfda',
        limit: 100,
        page: 1,
      }),
    }
  );

  return response.results.map((result) => ({
    id: result.code,
    cfda_number: result.code,
    cfda_title: result.name,
    agency_name: '',
    award_type: 'direct_loan' as const,
    total_obligation: result.amount,
    total_face_value: result.amount,
    transaction_count: 0,
  }));
}

// Get detailed awards for a specific program
export async function getProgramAwards(
  cfdaNumber: string,
  fiscalYearStart: number = 2020,
  fiscalYearEnd: number = 2024
): Promise<SpendingByAwardResponse> {
  const filters: SearchFilters = {
    award_type_codes: ['07', '08'],
    program_numbers: [cfdaNumber],
    time_period: [
      {
        start_date: `${fiscalYearStart}-10-01`,
        end_date: `${fiscalYearEnd}-09-30`,
      },
    ],
  };

  const response = await fetchWithCache<SpendingByAwardResponse>(
    `${BASE_URL}/search/spending_by_award/`,
    {
      method: 'POST',
      body: JSON.stringify({
        filters,
        fields: [
          'Award ID',
          'Recipient Name',
          'Start Date',
          'End Date',
          'Award Amount',
          'Total Outlays',
          'Award Type',
          'awarding_agency',
          'awarding_sub_agency',
          'generated_internal_id',
        ],
        limit: 100,
        page: 1,
        sort: 'Award Amount',
        order: 'desc',
        subawards: false,
      }),
    }
  );

  return response;
}

// Get spending by category for direct loans only
export async function getDirectLoanPrograms(
  agencyName?: string,
  fiscalYearStart: number = 2020,
  fiscalYearEnd: number = 2024
): Promise<Program[]> {
  const filters: SearchFilters = {
    award_type_codes: ['07'], // Direct loans only
    time_period: [
      {
        start_date: `${fiscalYearStart}-10-01`,
        end_date: `${fiscalYearEnd}-09-30`,
      },
    ],
  };

  if (agencyName) {
    filters.agencies = [
      {
        type: 'awarding',
        tier: 'toptier',
        name: agencyName,
      },
    ];
  }

  const response = await fetchWithCache<SpendingByCategoryResponse>(
    `${BASE_URL}/search/spending_by_category/cfda/`,
    {
      method: 'POST',
      body: JSON.stringify({
        filters,
        category: 'cfda',
        limit: 100,
        page: 1,
      }),
    }
  );

  return response.results.map((result) => ({
    id: result.code,
    cfda_number: result.code,
    cfda_title: result.name,
    agency_name: agencyName || '',
    award_type: 'direct_loan' as const,
    total_obligation: result.amount,
    total_face_value: result.amount,
    transaction_count: 0,
  }));
}

// Get spending by category for loan guarantees only
export async function getLoanGuaranteePrograms(
  agencyName?: string,
  fiscalYearStart: number = 2020,
  fiscalYearEnd: number = 2024
): Promise<Program[]> {
  const filters: SearchFilters = {
    award_type_codes: ['08'], // Loan guarantees only
    time_period: [
      {
        start_date: `${fiscalYearStart}-10-01`,
        end_date: `${fiscalYearEnd}-09-30`,
      },
    ],
  };

  if (agencyName) {
    filters.agencies = [
      {
        type: 'awarding',
        tier: 'toptier',
        name: agencyName,
      },
    ];
  }

  const response = await fetchWithCache<SpendingByCategoryResponse>(
    `${BASE_URL}/search/spending_by_category/cfda/`,
    {
      method: 'POST',
      body: JSON.stringify({
        filters,
        category: 'cfda',
        limit: 100,
        page: 1,
      }),
    }
  );

  return response.results.map((result) => ({
    id: result.code,
    cfda_number: result.code,
    cfda_title: result.name,
    agency_name: agencyName || '',
    award_type: 'loan_guarantee' as const,
    total_obligation: result.amount,
    total_face_value: result.amount,
    transaction_count: 0,
  }));
}

// Get time series data for a program
export async function getProgramTimeSeries(
  cfdaNumber: string,
  startYear: number = 2015,
  endYear: number = 2024
): Promise<{ fiscal_year: number; amount: number }[]> {
  const results: { fiscal_year: number; amount: number }[] = [];

  // Fetch data for each fiscal year
  for (let year = startYear; year <= endYear; year++) {
    const filters: SearchFilters = {
      award_type_codes: ['07', '08'],
      program_numbers: [cfdaNumber],
      time_period: [
        {
          start_date: `${year - 1}-10-01`,
          end_date: `${year}-09-30`,
        },
      ],
    };

    try {
      const response = await fetchWithCache<SpendingByCategoryResponse>(
        `${BASE_URL}/search/spending_by_category/cfda/`,
        {
          method: 'POST',
          body: JSON.stringify({
            filters,
            category: 'cfda',
            limit: 10,
            page: 1,
          }),
        }
      );

      const programData = response.results.find((r) => r.code === cfdaNumber);
      results.push({
        fiscal_year: year,
        amount: programData?.amount || 0,
      });
    } catch {
      results.push({
        fiscal_year: year,
        amount: 0,
      });
    }
  }

  return results;
}

// Get agencies that have loan programs
export async function getAgenciesWithLoanPrograms(): Promise<Agency[]> {
  // First get all agencies
  const agencies = await getAgencies();

  // Get all loan programs to see which agencies have them
  const filters: SearchFilters = {
    award_type_codes: ['07', '08'],
    time_period: [
      {
        start_date: '2020-10-01',
        end_date: '2024-09-30',
      },
    ],
  };

  const response = await fetchWithCache<SpendingByCategoryResponse>(
    `${BASE_URL}/search/spending_by_category/awarding_agency/`,
    {
      method: 'POST',
      body: JSON.stringify({
        filters,
        category: 'awarding_agency',
        limit: 100,
        page: 1,
      }),
    }
  );

  // Get the names of agencies with loan programs
  const agencyNamesWithLoans = new Set(
    response.results.map((r) => r.name.toLowerCase())
  );

  // Filter the full agency list
  return agencies.filter(
    (agency) =>
      agencyNamesWithLoans.has(agency.agency_name.toLowerCase()) ||
      agencyNamesWithLoans.has(agency.abbreviation?.toLowerCase() || '')
  );
}

// Clear the cache (useful for testing or forcing refresh)
export function clearCache(): void {
  cache.clear();
}
