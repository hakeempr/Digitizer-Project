/**
 * api.js — Centralized API client for Digitizer backend.
 *
 * All requests go to /api/v1/ (proxied to Django by Vite in dev,
 * served from the same origin in production).
 *
 * Token is stored in localStorage after login and attached to every
 * authenticated request via the Authorization header.
 */

const BASE = '/api/v1'

/** Read the auth token from localStorage. */
const getToken = () => localStorage.getItem('authToken')

/** Build standard headers, injecting the auth token if present. */
const headers = (extra = {}) => {
  const h = { 'Content-Type': 'application/json', ...extra }
  const token = getToken()
  if (token) h['Authorization'] = `Token ${token}`
  return h
}

/** Generic fetch wrapper with error normalisation. */
async function request(method, path, body = null, isMultipart = false) {
  const opts = {
    method,
    headers: isMultipart
      ? { Authorization: `Token ${getToken()}` }   // let browser set Content-Type for FormData
      : headers(),
  }
  if (body) opts.body = isMultipart ? body : JSON.stringify(body)

  const res = await fetch(`${BASE}${path}`, opts)
  const data = res.headers.get('Content-Type')?.includes('application/json')
    ? await res.json()
    : await res.text()

  if (!res.ok) {
    const message =
      typeof data === 'object'
        ? Object.values(data).flat().join(' ')
        : data || `HTTP ${res.status}`
    throw new Error(message)
  }

  return data
}

const get  = (path)        => request('GET',    path)
const post = (path, body, isMultipart = false) => request('POST', path, body, isMultipart)
const patch= (path, body)  => request('PATCH',  path, body)
const del  = (path)        => request('DELETE', path)

/* ─── Auth ──────────────────────────────────────────────── */

export const auth = {
  /** POST /auth/login/ → stores token, returns user info */
  login: async (email, password) => {
    const data = await post('/auth/login/', { email, password })
    localStorage.setItem('authToken', data.token)
    localStorage.setItem('userRole',  data.role)
    localStorage.setItem('userName',  data.full_name)
    localStorage.setItem('userEmail', data.email)
    localStorage.setItem('userId',    data.user_id)
    return data
  },

  /** POST /auth/logout/ → clears localStorage */
  logout: async () => {
    try { await post('/auth/logout/', {}) } catch (_) {}
    localStorage.clear()
  },

  /** POST /auth/register/ */
  register: (payload) => post('/auth/register/', payload),

  /** GET /auth/profile/ */
  getProfile: () => get('/auth/profile/'),

  /** PATCH /auth/profile/ */
  updateProfile: (payload) => patch('/auth/profile/', payload),

  /** POST /auth/change-password/ */
  changePassword: (oldPassword, newPassword) =>
    post('/auth/change-password/', { old_password: oldPassword, new_password: newPassword }),

  /** Helpers — read from localStorage without a network call */
  isLoggedIn: () => Boolean(getToken()),
  getRole:    () => localStorage.getItem('userRole'),
  getUser:    () => ({
    name:  localStorage.getItem('userName'),
    email: localStorage.getItem('userEmail'),
    id:    localStorage.getItem('userId'),
    role:  localStorage.getItem('userRole'),
  }),
}

/* ─── Customer — Documents ───────────────────────────────── */

export const documents = {
  /** POST /customer/documents/ — multipart upload */
  upload: (formData) => post('/customer/documents/', formData, true),

  /** GET /customer/documents/list/ */
  list: () => get('/customer/documents/list/'),

  /** GET /customer/documents/<id>/ */
  detail: (id) => get(`/customer/documents/${id}/`),

  /** GET /customer/documents/<id>/status/ */
  status: (id) => get(`/customer/documents/${id}/status/`),

  /** GET /api/v1/documents/<id>/download/ — returns a blob URL */
  downloadUrl: (id) => `${BASE}/documents/${id}/download/`,

  /** GET /api/v1/documents/<id>/export/html/ */
  exportHtmlUrl: (id) => `${BASE}/documents/${id}/export/html/`,

  /** POST /api/v1/documents/<id>/regenerate/ */
  regenerate: (id, styleTemplate) =>
    post(`/documents/${id}/regenerate/`, { style_template: styleTemplate }),

  /** GET /api/v1/documents/styles/ */
  styles: () => get('/documents/styles/'),
}

/* ─── Customer — Feedback ────────────────────────────────── */

export const feedback = {
  /** POST /customer/feedbacks/ */
  submit: (documentId, rating, body) =>
    post('/customer/feedbacks/', { document: documentId, rating, body }),

  /** GET /customer/feedbacks/list/ */
  list: () => get('/customer/feedbacks/list/'),
}

/* ─── Customer — Complaints ──────────────────────────────── */

export const complaints = {
  /** POST /customer/complaints/ */
  submit: (subject, body) =>
    post('/customer/complaints/', { subject, body }),

  /** GET /customer/complaints/list/ */
  list: () => get('/customer/complaints/list/'),
}

/* ─── Customer — Inbox ───────────────────────────────────── */

export const inbox = {
  /** GET /customer/inbox/ */
  list: () => get('/customer/inbox/'),

  /** POST /customer/inbox/<id>/read/ */
  markRead: (id) => post(`/customer/inbox/${id}/read/`, {}),

  /** GET /notify/unread-count/ */
  unreadCount: () => get('/notify/unread-count/'),

  /** POST /notify/mark-all-read/ */
  markAllRead: () => post('/notify/mark-all-read/', {}),
}

/* ─── Admin — Dashboard ──────────────────────────────────── */

export const adminDashboard = {
  /** GET /admin/dashboard/ */
  stats: () => get('/admin/dashboard/'),
}

/* ─── Admin — Account Requests ───────────────────────────── */

export const adminRequests = {
  /** GET /admin/account-requests/?decision=pending */
  list: (decision = '') =>
    get(`/admin/account-requests/${decision ? `?decision=${decision}` : ''}`),

  /** GET /admin/account-requests/<id>/ */
  detail: (id) => get(`/admin/account-requests/${id}/`),

  /** POST /admin/account-requests/<id>/decide/ */
  decide: (id, decision, adminNotes = '') =>
    post(`/admin/account-requests/${id}/decide/`, { decision, admin_notes: adminNotes }),
}

/* ─── Admin — Complaints ─────────────────────────────────── */

export const adminComplaints = {
  /** GET /admin/complaints/?status=open */
  list: (status = '') =>
    get(`/admin/complaints/${status ? `?status=${status}` : ''}`),

  /** GET /admin/complaints/<id>/ */
  detail: (id) => get(`/admin/complaints/${id}/`),

  /** POST /admin/complaints/<id>/reply/ */
  reply: (id, body) =>
    post(`/admin/complaints/${id}/reply/`, { body }),
}

/* ─── Admin — Feedback ───────────────────────────────────── */

export const adminFeedback = {
  /** GET /admin/feedbacks/ */
  list: () => get('/admin/feedbacks/'),

  /** POST /admin/feedbacks/<id>/reply/ */
  reply: (id, body) =>
    post(`/admin/feedbacks/${id}/reply/`, { body }),
}

/* ─── OCR Engine ─────────────────────────────────────────── */

export const ocr = {
  /** POST /ocr/trigger/<doc_id>/ — admin only */
  trigger: (docId) => post(`/ocr/trigger/${docId}/`, {}),

  /** GET /ocr/result/<doc_id>/ */
  rawResult: (docId) => get(`/ocr/result/${docId}/`),
}
