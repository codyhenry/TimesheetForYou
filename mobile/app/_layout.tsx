import { Stack, useRouter, useSegments } from "expo-router";
import { useEffect } from "react";
import { ActivityIndicator, View } from "react-native";
import { AuthProvider, useAuth } from "../src/context/AuthContext";

function RootLayoutNav() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const segments = useSegments();

  useEffect(() => {
    if (loading) {
      return;
    }

    const inAuthRoute = segments[0] === "login";
    if (!user && !inAuthRoute) {
      router.replace("/login");
    } else if (user && inAuthRoute) {
      router.replace("/timesheets/current");
    }
  }, [loading, router, segments, user]);

  if (loading) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    <Stack>
      <Stack.Screen
        name="login"
        options={{ title: "Login", headerShown: false }}
      />
      <Stack.Screen name="timesheets" options={{ headerShown: false }} />
      <Stack.Screen name="entries" options={{ headerShown: false }} />
      <Stack.Screen name="submit" options={{ headerShown: false }} />
      <Stack.Screen
        name="pdf/[timesheetId]"
        options={{ title: "Timesheet PDF" }}
      />
    </Stack>
  );
}

export default function RootLayout() {
  return (
    <AuthProvider>
      <RootLayoutNav />
    </AuthProvider>
  );
}
