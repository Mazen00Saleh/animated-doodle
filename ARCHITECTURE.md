# System Architecture — SimPatient v2.0

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         TRAINEE/EDUCATOR UI                          │
│  (Streamlit OR API Tester Frontend)                                  │
└────────┬────────────────────────────────────────────────────────────┘
         │
         │ 1. POST /chat/start
         │    condition: "Depression"
         │    language: "English"
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                                 │
│  api/routes/chat.py:start_session()                                 │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ 2. Generate Patient Profile                                  │  │
│  │    simulator.generate_profile()                              │  │
│  │    ↓                                                          │  │
│  │    Groq API (gpt-oss-20b)                                    │  │
│  │    [Temperature: 0.8, Max Tokens: 1024]                      │  │
│  │    ↓                                                          │  │
│  │    JSON Response: PatientProfile with 19 fields              │  │
│  │    [age, gender, chief_complaint, risk_positive, etc.]       │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                │                                     │
│                                ▼                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ 3. Build System Prompt from Profile                          │  │
│  │    build_system_prompt_from_profile(profile)                 │  │
│  │    ↓                                                          │  │
│  │    Generates rich prompt with:                               │  │
│  │    - Personal profile section                                │  │
│  │    - Risk status (suicidal ideation handling)                │  │
│  │    - Communication style (terse/normal/verbose)              │  │
│  │    - Emotional tone (flat/anxious/guarded/tearful)           │  │
│  │    - Disclosure model (freely/if-asked/resist)               │  │
│  │    - 8 absolute rules                                        │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                │                                     │
│                                ▼                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ 4. Save to Database                                          │  │
│  │    save_session(session_id, condition, language, profile_json)  │
│  │    add_message(session_id, "system", system_prompt_text)     │  │
│  │                                                               │  │
│  │    → sessions.session_id                                     │  │
│  │    → sessions.condition                                      │  │
│  │    → sessions.language                                       │  │
│  │    → sessions.profile (JSON serialized)                      │  │
│  │    → messages.role = "system"                                │  │
│  │    → messages.content = (rich prompt with profile data)      │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                │                                     │
│                                ▼                                     │
│                  Return: {session_id, expires_at}                   │
│                                                                      │
└────────┬────────────────────────────────────────────────────────────┘
         │
         │ 5. Response with session_id
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         TRAINEE/EDUCATOR UI                          │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ 6. Fetch Profile (API Tester only)                           │  │
│  │    GET /session/{session_id}/profile                         │  │
│  │    ↓                                                          │  │
│  │    Display in profile section:                               │  │
│  │    - Demographics (age, gender, occupation)                  │  │
│  │    - Clinical (chief_complaint, onset, severity)             │  │
│  │    - Communication (style, emotional_tone)                   │  │
│  │    - Risk Status (YES/No) + details if positive              │  │
│  │                                                               │  │
│  │    Collapsible: Can hide/show while chatting                 │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ 7. Chat Messages (unchanged)                                 │  │
│  │                                                               │  │
│  │    Trainee sends message                                     │  │
│  │    ↓                                                          │  │
│  │    POST /chat/message with session_id                        │  │
│  │    ↓                                                          │  │
│  │    Retrieve full conversation history from DB:               │  │
│  │    - system message (contains profile-based prompt)          │  │
│  │    - previous user messages                                  │  │
│  │    - previous assistant messages                             │  │
│  │    ↓                                                          │  │
│  │    Call Groq LLM with full history                           │  │
│  │    ↓                                                          │  │
│  │    Patient responds consistently (based on profile)          │  │
│  │    ↓                                                          │  │
│  │    Response saved to DB                                      │  │
│  │    ↓                                                          │  │
│  │    Displayed to trainee                                      │  │
│  │                                                               │  │
│  │    [Profile unchanged for entire session]                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Class Diagram

```
┌──────────────────────────────────────┐
│       PatientProfile                 │
├──────────────────────────────────────┤
│ condition: str                       │
│ language: str                        │
│ age: int                             │
│ gender: str                          │
│ occupation: str                      │
├──────────────────────────────────────┤
│ CLINICAL:                            │
│ chief_complaint: str                 │
│ symptom_onset: str                   │
│ symptom_severity: str                │
│ past_psychiatric_history: str        │
│ current_medications: List[str]       │
│ substance_use: str                   │
├──────────────────────────────────────┤
│ RISK:                                │
│ risk_positive: bool                  │
│ risk_detail: str                     │
├──────────────────────────────────────┤
│ BEHAVIOR:                            │
│ response_style: str                  │
│ emotional_tone: str                  │
├──────────────────────────────────────┤
│ DISCLOSURE:                          │
│ freely_disclose: List[str]           │
│ disclose_if_asked: List[str]         │
│ resist_disclosing: List[str]         │
│ relevant_life_events: List[str]      │
└──────────────────────────────────────┘
         ▲
         │ created_by
         │
┌────────┴────────────────────────────┐
│  GroqPatientSimulator                │
├──────────────────────────────────────┤
│ -_client: Groq                       │
├──────────────────────────────────────┤
│ +generate_profile()                  │
│   → PatientProfile                   │
│                                      │
│ +generate()                          │
│   → str (patient message)            │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│  Prompts                             │
├──────────────────────────────────────┤
│ build_system_prompt()                │
│   → static system prompt             │
│                                      │
│ build_profile_generation_prompt()    │
│   → LLM instruction for JSON         │
│                                      │
│ build_system_prompt_from_profile()   │
│   profile: PatientProfile            │
│   → rich system prompt               │
└──────────────────────────────────────┘
```

---

## Database Schema

```
┌──────────────────────────────────────────────────────────────┐
│                    sessions table                             │
├──────────────────────────────────────────────────────────────┤
│ Column          │ Type      │ Description                    │
├─────────────────┼───────────┼────────────────────────────────┤
│ session_id      │ TEXT PK   │ UUID identifier                │
│ condition       │ TEXT      │ Patient condition (e.g., "DEP")│
│ language        │ TEXT      │ Response language              │
│ created_at      │ TIMESTAMP │ When session started           │
│ expires_at      │ TIMESTAMP │ 10-min timer expiration        │
│ profile         │ TEXT      │ Serialized JSON PatientProfile │
│                 │           │ (NEW in v2.0)                  │
└──────────────────────────────────────────────────────────────┘
         │
         │ 1:Many
         ▼
┌──────────────────────────────────────────────────────────────┐
│                   messages table                              │
├──────────────────────────────────────────────────────────────┤
│ Column          │ Type      │ Description                    │
├─────────────────┼───────────┼────────────────────────────────┤
│ message_id      │ INT PK    │ Auto-increment                 │
│ session_id      │ TEXT FK   │ Reference to sessions          │
│ role            │ TEXT      │ "system", "user", "assistant"  │
│ content         │ TEXT      │ Message content                │
│ created_at      │ TIMESTAMP │ When message created           │
└──────────────────────────────────────────────────────────────┘
```

**Profile JSON Example (stored in sessions.profile):**
```json
{
  "age": 35,
  "gender": "female",
  "occupation": "teacher",
  "chief_complaint": "I feel sad and empty",
  "symptom_onset": "about 3 months ago",
  "symptom_severity": "moderate",
  "relevant_life_events": ["breakup", "moved"],
  "past_psychiatric_history": "none",
  "current_medications": [],
  "substance_use": "occasional wine",
  "risk_positive": false,
  "risk_detail": "",
  "response_style": "terse",
  "emotional_tone": "flat",
  "freely_disclose": ["sadness", "fatigue"],
  "disclose_if_asked": ["breakup", "relocation"],
  "resist_disclosing": ["suicidal ideation"]
}
```

---

## API Endpoints

```
POST /api/v1/chat/start
├─ Request: {condition: str, language: str}
├─ Response: {session_id, condition, language, expires_at}
└─ Side Effects:
   ├─ Calls simulator.generate_profile()
   ├─ Saves profile to sessions.profile
   ├─ Saves system prompt to messages table
   └─ Returns session for next 10 minutes

POST /api/v1/chat/message
├─ Request: {session_id, message, model?, reasoning_effort?}
├─ Response: {session_id, role, content}
└─ Side Effects:
   ├─ Retrieves session history (including profile-based system prompt)
   ├─ Calls LLM with full history
   ├─ Saves assistant response
   └─ Patient behavior determined by profile

GET /api/v1/session/{session_id}/profile
├─ Request: none
├─ Response: PatientProfile as JSON
└─ Status:
   ├─ 200 if profile found
   ├─ 404 if session not found
   └─ 404 if profile not available (older sessions)

GET /api/v1/session/{session_id}/time
├─ Request: none
├─ Response: {session_id, remaining_seconds, expired}
└─ Used for timer display

GET /api/v1/session/{session_id}/results
├─ Request: none
├─ Response: {strengths: [], weaknesses: [], improvement: str}
└─ Retrieved after session ends
```

---

## Frontend Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  index.html                                 │
├─────────────────────────────────────────────────────────────┤
│  Top Bar                                                     │
│  ├─ Logo + Status Dot                                       │
│  └─ Timer (10:00 → 00:00)                                   │
├─────────────────────────────────────────────────────────────┤
│  Main Content                                               │
│  ├─ Sidebar (config, overrides, inspector)                  │
│  └─ Main Panel                                              │
│     ├─ Tab Nav: Chat | Patient Eval | Trainee Eval         │
│     ├─ Chat Tab                                             │
│     │  ├─ 🆕 PROFILE SECTION (NEW v2.0)                    │
│     │  │  ├─ Header + Toggle Button                         │
│     │  │  └─ Profile Grid (3 columns)                       │
│     │  │     ├─ Demographics Card                           │
│     │  │     ├─ Clinical Card                               │
│     │  │     ├─ Communication Card                          │
│     │  │     └─ Risk Details (if risk_positive)             │
│     │  │                                                    │
│     │  ├─ Chat Area (messages)                              │
│     │  └─ Chat Input Bar                                    │
│     │                                                        │
│     ├─ Patient Eval Tab                                     │
│     ├─ Trainee Eval Tab                                     │
│     │                                                        │
│     └─ Results Panel (right sidebar)                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## State Management (Frontend)

```
sessionId: null → "uuid-123" (when session starts)
    │
    ├─ Timer starts (10:00 countdown)
    ├─ Profile fetched from GET /session/{id}/profile
    │  └─ loadPatientProfile() populates 13 UI fields
    ├─ Chat enabled
    ├─ Evaluation buttons enabled
    │
    └─ On timer expires or user clicks delete:
       sessionId = null
       ├─ Timer cleared
       ├─ Profile hidden
       ├─ Chat disabled
       └─ Results shown
```

---

## Profile Generation Process

```
1. START SESSION
   └─ POST /chat/start with condition="Depression"

2. PROFILE GENERATION (in start_session())
   ├─ simulator.generate_profile("Depression", "English")
   │
   └─ LLM CALL (Groq)
      ├─ Model: openai/gpt-oss-20b
      ├─ Temperature: 0.8
      ├─ Max Tokens: 1024
      ├─ System Prompt: build_profile_generation_prompt()
      │  └─ Contains JSON schema and rules:
      │     - Match response_style to condition
      │     - Make emotional_tone plausible
      │     - Include Chief Complaint in freely_disclose
      │     - Set risk_positive for ~40% of depression cases
      │     - Ensure internal consistency
      └─ User Message: "Generate patient profile for..."
         └─ Response: Valid JSON object
            ├─ age: 35
            ├─ gender: "female"
            ├─ occupation: "accountant"
            ├─ chief_complaint: "..."
            ├─ ... (19 total fields)
            └─ risk_positive: false/true

3. PROFILE STORAGE
   ├─ Validate JSON
   ├─ Construct PatientProfile dataclass
   ├─ Serialize to JSON string
   └─ Save to sessions.profile column

4. SYSTEM PROMPT GENERATION
   ├─ build_system_prompt_from_profile(profile)
   ├─ Generates 8 sections:
   │  ├─ Your Personal Profile (demographics + clinical)
   │  ├─ Your Risk Status (suicidal ideation rules)
   │  ├─ How You Communicate (style + tone + 2-sentence limit)
   │  ├─ What You Share And What You Don't (disclosure model)
   │  ├─ Absolute Rules (8 rules to enforce)
   │  └─ Language (respond in {language})
   └─ Save to messages table (role="system")

5. READY FOR CHAT
   └─ Profile is FIXED for entire 10-minute session
      └─ All subsequent messages use same system prompt
```

---

## Risk Assessment Model

```
                    PATIENT PROFILE
                            │
                            ▼
                    risk_positive: bool
                     /            \
                    /              \
                 true              false
                   │                │
                   ▼                ▼
             HAS SUICIDAL         NO SUICIDAL
             IDEATION (PASSIVE)   IDEATION
                   │                │
        risk_detail: str        risk_detail: ""
        "sometimes thinks       (empty)
         about not wanting
         to live, no plan"
                   │                │
                   ▼                ▼
        RESIST SHARING:     RESIST SHARING:
        ├─ Suicidal thoughts │ Some other topic
        └─ Only disclose    │ (no restriction)
           if asked         │
           directly         │
                   │
                   ▼
        RUBRIC GATE: patient_risk_positive
        └─ Deterministic check
           └─ If true, evaluator assesses risk handling
           └─ If false, risk handling not evaluated
```

---

## Session Lifecycle

```
TIME 0:00
    │
    ├─ Trainee enters condition + language
    │
    ├─ Trainee clicks "Start Session"
    │
    ├─ POST /chat/start
    │  ├─ Profile generated (LLM call)
    │  ├─ Profile stored
    │  ├─ System prompt built and stored
    │  └─ session_id returned
    │
    ├─ GET /session/{id}/profile
    │  └─ Profile displayed in examiner view
    │
    ├─ Timer starts: 10:00 countdown
    │
    └─ Chat enabled ✓

TIME 0:05 - 9:55
    │
    ├─ Trainee sends message
    │  └─ POST /chat/message
    │     ├─ Retrieve conversation history (system prompt + previous messages)
    │     ├─ LLM call with consistent system prompt
    │     ├─ Patient responds (behavior matches profile)
    │     └─ Response saved to history
    │
    ├─ Repeat: chat messages flowing
    │  └─ [Profile remains FIXED throughout]
    │
    └─ Examiner can toggle profile view while chatting

TIME 9:55 - 10:00
    │
    ├─ Timer nearing 0:00
    │
    └─ Last few messages exchanged

TIME 10:00
    │
    ├─ Timer expires
    │
    ├─ Chat disabled
    │
    ├─ Session no longer active
    │
    ├─ GET /session/{id}/results
    │  └─ Show strengths, weaknesses, improvement
    │
    └─ Evaluation triggered (if enabled)
```

---

## Error Handling & Fallbacks

```
SCENARIO 1: Profile Generation Fails
    ├─ LLM API timeout
    ├─ JSON parse error
    ├─ Invalid response format
    │
    └─ FALLBACK
       ├─ Catch exception
       ├─ Create minimal default PatientProfile
       ├─ Fall back to old build_system_prompt()
       └─ Session continues normally
          └─ User never notices, session still works

SCENARIO 2: Profile Not Available
    ├─ Session created before v2.0
    ├─ Database corruption
    ├─ GET /session/{id}/profile called
    │
    └─ RESPONSE: 404 "Profile not available"
       └─ Frontend gracefully handles
          └─ Profile section shows "N/A"

SCENARIO 3: GROQ_API_KEY Missing
    ├─ Server started without API key
    ├─ POST /chat/start called
    │
    └─ Profile generation tries
       └─ Exception caught
       └─ Falls back to static prompt
       └─ Chat works (profile-less)

SCENARIO 4: Profile Endpoint 404
    ├─ Frontend calls GET /session/{bad-id}/profile
    │
    └─ RESPONSE: 404 "Session not found"
       └─ Frontend catches 404
       └─ Doesn't show profile section
       └─ Chat continues
```

---

## Summary

**SimPatient v2.0** introduces a sophisticated profile-based patient simulation system that:

1. **Generates realistic profiles** on session start (LLM-powered)
2. **Anchors patient behavior** in profile data (via system prompt)
3. **Maintains consistency** throughout session (profile fixed)
4. **Enables examiner visibility** (profile viewer in UI)
5. **Determines risk assessment** (risk_positive flag)
6. **Gracefully degrades** (fallback to static prompts)

All components work together to create a more immersive, consistent, and educationally effective patient simulation experience.
