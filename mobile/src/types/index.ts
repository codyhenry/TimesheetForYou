export interface User {
  id: number;
  name?: string;
  email: string;
  role: 'nanny' | 'office' | 'admin';
  username: string;
  first_name: string;
  last_name: string;
  phone?: string;
  is_active?: boolean;
  is_staff?: boolean;
  force_password_change?: boolean;
  can_access_dashboard?: boolean;
  can_access_django_admin?: boolean;
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
  submitted_at?: string;
  total_hours: string;
  signed_entry_count: number;
  unsigned_entry_count: number;
  requested_entry_count: number;
  request_incentive_count: number;
  lifetime_requested_entry_count: number;
  requests_until_next_incentive: number;
  request_incentive_groups?: RequestIncentiveGroup[];
  is_late_submission?: boolean;
  late_submission_note?: string;
  is_week_locked?: boolean;
  admin_notes?: string;
  entries?: TimeEntry[];
  submission?: TimesheetSubmission;
}
