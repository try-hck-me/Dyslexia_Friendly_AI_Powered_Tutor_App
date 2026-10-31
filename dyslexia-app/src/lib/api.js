/**
 * Frontend API layer — all calls to the FastAPI backend.
 *
 * All functions return a standard shape:
 *   { success: boolean, data?: any, error?: string, message?: string }
 *
 * API_BASE is set in constants.js (e.g. "http://localhost:8000")
 */

import { API_BASE } from './constants';

// ── Low-level helpers ─────────────────────────────────────────────

async function request(path, options = {}) {
  try {
    const res = await fetch(`${API_BASE}${path}`, options);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || `Request failed (${res.status})`);
    return data;
  } catch (err) {
    if (err.name === 'TypeError') {
      throw new Error('Cannot connect to server. Is the backend running on port 8000?');
    }
    throw err;
  }
}

function post(path, body) {
  return request(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

// ── Health ────────────────────────────────────────────────────────

/** Basic liveness check — returns { status: "healthy" } */
export function healthCheck()  { return request('/'); }

/** Detailed component status — DB, ChromaDB, Knowledge Graph */
export function getStatus()    { return request('/status'); }

// ── Auth / User management ────────────────────────────────────────

/**
 * Register (upsert) a user in SQLite.
 * Called on Sign Up so the DB always has the user before any other action.
 */
export function registerUser(userId, name, role) {
  return post('/users/register', { user_id: userId, name, role });
}

/**
 * Look up a user by ID.
 * Always returns 200 with an `exists` boolean flag.
 * Used by Sign In to verify the user exists, and by parents to verify a child ID.
 */
export function getUser(userId) {
  return request(`/users/${encodeURIComponent(userId)}`);
}

// ── Documents ────────────────────────────────────────────────────

/** Upload a PDF for background processing */
export function uploadPDF(file) {
  const formData = new FormData();
  formData.append('file', file);
  return request('/upload', { method: 'POST', body: formData });
}

/** Poll the progress of an in-flight upload */
export function getUploadStatus(filename) {
  return request(`/upload/status/${encodeURIComponent(filename)}`);
}

/**
 * Get the list of documents that are actually indexed in ChromaDB.
 * This is the authoritative list — not localStorage.
 */
export function getDocuments() {
  return request('/documents');
}

/**
 * Fetch the full extracted text for a specific document.
 */
export function getDocumentContent(filename) {
  return request(`/documents/${encodeURIComponent(filename)}/content`);
}

/**
 * Delete a document from the backend.
 */
export function deleteDocument(filename) {
  return request(`/documents/${encodeURIComponent(filename)}`, { method: 'DELETE' });
}

// ── Chat ─────────────────────────────────────────────────────────

/** Ask a RAG question about uploaded notes */
export function sendChat(userId, question) {
  return post('/chat', { user_id: userId, question });
}

/**
 * Retrieve the last N chat messages for a user (chronological order).
 * @param {number} limit  Max messages to return (default 20)
 */
export function getChatHistory(userId, limit = 20) {
  return request(`/chat/history/${encodeURIComponent(userId)}?limit=${limit}`);
}

// ── FriendlyBot ──────────────────────────────────────────────────

/** Send a message to FriendlyBot (emotional support AI) */
export function sendFriendly(userId, message) {
  return post('/friendly', { user_id: userId, message });
}

// ── Quiz ─────────────────────────────────────────────────────────

/** Generate an adaptive quiz for a topic */
export function generateQuiz(userId, topic, numQuestions = 5) {
  return post('/quiz', { user_id: userId, topic, num_questions: numQuestions });
}

/**
 * Submit quiz answers.
 * @param {string} difficulty  The difficulty returned by /quiz — passed back so it's stored correctly
 */
export function submitQuiz(userId, topic, difficulty, questions, answers) {
  return post('/quiz/submit', {
    user_id: userId,
    topic,
    difficulty,      // ← now properly forwarded to the backend
    questions,
    answers,
  });
}

// ── Analytics ─────────────────────────────────────────────────────

/**
 * Get full analytics dashboard for a user.
 * Returns: study_stats, all_topics, weak_topics, mood_trends, recommendations
 */
export function getAnalytics(userId) {
  return request(`/analytics/${encodeURIComponent(userId)}`);
}

// ── Knowledge Graph ───────────────────────────────────────────────

/** Get graph nodes and edges for the SVG visualisation */
export function getGraphViz() {
  return request('/graph/viz');
}

// ── Text-to-Speech ────────────────────────────────────────────────

/** Synthesise speech via Sarvam AI. Text is capped at 2490 chars. */
export function synthesizeTTS(text, speaker = 'shubh') {
  return post('/tts', { text: String(text).slice(0, 2490), speaker });
}
