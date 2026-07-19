import React from "react";
import {
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";

export default function SubmissionConfirmationScreen() {
  const { timesheetId, submittedAt, totalHours, status } =
    useLocalSearchParams<{
      timesheetId: string;
      submittedAt: string;
      totalHours: string;
      status: string;
    }>();
  const router = useRouter();

  const statusLabel =
    status === "submitted_fully_signed"
      ? "✓ Fully Signed"
      : "⚠ Submitted with Unsigned Entries";

  return (
    <ScrollView style={styles.container}>
      <View style={styles.successBanner}>
        <Text style={styles.successIcon}>✓</Text>
        <Text style={styles.successTitle}>Timesheet Submitted!</Text>
        <Text style={styles.successSub}>
          Your timesheet has been submitted successfully.
        </Text>
      </View>

      <View style={styles.card}>
        <View style={styles.row}>
          <Text style={styles.label}>Status</Text>
          <Text style={styles.value}>{statusLabel}</Text>
        </View>
        <View style={styles.row}>
          <Text style={styles.label}>Total Hours</Text>
          <Text style={styles.value}>{totalHours}h</Text>
        </View>
        {submittedAt && (
          <View style={styles.row}>
            <Text style={styles.label}>Submitted At</Text>
            <Text style={styles.value}>
              {new Date(decodeURIComponent(submittedAt)).toLocaleString()}
            </Text>
          </View>
        )}
      </View>

      <View style={styles.actions}>
        <TouchableOpacity
          style={styles.pdfButton}
          onPress={() => router.push(`/pdf/${timesheetId}`)}
        >
          <Text style={styles.buttonText}>📄 View PDF</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.primaryButton}
          onPress={() => router.replace("/timesheets/current")}
        >
          <Text style={styles.buttonText}>Return Home</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.secondaryButton}
          onPress={() => router.push("/timesheets/past")}
        >
          <Text style={styles.secondaryText}>View Past Timesheets</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f8f9fa" },
  successBanner: {
    backgroundColor: "#d4edda",
    padding: 32,
    alignItems: "center",
  },
  successIcon: { fontSize: 48, color: "#28a745", marginBottom: 8 },
  successTitle: {
    fontSize: 24,
    fontWeight: "700",
    color: "#155724",
    marginBottom: 4,
  },
  successSub: { fontSize: 15, color: "#155724", textAlign: "center" },
  card: {
    backgroundColor: "#fff",
    margin: 12,
    borderRadius: 8,
    padding: 16,
    gap: 2,
  },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: "#f0f0f0",
  },
  label: { fontSize: 14, color: "#6c757d" },
  value: {
    fontSize: 14,
    fontWeight: "600",
    color: "#212529",
    flex: 1,
    textAlign: "right",
  },
  actions: { padding: 12, gap: 8 },
  pdfButton: {
    backgroundColor: "#007bff",
    borderRadius: 8,
    padding: 14,
    alignItems: "center",
  },
  primaryButton: {
    backgroundColor: "#2c3e50",
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
  buttonText: { color: "#fff", fontSize: 16, fontWeight: "600" },
  secondaryText: { color: "#2c3e50", fontSize: 16, fontWeight: "600" },
});
