export interface User {
  id: number;
  name?: string;
  email: string;
  role: 'nanny' | 'admin';
  username: string;
  first_name: string;
  last_name: string;
  phone?: string;
  is_staff?: boolean;
}

export interface FamilyHours {
  family_name: string;
  total_hours: string;
}

export type TimesheetStatus =
  | 'draft'
  | 'partially_signed'
  | 'fully_signed'
  | 'submitted_with_unsigned_entries'
  | 'submitted_fully_signed';

export type SignatureStatus = 'unsigned' | 'signed' | 'signature_invalidated';

export interface TimeEntrySignature {
  id: number;
  signature_image: string;
  signed_at: string;
  approved_date: string;
  approved_start_time: string;
  approved_end_time: string;
  approved_total_hours: string;
  approved_family_requested_nanny?: boolean;
}

export interface TimeEntry {
  id: number;
  date: string;
  family_name: string;
  start_time: string;
  end_time: string;
  total_hours: string;
  notes: string;
  family_requested_nanny: boolean;
  signature_status: SignatureStatus;
  has_signature: boolean;
  signature?: TimeEntrySignature;
}

export interface TimesheetSubmission {
  id: number;
  submitted_at: string;
  total_hours: string;
  signed_entry_count: number;
  unsigned_entry_count: number;
  pdf_file: string;
  status: string;
}

export interface RequestIncentiveEntry {
  request_number: number;
  entry_id: number;
  timesheet_id: number;
  work_date: string;
  family_name: string;
  week_start_date: string;
  week_end_date: string;
}

export interface RequestIncentiveGroup {
  incentive_number: number;
  milestone_request_number: number;
  milestone_entry_id: number;
  entries: RequestIncentiveEntry[];
}

export interface WeeklyTimesheet {
  id: number;
  week_start_date: string;
  week_end_date: string;
  status: TimesheetStatus;
  submitted_at: string | null;
  pdf_file: string | null;
  entries?: TimeEntry[];
  total_hours: string;
  signed_entry_count: number;
  unsigned_entry_count: number;
  requested_entry_count: number;
  request_incentive_count: number;
  lifetime_requested_entry_count: number;
  requests_until_next_incentive: number;
  request_incentive_groups?: RequestIncentiveGroup[];
  is_week_locked?: boolean;
  total_hours_by_family: FamilyHours[];
  created_at?: string;
  updated_at?: string;
  admin_notes?: string;
  submission?: TimesheetSubmission | null;
}
