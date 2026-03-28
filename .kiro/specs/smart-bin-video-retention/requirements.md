# Requirements Document

## Introduction

The Smart Bin Video Retention feature automatically captures and archives video clips when a threat escalates beyond the configured alert threshold in the AURORA violence detection system. When a risk score crosses the alert threshold, the system trims the live video stream into a configurable-length clip and stores it in the Smart Bin (video archive). Clips are surfaced on the map and in the alert queue. A configurable retention policy governs how long clips remain in the Smart Bin before automatic deletion.

## Glossary

- **AURORA**: The violence detection system this feature is built within.
- **Smart_Bin**: The video archive that stores automatically captured threat clips.
- **Clip**: A trimmed video segment captured around the moment a threat escalation is detected.
- **Risk_Score**: A numeric value (0–100) produced by the scoring service representing the current threat level for a camera feed.
- **Alert_Threshold**: The configurable Risk_Score value above which a threat escalation is triggered.
- **Clip_Duration**: The configurable length (in seconds) of each captured Clip.
- **Retention_Period**: The configurable number of days a Clip remains in the Smart_Bin before automatic deletion.
- **Scoring_Service**: The backend service (`scoring_service.py`) that produces Risk_Score values.
- **Clip_Capture_Service**: The backend service responsible for trimming the live stream and writing Clips to storage.
- **Smart_Bin_Service**: The backend service responsible for managing Clip metadata, retrieval, and retention enforcement.
- **Retention_Scheduler**: The background task that periodically checks and deletes expired Clips.
- **Alert_Service**: The existing backend service (`alert_service.py`) that manages alert records.
- **Video_Storage_Service**: The existing backend service (`video_storage_service.py`) that handles raw video I/O.
- **Settings_Page**: The existing frontend page (`System.jsx`) where users configure system behaviour.
- **Archives_Page**: The existing frontend page (`Archives.jsx`) where users browse stored Clips.
- **Alert_Queue**: The UI component on the Alerts page that lists active and recent alerts.
- **Map_View**: The UI component that displays camera locations and alert markers on a geographic map.
- **WebSocket_Manager**: The existing service (`ws_manager.py`) that pushes real-time events to connected clients.
- **SystemSetting**: The existing database model used to persist key-value configuration entries.
- **ClipRecord**: The database model that stores metadata for each captured Clip (camera ID, timestamp, file path, expiry date).

---

## Requirements

### Requirement 1: Smart Bin Feature Toggle

**User Story:** As a system administrator, I want to enable or disable the Smart Bin feature from Settings, so that I can control whether threat clips are captured without redeploying the system.

#### Acceptance Criteria

1. THE Settings_Page SHALL display a toggle control labelled "Smart Bin Video Retention" that reflects the current enabled/disabled state stored in SystemSetting.
2. WHEN the administrator changes the toggle state, THE Settings_Page SHALL persist the new value to the SystemSetting store via the settings API within 2 seconds.
3. WHILE the Smart Bin feature is disabled, THE Clip_Capture_Service SHALL NOT create Clips regardless of Risk_Score values.
4. WHILE the Smart Bin feature is enabled, THE Clip_Capture_Service SHALL capture Clips when the Alert_Threshold is crossed.
5. IF the SystemSetting for the Smart Bin toggle is absent, THEN THE Smart_Bin_Service SHALL treat the feature as disabled and log a warning.

---

### Requirement 2: Clip Duration Configuration

**User Story:** As a system administrator, I want to configure the length of captured clips, so that I can balance storage usage against the amount of context captured per incident.

#### Acceptance Criteria

1. THE Settings_Page SHALL display a numeric input labelled "Clip Duration (seconds)" that reflects the current Clip_Duration stored in SystemSetting.
2. WHEN the administrator submits a Clip_Duration value, THE Settings_Page SHALL accept only integer values between 5 and 300 seconds (inclusive).
3. IF the administrator submits a Clip_Duration value outside the range 5–300, THEN THE Settings_Page SHALL display a validation error and SHALL NOT persist the value.
4. WHEN a valid Clip_Duration is submitted, THE Settings_Page SHALL persist the new value to the SystemSetting store via the settings API within 2 seconds.
5. WHEN a Clip is captured, THE Clip_Capture_Service SHALL produce a Clip whose duration equals the configured Clip_Duration, ending at the moment the Alert_Threshold was crossed.
6. IF the SystemSetting for Clip_Duration is absent, THEN THE Clip_Capture_Service SHALL use a default Clip_Duration of 10 seconds.

---

### Requirement 3: Automatic Clip Capture on Threat Escalation

**User Story:** As a security operator, I want the system to automatically capture a video clip when a threat escalates, so that I have recorded evidence without manual intervention.

#### Acceptance Criteria

1. WHEN the Scoring_Service produces a Risk_Score that crosses the Alert_Threshold for a camera feed, THE Clip_Capture_Service SHALL initiate clip capture for that camera within 1 second of the threshold crossing.
2. WHILE the Smart Bin feature is enabled, THE Clip_Capture_Service SHALL pass the camera ID, threshold-crossing timestamp, and configured Clip_Duration to the Video_Storage_Service to retrieve the corresponding video segment.
3. WHEN the Video_Storage_Service returns the video segment, THE Clip_Capture_Service SHALL write the segment to persistent storage and create a ClipRecord containing the camera ID, capture timestamp, file path, and calculated expiry date.
4. IF the Video_Storage_Service returns an error during clip retrieval, THEN THE Clip_Capture_Service SHALL log the error with the camera ID and timestamp and SHALL NOT create a partial ClipRecord.
5. WHEN a ClipRecord is successfully created, THE Clip_Capture_Service SHALL notify the Alert_Service to associate the ClipRecord with the corresponding alert.
6. THE Clip_Capture_Service SHALL capture at most one Clip per camera per alert event, preventing duplicate Clips for the same threshold-crossing event.

---

### Requirement 4: Alert Integration

**User Story:** As a security operator, I want captured clips to appear in the alert queue and on the map, so that I can immediately locate and review incidents.

#### Acceptance Criteria

1. WHEN a ClipRecord is created, THE Alert_Service SHALL create or update an Alert record that references the ClipRecord's file path and camera ID.
2. WHEN an Alert referencing a ClipRecord is created, THE WebSocket_Manager SHALL broadcast an alert event to all connected clients within 500 milliseconds.
3. WHEN a connected client receives the alert event, THE Alert_Queue SHALL display the new alert entry including camera ID, capture timestamp, and a link to the Clip.
4. WHEN a connected client receives the alert event, THE Map_View SHALL display an alert marker at the geographic coordinates associated with the camera ID.
5. IF the camera ID in the ClipRecord has no associated geographic coordinates, THEN THE Map_View SHALL display the alert marker at a default "unknown location" position and SHALL label it accordingly.

---

### Requirement 5: Smart Bin Clip Browsing

**User Story:** As a security operator, I want to browse and play back clips stored in the Smart Bin, so that I can review past incidents.

#### Acceptance Criteria

1. THE Archives_Page SHALL display a list of ClipRecords from the Smart_Bin_Service, ordered by capture timestamp descending.
2. WHEN the Archives_Page loads, THE Smart_Bin_Service SHALL return all non-expired ClipRecords including camera ID, capture timestamp, Clip_Duration, and expiry date.
3. WHEN an operator selects a ClipRecord, THE Archives_Page SHALL play back the associated Clip using the stored file path.
4. IF a ClipRecord's file is not found in storage, THEN THE Smart_Bin_Service SHALL return a 404 status for that Clip and THE Archives_Page SHALL display an error message indicating the clip is unavailable.
5. THE Archives_Page SHALL display the expiry date for each ClipRecord so operators know how long the clip will remain available.

---

### Requirement 6: Retention Period Configuration

**User Story:** As a system administrator, I want to configure how long clips are retained in the Smart Bin, so that I can manage storage capacity and comply with data retention policies.

#### Acceptance Criteria

1. THE Settings_Page SHALL display a numeric input labelled "Clip Retention Period (days)" that reflects the current Retention_Period stored in SystemSetting.
2. WHEN the administrator submits a Retention_Period value, THE Settings_Page SHALL accept only integer values between 1 and 365 days (inclusive).
3. IF the administrator submits a Retention_Period value outside the range 1–365, THEN THE Settings_Page SHALL display a validation error and SHALL NOT persist the value.
4. WHEN a valid Retention_Period is submitted, THE Settings_Page SHALL persist the new value to the SystemSetting store via the settings API within 2 seconds.
5. WHEN a ClipRecord is created, THE Clip_Capture_Service SHALL set the ClipRecord's expiry date to the capture timestamp plus the current Retention_Period in days.
6. IF the SystemSetting for Retention_Period is absent, THEN THE Clip_Capture_Service SHALL use a default Retention_Period of 10 days.

---

### Requirement 7: Automatic Clip Deletion After Retention Period

**User Story:** As a system administrator, I want expired clips to be automatically deleted, so that storage is reclaimed without manual cleanup.

#### Acceptance Criteria

1. THE Retention_Scheduler SHALL run a deletion check at least once every 24 hours.
2. WHEN the Retention_Scheduler runs, THE Retention_Scheduler SHALL query all ClipRecords whose expiry date is earlier than the current UTC timestamp.
3. WHEN an expired ClipRecord is identified, THE Retention_Scheduler SHALL delete the associated video file from storage and then delete the ClipRecord from the database.
4. IF the video file for an expired ClipRecord is not found in storage, THEN THE Retention_Scheduler SHALL log a warning and SHALL still delete the ClipRecord from the database.
5. IF a file deletion fails due to a storage error, THEN THE Retention_Scheduler SHALL log the error with the ClipRecord ID and file path and SHALL NOT delete the ClipRecord, retrying on the next scheduled run.
6. WHEN a ClipRecord is deleted by the Retention_Scheduler, THE Smart_Bin_Service SHALL no longer return that ClipRecord in any query response.
