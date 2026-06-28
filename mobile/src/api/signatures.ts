import client from './client';

export const captureSignature = async (entryId: number, signatureBase64: string) => {
  const response = await client.post(`/api/entries/${entryId}/signature/`, {
    image: signatureBase64,
  });
  return response.data;
};
