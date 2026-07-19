import DateTimePicker, {
  DateTimePickerEvent,
} from "@react-native-community/datetimepicker";
import React, { useMemo, useState } from "react";
import {
  Keyboard,
  Platform,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { formatTime } from "../utils/dates";

interface Props {
  label: string;
  value: string;
  onChange: (value: string) => void;
  error?: string;
}

const toApiTime = (date: Date): string => {
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  return `${hours}:${minutes}`;
};

const parseApiTime = (value: string): Date => {
  const now = new Date();
  const match = /^([01]\d|2[0-3]):([0-5]\d)$/.exec(value);
  if (!match) {
    now.setHours(8, 0, 0, 0);
    return now;
  }

  now.setHours(Number(match[1]), Number(match[2]), 0, 0);
  return now;
};

export const TimeInput: React.FC<Props> = ({
  label,
  value,
  onChange,
  error,
}) => {
  const [showPicker, setShowPicker] = useState(false);
  const pickerValue = useMemo(() => parseApiTime(value), [value]);

  const handleChange = (event: DateTimePickerEvent, selectedDate?: Date) => {
    if (Platform.OS === "android") {
      setShowPicker(false);
      if (event.type === "set" && selectedDate) {
        onChange(toApiTime(selectedDate));
      }
      return;
    }

    if (selectedDate) {
      onChange(toApiTime(selectedDate));
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.label}>{label}</Text>
      <TouchableOpacity
        style={[styles.input, error ? styles.inputError : null]}
        onPress={() => {
          Keyboard.dismiss();
          setShowPicker(true);
        }}
      >
        <Text style={value ? styles.inputText : styles.placeholderText}>
          {value ? formatTime(value) : "Select time"}
        </Text>
      </TouchableOpacity>

      {showPicker && (
        <View style={styles.pickerContainer}>
          <DateTimePicker
            value={pickerValue}
            mode="time"
            is24Hour={false}
            display={Platform.OS === "ios" ? "spinner" : "default"}
            {...(Platform.OS === "ios"
              ? { themeVariant: "light", textColor: "#212529" }
              : {})}
            onChange={handleChange}
          />
          {Platform.OS === "ios" && (
            <TouchableOpacity
              style={styles.doneButton}
              onPress={() => {
                onChange(toApiTime(pickerValue));
                setShowPicker(false);
              }}
            >
              <Text style={styles.doneButtonText}>Done</Text>
            </TouchableOpacity>
          )}
        </View>
      )}

      {error && <Text style={styles.error}>{error}</Text>}
    </View>
  );
};

const styles = StyleSheet.create({
  container: { marginBottom: 12 },
  label: { fontSize: 14, fontWeight: "600", marginBottom: 4, color: "#212529" },
  input: {
    borderWidth: 1,
    borderColor: "#ced4da",
    borderRadius: 6,
    padding: 10,
    fontSize: 16,
    backgroundColor: "#fff",
  },
  inputText: { fontSize: 16, color: "#212529" },
  placeholderText: { fontSize: 16, color: "#495057" },
  pickerContainer: {
    marginTop: 8,
    backgroundColor: "#f8f9fa",
    borderRadius: 6,
    borderWidth: 1,
    borderColor: "#adb5bd",
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
  error: { color: "#dc3545", fontSize: 12, marginTop: 4 },
});
