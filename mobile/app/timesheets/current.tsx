import React, { useCallback, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import { EntryRow } from "../../src/components/EntryRow";
import { TimesheetSummaryCard } from "../../src/components/TimesheetSummaryCard";
import { useAuth } from "../../src/context/AuthContext";
import { getCurrentTimesheet } from "../../src/api/timesheets";
import { WeeklyTimesheet } from "../../src/types";

export default function CurrentTimesheetScreen() {
  const [timesheet, setTimesheet] = useState<WeeklyTimesheet | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const router = useRouter();
  const { user, loading: authLoading, logout } = useAuth();

  const fetchTimesheet = async () => {
    try {
      const data = await getCurrentTimesheet();
      setTimesheet(data);
    } catch (error: any) {
      if (error.response?.status === 403) {
        Alert.alert("Error", "You do not have permission to view timesheets.");
      } else {
        Alert.alert("Error", "Failed to load timesheet. Please try again.");
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useFocusEffect(
    useCallback(() => {
      if (authLoading || !user) {
        setLoading(false);
        setRefreshing(false);
        return;
      }

      setLoading(true);
      void fetchTimesheet();
    }, [authLoading, user]),
  );

  const onRefresh = () => {
    setRefreshing(true);
    void fetchTimesheet();
  };

  const isSubmitted =
    timesheet?.status === "submitted_with_unsigned_entries" ||
    timesheet?.status === "submitted_fully_signed";

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  if (!timesheet) {
    return (
      <View style={styles.container}>
        <View style={styles.center}>
          <Text style={styles.emptyText}>
            Unable to load the current timesheet.
          </Text>
        </View>
        <View style={styles.footer}>
          <TouchableOpacity
            style={styles.secondaryButton}
            onPress={() => router.push("/timesheets/past")}
          >
            <Text style={styles.secondaryButtonText}>Past Timesheets</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.logoutButton}
            onPress={() => void logout()}
          >
            <Text style={styles.logoutText}>Log Out</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        <TimesheetSummaryCard timesheet={timesheet} />

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Time Entries</Text>
          {timesheet.entries?.length === 0 && (
            <Text style={styles.emptyText}>
              No entries yet. Add your first time entry.
            </Text>
          )}
          {timesheet.entries?.map((entry) => (
            <EntryRow
              key={entry.id}
              entry={entry}
              timesheetId={timesheet.id}
              isReadOnly={isSubmitted}
            />
          ))}
        </View>
      </ScrollView>

      <View style={styles.footer}>
        {!isSubmitted && (
          <>
            <TouchableOpacity
              style={styles.primaryButton}
              onPress={() =>
                router.push(`/entries/new?timesheetId=${timesheet.id}`)
              }
            >
              <Text style={styles.buttonText}>+ Add Time Entry</Text>
            </TouchableOpacity>
            {(timesheet.entries?.length ?? 0) > 0 && (
              <TouchableOpacity
                style={styles.submitButton}
                onPress={() => router.push(`/submit/${timesheet.id}`)}
              >
                <Text style={styles.buttonText}>Submit Timesheet</Text>
              </TouchableOpacity>
            )}
          </>
        )}
        {isSubmitted && (
          <TouchableOpacity
            style={styles.pdfButton}
            onPress={() => router.push(`/pdf/${timesheet.id}`)}
          >
            <Text style={styles.buttonText}>📄 View PDF</Text>
          </TouchableOpacity>
        )}
        <TouchableOpacity
          style={styles.secondaryButton}
          onPress={() => router.push("/timesheets/past")}
        >
          <Text style={styles.secondaryButtonText}>Past Timesheets</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.logoutButton}
          onPress={() => void logout()}
        >
          <Text style={styles.logoutText}>Log Out</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f8f9fa" },
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
  section: { marginTop: 8 },
  sectionTitle: {
    fontSize: 16,
    fontWeight: "700",
    padding: 12,
    color: "#212529",
    backgroundColor: "#f8f9fa",
  },
  emptyText: { textAlign: "center", color: "#6c757d", padding: 24 },
  footer: {
    padding: 12,
    gap: 8,
    backgroundColor: "#fff",
    borderTopWidth: 1,
    borderTopColor: "#e9ecef",
  },
  primaryButton: {
    backgroundColor: "#2c3e50",
    borderRadius: 8,
    padding: 14,
    alignItems: "center",
  },
  submitButton: {
    backgroundColor: "#28a745",
    borderRadius: 8,
    padding: 14,
    alignItems: "center",
  },
  pdfButton: {
    backgroundColor: "#007bff",
    borderRadius: 8,
    padding: 14,
    alignItems: "center",
  },
  secondaryButton: {
    borderWidth: 1,
    borderColor: "#2c3e50",
    borderRadius: 8,
    padding: 14,
    alignItems: "center",
  },
  logoutButton: { padding: 10, alignItems: "center" },
  buttonText: { color: "#fff", fontSize: 16, fontWeight: "600" },
  secondaryButtonText: { color: "#2c3e50", fontSize: 16, fontWeight: "600" },
  logoutText: { color: "#6c757d", fontSize: 14 },
});
