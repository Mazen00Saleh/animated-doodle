# Frontend Updates — Patient Profile Display

## Summary of Changes

### HTML (frontend/index.html)
Added a new **Patient Profile Section** in the Chat tab with:
- Collapsible header with toggle button
- Three-column responsive grid for profile display
- Profile cards for Demographics, Clinical, and Communication Style
- Risk status indicator with detail panel (visible only when risk_positive=true)

### JavaScript (frontend/app.js)
Added profile functionality:
- **13 new DOM element references** for profile fields
- **`loadPatientProfile(sessionId)`** function to fetch and display profile
- **Profile toggle handler** for collapse/expand behavior
- **Automatic profile loading** when session starts
- **Automatic profile hiding** when session clears

### CSS (frontend/style.css)
Added ~120 lines of styling:
- `.profile-section` and related classes
- Responsive grid layout (auto-fit, minmax)
- Smooth collapse/expand transitions
- Color-coded risk indicator
- Mobile-friendly responsive design

## Profile Fields Displayed

| Field            | Type    | Display                                                          |
| ---------------- | ------- | ---------------------------------------------------------------- |
| Age              | Integer | "35"                                                             |
| Gender           | String  | "Male", "Female", "Non-binary"                                   |
| Occupation       | String  | "Software Engineer"                                              |
| Chief Complaint  | String  | Patient's description of problem                                 |
| Symptom Severity | String  | "mild", "moderate", "severe"                                     |
| Onset            | String  | "about 3 months ago"                                             |
| Response Style   | String  | "terse", "normal", "verbose"                                     |
| Emotional Tone   | String  | "flat", "anxious", "guarded", "tearful", "irritable"             |
| Risk Status      | Boolean | "YES" (red) or "No"                                              |
| Risk Detail      | String  | Description of passive suicidal ideation (if risk_positive=true) |

## API Integration

The frontend now calls:
- **`GET /api/v1/session/{session_id}/profile`** when session starts
- Returns ProfileProfile as JSON, or 404 if unavailable
- Gracefully handles missing profiles (older sessions)

## User Experience

1. User starts a session
2. Profile section appears with a spinner
3. Profile populates automatically from API
4. Examiner can collapse/expand to focus on chat
5. On session clear, profile disappears

## Mobile Responsiveness

Profile grid adapts to screen size:
- **Desktop:** 3 columns (Demographics | Clinical | Communication)
- **Tablet:** 2 columns (Demographics+Clinical | Communication)
- **Mobile:** 1 column (all stacked)

## Accessibility

- Profile toggle is keyboard-accessible
- Color contrast meets WCAG AA standards
- Risk indicator uses both color AND text ("YES" vs "No")
- Smooth transitions don't disable motion for users with vestibular disorders
