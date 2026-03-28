// Feature: smart-bin-video-retention, Property 10: Alert queue event contains required fields

import * as fc from 'fast-check';

/**
 * Validates: Requirements 4.3
 *
 * Property 10: Alert queue event contains required fields
 *
 * For any alert WebSocket event received by the frontend, the rendered alert
 * queue entry should contain the camera_id, timestamp, and a clip_url link.
 *
 * This test validates the data transformation logic: given a raw WebSocket
 * alert event object, verify it carries the required fields and that a
 * clip_url can be derived from clip_id.
 */

/** Mirrors the shape broadcast by ClipCaptureService via WebSocketManager */
interface AlertEvent {
  camera_id: string;
  timestamp: Date;
  clip_id: number;
}

/** Derives the clip_url from a clip_id, matching the backend convention */
function deriveClipUrl(clip_id: number): string {
  return `/smart-bin/clips/${clip_id}/stream`;
}

/**
 * Simulates the frontend transformation that maps a raw WebSocket alert event
 * into the data shape rendered by the AlertQueue component.
 */
function transformAlertEvent(event: AlertEvent): {
  camera_id: string;
  timestamp: Date;
  clip_url: string;
} {
  return {
    camera_id: event.camera_id,
    timestamp: event.timestamp,
    clip_url: deriveClipUrl(event.clip_id),
  };
}

describe('Property 10: Alert queue event contains required fields', () => {
  it('transformed alert entry always contains camera_id, timestamp, and clip_url', () => {
    fc.assert(
      fc.property(
        fc.record({
          camera_id: fc.string(),
          timestamp: fc.date(),
          clip_id: fc.integer(),
        }),
        (event: AlertEvent) => {
          const entry = transformAlertEvent(event);

          // camera_id must be present and match the source event
          expect(entry.camera_id).toBe(event.camera_id);

          // timestamp must be present and match the source event
          expect(entry.timestamp).toEqual(event.timestamp);

          // clip_url must be a non-empty string containing the clip_id
          expect(typeof entry.clip_url).toBe('string');
          expect(entry.clip_url.length).toBeGreaterThan(0);
          expect(entry.clip_url).toContain(String(event.clip_id));
        }
      ),
      { numRuns: 100 }
    );
  });
});
