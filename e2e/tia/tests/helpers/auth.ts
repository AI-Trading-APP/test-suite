import { APIRequestContext, expect } from '@playwright/test';

// Email-auth admin account on test VPS (see runbooks/test-credentials.md).
// We deliberately avoid the Google-OAuth owner account here, since password login fails.
export const TEST_EMAIL = process.env.TIA_TEST_EMAIL ?? 'e2etest@ktrading.tech';
export const TEST_PASSWORD = process.env.TIA_TEST_PASSWORD ?? 'TestAdmin@2026';

export async function loginViaApi(request: APIRequestContext, baseURL: string) {
  const res = await request.post(`${baseURL}/api/auth/login`, {
    data: { email: TEST_EMAIL, password: TEST_PASSWORD },
    headers: { 'Content-Type': 'application/json' },
  });
  expect(res.status(), `login failed: ${res.status()}`).toBe(200);
  const body = await res.json();
  expect(body.token, 'login response missing token').toBeTruthy();
  return body.token as string;
}
