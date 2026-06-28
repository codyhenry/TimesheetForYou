import client from './client';
import { TimeEntry } from '../types';

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

export interface CreateEntryData {
  date: string;
  family_name: string;
  start_time: string;
  end_time: string;
  notes?: string;
}

export interface UpdateEntryData extends Partial<CreateEntryData> {
  confirm_invalidate_signature?: boolean;
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

const toApiPayload = (data: Partial<CreateEntryData>) => ({
  ...(data.date ? { work_date: data.date } : {}),
  ...(data.family_name !== undefined ? { family_name: data.family_name } : {}),
  ...(data.start_time !== undefined ? { start_time: data.start_time } : {}),
  ...(data.end_time !== undefined ? { end_time: data.end_time } : {}),
  ...(data.notes !== undefined ? { notes: data.notes } : {}),
});

export const createEntry = async (timesheetId: number, data: CreateEntryData): Promise<TimeEntry> => {
  const response = await client.post(`/api/timesheets/${timesheetId}/entries/`, toApiPayload(data));
  return normalizeEntry(response.data as ApiTimeEntry);
};

export const listEntries = async (timesheetId: number): Promise<TimeEntry[]> => {
  const response = await client.get(`/api/timesheets/${timesheetId}/entries/`);
  return (response.data as ApiTimeEntry[]).map(normalizeEntry);
};

export const getEntry = async (id: number): Promise<TimeEntry> => {
  const response = await client.get(`/api/entries/${id}/`);
  return normalizeEntry(response.data as ApiTimeEntry);
};

export const updateEntry = async (id: number, data: UpdateEntryData): Promise<TimeEntry> => {
  const payload = {
    ...toApiPayload(data),
    ...(data.confirm_invalidate_signature !== undefined
      ? { confirm_invalidate_signature: data.confirm_invalidate_signature }
      : {}),
  };
  const response = await client.patch(`/api/entries/${id}/`, payload);
  return normalizeEntry(response.data as ApiTimeEntry);
};

export const deleteEntry = async (id: number): Promise<void> => {
  await client.delete(`/api/entries/${id}/`);
};
