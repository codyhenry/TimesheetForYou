import React, { useEffect, useState } from "react";
import { ActivityIndicator, Alert, StyleSheet, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import * as SecureStore from "expo-secure-store";
import { WebView } from "react-native-webview";

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || "http://localhost:8000";

export default function TimesheetPdfScreen() {
  const { timesheetId } = useLocalSearchParams<{ timesheetId: string }>();
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [loadingToken, setLoadingToken] = useState(true);

  useEffect(() => {
    const loadToken = async () => {
      try {
        const accessToken = await SecureStore.getItemAsync("access_token");
        if (!accessToken) {
          Alert.alert("Session Expired", "Please log in again.", [
            { text: "OK", onPress: () => router.replace("/login") },
          ]);
          return;
        }
        setToken(accessToken);
      } finally {
        setLoadingToken(false);
      }
    };

    void loadToken();
  }, [router]);

  if (loadingToken) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  if (!token || !timesheetId) {
    return <View style={styles.center} />;
  }

  return (
    <WebView
      source={{
        uri: `${API_BASE_URL}/api/timesheets/${timesheetId}/pdf/`,
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }}
      startInLoadingState
      renderLoading={() => (
        <View style={styles.center}>
          <ActivityIndicator size="large" />
        </View>
      )}
      onHttpError={(event) => {
        const status = event.nativeEvent.statusCode;
        if (status === 401) {
          Alert.alert("Unauthorized", "Please log in again to view this PDF.");
        } else {
          Alert.alert("Error", `Failed to load PDF (HTTP ${status}).`);
        }
      }}
      onError={() => {
        Alert.alert("Error", "Unable to load PDF. Please try again.");
      }}
    />
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
});
