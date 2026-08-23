import React, { useState } from "react";
import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { changePassword } from "../src/api/auth";
import { useAuth } from "../src/context/AuthContext";

export default function PasswordSetupScreen() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const { updateUser, logout } = useAuth();

  const handleSubmit = async () => {
    if (!currentPassword.trim() || !newPassword.trim() || !confirmPassword.trim()) {
      Alert.alert("Error", "Please complete all password fields.");
      return;
    }

    if (newPassword !== confirmPassword) {
      Alert.alert("Error", "New passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      const user = await changePassword(currentPassword, newPassword, confirmPassword);
      updateUser(user);
      Alert.alert("Password Updated", "Your password has been updated.");
    } catch (error: any) {
      const data = error.response?.data;
      const message =
        data?.detail ||
        data?.current_password?.[0] ||
        data?.new_password?.[0] ||
        data?.confirm_password?.[0] ||
        data?.non_field_errors?.[0] ||
        error.message ||
        "Unable to update password.";
      Alert.alert("Password Update Failed", message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
        <View style={styles.header}>
          <Text style={styles.title}>Set your password</Text>
          <Text style={styles.subtitle}>
            Your account is using a temporary password. Create a new password before continuing.
          </Text>
        </View>

        <View style={styles.form}>
          <Text style={styles.label}>Current password</Text>
          <TextInput
            style={styles.input}
            value={currentPassword}
            onChangeText={setCurrentPassword}
            placeholder="Enter current password"
            secureTextEntry
          />

          <Text style={styles.label}>New password</Text>
          <TextInput
            style={styles.input}
            value={newPassword}
            onChangeText={setNewPassword}
            placeholder="Enter new password"
            secureTextEntry
          />

          <Text style={styles.label}>Confirm new password</Text>
          <TextInput
            style={styles.input}
            value={confirmPassword}
            onChangeText={setConfirmPassword}
            placeholder="Confirm new password"
            secureTextEntry
          />

          <TouchableOpacity style={styles.button} onPress={handleSubmit} disabled={loading}>
            {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Update Password</Text>}
          </TouchableOpacity>

          <TouchableOpacity style={styles.secondaryButton} onPress={logout} disabled={loading}>
            <Text style={styles.secondaryButtonText}>Log Out</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f8f9fa" },
  scroll: { flexGrow: 1, justifyContent: "center", padding: 24 },
  header: { alignItems: "center", marginBottom: 32 },
  title: { fontSize: 30, fontWeight: "700", color: "#2c3e50", marginBottom: 8 },
  subtitle: { fontSize: 16, color: "#6c757d", textAlign: "center", lineHeight: 22 },
  form: {},
  label: { fontSize: 14, fontWeight: "600", marginBottom: 6, color: "#212529" },
  input: {
    borderWidth: 1,
    borderColor: "#ced4da",
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    backgroundColor: "#fff",
    marginBottom: 16,
  },
  button: {
    backgroundColor: "#2c3e50",
    borderRadius: 8,
    padding: 14,
    alignItems: "center",
    marginTop: 8,
  },
  buttonText: { color: "#fff", fontSize: 16, fontWeight: "600" },
  secondaryButton: { padding: 14, alignItems: "center", marginTop: 8 },
  secondaryButtonText: { color: "#2c3e50", fontSize: 16, fontWeight: "600" },
});
