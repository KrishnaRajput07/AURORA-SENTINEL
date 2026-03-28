import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  Switch,
  FormControlLabel,
  TextField,
  CircularProgress,
} from '@mui/material';
import { API_BASE_URL } from '../config';

const DEBOUNCE_MS = 1500;

function useSetting(key) {
  const [value, setValue] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    fetch(`${API_BASE_URL}/settings/${key}`)
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to load ${key}`);
        return res.json();
      })
      .then((data) => {
        setValue(data.value);
        setError(null);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [key]);

  return { value, setValue, loading, error };
}

async function postSetting(key, value) {
  const res = await fetch(`${API_BASE_URL}/settings/${key}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ value: String(value) }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.detail || `Failed to save ${key}`);
  }
  return res.json();
}

export default function SmartBinSettings() {
  // ── smart_bin_enabled ──────────────────────────────────────────────────────
  const {
    value: enabledRaw,
    setValue: setEnabledRaw,
    loading: enabledLoading,
  } = useSetting('smart_bin_enabled');

  const enabled = enabledRaw === 'true';

  const handleToggle = async (e) => {
    const next = e.target.checked;
    setEnabledRaw(next ? 'true' : 'false');
    try {
      await postSetting('smart_bin_enabled', next ? 'true' : 'false');
    } catch {
      setEnabledRaw(next ? 'false' : 'true'); // revert on failure
    }
  };

  // ── clip_duration_seconds ──────────────────────────────────────────────────
  const {
    value: durationRaw,
    setValue: setDurationRaw,
    loading: durationLoading,
  } = useSetting('clip_duration_seconds');

  const [durationInput, setDurationInput] = useState('');
  const [durationError, setDurationError] = useState('');
  const durationTimer = useRef(null);

  useEffect(() => {
    if (durationRaw !== null) setDurationInput(durationRaw);
  }, [durationRaw]);

  const handleDurationChange = (e) => {
    const raw = e.target.value;
    setDurationInput(raw);
    const num = parseInt(raw, 10);
    if (!raw || isNaN(num) || num < 5 || num > 300) {
      setDurationError('Must be an integer between 5 and 300');
      clearTimeout(durationTimer.current);
      return;
    }
    setDurationError('');
    clearTimeout(durationTimer.current);
    durationTimer.current = setTimeout(async () => {
      try {
        await postSetting('clip_duration_seconds', num);
        setDurationRaw(String(num));
      } catch (err) {
        setDurationError(err.message);
      }
    }, DEBOUNCE_MS);
  };

  // ── clip_retention_days ────────────────────────────────────────────────────
  const {
    value: retentionRaw,
    setValue: setRetentionRaw,
    loading: retentionLoading,
  } = useSetting('clip_retention_days');

  const [retentionInput, setRetentionInput] = useState('');
  const [retentionError, setRetentionError] = useState('');
  const retentionTimer = useRef(null);

  useEffect(() => {
    if (retentionRaw !== null) setRetentionInput(retentionRaw);
  }, [retentionRaw]);

  const handleRetentionChange = (e) => {
    const raw = e.target.value;
    setRetentionInput(raw);
    const num = parseInt(raw, 10);
    if (!raw || isNaN(num) || num < 1 || num > 365) {
      setRetentionError('Must be an integer between 1 and 365');
      clearTimeout(retentionTimer.current);
      return;
    }
    setRetentionError('');
    clearTimeout(retentionTimer.current);
    retentionTimer.current = setTimeout(async () => {
      try {
        await postSetting('clip_retention_days', num);
        setRetentionRaw(String(num));
      } catch (err) {
        setRetentionError(err.message);
      }
    }, DEBOUNCE_MS);
  };

  const anyLoading = enabledLoading || durationLoading || retentionLoading;

  return (
    <Paper sx={{ p: 0, borderRadius: 2, border: '1px solid #E2E8F0', overflow: 'hidden' }}>
      <Box
        sx={{
          px: 2,
          py: 1.5,
          bgcolor: '#F7FAFC',
          borderBottom: '1px solid #E2E8F0',
          display: 'flex',
          alignItems: 'center',
          gap: 1,
        }}
      >
        <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#4A5568' }}>
          SMART BIN VIDEO RETENTION
        </Typography>
        {anyLoading && <CircularProgress size={14} />}
      </Box>

      <Box sx={{ p: 3, display: 'flex', flexDirection: 'column', gap: 2 }}>
        <FormControlLabel
          control={
            <Switch
              size="small"
              checked={enabled}
              onChange={handleToggle}
              disabled={enabledLoading}
            />
          }
          label={<Typography variant="body2">Smart Bin Video Retention</Typography>}
        />

        <TextField
          label="Clip Duration (seconds)"
          type="number"
          size="small"
          value={durationInput}
          onChange={handleDurationChange}
          disabled={durationLoading}
          error={Boolean(durationError)}
          helperText={durationError || ' '}
          inputProps={{ min: 5, max: 300 }}
          sx={{ maxWidth: 260 }}
        />

        <TextField
          label="Clip Retention Period (days)"
          type="number"
          size="small"
          value={retentionInput}
          onChange={handleRetentionChange}
          disabled={retentionLoading}
          error={Boolean(retentionError)}
          helperText={retentionError || ' '}
          inputProps={{ min: 1, max: 365 }}
          sx={{ maxWidth: 260 }}
        />
      </Box>
    </Paper>
  );
}
