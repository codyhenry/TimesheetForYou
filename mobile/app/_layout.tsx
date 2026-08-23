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

    const inLoginRoute = segments[0] === "login";
    const inPasswordSetupRoute = segments[0] === "password-setup";

    if (!user && !inLoginRoute) {
      router.replace("/login");
    } else if (user?.force_password_change && !inPasswordSetupRoute) {
      router.replace("/password-setup");
    } else if (user && !user.force_password_change && (inLoginRoute || inPasswordSetupRoute)) {
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
      <Stack.Screen
        name="password-setup"
        options={{ title: "Set Password", headerShown: false }}
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
