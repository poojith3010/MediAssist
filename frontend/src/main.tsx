import { FormEvent, useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

const API = ((import.meta as ImportMeta & { env?: { VITE_API_URL?: string } }).env?.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");

type User = { id: number; email: string };
type DocumentItem = { id: number; filename: string; status: string; extracted_text: string; created_at: string };
type Source = { document_id: number; title: string; page_number: number | null };
type Message = { role: "user" | "assistant"; text: string; sources?: Source[] };

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API}${path}`, { credentials: "include", ...options });
  if (!response.ok) {
    let detail = "Something went wrong. Please try again.";
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch { /* empty error response */ }
    throw new Error(detail);
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [checking, setChecking] = useState(true);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [error, setError] = useState("");

  useEffect(() => {
    request<User>("/api/v1/users/me").then(setUser).catch(() => undefined).finally(() => setChecking(false));
  }, []);

  async function authenticate(email: string, password: string) {
    setError("");
    try {
      const result = await request<User>(`/api/v1/auth/${authMode === "login" ? "login" : "register"}`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email, password }),
      });
      setUser(result);
    } catch (err) { setError(err instanceof Error ? err.message : "Unable to authenticate."); }
  }

  if (checking) return <div className="loading-screen"><span className="spinner" />Loading your workspace…</div>;
  return user ? <Dashboard user={user} onLogout={() => setUser(null)} /> :
    <Auth mode={authMode} setMode={setAuthMode} onSubmit={authenticate} error={error} />;
}

function Auth({ mode, setMode, onSubmit, error }: { mode: "login" | "register"; setMode: (m: "login" | "register") => void; onSubmit: (email: string, password: string) => void; error: string }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const submit = (event: FormEvent) => { event.preventDefault(); onSubmit(email, password); };
  return <main className="auth-page">
    <div className="auth-brand"><div className="brand-mark">✦</div><span>MediAssist</span></div>
    <section className="auth-card">
      <div className="auth-intro"><p className="eyebrow">YOUR PRIVATE HEALTH LIBRARY</p><h1>{mode === "login" ? "Welcome back." : "Create your safe space."}</h1><p>Understand your health information with clarity, grounded in your own documents.</p></div>
      <div className="tabs"><button className={mode === "login" ? "active" : ""} onClick={() => { setMode("login"); }} type="button">Sign in</button><button className={mode === "register" ? "active" : ""} onClick={() => { setMode("register"); }} type="button">Create account</button></div>
      <form onSubmit={submit}>
        <label>Email address<input required type="email" autoComplete="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" /></label>
        <label>Password<input required minLength={8} type="password" autoComplete={mode === "login" ? "current-password" : "new-password"} value={password} onChange={e => setPassword(e.target.value)} placeholder="At least 8 characters" /></label>
        {error && <p className="form-error" role="alert">{error}</p>}
        <button className="primary full" type="submit">{mode === "login" ? "Sign in to MediAssist" : "Create my account"} <span>→</span></button>
      </form>
      <p className="privacy-note">🔒 Your session is private and protected.</p>
    </section>
    <p className="auth-disclaimer">MediAssist is for education only — not medical advice, diagnosis, or treatment.</p>
  </main>;
}

function Dashboard({ user, onLogout }: { user: User; onLogout: () => void }) {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [loadingChat, setLoadingChat] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const fileInput = useRef<HTMLInputElement>(null);

  async function loadDocuments() {
    try { setDocuments(await request<DocumentItem[]>("/api/v1/documents")); } catch (err) { setError(err instanceof Error ? err.message : "Unable to load documents."); }
  }
  useEffect(() => { loadDocuments(); }, []);

  async function upload(file?: File) {
    if (!file) return;
    if (file.type !== "application/pdf") { setError("Only PDF files can be uploaded."); return; }
    setUploading(true); setError(""); setNotice("");
    const body = new FormData(); body.append("file", file);
    try { await request<DocumentItem>("/api/v1/documents", { method: "POST", body }); await loadDocuments(); setNotice(`${file.name} is ready to use.`); }
    catch (err) { setError(err instanceof Error ? err.message : "Upload failed."); } finally { setUploading(false); }
  }
  async function removeDocument(doc: DocumentItem) {
    if (!window.confirm(`Delete “${doc.filename}”?`)) return;
    try { await request<void>(`/api/v1/documents/${doc.id}`, { method: "DELETE" }); setDocuments(items => items.filter(item => item.id !== doc.id)); }
    catch (err) { setError(err instanceof Error ? err.message : "Unable to delete document."); }
  }
  async function ask(event: FormEvent) {
    event.preventDefault(); const text = question.trim(); if (!text || loadingChat) return;
    setQuestion(""); setError(""); setMessages(items => [...items, { role: "user", text }]); setLoadingChat(true);
    try {
      const result = await request<{ answer: string; sources: Source[] }>("/api/v1/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question: text }) });
      setMessages(items => [...items, { role: "assistant", text: result.answer, sources: result.sources }]);
    } catch (err) { setMessages(items => [...items, { role: "assistant", text: err instanceof Error ? err.message : "The assistant is unavailable right now." }]); }
    finally { setLoadingChat(false); }
  }
  async function logout() { await request<void>("/api/v1/auth/logout", { method: "POST" }).catch(() => undefined); onLogout(); }

  return <div className="app-shell">
    <aside className="sidebar"><div className="brand"><div className="brand-mark">✦</div><strong>MediAssist</strong></div><div className="side-label">Workspace</div><div className="nav-item active"><span>◈</span> Overview</div><div className="side-footer"><div className="user-chip"><div className="avatar">{user.email[0].toUpperCase()}</div><div><strong>{user.email.split("@")[0]}</strong><small>{user.email}</small></div></div><button className="logout" onClick={logout}>Sign out</button></div></aside>
    <main className="dashboard">
      <header className="topbar"><div><p className="eyebrow">OVERVIEW</p><h1>Your health workspace</h1></div><div className="status-pill"><span /> Private & secure</div></header>
      {error && <div className="alert error" role="alert">{error}<button onClick={() => setError("")}>×</button></div>}
      {notice && <div className="alert success">{notice}<button onClick={() => setNotice("")}>×</button></div>}
      <div className="disclaimer"><span className="shield">♢</span><div><strong>A safe place to learn</strong><p>MediAssist provides educational information from your documents, not medical advice. Always consult a qualified healthcare professional for decisions about your care.</p></div></div>
      <div className="content-grid">
        <section className="panel documents-panel"><div className="panel-heading"><div><p className="eyebrow">YOUR LIBRARY</p><h2>Documents <span>{documents.length}</span></h2></div><button className="icon-button" title="Upload document" onClick={() => fileInput.current?.click()}>＋</button></div>
          <input ref={fileInput} hidden type="file" accept="application/pdf" onChange={e => upload(e.target.files?.[0])} />
          <button className="dropzone" onClick={() => fileInput.current?.click()} onDragOver={e => e.preventDefault()} onDrop={e => { e.preventDefault(); upload(e.dataTransfer.files[0]); }} disabled={uploading}><span className="upload-icon">↑</span><strong>{uploading ? "Processing document…" : "Drop a PDF here or browse"}</strong><small>PDF files only · securely processed</small></button>
          {documents.length === 0 ? <div className="empty"><span>▤</span><p>Your library is empty</p><small>Upload a health document to ask grounded questions.</small></div> : <div className="document-list">{documents.map(doc => <div className="document-row" key={doc.id}><span className="file-icon">PDF</span><div className="doc-info"><strong>{doc.filename}</strong><small>{new Date(doc.created_at).toLocaleDateString()} · {doc.status === "processed" ? "Ready" : "Needs review"}</small></div><button className="delete-button" title={`Delete ${doc.filename}`} onClick={() => removeDocument(doc)}>×</button></div>)}</div>}
        </section>
        <section className="panel chat-panel"><div className="panel-heading"><div><p className="eyebrow">DOCUMENT Q&A</p><h2>Ask MediAssist <span className="online-dot" /></h2></div><span className="ai-label">AI assistant</span></div><div className="chat-body">{messages.length === 0 ? <div className="chat-empty"><div className="sparkle">✦</div><h3>What would you like to understand?</h3><p>Ask a question about your uploaded documents. Answers include page citations so you can verify the context.</p><div className="suggestions"><button onClick={() => setQuestion("Summarize my latest document")}>Summarize my latest document</button><button onClick={() => setQuestion("What should I ask my doctor?")}>What should I ask my doctor?</button></div></div> : messages.map((message, index) => <div className={`message ${message.role}`} key={index}><div className="message-avatar">{message.role === "user" ? user.email[0].toUpperCase() : "✦"}</div><div className="message-content"><p>{message.text}</p>{message.sources && message.sources.length > 0 && <div className="citations"><small>Sources</small>{message.sources.map((source, i) => <span key={i}>▧ {source.title}{source.page_number ? ` · p. ${source.page_number}` : ""}</span>)}</div>}</div></div>)}</div><form className="chat-input" onSubmit={ask}><input value={question} onChange={e => setQuestion(e.target.value)} placeholder="Ask a question about your documents…" aria-label="Ask a question" /><button className="send-button" disabled={loadingChat || !question.trim()}>{loadingChat ? <span className="spinner" /> : "↑"}</button></form></section>
      </div>
      <footer className="footer-note">MediAssist can make mistakes. Verify important information with your healthcare provider.</footer>
    </main>
  </div>;
}

createRoot(document.getElementById("root")!).render(<App />);
