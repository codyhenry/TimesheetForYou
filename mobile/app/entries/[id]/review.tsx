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
import { getEntry } from "../../../src/api/entries";
import { TimeEntry } from "../../../src/types";
import { formatDateLong, formatTime } from "../../../src/utils/dates";

export default function ParentReviewScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [entry, setEntry] = useState<TimeEntry | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) {
      return;
    }

    getEntry(Number(id))
      .then(setEntry)
      .catch(() => Alert.alert("Error", "Failed to load entry."))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  if (!entry) {
    return (
      <View style={styles.center}>
        <Text>Entry not found.</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.card}>
        <Text style={styles.heading}>
          Please review this time entry before signing.
        </Text>

        <View style={styles.divider} />

        <View style={styles.row}>
          <Text style={styles.fieldLabel}>Family</Text>
          <Text style={styles.fieldValue}>{entry.family_name}</Text>
        </View>
        <View style={styles.row}>
          <Text style={styles.fieldLabel}>Date</Text>
          <Text style={styles.fieldValue}>{formatDateLong(entry.date)}</Text>
        </View>
        <View style={styles.row}>
          <Text style={styles.fieldLabel}>Start</Text>
          <Text style={styles.fieldValue}>{formatTime(entry.start_time)}</Text>
        </View>
        <View style={styles.row}>
          <Text style={styles.fieldLabel}>End</Text>
          <Text style={styles.fieldValue}>{formatTime(entry.end_time)}</Text>
        </View>
        <View style={styles.row}>
          <Text style={styles.fieldLabel}>Total Hours</Text>
          <Text style={[styles.fieldValue, styles.bold]}>
            {entry.total_hours} hours
          </Text>
        </View>

        <View style={styles.divider} />

        <Text style={styles.confirmText}>
          By signing, you confirm this time entry is accurate.
        </Text>
      </View>

      <View style={styles.actions}>
        <TouchableOpacity
          style={styles.continueButton}
          onPress={() => router.push(`/entries/${id}/signature`)}
        >
          <Text style={styles.buttonText}>Continue to Signature</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.cancelButton}
          onPress={() => router.back()}
        >
          <Text style={styles.cancelText}>Back</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f8f9fa" },
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
  card: { backgroundColor: "#fff", margin: 16, borderRadius: 8, padding: 20 },
  heading: {
    fontSize: 16,
    fontWeight: "600",
    color: "#212529",
    marginBottom: 16,
    lineHeight: 24,
  },
  divider: { height: 1, backgroundColor: "#dee2e6", marginVertical: 12 },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 8,
  },
  fieldLabel: { fontSize: 15, color: "#6c757d", fontWeight: "600" },
  fieldValue: {
    fontSize: 15,
    color: "#212529",
    flexShrink: 1,
    textAlign: "right",
  },
  bold: { fontWeight: "700" },
  confirmText: {
    fontSize: 14,
    color: "#6c757d",
    fontStyle: "italic",
    lineHeight: 20,
  },
  actions: { padding: 16, gap: 10 },
  continueButton: {
    backgroundColor: "#2c3e50",
    borderRadius: 8,
    padding: 14,
    alignItems: "center",
  },
  cancelButton: {
    borderWidth: 1,
    borderColor: "#6c757d",
    borderRadius: 8,
    padding: 14,
    alignItems: "center",
  },
  buttonText: { color: "#fff", fontSize: 16, fontWeight: "600" },
  cancelText: { color: "#6c757d", fontSize: 16, fontWeight: "600" },
});
