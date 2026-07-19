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
import {
  checkServerAccess,
  getCurrentUser,
  login as apiLogin,
  logout as apiLogout,
} from "../src/api/auth";
import { useAuth } from "../src/context/AuthContext";

export default function LoginScreen() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleLogin = async () => {
    if (!username.trim() || !password.trim()) {
      Alert.alert("Error", "Please enter your username and password.");
      return;
    }

    setLoading(true);
    try {
      // Check server connectivity first
      console.log("Checking server access...");
      const serverCheck = await checkServerAccess();
      if (!serverCheck.connected) {
        Alert.alert("Server Connection Error", serverCheck.message);
        return;
      }

      console.log("Server check passed, attempting login...");
      await apiLogin(username.trim(), password);
      console.log("Login successful, fetching user...");

      const user = await getCurrentUser();
      console.log("Got user:", user);

      if (user.role === "admin") {
        await apiLogout();
        Alert.alert(
          "Admin Account",
          "Admin users should use the web portal for timesheet management.",
        );
        return;
      }

      console.log("Calling login context with user:", user);
      login(user);
      console.log("Login complete");
    } catch (error: any) {
      console.error("Login error:", error);
      const message =
        error.response?.data?.detail ||
        error.message ||
        "Invalid username or password.";
      Alert.alert("Login Failed", message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <ScrollView
        contentContainerStyle={styles.scroll}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.header}>
          <Text style={styles.title}>TimesheetForYou</Text>
          <Text style={styles.subtitle}>Nanny Timesheet App</Text>
        </View>
        <View style={styles.form}>
          <Text style={styles.label}>Username</Text>
          <TextInput
            style={styles.input}
            value={username}
            onChangeText={setUsername}
            placeholder="Enter username"
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="email-address"
          />
          <Text style={styles.label}>Password</Text>
          <TextInput
            style={styles.input}
            value={password}
            onChangeText={setPassword}
            placeholder="Enter password"
            secureTextEntry
          />
          <TouchableOpacity
            style={styles.button}
            onPress={handleLogin}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.buttonText}>Log In</Text>
            )}
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f8f9fa" },
  scroll: { flexGrow: 1, justifyContent: "center", padding: 24 },
  header: { alignItems: "center", marginBottom: 40 },
  title: { fontSize: 32, fontWeight: "700", color: "#2c3e50", marginBottom: 8 },
  subtitle: { fontSize: 16, color: "#6c757d" },
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
});
