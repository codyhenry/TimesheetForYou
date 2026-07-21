import React, { useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Keyboard,
  Platform,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import DateTimePicker, {
  DateTimePickerEvent,
} from "@react-native-community/datetimepicker";
import { format } from "date-fns";
import { createEntry } from "../../src/api/entries";
import { FamilyNameInput } from "../../src/components/FamilyNameInput";
import { TimeInput } from "../../src/components/TimeInput";
import { calculateHoursPreview } from "../../src/utils/hours";

export default function NewEntryScreen() {
  const { timesheetId } = useLocalSearchParams<{ timesheetId: string }>();
  const router = useRouter();

  const [selectedDate, setSelectedDate] = useState(new Date());
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [familyName, setFamilyName] = useState("");
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [notes, setNotes] = useState("");
  const [familyRequestedNanny, setFamilyRequestedNanny] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const date = format(selectedDate, "yyyy-MM-dd");
  const hoursPreview = calculateHoursPreview(startTime, endTime);

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!familyName.trim()) newErrors.familyName = "Family name is required";
    if (!startTime) newErrors.startTime = "Start time is required";
    if (!endTime) newErrors.endTime = "End time is required";
    if (startTime && endTime && !calculateHoursPreview(startTime, endTime)) {
      newErrors.endTime = "End time must be after start time";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleDateChange = (event: DateTimePickerEvent, pickedDate?: Date) => {
    if (Platform.OS === "android") {
      setShowDatePicker(false);
      if (event.type === "set" && pickedDate) {
        setSelectedDate(pickedDate);
      }
      return;
    }

    if (pickedDate) {
      setSelectedDate(pickedDate);
    }
  };

  const handleSubmit = async () => {
    if (!validate()) {
      return;
    }

    setLoading(true);
    try {
      await createEntry(Number(timesheetId), {
        date,
        family_name: familyName.trim(),
        start_time: startTime,
        end_time: endTime,
        notes: notes.trim(),
        family_requested_nanny: familyRequestedNanny,
      });
      router.back();
    } catch (error: any) {
      const data = error.response?.data;
      if (data) {
        const message = Object.values(data).flat().join("\n");
        Alert.alert("Validation Error", message);
      } else {
        Alert.alert("Error", "Failed to create entry. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container} keyboardShouldPersistTaps="handled">
      <View style={styles.form}>
        <Text style={styles.label}>Date</Text>
        <TouchableOpacity
          style={[styles.input, errors.date ? styles.inputError : null]}
          onPress={() => {
            Keyboard.dismiss();
            setShowDatePicker(true);
          }}
        >
          <Text style={styles.inputText}>
            {format(selectedDate, "EEEE, MMM d, yyyy")}
          </Text>
        </TouchableOpacity>

        {showDatePicker && (
          <View style={styles.datePickerContainer}>
            <DateTimePicker
              value={selectedDate}
              mode="date"
              display={Platform.OS === "ios" ? "spinner" : "default"}
              {...(Platform.OS === "ios"
                ? { themeVariant: "light", textColor: "#212529" }
                : {})}
              onChange={handleDateChange}
            />
            {Platform.OS === "ios" && (
              <TouchableOpacity
                style={styles.doneButton}
                onPress={() => setShowDatePicker(false)}
              >
                <Text style={styles.doneButtonText}>Done</Text>
              </TouchableOpacity>
            )}
          </View>
        )}

        {errors.date && <Text style={styles.error}>{errors.date}</Text>}

        <FamilyNameInput
          value={familyName}
          onChange={setFamilyName}
          error={errors.familyName}
        />

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
          error={errors.startTime}
        />

        <TimeInput
          label="End Time"
          value={endTime}
          onChange={setEndTime}
          error={errors.endTime}
        />

        {hoursPreview && (
          <View style={styles.previewBox}>
            <Text style={styles.previewText}>
              Preview: {hoursPreview} hours
            </Text>
          </View>
        )}

        <Text style={styles.label}>Notes (optional)</Text>
        <Text style={styles.helpText}>Notes are visible to admins.</Text>
        <TextInput
          style={[styles.input, styles.textarea]}
          value={notes}
          onChangeText={setNotes}
          placeholder="Any additional notes..."
          placeholderTextColor="#495057"
          multiline
          numberOfLines={3}
        />

        <TouchableOpacity
          style={styles.button}
          onPress={handleSubmit}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>Add Entry</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.secondaryButton}
          onPress={() => router.back()}
          disabled={loading}
        >
          <Text style={styles.secondaryButtonText}>Back</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f8f9fa" },
  form: { padding: 16 },
  label: { fontSize: 14, fontWeight: "600", marginBottom: 4, color: "#212529" },
  input: {
    borderWidth: 1,
    borderColor: "#ced4da",
    borderRadius: 6,
    padding: 10,
    fontSize: 16,
    backgroundColor: "#fff",
    color: "#212529",
    marginBottom: 12,
  },
  inputText: { fontSize: 16, color: "#212529" },
  datePickerContainer: {
    marginTop: -4,
    marginBottom: 12,
    backgroundColor: "#f8f9fa",
    borderWidth: 1,
    borderColor: "#adb5bd",
    borderRadius: 6,
    padding: 8,
  },
  doneButton: {
    alignSelf: "flex-end",
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    backgroundColor: "#2c3e50",
    marginTop: 4,
  },
  doneButtonText: { color: "#fff", fontWeight: "600" },
  inputError: { borderColor: "#dc3545" },
  textarea: { height: 80, textAlignVertical: "top" },
  error: { color: "#dc3545", fontSize: 12, marginTop: -8, marginBottom: 8 },
  helpText: { color: "#6c757d", fontSize: 12, lineHeight: 18, marginBottom: 8 },
  requestRow: {
    backgroundColor: "#fff",
    borderWidth: 1,
    borderColor: "#ced4da",
    borderRadius: 6,
    padding: 12,
    marginBottom: 12,
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
    marginBottom: 12,
  },
  previewText: { color: "#155724", fontWeight: "600" },
  button: {
    backgroundColor: "#2c3e50",
    borderRadius: 8,
    padding: 14,
    alignItems: "center",
    marginTop: 8,
  },
  secondaryButton: {
    borderWidth: 1,
    borderColor: "#6c757d",
    borderRadius: 8,
    padding: 14,
    alignItems: "center",
    marginTop: 8,
    backgroundColor: "#fff",
  },
  buttonText: { color: "#fff", fontSize: 16, fontWeight: "600" },
  secondaryButtonText: { color: "#6c757d", fontSize: 16, fontWeight: "600" },
});
