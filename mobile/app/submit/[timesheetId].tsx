import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { getTimesheet, submitTimesheet } from '../../src/api/timesheets';
import { WeeklyTimesheet } from '../../src/types';
import { formatWeekRange } from '../../src/utils/dates';

export default function SubmitTimesheetScreen() {
  const { timesheetId } = useLocalSearchParams<{ timesheetId: string }>();
  const router = useRouter();
  const [timesheet, setTimesheet] = useState<WeeklyTimesheet | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!timesheetId) {
      return;
    }

    getTimesheet(Number(timesheetId))
      .then(setTimesheet)
      .catch(() => Alert.alert('Error', 'Failed to load timesheet.'))
      .finally(() => setLoading(false));
  }, [timesheetId]);

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const result = await submitTimesheet(Number(timesheetId));
      router.replace(
        `/submit/confirmation?timesheetId=${timesheetId}&submittedAt=${encodeURIComponent(
          result.submitted_at || new Date().toISOString()
        )}&totalHours=${result.total_hours}&status=${result.status}`
      );
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Failed to submit timesheet. Please try again.';
      Alert.alert('Submission Error', message);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  if (!timesheet) {
    return (
      <View style={styles.center}>
        <Text>Timesheet not found.</Text>
      </View>
    );
  }

  const hasUnsigned = timesheet.unsigned_entry_count > 0;

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Submit Timesheet</Text>
        <Text style={styles.weekRange}>{formatWeekRange(timesheet.week_start_date, timesheet.week_end_date)}</Text>
      </View>

      <View style={styles.card}>
        <View style={styles.row}>
          <Text style={styles.label}>Total Hours</Text>
          <Text style={styles.value}>{timesheet.total_hours}h</Text>
        </View>
        <View style={styles.row}>
          <Text style={styles.label}>Signed Entries</Text>
          <Text style={[styles.value, styles.green]}>{timesheet.signed_entry_count}</Text>
        </View>
        <View style={styles.row}>
          <Text style={styles.label}>Unsigned Entries</Text>
          <Text style={[styles.value, hasUnsigned ? styles.red : styles.green]}>{timesheet.unsigned_entry_count}</Text>
        </View>
      </View>

      {timesheet.total_hours_by_family?.length > 0 && (
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Hours by Family</Text>
          {timesheet.total_hours_by_family.map((fam) => (
            <View key={fam.family_name} style={styles.row}>
              <Text style={styles.label}>{fam.family_name}</Text>
              <Text style={styles.value}>{fam.total_hours}h</Text>
            </View>
          ))}
        </View>
      )}

      {hasUnsigned && (
        <View style={styles.warningCard}>
          <Text style={styles.warningTitle}>⚠ Unsigned Entries</Text>
          <Text style={styles.warningText}>
            This timesheet contains {timesheet.unsigned_entry_count} unsigned{' '}
            {timesheet.unsigned_entry_count === 1 ? 'entry' : 'entries'}.
          </Text>
          <Text style={styles.warningText}>
            Unsigned entries will be visible to the company and marked as UNSIGNED on the PDF.
          </Text>
        </View>
      )}

      <View style={styles.actions}>
        {hasUnsigned && (
          <TouchableOpacity style={styles.reviewButton} onPress={() => router.back()}>
            <Text style={styles.reviewText}>Review Entries First</Text>
          </TouchableOpacity>
        )}
        <TouchableOpacity style={styles.submitButton} onPress={handleSubmit} disabled={submitting}>
          {submitting ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>{hasUnsigned ? 'Submit Anyway' : 'Submit Timesheet'}</Text>
          )}
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8f9fa' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: { padding: 20, backgroundColor: '#fff', borderBottomWidth: 1, borderBottomColor: '#e9ecef' },
  title: { fontSize: 22, fontWeight: '700', color: '#212529', marginBottom: 4 },
  weekRange: { fontSize: 15, color: '#6c757d' },
  card: { backgroundColor: '#fff', margin: 12, borderRadius: 8, padding: 16, gap: 2 },
  sectionTitle: { fontSize: 16, fontWeight: '700', marginBottom: 8 },
  row: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 6, borderBottomWidth: 1, borderBottomColor: '#f0f0f0' },
  label: { fontSize: 15, color: '#6c757d' },
  value: { fontSize: 15, fontWeight: '600', color: '#212529' },
  green: { color: '#28a745' },
  red: { color: '#dc3545' },
  warningCard: {
    backgroundColor: '#fff3cd',
    margin: 12,
    borderRadius: 8,
    padding: 16,
    borderLeftWidth: 4,
    borderLeftColor: '#ffc107',
  },
  warningTitle: { fontSize: 16, fontWeight: '700', color: '#856404', marginBottom: 8 },
  warningText: { fontSize: 14, color: '#856404', lineHeight: 20, marginBottom: 4 },
  actions: { padding: 12, gap: 8 },
  submitButton: { backgroundColor: '#28a745', borderRadius: 8, padding: 14, alignItems: 'center' },
  reviewButton: { borderWidth: 1, borderColor: '#2c3e50', borderRadius: 8, padding: 14, alignItems: 'center' },
  buttonText: { color: '#fff', fontSize: 16, fontWeight: '600' },
  reviewText: { color: '#2c3e50', fontSize: 16, fontWeight: '600' },
});
