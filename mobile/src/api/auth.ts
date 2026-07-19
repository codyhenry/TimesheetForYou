import client from "./client";
import * as SecureStore from "expo-secure-store";
import { User } from "../types";

interface ApiUser extends Omit<User, "name"> {
  name?: string;
}

const normalizeUser = (user: ApiUser): User => ({
  ...user,
  name:
    user.name || `${user.first_name} ${user.last_name}`.trim() || user.username,
});

export const checkServerAccess = async (): Promise<{
  connected: boolean;
  message: string;
}> => {
  try {
    const response = await client.get("/api/token/");
    // If we get a 400 or 401, the server is up
    return { connected: true, message: "Server is accessible" };
  } catch (error: any) {
    if (
      error.response?.status === 400 ||
      error.response?.status === 401 ||
      error.response?.status === 405
    ) {
      // Server is up, just auth failed as expected
      return { connected: true, message: "Server is accessible" };
    }
    if (error.code === "ECONNREFUSED") {
      return {
        connected: false,
        message: "Cannot connect to server. Check your network and server URL.",
      };
    }
    if (
      error.code === "ENOTFOUND" ||
      error.message?.includes("Network request failed")
    ) {
      return {
        connected: false,
        message: "Server not found. Check your API URL configuration.",
      };
    }
    return { connected: false, message: `Server error: ${error.message}` };
  }
};

export const login = async (username: string, password: string) => {
  const response = await client.post("/api/token/", { username, password });
  const { access, refresh } = response.data;
  await SecureStore.setItemAsync("access_token", access);
  await SecureStore.setItemAsync("refresh_token", refresh);
  return response.data;
};

export const logout = async () => {
  await SecureStore.deleteItemAsync("access_token");
  await SecureStore.deleteItemAsync("refresh_token");
};

export const getCurrentUser = async (): Promise<User> => {
  const response = await client.get("/api/auth/me/");
  return normalizeUser(response.data as ApiUser);
};
