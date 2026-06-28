import React, { useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  FlatList,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { listTimesheets } from '../../src/api/timesheets';
import { WeeklyTimesheet } from '../../src/types';
import { formatWeekRange, getCurrentWeekRange } from '../../src/utils/dates';

export default function PastTimesheetsScreen() {
  const [timesheets, setTimesheets] = useState<WeeklyTimesheet[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    listTimesheets()
      .then(setTimesheets)
      .catch(() => Alert.alert('Error', 'Failed to load timesheets.'))
      .finally(() => setLoading(false));
  }, []);

  const pastTimesheets = useMemo(() => {
    const currentWeek = getCurrentWeekRange();
    return timesheets.filter(
      (item) =>
        !(item.week_start_date === currentWeek.start && item.week_end_date === currentWeek.end)
    );
  }, [timesheets]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'submitted_fully_signed':
        return '✓ Fully Signed';
      case 'submitted_with_unsigned_entries':
        return '⚠ Has Unsigned';
      case 'fully_signed':
        return 'Fully Signed (Draft)';
      case 'partially_signed':
        return 'Partially Signed';
      default:
        return 'Draft';
    }
  };

  return (
    <View style={styles.container}>
      <FlatList
        data={pastTimesheets}
        keyExtractor={(item) => item.id.toString()}
        renderItem={({ item }) => (
          <TouchableOpacity style={styles.item} onPress={() => router.push(`/timesheets/${item.id}`)}>
            <View style={styles.left}>
              <Text style={styles.weekRange}>{formatWeekRange(item.week_start_date, item.week_end_date)}</Text>
              <Text style={styles.status}>{getStatusLabel(item.status)}</Text>
            </View>
            <View style={styles.right}>
              <Text style={styles.hours}>{item.total_hours}h</Text>
              {item.unsigned_entry_count > 0 && (
                <Text style={styles.unsigned}>{item.unsigned_entry_count} unsigned</Text>
              )}
            </View>
          </TouchableOpacity>
        )}
        ListEmptyComponent={<Text style={styles.empty}>No past timesheets found.</Text>}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8f9fa' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  item: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e9ecef',
  },
  left: { flex: 1 },
  right: { alignItems: 'flex-end' },
  weekRange: { fontSize: 16, fontWeight: '600', marginBottom: 4 },
  status: { fontSize: 13, color: '#6c757d' },
  hours: { fontSize: 18, fontWeight: '700' },
  unsigned: { fontSize: 12, color: '#dc3545', marginTop: 2 },
  empty: { textAlign: 'center', color: '#6c757d', padding: 40 },
});
