import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { WeeklyTimesheet } from '../types';
import { formatWeekRange } from '../utils/dates';

interface Props {
  timesheet: WeeklyTimesheet;
}

export const TimesheetSummaryCard: React.FC<Props> = ({ timesheet }) => {
  return (
    <View style={styles.card}>
      <Text style={styles.weekRange}>
        {formatWeekRange(timesheet.week_start_date, timesheet.week_end_date)}
      </Text>
      <View style={styles.stats}>
        <View style={styles.stat}>
          <Text style={styles.statValue}>{timesheet.total_hours}h</Text>
          <Text style={styles.statLabel}>Total Hours</Text>
        </View>
        <View style={styles.stat}>
          <Text style={[styles.statValue, styles.signed]}>{timesheet.signed_entry_count}</Text>
          <Text style={styles.statLabel}>Signed</Text>
        </View>
        <View style={styles.stat}>
          <Text
            style={[
              styles.statValue,
              timesheet.unsigned_entry_count > 0 ? styles.unsigned : styles.signed,
            ]}
          >
            {timesheet.unsigned_entry_count}
          </Text>
          <Text style={styles.statLabel}>Unsigned</Text>
        </View>
      </View>

      <View style={styles.incentiveBox}>
        <Text style={styles.incentiveTitle}>Family Request Incentives</Text>
        <Text style={styles.incentiveText}>
          {timesheet.lifetime_requested_entry_count} lifetime requested{' '}
          {timesheet.lifetime_requested_entry_count === 1 ? 'day' : 'days'}.
        </Text>
        {timesheet.request_incentive_count > 0 ? (
          <Text style={styles.incentiveEarned}>
            🎁 This timesheet earned {timesheet.request_incentive_count}{' '}
            {timesheet.request_incentive_count === 1 ? 'incentive' : 'incentives'}.
          </Text>
        ) : (
          <Text style={styles.incentiveText}>
            {timesheet.requests_until_next_incentive} more requested{' '}
            {timesheet.requests_until_next_incentive === 1 ? 'day' : 'days'} until your next incentive.
          </Text>
        )}
      </View>

      {timesheet.total_hours_by_family?.length > 0 && (
        <View style={styles.families}>
          {timesheet.total_hours_by_family.map((fam) => (
            <View key={fam.family_name} style={styles.familyRow}>
              <Text style={styles.familyName}>{fam.family_name}</Text>
              <Text style={styles.familyHours}>{fam.total_hours}h</Text>
            </View>
          ))}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 16,
    margin: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  weekRange: { fontSize: 18, fontWeight: '700', marginBottom: 12 },
  stats: { flexDirection: 'row', justifyContent: 'space-around', marginBottom: 12 },
  stat: { alignItems: 'center' },
  statValue: { fontSize: 24, fontWeight: '700' },
  statLabel: { fontSize: 12, color: '#6c757d' },
  signed: { color: '#28a745' },
  unsigned: { color: '#dc3545' },
  incentiveBox: {
    borderTopWidth: 1,
    borderTopColor: '#e9ecef',
    paddingTop: 10,
    marginBottom: 10,
    gap: 2,
  },
  incentiveTitle: { fontSize: 14, fontWeight: '700', color: '#212529' },
  incentiveText: { fontSize: 13, color: '#495057', lineHeight: 18 },
  incentiveEarned: { fontSize: 13, color: '#856404', fontWeight: '700', lineHeight: 18 },
  families: { borderTopWidth: 1, borderTopColor: '#e9ecef', paddingTop: 8 },
  familyRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 4 },
  familyName: { fontSize: 14, color: '#495057' },
  familyHours: { fontSize: 14, fontWeight: '600' },
});
