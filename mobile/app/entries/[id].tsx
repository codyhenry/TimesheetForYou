import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Image,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { deleteEntry, getEntry, updateEntry } from "../../src/api/entries";
import { FamilyNameInput } from "../../src/components/FamilyNameInput";
import { SignatureStatusBadge } from "../../src/components/SignatureStatusBadge";
import { TimeInput } from "../../src/components/TimeInput";
import { TimeEntry } from "../../src/types";
import { formatDateLong, formatTime } from "../../src/utils/dates";
import { calculateHoursPreview } from "../../src/utils/hours";

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || "http://localhost:8000";

export default function EntryDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [entry, setEntry] = useState<TimeEntry | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [familyName, setFamilyName] = useState("");
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [notes, setNotes] = useState("");
  const [familyRequestedNanny, setFamilyRequestedNanny] = useState(false);

  useEffect(() => {
    if (!id) {
      return;
    }

    getEntry(Number(id))
      .then((data) => {
        setEntry(data);
        setFamilyName(data.family_name);
        setStartTime(data.start_time);
        setEndTime(data.end_time);
        setNotes(data.notes);
        setFamilyRequestedNanny(data.family_requested_nanny);
      })
      .catch(() => Alert.alert("Error", "Failed to load entry."))
      .finally(() => setLoading(false));
  }, [id]);

  const handleEdit = () => {
    if (entry?.signature_status === "signed") {
      Alert.alert(
        "Edit Signed Entry",
        "Editing this entry will invalidate the parent signature. The parent will need to sign again.",
        [
          { text: "Cancel", style: "cancel" },
          { text: "Edit Anyway", onPress: () => setEditing(true) },
        ],
      );
    } else {
      setEditing(true);
    }
  };

  const handleSave = async () => {
    if (!familyName.trim()) {
      Alert.alert("Error", "Family name is required.");
      return;
    }
    if (!calculateHoursPreview(startTime, endTime)) {
      Alert.alert("Error", "End time must be after start time.");
      return;
    }

    setSaving(true);
    try {
      const isSigned = entry?.signature_status === "signed";
      const updated = await updateEntry(Number(id), {
        family_name: familyName.trim(),
        start_time: startTime,
        end_time: endTime,
        notes: notes.trim(),
        family_requested_nanny: familyRequestedNanny,
        ...(isSigned ? { confirm_invalidate_signature: true } : {}),
      });
      setEntry(updated);
      setEditing(false);
    } catch (error: any) {
      const data = error.response?.data;
      const message = data
        ? Object.values(data).flat().join("\n")
        : "Failed to save entry.";
      Alert.alert("Error", message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = () => {
    Alert.alert("Delete Entry", "Are you sure you want to delete this entry?", [
      { text: "Cancel", style: "cancel" },
      {
        text: "Delete",
        style: "destructive",
        onPress: async () => {
          try {
            await deleteEntry(Number(id));
            router.back();
          } catch (error: any) {
            Alert.alert(
              "Error",
              error.response?.data?.detail || "Failed to delete entry.",
            );
          }
        },
      },
    ]);
  };

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

  const hoursPreview = calculateHoursPreview(startTime, endTime);

  return (
    <ScrollView style={styles.container}>
      <View style={styles.card}>
        <View style={styles.row}>
          <Text style={styles.label}>Date</Text>
          <Text style={styles.value}>{formatDateLong(entry.date)}</Text>
        </View>

        {editing ? (
          <>
            <FamilyNameInput value={familyName} onChange={setFamilyName} />
            <View style={styles.requestRow}>
              <View style={styles.requestCopy}>
                <Text style={styles.requestTitle}>Requested by family</Text>
                <Text style={styles.helpText}>
                  Turn this on when the family specifically requested you for this day.
                </Text>
              </View>
              <Switch
                value={familyRequestedNanny}
                onValueChange={setFamilyRequestedNanny}
              />
            </View>
            <TimeInput
              label="Start Time"
              value={startTime}
              onChange={setStartTime}
            />
            <TimeInput label="End Time" value={endTime} onChange={setEndTime} />
            {hoursPreview && (
              <View style={styles.previewBox}>
                <Text style={styles.previewText}>
                  Preview: {hoursPreview} hours
                </Text>
              </View>
            )}
            <Text style={styles.label}>Notes</Text>
            <Text style={styles.helpText}>Notes are visible to admins.</Text>
            <TextInput
              style={[styles.input, styles.textarea]}
              value={notes}
              onChangeText={setNotes}
              multiline
              numberOfLines={3}
            />
          </>
        ) : (
          <>
            <View style={styles.row}>
              <Text style={styles.label}>Family</Text>
              <Text style={styles.value}>{entry.family_name}</Text>
            </View>
            <View style={styles.row}>
              <Text style={styles.label}>Requested by Family</Text>
              <Text style={[styles.value, entry.family_requested_nanny ? styles.bold : null]}>
                {entry.family_requested_nanny ? "Yes" : "No"}
              </Text>
            </View>
            <View style={styles.row}>
              <Text style={styles.label}>Start</Text>
              <Text style={styles.value}>{formatTime(entry.start_time)}</Text>
            </View>
            <View style={styles.row}>
              <Text style={styles.label}>End</Text>
              <Text style={styles.value}>{formatTime(entry.end_time)}</Text>
            </View>
            <View style={styles.row}>
              <Text style={styles.label}>Total Hours</Text>
              <Text style={[styles.value, styles.bold]}>
                {entry.total_hours}h
              </Text>
            </View>
            {entry.notes ? (
              <View style={styles.row}>
                <Text style={styles.label}>Notes</Text>
                <Text style={styles.value}>{entry.notes}</Text>
              </View>
            ) : null}
          </>
        )}

        <View style={styles.signatureRow}>
          <Text style={styles.label}>Signature Status</Text>
          <SignatureStatusBadge status={entry.signature_status} />
        </View>

        {entry.has_signature && entry.signature && !editing && (
          <View style={styles.signatureImageContainer}>
            <Text style={styles.label}>Parent Signature</Text>
            <Image
              source={{
                uri: entry.signature.signature_image.startsWith("http")
                  ? entry.signature.signature_image
                  : `${API_BASE_URL}${entry.signature.signature_image}`,
              }}
              style={styles.signatureImage}
              resizeMode="contain"
            />
          </View>
        )}
      </View>

      <View style={styles.actions}>
        <TouchableOpacity
          style={styles.homeButton}
          onPress={() => router.replace("/timesheets/current")}
        >
          <Text style={styles.homeText}>Home</Text>
        </TouchableOpacity>

        {editing ? (
          <>
            <TouchableOpacity
              style={styles.saveButton}
              onPress={handleSave}
              disabled={saving}
            >
              {saving ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.buttonText}>Save Changes</Text>
              )}
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.cancelButton}
              onPress={() => setEditing(false)}
            >
              <Text style={styles.cancelText}>Cancel</Text>
            </TouchableOpacity>
          </>
        ) : (
          <>
            <TouchableOpacity
              style={styles.backButton}
              onPress={() => router.back()}
            >
              <Text style={styles.backText}>Back</Text>
            </TouchableOpacity>
            {entry.signature_status !== "signed" && (
              <TouchableOpacity
                style={styles.signButton}
                onPress={() => router.push(`/entries/${entry.id}/review`)}
              >
                <Text style={styles.buttonText}>Get Parent Signature</Text>
              </TouchableOpacity>
            )}
            <TouchableOpacity style={styles.editButton} onPress={handleEdit}>
              <Text style={styles.buttonText}>Edit Entry</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.deleteButton}
              onPress={handleDelete}
            >
              <Text style={styles.buttonText}>Delete Entry</Text>
            </TouchableOpacity>
          </>
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f8f9fa" },
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
  card: {
    backgroundColor: "#fff",
    margin: 12,
    borderRadius: 8,
    padding: 16,
    gap: 8,
  },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 6,
    borderBottomWidth: 1,
    borderBottomColor: "#f0f0f0",
  },
  signatureRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 6,
  },
  label: { fontSize: 14, color: "#6c757d", fontWeight: "600" },
  value: { fontSize: 15, color: "#212529", flexShrink: 1, textAlign: "right" },
  bold: { fontWeight: "700" },
  input: {
    borderWidth: 1,
    borderColor: "#ced4da",
    borderRadius: 6,
    padding: 10,
    fontSize: 16,
    backgroundColor: "#fff",
    marginBottom: 8,
  },
  textarea: { height: 80, textAlignVertical: "top" },
  helpText: { color: "#6c757d", fontSize: 12, lineHeight: 18, marginBottom: 8 },
  requestRow: {
    backgroundColor: "#fff",
    borderWidth: 1,
    borderColor: "#ced4da",
    borderRadius: 6,
    padding: 12,
    marginBottom: 8,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12,
  },
  requestCopy: { flex: 1 },
  requestTitle: { fontSize: 15, fontWeight: "700", color: "#212529", marginBottom: 2 },
  previewBox: {
    backgroundColor: "#d4edda",
    borderRadius: 6,
    padding: 10,
    marginBottom: 8,
  },
  previewText: { color: "#155724", fontWeight: "600" },
  signatureImageContainer: { marginTop: 8 },
  signatureImage: {
    width: "100%",
    height: 120,
    borderWidth: 1,
    borderColor: "#dee2e6",
    borderRadius: 4,
  },
  actions: { padding: 12, gap: 8 },
  homeButton: {
    borderWidth: 1,
    borderColor: "#2c3e50",
    borderRadius: 8,
    padding: 14,
    alignItems: "center",
    backgroundColor: "#fff",
  },
  homeText: { color: "#2c3e50", fontSize: 16, fontWeight: "600" },
  backButton: {
    borderWidth: 1,
    borderColor: "#6c757d",
    borderRadius: 8,
    padding: 14,
    alignItems: "center",
    backgroundColor: "#fff",
  },
  backText: { color: "#6c757d", fontSize: 16, fontWeight: "600" },
  signButton: {
    backgroundColor: "#28a745",
    borderRadius: 8,
    padding: 14,
    alignItems: "center",
  },
  editButton: {
    backgroundColor: "#2c3e50",
    borderRadius: 8,
    padding: 14,
    alignItems: "center",
  },
  saveButton: {
    backgroundColor: "#28a745",
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
  deleteButton: {
    backgroundColor: "#dc3545",
    borderRadius: 8,
    padding: 14,
    alignItems: "center",
  },
  buttonText: { color: "#fff", fontSize: 16, fontWeight: "600" },
  cancelText: { color: "#6c757d", fontSize: 16, fontWeight: "600" },
});
