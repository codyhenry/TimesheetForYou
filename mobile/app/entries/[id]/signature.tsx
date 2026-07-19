import React, { useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import SignatureCanvas from "react-native-signature-canvas";
import { captureSignature } from "../../../src/api/signatures";

export default function SignatureCaptureScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const signatureRef = useRef<any>(null);
  const [hasSignature, setHasSignature] = useState(false);
  const [pendingSave, setPendingSave] = useState(false);
  const [saving, setSaving] = useState(false);

  const persistSignature = async (sig: string) => {
    setSaving(true);
    try {
      await captureSignature(Number(id), sig);
      Alert.alert("Success", "Signature captured successfully.", [
        { text: "View Entry", onPress: () => router.replace(`/entries/${id}`) },
        {
          text: "Go to Home",
          onPress: () => router.replace("/timesheets/current"),
        },
      ]);
    } catch (error: any) {
      const message =
        error.response?.data?.detail ||
        error.response?.data?.image ||
        "Failed to save signature.";
      Alert.alert("Error", message);
    } finally {
      setSaving(false);
      setPendingSave(false);
    }
  };

  const handleOK = (sig: string) => {
    if (pendingSave) {
      void persistSignature(sig);
    }
  };

  const handleClear = () => {
    signatureRef.current?.clearSignature();
    setHasSignature(false);
    setPendingSave(false);
  };

  const handleConfirm = async () => {
    if (!hasSignature) {
      Alert.alert("Error", "Please provide a signature before confirming.");
      return;
    }
    setPendingSave(true);
    signatureRef.current?.readSignature();
  };

  return (
    <View style={styles.container}>
      <Text style={styles.instruction}>
        Please sign below to confirm this time entry:
      </Text>

      <View style={styles.canvasContainer}>
        <SignatureCanvas
          ref={signatureRef}
          onOK={handleOK}
          onEnd={() => setHasSignature(true)}
          onEmpty={() => setHasSignature(false)}
          descriptionText=""
          clearText="Clear"
          confirmText="Save"
          webStyle={`
            .m-signature-pad { border: none; box-shadow: none; }
            .m-signature-pad--body { border: 1px solid #dee2e6; border-radius: 4px; }
            .m-signature-pad--footer { display: none; }
          `}
          style={styles.canvas}
        />
      </View>

      <View style={styles.actions}>
        <TouchableOpacity style={styles.clearButton} onPress={handleClear}>
          <Text style={styles.clearText}>Clear Signature</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.confirmButton, !hasSignature && styles.disabled]}
          onPress={handleConfirm}
          disabled={!hasSignature || saving}
        >
          {saving ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>Confirm Signature</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.cancelButton}
          onPress={() => router.back()}
        >
          <Text style={styles.cancelText}>Back</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.homeButton}
          onPress={() => router.replace("/timesheets/current")}
        >
          <Text style={styles.homeText}>Home</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f8f9fa" },
  instruction: {
    fontSize: 15,
    padding: 16,
    color: "#212529",
    textAlign: "center",
  },
  canvasContainer: {
    flex: 1,
    margin: 16,
    backgroundColor: "#fff",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#dee2e6",
    overflow: "hidden",
  },
  canvas: { flex: 1 },
  actions: { padding: 16, gap: 8 },
  clearButton: {
    borderWidth: 1,
    borderColor: "#6c757d",
    borderRadius: 8,
    padding: 12,
    alignItems: "center",
  },
  clearText: { color: "#6c757d", fontSize: 16, fontWeight: "600" },
  confirmButton: {
    backgroundColor: "#28a745",
    borderRadius: 8,
    padding: 14,
    alignItems: "center",
  },
  disabled: { backgroundColor: "#6c757d", opacity: 0.6 },
  cancelButton: { padding: 10, alignItems: "center" },
  cancelText: { color: "#6c757d", fontSize: 14 },
  homeButton: {
    borderWidth: 1,
    borderColor: "#2c3e50",
    borderRadius: 8,
    padding: 12,
    alignItems: "center",
    backgroundColor: "#fff",
  },
  homeText: { color: "#2c3e50", fontSize: 16, fontWeight: "600" },
  buttonText: { color: "#fff", fontSize: 16, fontWeight: "600" },
});
