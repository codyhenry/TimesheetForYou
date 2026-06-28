import React, { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { createEntry } from '../../src/api/entries';
import { FamilyNameInput } from '../../src/components/FamilyNameInput';
import { TimeInput } from '../../src/components/TimeInput';
import { calculateHoursPreview } from '../../src/utils/hours';

export default function NewEntryScreen() {
  const { timesheetId } = useLocalSearchParams<{ timesheetId: string }>();
  const router = useRouter();

  const [date, setDate] = useState('');
  const [familyName, setFamilyName] = useState('');
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const hoursPreview = calculateHoursPreview(startTime, endTime);

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!date) newErrors.date = 'Date is required';
    if (!familyName.trim()) newErrors.familyName = 'Family name is required';
    if (!startTime) newErrors.startTime = 'Start time is required';
    if (!endTime) newErrors.endTime = 'End time is required';
    if (startTime && endTime && !calculateHoursPreview(startTime, endTime)) {
      newErrors.endTime = 'End time must be after start time';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
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
      });
      router.back();
    } catch (error: any) {
      const data = error.response?.data;
      if (data) {
        const message = Object.values(data).flat().join('
');
        Alert.alert('Validation Error', message);
      } else {
        Alert.alert('Error', 'Failed to create entry. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container} keyboardShouldPersistTaps="handled">
      <View style={styles.form}>
        <Text style={styles.label}>Date (YYYY-MM-DD)</Text>
        <TextInput
          style={[styles.input, errors.date ? styles.inputError : null]}
          value={date}
          onChangeText={setDate}
          placeholder="2026-06-22"
          keyboardType="numbers-and-punctuation"
        />
        {errors.date && <Text style={styles.error}>{errors.date}</Text>}

        <FamilyNameInput value={familyName} onChange={setFamilyName} error={errors.familyName} />

        <TimeInput label="Start Time" value={startTime} onChange={setStartTime} error={errors.startTime} />

        <TimeInput label="End Time" value={endTime} onChange={setEndTime} error={errors.endTime} />

        {hoursPreview && (
          <View style={styles.previewBox}>
            <Text style={styles.previewText}>Preview: {hoursPreview} hours</Text>
          </View>
        )}

        <Text style={styles.label}>Notes (optional)</Text>
        <TextInput
          style={[styles.input, styles.textarea]}
          value={notes}
          onChangeText={setNotes}
          placeholder="Any additional notes..."
          multiline
          numberOfLines={3}
        />

        <TouchableOpacity style={styles.button} onPress={handleSubmit} disabled={loading}>
          {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Add Entry</Text>}
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8f9fa' },
  form: { padding: 16 },
  label: { fontSize: 14, fontWeight: '600', marginBottom: 4, color: '#212529' },
  input: {
    borderWidth: 1,
    borderColor: '#ced4da',
    borderRadius: 6,
    padding: 10,
    fontSize: 16,
    backgroundColor: '#fff',
    marginBottom: 12,
  },
  inputError: { borderColor: '#dc3545' },
  textarea: { height: 80, textAlignVertical: 'top' },
  error: { color: '#dc3545', fontSize: 12, marginTop: -8, marginBottom: 8 },
  previewBox: {
    backgroundColor: '#d4edda',
    borderRadius: 6,
    padding: 10,
    marginBottom: 12,
  },
  previewText: { color: '#155724', fontWeight: '600' },
  button: {
    backgroundColor: '#2c3e50',
    borderRadius: 8,
    padding: 14,
    alignItems: 'center',
    marginTop: 8,
  },
  buttonText: { color: '#fff', fontSize: 16, fontWeight: '600' },
});
