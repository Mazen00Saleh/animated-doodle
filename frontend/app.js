/* ═══════════════════════════════════════════
   SimPatient API Tester — JavaScript
   ═══════════════════════════════════════════ */

const API = '/api/v1';

// ── State ──────────────────────────────────
let sessionId = null;
let isPending = false;
let timerInterval = null;
let sessionExpired = false;

// ── DOM Refs ───────────────────────────────
const $ = id => document.getElementById(id);
const qsa = sel => document.querySelectorAll(sel);

const conditionInput = $('condition');
const languageSelect = $('language');
const modelOverride = $('model-override');
const reasoningOverride = $('reasoning-override');
const btnStart = $('btn-start');
const btnDelete = $('btn-delete');
const statusDot = $('status-dot');
const statusText = $('status-text');

const timerDisplay = $('timer-display');
const timerText = $('timer-text');

const resultsPanel = $('results-panel');
const closeResults = $('close-results');
const strengthsList = $('strengths-list');
const weaknessesList = $('weaknesses-list');
const improvementText = $('improvement-text');

const chatArea = $('chat-area');
const chatEmpty = $('chat-empty');
const chatInput = $('chat-input');
const btnSend = $('btn-send');

const profileSection = $('profile-section');
const profileToggle = $('profile-toggle');
const profileContent = $('profile-content');
const profileAge = $('profile-age');
const profileGender = $('profile-gender');
const profileOccupation = $('profile-occupation');
const profileChiefComplaint = $('profile-chief-complaint');
const profileSeverity = $('profile-severity');
const profileOnset = $('profile-onset');
const profileResponseStyle = $('profile-response-style');
const profileEmotionalTone = $('profile-emotional-tone');
const profileRisk = $('profile-risk');
const profileRiskDetail = $('profile-risk-detail');
const profileRiskText = $('profile-risk-text');

const btnEvalPatient = $('btn-eval-patient');
const roleThresh = $('role-thresh');
const roleThreshVal = $('role-thresh-val');
const convoThresh = $('convo-thresh');
const convoThreshVal = $('convo-thresh-val');
const patientResults = $('patient-results');
const patientResultsBody = $('patient-results-body');
const patientResultsSid = $('patient-results-sid');

const btnEvalTrainee = $('btn-eval-trainee');
const judgeModel = $('judge-model');
const rubricPath = $('rubric-path');
const judgeTemp = $('judge-temp');
const judgeTempVal = $('judge-temp-val');
const strictSchema = $('strict-schema');
const traineeResults = $('trainee-results');
const traineeResultsBody = $('trainee-results-body');
const traineeResultsSid = $('trainee-results-sid');

const inspectorJson = $('inspector-json');
const inspectorMeta = $('inspector-meta');
const toggleInspector = $('toggle-inspector');
const inspectorBody = $('inspector-body');
const inspectorChevron = $('inspector-chevron');

// ── Tab Navigation ─────────────────────────
qsa('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        qsa('.tab-btn').forEach(b => b.classList.remove('active'));
        qsa('.tab-pane').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        $('tab-' + btn.dataset.tab).classList.add('active');
    });
});

// ── Profile Toggle ─────────────────────────
profileToggle.addEventListener('click', () => {
    profileContent.classList.toggle('collapsed');
    profileToggle.classList.toggle('collapsed');
});

// ── Inspector Panel ────────────────────────
toggleInspector.addEventListener('click', () => {
    inspectorBody.classList.toggle('hidden');
    inspectorChevron.classList.toggle('open');
});

function updateInspector(method, url, status, data) {
    inspectorMeta.textContent = `${method} ${url} → ${status}`;
    inspectorJson.textContent = JSON.stringify(data, null, 2);
    // Auto-open when first used
    if (inspectorBody.classList.contains('hidden')) {
        inspectorBody.classList.remove('hidden');
        inspectorChevron.classList.add('open');
    }
}

// ── Timer & Results Functions ──────────────
function startTimer() {
    if (timerInterval) clearInterval(timerInterval);
    timerDisplay.classList.remove('hidden');
    sessionExpired = false;
    updateTimerDisplay();

    timerInterval = setInterval(async () => {
        if (!sessionId) return;
        try {
            const resp = await fetch(`${API}/session/${sessionId}/time`);
            const data = await resp.json();
            updateInspector('GET', `${API}/session/${sessionId}/time`, resp.status, data);

            if (data.expired) {
                sessionExpired = true;
                clearInterval(timerInterval);
                timerDisplay.classList.add('expired');
                disableChat();
                showResults();
            } else {
                updateTimerDisplay(data.remaining_seconds);
            }
        } catch (err) {
            console.error('Timer poll failed:', err);
        }
    }, 1000);
}

function updateTimerDisplay(seconds) {
    if (seconds === undefined) {
        timerText.textContent = '10:00';
        return;
    }
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    timerText.textContent = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function disableChat() {
    chatInput.disabled = true;
    btnSend.disabled = true;
    chatInput.placeholder = 'Session expired - chat disabled';
}

function showResults() {
    if (!sessionId) return;
    fetch(`${API}/session/${sessionId}/results`)
        .then(resp => resp.json())
        .then(data => {
            updateInspector('GET', `${API}/session/${sessionId}/results`, 200, data);
            strengthsList.innerHTML = data.strengths.map(s => `<li>${s}</li>`).join('');
            weaknessesList.innerHTML = data.weaknesses.map(w => `<li>${w}</li>`).join('');
            improvementText.value = data.improvement;
            resultsPanel.classList.add('visible');
        })
        .catch(err => console.error('Results fetch failed:', err));
}

function hideResults() {
    resultsPanel.classList.remove('visible');
}

// ── Fetch and Display Patient Profile ──────
async function loadPatientProfile(sid) {
    try {
        const resp = await fetch(`${API}/session/${sid}/profile`);
        if (!resp.ok) return; // Profile not available
        const profile = await resp.json();
        updateInspector('GET', `${API}/session/${sid}/profile`, resp.status, profile);

        // Populate profile UI
        profileAge.textContent = profile.age;
        profileGender.textContent = profile.gender;
        profileOccupation.textContent = profile.occupation;
        profileChiefComplaint.textContent = profile.chief_complaint;
        profileSeverity.textContent = profile.symptom_severity;
        profileOnset.textContent = profile.symptom_onset;
        profileResponseStyle.textContent = profile.response_style;
        profileEmotionalTone.textContent = profile.emotional_tone;

        // Risk status
        if (profile.risk_positive) {
            profileRisk.textContent = 'YES';
            profileRisk.classList.add('risk-positive');
            profileRiskText.textContent = profile.risk_detail;
            profileRiskDetail.style.display = 'block';
        } else {
            profileRisk.textContent = 'No';
            profileRisk.classList.remove('risk-positive');
            profileRiskDetail.style.display = 'none';
        }

        // Show profile section
        profileSection.classList.remove('hidden');
    } catch (err) {
        console.error('Could not load profile:', err);
    }
}

// ── Slider live-values ─────────────────────
roleThresh.addEventListener('input', () => {
    roleThreshVal.textContent = parseFloat(roleThresh.value).toFixed(2);
});
convoThresh.addEventListener('input', () => {
    convoThreshVal.textContent = parseFloat(convoThresh.value).toFixed(2);
});
judgeTemp.addEventListener('input', () => {
    judgeTempVal.textContent = parseFloat(judgeTemp.value).toFixed(2);
});

// ── Session state ─────────────────────────
function setSessionActive(id, condition, language) {
    sessionId = id;
    statusDot.classList.add('active');
    statusText.textContent = `Session: ${id.slice(0, 8)}…  |  ${condition} (${language})`;

    btnDelete.classList.remove('hidden');
    btnEvalPatient.disabled = false;
    btnEvalTrainee.disabled = false;
    chatInput.disabled = false;
    btnSend.disabled = false;
    chatEmpty.classList.add('hidden');

    // Load and display patient profile
    loadPatientProfile(id);

    // Start the timer
    startTimer();
}

function clearSession() {
    sessionId = null;
    statusDot.classList.remove('active');
    statusText.textContent = 'No active session';

    btnDelete.classList.add('hidden');
    btnEvalPatient.disabled = true;
    btnEvalTrainee.disabled = true;
    chatInput.disabled = true;
    btnSend.disabled = true;

    chatArea.innerHTML = '';
    chatArea.appendChild(chatEmpty);
    chatEmpty.classList.remove('hidden');

    profileSection.classList.add('hidden');
    patientResults.classList.add('hidden');
    traineeResults.classList.add('hidden');

    // Stop timer and hide results
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
    timerDisplay.classList.add('hidden');
    timerDisplay.classList.remove('expired');
    sessionExpired = false;
    hideResults();
}

// ── API helpers ───────────────────────────
async function apiCall(method, path, body = null) {
    const url = API + path;
    const opts = {
        method,
        headers: { 'Content-Type': 'application/json' },
    };
    if (body) opts.body = JSON.stringify(body);
    const resp = await fetch(url, opts);
    const data = await resp.json().catch(() => ({}));
    updateInspector(method, url, resp.status, data);
    return { ok: resp.ok, status: resp.status, data };
}

// ── Start Session ─────────────────────────
btnStart.addEventListener('click', async () => {
    const condition = conditionInput.value.trim();
    const language = languageSelect.value;
    if (!condition) return alert('Enter a patient condition first.');

    btnStart.disabled = true;
    btnStart.textContent = '…';

    try {
        const { ok, data } = await apiCall('POST', '/chat/start', { condition, language });
        if (ok) {
            setSessionActive(data.session_id, condition, language);
            addBubble('system', `Session started — ${condition} (${language})`);
        } else {
            alert(`Error: ${data.detail || 'Could not start session'}`);
        }
    } catch {
        alert('Could not connect to the API.');
    } finally {
        btnStart.disabled = false;
        btnStart.textContent = '▶ Start Session';
    }
});

// ── Delete Session ────────────────────────
btnDelete.addEventListener('click', async () => {
    if (!sessionId) return;
    if (!confirm('Delete this session and all its data?')) return;
    await apiCall('DELETE', `/chat/session/${sessionId}`);
    clearSession();
});

// ── Chat ──────────────────────────────────
function addBubble(role, content) {
    const div = document.createElement('div');
    div.className = `bubble ${role}`;
    div.textContent = content;
    chatArea.appendChild(div);
    chatArea.scrollTop = chatArea.scrollHeight;
    return div;
}

function addTyping() {
    const el = document.createElement('div');
    el.className = 'typing-indicator';
    el.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
    chatArea.appendChild(el);
    chatArea.scrollTop = chatArea.scrollHeight;
    return el;
}

async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text || isPending || !sessionId || sessionExpired) return;

    chatInput.value = '';
    chatInput.style.height = 'auto';
    addBubble('user', text);

    isPending = true;
    btnSend.disabled = true;
    chatInput.disabled = true;
    const typing = addTyping();

    const body = { session_id: sessionId, message: text };
    if (modelOverride.value.trim()) body.model = modelOverride.value.trim();
    if (reasoningOverride.value.trim()) body.reasoning_effort = reasoningOverride.value.trim();

    try {
        const { ok, data } = await apiCall('POST', '/chat/message', body);
        typing.remove();
        if (ok) {
            addBubble('assistant', data.content);
        } else {
            addBubble('system', `Error ${data.detail || 'LLM call failed'}`);
        }
    } catch {
        typing.remove();
        addBubble('system', 'Network error — check if the server is running.');
    } finally {
        isPending = false;
        btnSend.disabled = false;
        chatInput.disabled = false;
        chatInput.focus();
    }
}

btnSend.addEventListener('click', sendMessage);

chatInput.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});

// Auto-resize textarea
chatInput.addEventListener('input', () => {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
});

// ── Patient Evaluation ───────────────────
btnEvalPatient.addEventListener('click', async () => {
    if (!sessionId) return;
    btnEvalPatient.disabled = true;
    btnEvalPatient.textContent = 'Running…';
    patientResults.classList.add('hidden');

    const body = {
        session_id: sessionId,
        role_adherence_threshold: parseFloat(roleThresh.value),
        convo_quality_threshold: parseFloat(convoThresh.value),
    };

    try {
        const { ok, data } = await apiCall('POST', '/eval/patient', body);
        patientResultsSid.textContent = sessionId.slice(0, 8) + '…';
        patientResultsBody.innerHTML = ok ? renderPatientResults(data) : `<p style="color:var(--danger)">Error: ${data.detail || 'Evaluation failed'}</p>`;
        patientResults.classList.remove('hidden');
    } catch {
        patientResultsBody.innerHTML = '<p style="color:var(--danger)">Network error.</p>';
        patientResults.classList.remove('hidden');
    } finally {
        btnEvalPatient.disabled = false;
        btnEvalPatient.textContent = 'Run Patient Evaluation';
    }
});

function renderPatientResults(data) {
    const passCount = data.metrics.filter(m => m.passed).length;
    const total = data.metrics.length;

    let html = `
        <div class="score-summary">
            <div class="score-number neutral">${passCount}/${total}</div>
            <div class="score-details">
                <strong>Metrics Passed</strong>
                <p>Condition: ${data.condition} &nbsp;|&nbsp; Language: ${data.language}</p>
            </div>
            <span class="pass-badge ${passCount === total ? 'pass' : 'fail'}">${passCount === total ? 'ALL PASSED' : 'SOME FAILED'}</span>
        </div>
        <div class="metric-grid">
    `;

    data.metrics.forEach(m => {
        const pct = Math.round((m.score || 0) * 100);
        html += `
            <div class="metric-card ${m.passed ? 'pass-card' : 'fail-card'}">
                <div class="metric-header">
                    <div class="metric-name">${m.name || m.class}</div>
                    <div class="metric-score ${m.passed ? 'pass' : 'fail'}">${pct}%</div>
                </div>
                ${m.reason ? `<div class="metric-reason">${m.reason}</div>` : ''}
            </div>
        `;
    });

    html += '</div>';
    return html;
}

// ── Trainee Evaluation ────────────────────
btnEvalTrainee.addEventListener('click', async () => {
    if (!sessionId) return;
    btnEvalTrainee.disabled = true;
    btnEvalTrainee.textContent = 'Running…';
    traineeResults.classList.add('hidden');

    const body = { session_id: sessionId };
    if (rubricPath.value.trim()) body.rubric_path = rubricPath.value.trim();
    if (judgeModel.value.trim()) body.judge_model = judgeModel.value.trim();

    const judgeConfig = {};
    const temp = parseFloat(judgeTemp.value);
    if (temp > 0) judgeConfig.temperature = temp;
    judgeConfig.strict_schema = strictSchema.checked;
    body.judge_config = judgeConfig;

    try {
        const { ok, data } = await apiCall('POST', '/eval/trainee', body);
        traineeResultsSid.textContent = sessionId.slice(0, 8) + '…';
        traineeResultsBody.innerHTML = ok ? renderTraineeResults(data) : `<p style="color:var(--danger)">Error: ${data.detail || 'Evaluation failed'}</p>`;
        traineeResults.classList.remove('hidden');
    } catch {
        traineeResultsBody.innerHTML = '<p style="color:var(--danger)">Network error.</p>';
        traineeResults.classList.remove('hidden');
    } finally {
        btnEvalTrainee.disabled = false;
        btnEvalTrainee.textContent = 'Run Trainee Evaluation';
    }
});

function renderTraineeResults(d) {
    const pct = Math.round((d.percent || 0) * 100);
    const passClass = d.pass ? 'pass' : 'fail';

    let html = `
        <div class="score-summary">
            <div class="score-number ${passClass}">${pct}%</div>
            <div class="score-details">
                <strong>${d.pass ? 'Requirements Met' : 'Requirements Not Met'}</strong>
                <p>Score: ${d.total_score ?? '?'} / ${d.total_possible ?? '?'} &nbsp;|&nbsp; Minimum: ${Math.round((d.min_percent ?? 0) * 100)}%</p>
            </div>
            <span class="pass-badge ${passClass}">${d.pass ? 'PASS' : 'FAIL'}</span>
        </div>
    `;

    // Flags
    if (d.flags && d.flags.length > 0) {
        html += `<div class="flags-section"><h4>⚠ Flags (${d.flags.length})</h4>`;
        d.flags.forEach(f => {
            html += `<div class="flag-item"><span class="flag-type">${f.type}</span>: ${f.message} <span style="opacity:0.5">[${f.item_id}]</span></div>`;
        });
        html += '</div>';
    }

    // Feedback
    if (d.summary_feedback && d.summary_feedback.length > 0) {
        html += `<div class="section-title">📝 Reviewer Feedback</div><ul class="feedback-list">`;
        d.summary_feedback.forEach(s => { html += `<li>${s}</li>`; });
        html += '</ul>';
    }

    // Rubric table
    if (d.items && d.items.length > 0) {
        html += `
            <div class="section-title">📋 Rubric Checklist</div>
            <table class="rubric-table">
                <thead>
                    <tr>
                        <th>Item ID</th>
                        <th>Description</th>
                        <th>Achieved</th>
                        <th>Points</th>
                    </tr>
                </thead>
                <tbody>
        `;
        d.items.forEach(item => {
            const icon = !item.included ? '—' : item.achieved ? '✅' : '❌';
            const desc = item.description ? item.description.slice(0, 80) + (item.description.length > 80 ? '…' : '') : item.id;
            html += `
                <tr>
                    <td>${item.id}</td>
                    <td>${desc}</td>
                    <td class="status-icon">${icon}</td>
                    <td>${item.points_awarded ?? 0} / ${item.weight ?? 1}</td>
                </tr>
            `;
        });
        html += '</tbody></table>';
    }

    return html;
}

// ── Results Panel ──────────────────────────
closeResults.addEventListener('click', hideResults);
