import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { SignatureStatus } from '../types';

interface Props {
  status: SignatureStatus;
}

export const SignatureStatusBadge: React.FC<Props> = ({ status }) => {
  const getStyle = () => {
    switch (status) {
      case 'signed':
        return styles.signed;
      case 'signature_invalidated':
        return styles.invalidated;
      default:
        return styles.unsigned;
    }
  };

  const getLabel = () => {
    switch (status) {
      case 'signed':
        return '✓ Signed';
      case 'signature_invalidated':
        return '⚠ Signature Invalidated';
      default:
        return 'Unsigned';
    }
  };

  return (
    <View style={[styles.badge, getStyle()]}>
      <Text style={styles.text}>{getLabel()}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  signed: { backgroundColor: '#d4edda' },
  unsigned: { backgroundColor: '#f8d7da' },
  invalidated: { backgroundColor: '#fff3cd' },
  text: { fontSize: 12, fontWeight: '600' },
});
