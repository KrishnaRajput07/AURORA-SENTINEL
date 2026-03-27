import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import SmartBinSettings from '../SmartBinSettings';

// Helper: build a fetch mock that returns the given value for a specific settings key
function makeFetchMock(overrides = {}) {
  return jest.fn((url) => {
    const defaults = {
      smart_bin_enabled: 'false',
      clip_duration_seconds: '10',
      clip_retention_days: '10',
    };

    const key = Object.keys(defaults).find((k) => url.includes(k));
    const value = key !== undefined
      ? (overrides[key] !== undefined ? overrides[key] : defaults[key])
      : defaults[key];

    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ key, value }),
    });
  });
}

beforeEach(() => {
  global.fetch = makeFetchMock();
});

afterEach(() => {
  jest.restoreAllMocks();
});

// Requirements: 1.1
test('test_toggle_renders_with_correct_initial_state', async () => {
  global.fetch = makeFetchMock({ smart_bin_enabled: 'true' });

  render(<SmartBinSettings />);

  const toggle = await waitFor(() =>
    screen.getByRole('checkbox')
  );

  expect(toggle).toBeChecked();
});

// Requirements: 1.1
test('test_toggle_renders_disabled_state', async () => {
  global.fetch = makeFetchMock({ smart_bin_enabled: 'false' });

  render(<SmartBinSettings />);

  const toggle = await waitFor(() =>
    screen.getByRole('checkbox')
  );

  expect(toggle).not.toBeChecked();
});

// Requirements: 2.2
test('test_duration_input_renders_with_correct_value', async () => {
  global.fetch = makeFetchMock({ clip_duration_seconds: '30' });

  render(<SmartBinSettings />);

  const input = await waitFor(() =>
    screen.getByLabelText(/clip duration/i)
  );

  expect(input.value).toBe('30');
});

// Requirements: 6.2
test('test_retention_input_renders_with_correct_value', async () => {
  global.fetch = makeFetchMock({ clip_retention_days: '14' });

  render(<SmartBinSettings />);

  const input = await waitFor(() =>
    screen.getByLabelText(/clip retention period/i)
  );

  expect(input.value).toBe('14');
});

// Requirements: 2.3
test('test_duration_validation_error_below_min', async () => {
  render(<SmartBinSettings />);

  const input = await waitFor(() =>
    screen.getByLabelText(/clip duration/i)
  );

  fireEvent.change(input, { target: { value: '4' } });

  expect(
    await screen.findByText(/must be an integer between 5 and 300/i)
  ).toBeInTheDocument();
});

// Requirements: 2.3
test('test_duration_validation_error_above_max', async () => {
  render(<SmartBinSettings />);

  const input = await waitFor(() =>
    screen.getByLabelText(/clip duration/i)
  );

  fireEvent.change(input, { target: { value: '301' } });

  expect(
    await screen.findByText(/must be an integer between 5 and 300/i)
  ).toBeInTheDocument();
});

// Requirements: 6.3
test('test_retention_validation_error_below_min', async () => {
  render(<SmartBinSettings />);

  const input = await waitFor(() =>
    screen.getByLabelText(/clip retention period/i)
  );

  fireEvent.change(input, { target: { value: '0' } });

  expect(
    await screen.findByText(/must be an integer between 1 and 365/i)
  ).toBeInTheDocument();
});

// Requirements: 6.3
test('test_retention_validation_error_above_max', async () => {
  render(<SmartBinSettings />);

  const input = await waitFor(() =>
    screen.getByLabelText(/clip retention period/i)
  );

  fireEvent.change(input, { target: { value: '366' } });

  expect(
    await screen.findByText(/must be an integer between 1 and 365/i)
  ).toBeInTheDocument();
});
