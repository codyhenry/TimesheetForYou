import React from 'react';
import { View, Text, TextInput, StyleSheet } from 'react-native';

interface Props {
  label: string;
  value: string;
  onChange: (value: string) => void;
  error?: string;
}

export const TimeInput: React.FC<Props> = ({ label, value, onChange, error }) => {
  return (
    <View style={styles.container}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        style={[styles.input, error ? styles.inputError : null]}
        value={value}
        onChangeText={onChange}
        placeholder="HH:MM"
        keyboardType="numbers-and-punctuation"
        maxLength={5}
      />
      {error && <Text style={styles.error}>{error}</Text>}
    </View>
  );
};

const styles = StyleSheet.create({
  container: { marginBottom: 12 },
  label: { fontSize: 14, fontWeight: '600', marginBottom: 4, color: '#212529' },
  input: {
    borderWidth: 1,
    borderColor: '#ced4da',
    borderRadius: 6,
    padding: 10,
    fontSize: 16,
    backgroundColor: '#fff',
  },
  inputError: { borderColor: '#dc3545' },
  error: { color: '#dc3545', fontSize: 12, marginTop: 4 },
});
