import client from './client';
import * as SecureStore from 'expo-secure-store';
import { User } from '../types';

interface ApiUser extends Omit<User, 'name'> {
  name?: string;
}

const normalizeUser = (user: ApiUser): User => ({
  ...user,
  name: user.name || `${user.first_name} ${user.last_name}`.trim() || user.username,
});

export const login = async (username: string, password: string) => {
  const response = await client.post('/api/token/', { username, password });
  const { access, refresh } = response.data;
  await SecureStore.setItemAsync('access_token', access);
  await SecureStore.setItemAsync('refresh_token', refresh);
  return response.data;
};

export const logout = async () => {
  await SecureStore.deleteItemAsync('access_token');
  await SecureStore.deleteItemAsync('refresh_token');
};

export const getCurrentUser = async (): Promise<User> => {
  const response = await client.get('/api/auth/me/');
  return normalizeUser(response.data as ApiUser);
};
