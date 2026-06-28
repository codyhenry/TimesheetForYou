import client from './client';
import { FamilyHours, TimeEntry, TimesheetSubmission, WeeklyTimesheet } from '../types';

interface ApiParentSignature {
  id: number;
  image: string;
  signed_at: string;
  approved_snapshot?: {
    work_date?: string;
    start_time?: string;
    end_time?: string;
    total_hours?: string;
  };
}

interface ApiTimeEntry {
  id: number;
  work_date: string;
  family_name: string;
  start_time: string;
  end_time: string;
  total_hours: string | number;
  notes: string;
  signature_status: TimeEntry['signature_status'];
  has_signature: boolean;
  parent_signature?: ApiParentSignature;
}

interface ApiSubmission {
  id: number;
  submitted_at: string;
  total_hours: string | number;
  pdf_file: string;
  status: string;
}

interface ApiTimesheet {
  id: number;
  week_start_date: string;
  week_end_date: string;
  status: WeeklyTimesheet['status'];
  submitted_at: string | null;
  pdf_file?: string | null;
  entries?: ApiTimeEntry[];
  total_hours: string | number;
  signed_entry_count: number;
  unsigned_entry_count: number;
  total_hours_by_family: Array<{ family_name: string; total_hours: string | number }>;
  created_at?: string;
  updated_at?: string;
  admin_notes?: string;
  submission?: ApiSubmission | null;
}

const normalizeHours = (value: string | number) => String(value);
const normalizeTime = (value: string) => value.slice(0, 5);

const normalizeEntry = (entry: ApiTimeEntry): TimeEntry => ({
  id: entry.id,
  date: entry.work_date,
  family_name: entry.family_name,
  start_time: normalizeTime(entry.start_time),
  end_time: normalizeTime(entry.end_time),
  total_hours: normalizeHours(entry.total_hours),
  notes: entry.notes || '',
  signature_status: entry.signature_status,
  has_signature: entry.has_signature,
  signature: entry.parent_signature
    ? {
        id: entry.parent_signature.id,
        signature_image: entry.parent_signature.image,
        signed_at: entry.parent_signature.signed_at,
        approved_date: entry.parent_signature.approved_snapshot?.work_date || entry.work_date,
        approved_start_time: normalizeTime(entry.parent_signature.approved_snapshot?.start_time || entry.start_time),
        approved_end_time: normalizeTime(entry.parent_signature.approved_snapshot?.end_time || entry.end_time),
        approved_total_hours: normalizeHours(
          entry.parent_signature.approved_snapshot?.total_hours || entry.total_hours
        ),
      }
    : undefined,
});

const normalizeSubmission = (
  submission: ApiSubmission | null | undefined,
  timesheet: Pick<WeeklyTimesheet, 'signed_entry_count' | 'unsigned_entry_count'>
): TimesheetSubmission | null => {
  if (!submission) {
    return null;
  }
  return {
    id: submission.id,
    submitted_at: submission.submitted_at,
    total_hours: normalizeHours(submission.total_hours),
    signed_entry_count: timesheet.signed_entry_count,
    unsigned_entry_count: timesheet.unsigned_entry_count,
    pdf_file: submission.pdf_file,
    status: submission.status,
  };
};

export const normalizeTimesheet = (timesheet: ApiTimesheet): WeeklyTimesheet => {
  const total_hours_by_family: FamilyHours[] = (timesheet.total_hours_by_family || []).map((family) => ({
    family_name: family.family_name,
    total_hours: normalizeHours(family.total_hours),
  }));

  const normalized: WeeklyTimesheet = {
    id: timesheet.id,
    week_start_date: timesheet.week_start_date,
    week_end_date: timesheet.week_end_date,
    status: timesheet.status,
    submitted_at: timesheet.submitted_at,
    pdf_file: timesheet.pdf_file || timesheet.submission?.pdf_file || null,
    entries: timesheet.entries?.map(normalizeEntry),
    total_hours: normalizeHours(timesheet.total_hours),
    signed_entry_count: timesheet.signed_entry_count,
    unsigned_entry_count: timesheet.unsigned_entry_count,
    total_hours_by_family,
    created_at: timesheet.created_at,
    updated_at: timesheet.updated_at,
    admin_notes: timesheet.admin_notes,
    submission: null,
  };

  normalized.submission = normalizeSubmission(timesheet.submission, normalized);
  return normalized;
};

export const getCurrentTimesheet = async (): Promise<WeeklyTimesheet> => {
  const response = await client.get('/api/timesheets/current/');
  return normalizeTimesheet(response.data as ApiTimesheet);
};

export const listTimesheets = async (): Promise<WeeklyTimesheet[]> => {
  const response = await client.get('/api/timesheets/');
  return (response.data as ApiTimesheet[]).map(normalizeTimesheet);
};

export const getTimesheet = async (id: number): Promise<WeeklyTimesheet> => {
  const response = await client.get(`/api/timesheets/${id}/`);
  return normalizeTimesheet(response.data as ApiTimesheet);
};

export const submitTimesheet = async (id: number): Promise<WeeklyTimesheet> => {
  const response = await client.post(`/api/timesheets/${id}/submit/`);
  return normalizeTimesheet(response.data as ApiTimesheet);
};
