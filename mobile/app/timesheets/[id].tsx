import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { EntryRow } from "../../src/components/EntryRow";
import { TimesheetSummaryCard } from "../../src/components/TimesheetSummaryCard";
import { getTimesheet } from "../../src/api/timesheets";
import { WeeklyTimesheet } from "../../src/types";
import { formatLocalDateTime } from "../../src/utils/dates";
import { isTimesheetSubmitted } from "../../src/utils/timesheetReminders";

export default function TimesheetDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [timesheet, setTimesheet] = useState<WeeklyTimesheet | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) {
      return;
    }

    getTimesheet(Number(id))
      .then(setTimesheet)
      .catch(() => Alert.alert("Error", "Failed to load timesheet."))
      .finally(() => setLoading(false));
  }, [id]);

  const isSubmitted = timesheet ? isTimesheetSubmitted(timesheet) : false;
  const isWeekLocked = Boolean(timesheet?.is_week_locked);

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

  return (
    <ScrollView style={styles.container}>
      <TimesheetSummaryCard timesheet={timesheet} />
      {isSubmitted && (
        <View style={styles.submittedBanner}>
          <Text style={styles.submittedText}>
            ✓ Submitted {isWeekLocked ? "— Locked" : "— Editable Until Week Lock"}
          </Text>
          {timesheet.submitted_at && (
            <Text style={styles.submittedAt}>
              Submitted: {formatLocalDateTime(timesheet.submitted_at)}
            </Text>
          )}
        </View>
      )}
      {isSubmitted && (
        <TouchableOpacity
          style={styles.pdfButton}
          onPress={() => router.push(`/pdf/${timesheet.id}`)}
        >
          <Text style={styles.pdfButtonText}>📄 View PDF</Text>
        </TouchableOpacity>
      )}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Time Entries</Text>
        {timesheet.entries?.map((entry) => (
          <EntryRow
            key={entry.id}
            entry={entry}
            timesheetId={timesheet.id}
            isReadOnly={isWeekLocked}
          />
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f8f9fa" },
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
  submittedBanner: {
    backgroundColor: "#d4edda",
    padding: 12,
    margin: 12,
    borderRadius: 8,
  },
  submittedText: { fontSize: 15, fontWeight: "700", color: "#155724" },
  submittedAt: { fontSize: 12, color: "#155724", marginTop: 4 },
  pdfButton: {
    backgroundColor: "#007bff",
    margin: 12,
    borderRadius: 8,
    padding: 14,
    alignItems: "center",
  },
  pdfButtonText: { color: "#fff", fontSize: 16, fontWeight: "600" },
  section: { marginTop: 8 },
  sectionTitle: {
    fontSize: 16,
    fontWeight: "700",
    padding: 12,
    backgroundColor: "#f8f9fa",
  },
});
