import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { TimeEntry } from '../types';
import { SignatureStatusBadge } from './SignatureStatusBadge';
import { formatDate, formatTime } from '../utils/dates';
import { useRouter } from 'expo-router';

interface Props {
  entry: TimeEntry;
  timesheetId: number;
  isReadOnly?: boolean;
}

export const EntryRow: React.FC<Props> = ({ entry }) => {
  const router = useRouter();

  return (
    <TouchableOpacity style={styles.row} onPress={() => router.push(`/entries/${entry.id}`)}>
      <View style={styles.left}>
        <Text style={styles.date}>{formatDate(entry.date)}</Text>
        <Text style={styles.family}>{entry.family_name}</Text>
        <Text style={styles.times}>
          {formatTime(entry.start_time)} – {formatTime(entry.end_time)}
        </Text>
      </View>
      <View style={styles.right}>
        <Text style={styles.hours}>{entry.total_hours}h</Text>
        <SignatureStatusBadge status={entry.signature_status} />
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 12,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e9ecef',
  },
  left: { flex: 1 },
  right: { alignItems: 'flex-end', gap: 4 },
  date: { fontSize: 13, color: '#6c757d', marginBottom: 2 },
  family: { fontSize: 15, fontWeight: '600', marginBottom: 2 },
  times: { fontSize: 13, color: '#495057' },
  hours: { fontSize: 16, fontWeight: '700', color: '#212529' },
});
