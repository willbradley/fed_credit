// Agency types from USAspending API
export interface Agency {
  agency_id: number;
  toptier_code: string;
  abbreviation: string;
  agency_name: string;
  congressional_justification_url: string | null;
  active_fy: string;
  active_fq: string;
  outlay_amount: number;
  obligated_amount: number;
  budget_authority_amount: number;
  current_total_budget_authority_amount: number;
  percentage_of_total_budget_authority: number;
  agency_slug: string;
}

// CFDA/Assistance Listing program
export interface Program {
  id: string;
  cfda_number: string;
  cfda_title: string;
  agency_name: string;
  award_type: 'direct_loan' | 'loan_guarantee';
  total_obligation: number;
  total_face_value: number;
  transaction_count: number;
}

// Program statistics from API
export interface ProgramStatistics {
  cfda_number: string;
  cfda_title: string;
  total_disbursements: number;
  total_face_value: number;
  total_subsidy_cost: number;
  award_count: number;
  fiscal_year_data: FiscalYearData[];
}

// Time series data for charts
export interface FiscalYearData {
  fiscal_year: number;
  disbursements: number;
  face_value: number;
  subsidy_cost: number;
  new_loans: number;
}

// Award record from spending_by_award endpoint
export interface Award {
  Award_ID: string;
  Recipient_Name: string;
  Start_Date: string;
  End_Date: string;
  Award_Amount: number;
  Total_Outlays: number;
  description: string;
  def_codes: string[];
  awarding_agency: string;
  awarding_sub_agency: string;
  Award_Type: string;
  recipient_id: string;
  prime_award_recipient_id: string;
  generated_internal_id: string;
}

// Spending by category result
export interface SpendingByCategory {
  id: number | null;
  code: string;
  name: string;
  amount: number;
}

// Federal Credit Supplement static data
export interface CreditSupplementProgram {
  cfda_number: string;
  program_name: string;
  agency_name: string;
  subsidy_rate: number;
  default_rate: number;
  average_maturity_years: number;
  grace_period_months: number;
  interest_rate_type: 'fixed' | 'variable' | 'mixed';
  cohort_data: CohortData[];
}

export interface CohortData {
  cohort_year: number;
  obligations: number;
  disbursements: number;
  unpaid_principal: number;
  subsidy_cost: number;
  default_amount: number;
}

// API response types
export interface AgencyListResponse {
  results: Agency[];
  messages?: string[];
}

export interface SpendingByCategoryResponse {
  category: string;
  results: SpendingByCategory[];
  limit: number;
  page_metadata: {
    page: number;
    next: number | null;
    previous: number | null;
    hasNext: boolean;
    hasPrevious: boolean;
    total: number;
  };
  messages?: string[];
}

export interface SpendingByAwardResponse {
  results: Award[];
  limit: number;
  page_metadata: {
    page: number;
    hasNext: boolean;
    hasPrevious: boolean;
    total: number;
  };
  messages?: string[];
}

// Filter types for API requests
export interface TimeFilter {
  start_date: string;
  end_date: string;
}

export interface AgencyFilter {
  type: 'awarding' | 'funding';
  tier: 'toptier' | 'subtier';
  name: string;
  toptier_name?: string;
}

export interface SearchFilters {
  award_type_codes?: string[];
  agencies?: AgencyFilter[];
  time_period?: TimeFilter[];
  program_numbers?: string[];
}

// App state types
export interface AppState {
  selectedAgency: Agency | null;
  selectedProgram: Program | null;
  searchQuery: string;
}
