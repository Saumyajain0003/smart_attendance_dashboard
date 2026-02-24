import { useState, useEffect, useRef, useCallback } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

// ─── STYLES ──────────────────────────────────────────────────────────────────
const G = {
  bg: "#04050a",
  surface: "#0c0e1a",
  surface2: "#111628",
  accent: "#00f5c4",
  accent2: "#7b61ff",
  danger: "#ff4b6e",
  warning: "#ffb830",
  text: "#e8eaf6",
  muted: "#6b7299",
  border: "rgba(255,255,255,0.07)",
};

const injectFonts = () => {
  if (document.getElementById("aq-fonts")) return;
  const l = document.createElement("link");
  l.id = "aq-fonts";
  l.rel = "stylesheet";
  l.href = "https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Space+Mono:wght@400;700&display=swap";
  document.head.appendChild(l);

  const s = document.createElement("style");
  s.textContent = `
    *{box-sizing:border-box;margin:0;padding:0}
    body{background:${G.bg};color:${G.text};font-family:'Syne',sans-serif}
    input[type=range]{-webkit-appearance:none;width:100%;height:4px;border-radius:10px;background:rgba(255,255,255,0.08);outline:none;cursor:pointer}
    input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:16px;height:16px;border-radius:50%;background:${G.accent};box-shadow:0 0 10px ${G.accent};cursor:pointer}
    ::-webkit-scrollbar{width:5px}
    ::-webkit-scrollbar-track{background:transparent}
    ::-webkit-scrollbar-thumb{background:rgba(255,255,255,0.1);border-radius:10px}
    @keyframes aq-pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.5;transform:scale(.8)}}
    @keyframes aq-fadeUp{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}
    @keyframes aq-spin{to{transform:rotate(360deg)}}
    @keyframes aq-toast{from{transform:translateX(30px);opacity:0}to{transform:translateX(0);opacity:1}}
    @keyframes aq-slideIn{from{transform:translateX(-18px);opacity:0}to{transform:translateX(0);opacity:1}}
  `;
  document.head.appendChild(s);
};

// ─── DATA ────────────────────────────────────────────────────────────────────
const API_BASE = "http://localhost:8000";

const fetchStudents = async () => {
  try {
    const res = await fetch(`${API_BASE}/attendance/below-threshold?threshold=100`);
    if (!res.ok) throw new Error("API Offline");
    return await res.json();
  } catch (e) {
    console.error("Fetch error:", e);
    return [];
  }
};

const deleteStudent = async (id) => {
  try {
    const res = await fetch(`${API_BASE}/students/${id}`, { method: "DELETE" });
    return res.ok;
  } catch (e) {
    console.error("Delete error:", e);
    return false;
  }
};

// ─── HELPERS ─────────────────────────────────────────────────────────────────
const delay = (ms) => new Promise((r) => setTimeout(r, ms));

const attColor = (a) => (a < 60 ? G.danger : a < 75 ? G.warning : G.accent);

const realPredict = async (name, t1, t2, t3, att) => {
  try {
    const res = await fetch(`${API_BASE}/predict/realtime`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, term1: t1, term2: t2, term3: t3, attendance_score: att }),
    });
    const data = await res.json();
    return { passed: data.predicted_pass, confidence: data.probability, model: data.model_used };
  } catch (e) {
    console.error("Prediction error:", e);
    return { passed: false, confidence: 0, model: "Error" };
  }
};

// ─── 3D GRID CANVAS ──────────────────────────────────────────────────────────
function Grid3D() {
  const canvasRef = useRef(null);
  const mouse = useRef({ x: 0.5, y: 0.5 });
  const tRef = useRef(0);
  const rafRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener("resize", resize);

    const onMouse = (e) => {
      mouse.current.x = e.clientX / window.innerWidth;
      mouse.current.y = e.clientY / window.innerHeight;
    };
    window.addEventListener("mousemove", onMouse);

    const COLS = 22, ROWS = 16, PERSP = 600;

    const project = (x, y, z, tiltX, tiltY, cw, ch) => {
      const scale = PERSP / (PERSP + z);
      const cx = cw / 2, cy = ch * 0.65;
      const rx = (x * Math.cos(tiltY) - z * Math.sin(tiltY)) * scale;
      const ry = y * Math.cos(tiltX) * scale;
      return [cx + rx, cy + ry, scale];
    };

    const draw = () => {
      tRef.current += 0.006;
      const t = tRef.current;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const tiltX = (mouse.current.y - 0.5) * 0.4;
      const tiltY = (mouse.current.x - 0.5) * 0.4;
      const cellW = 120, cellH = 80;
      const totalW = COLS * cellW, totalH = ROWS * cellH;
      const ox = t * 30, oy = t * 20;

      for (let r = 0; r <= ROWS; r++) {
        for (let c = 0; c <= COLS; c++) {
          const x = c * cellW - totalW / 2 + (ox % cellW);
          const y = r * cellH - totalH / 2 + (oy % cellH);
          const wave = Math.sin(x * 0.01 + t) * Math.cos(y * 0.01 + t * 0.7) * 30;
          const [px, py, sc] = project(x, y, wave * 3, tiltX, tiltY, canvas.width, canvas.height);

          if (c < COLS) {
            const x2 = (c + 1) * cellW - totalW / 2 + (ox % cellW);
            const wave2 = Math.sin(x2 * 0.01 + t) * Math.cos(y * 0.01 + t * 0.7) * 30;
            const [px2, py2] = project(x2, y, wave2 * 3, tiltX, tiltY, canvas.width, canvas.height);
            ctx.beginPath(); ctx.moveTo(px, py); ctx.lineTo(px2, py2);
            ctx.strokeStyle = `rgba(0,245,196,${Math.min(sc * 0.4, 0.15)})`;
            ctx.lineWidth = 0.5; ctx.stroke();
          }
          if (r < ROWS) {
            const y2 = (r + 1) * cellH - totalH / 2 + (oy % cellH);
            const wave2 = Math.sin(x * 0.01 + t) * Math.cos(y2 * 0.01 + t * 0.7) * 30;
            const [px2, py2] = project(x, y2, wave2 * 3, tiltX, tiltY, canvas.width, canvas.height);
            ctx.beginPath(); ctx.moveTo(px, py); ctx.lineTo(px2, py2);
            ctx.strokeStyle = `rgba(123,97,255,${Math.min(sc * 0.4, 0.12)})`;
            ctx.lineWidth = 0.5; ctx.stroke();
          }
        }
      }
      rafRef.current = requestAnimationFrame(draw);
    };
    draw();

    return () => {
      window.removeEventListener("resize", resize);
      window.removeEventListener("mousemove", onMouse);
      cancelAnimationFrame(rafRef.current);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{ position: "fixed", top: 0, left: 0, width: "100%", height: "100%", zIndex: 0, pointerEvents: "none" }}
    />
  );
}

// ─── TOAST ───────────────────────────────────────────────────────────────────
function Toast({ msg, type, visible }) {
  if (!visible) return null;
  return (
    <div style={{
      position: "fixed", bottom: "2rem", right: "2rem", zIndex: 9999,
      background: G.surface, border: `1px solid ${G.border}`,
      borderLeft: `3px solid ${type === "error" ? G.danger : G.accent}`,
      borderRadius: 12, padding: "0.9rem 1.4rem", fontSize: "0.83rem",
      boxShadow: "0 20px 60px rgba(0,0,0,0.6)", maxWidth: 300,
      fontFamily: "'Space Mono',monospace", color: G.text,
      animation: "aq-toast 0.4s ease",
    }}>{msg}</div>
  );
}

// ─── STAT CARD ───────────────────────────────────────────────────────────────
function StatCard({ label, value, sub, color, icon }) {
  const [hov, setHov] = useState(false);
  return (
    <div
      onMouseEnter={() => setHov(true)}
      onMouseLeave={() => setHov(false)}
      style={{
        background: G.surface, border: `1px solid ${hov ? "rgba(255,255,255,0.14)" : G.border}`,
        borderRadius: 16, padding: "1.4rem", position: "relative", overflow: "hidden",
        transform: hov ? "translateY(-4px)" : "translateY(0)",
        transition: "all 0.3s", cursor: "default",
        boxShadow: hov ? `0 16px 40px rgba(0,0,0,0.4)` : "none",
      }}
    >
      <div style={{ position: "absolute", top: "1.1rem", right: "1.1rem", fontSize: "1.3rem", opacity: 0.45 }}>{icon}</div>
      <div style={{ fontSize: "0.68rem", fontFamily: "'Space Mono',monospace", letterSpacing: "1.5px", textTransform: "uppercase", color: G.muted, marginBottom: "0.7rem" }}>{label}</div>
      <div style={{ fontSize: "2.6rem", fontWeight: 800, lineHeight: 1, color, marginBottom: "0.3rem" }}>{value}</div>
      <div style={{ fontSize: "0.76rem", color: G.muted }}>{sub}</div>
    </div>
  );
}

// ─── PANEL WRAPPER ────────────────────────────────────────────────────────────
function Panel({ title, badge, children, style = {} }) {
  return (
    <div style={{ background: G.surface, border: `1px solid ${G.border}`, borderRadius: 20, overflow: "hidden", ...style }}>
      <div style={{ padding: "1.1rem 1.5rem", borderBottom: `1px solid ${G.border}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ fontSize: "0.7rem", fontFamily: "'Space Mono',monospace", letterSpacing: "1px", textTransform: "uppercase", color: G.muted }}>{title}</div>
        {badge && <div style={{ fontSize: "0.68rem", fontFamily: "'Space Mono',monospace", color: G.accent }}>{badge}</div>}
      </div>
      <div style={{ padding: "1.4rem" }}>{children}</div>
    </div>
  );
}

// ─── STUDENT TABLE ───────────────────────────────────────────────────────────
function StudentTable({ onPredict, onDelete, students }) {
  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ borderBottom: `1px solid ${G.border}` }}>
            {["ID", "Student", "Attendance", "T1", "T2", "T3", "Action"].map((h) => (
              <th key={h} style={{
                textAlign: "left", padding: "0 1rem 0.9rem", fontSize: "0.68rem",
                fontFamily: "'Space Mono',monospace", letterSpacing: "1.5px", textTransform: "uppercase",
                color: G.muted, fontWeight: 400, whiteSpace: "nowrap"
              }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {students.map((s) => (
            <tr key={s.student_id} style={{ borderBottom: `1px solid ${G.border}` }}
              onMouseEnter={(e) => e.currentTarget.style.background = "rgba(255,255,255,0.025)"}
              onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}>
              <td style={{ padding: "0.85rem 1rem", fontFamily: "'Space Mono',monospace", fontSize: "0.68rem", color: G.muted }}>
                {s.student_code}
              </td>
              <td style={{ padding: "0.85rem 1rem" }}>
                <div style={{ fontWeight: 700, fontSize: "0.88rem" }}>{s.name}</div>
              </td>
              <td style={{ padding: "0.85rem 1rem" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <div style={{ width: 72, height: 4, background: "rgba(255,255,255,0.08)", borderRadius: 10, overflow: "hidden" }}>
                    <div style={{ width: `${s.attendance_percentage}%`, height: "100%", background: attColor(s.attendance_percentage), borderRadius: 10, transition: "width 1s ease" }} />
                  </div>
                  <span style={{ fontFamily: "'Space Mono',monospace", fontSize: "0.73rem", color: attColor(s.attendance_percentage) }}>{s.attendance_percentage}%</span>
                </div>
              </td>
              {[s.term1, s.term2, s.term3].map((v, i) => (
                <td key={i} style={{ padding: "0.85rem 1rem", fontFamily: "'Space Mono',monospace", fontSize: "0.78rem", color: (v || 0) < 50 ? G.danger : G.text }}>{v ? Number(v).toFixed(0) : 0}</td>
              ))}
              <td style={{ padding: "0.85rem 1rem" }}>
                <div style={{ display: "flex", gap: "0.5rem" }}>
                  <button onClick={() => onPredict(s)}
                    style={{
                      background: "rgba(255,255,255,0.05)", border: `1px solid ${G.border}`,
                      color: G.muted, padding: "0.28rem 0.7rem", borderRadius: 6,
                      fontSize: "0.68rem", fontFamily: "'Space Mono',monospace", cursor: "pointer",
                      transition: "all 0.2s"
                    }}
                    onMouseEnter={(e) => { e.target.style.background = "rgba(0,245,196,0.1)"; e.target.style.color = G.accent; e.target.style.borderColor = `${G.accent}55`; }}
                    onMouseLeave={(e) => { e.target.style.background = "rgba(255,255,255,0.05)"; e.target.style.color = G.muted; e.target.style.borderColor = G.border; }}
                  >Predict</button>
                  <button onClick={() => onDelete(s.student_id)}
                    style={{
                      background: "rgba(255,75,110,0.05)", border: `1px solid rgba(255,75,110,0.2)`,
                      color: G.danger, padding: "0.28rem 0.7rem", borderRadius: 6,
                      fontSize: "0.68rem", fontFamily: "'Space Mono',monospace", cursor: "pointer",
                      transition: "all 0.2s"
                    }}
                    onMouseEnter={(e) => { e.target.style.background = G.danger; e.target.style.color = "#000"; }}
                    onMouseLeave={(e) => { e.target.style.background = "rgba(255,75,110,0.05)"; e.target.style.color = G.danger; }}
                  >×</button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─── PREDICTOR ───────────────────────────────────────────────────────────────
function Predictor({ initial, toast }) {
  const [vals, setVals] = useState(initial || { t1: 65, t2: 58, t3: 52, att: 68 });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => { if (initial) setVals(initial); }, [initial]);

  const update = (key, v) => setVals((p) => ({ ...p, [key]: +v }));

  const run = async () => {
    setLoading(true);
    setResult(null);
    const res = await realPredict("New Student", vals.t1, vals.t2, vals.t3, vals.att);
    setResult(res);
    setLoading(false);
    toast(`${res.passed ? "✅ PASS" : "❌ FAIL"} predicted via ${res.model}`);
  };

  const sliders = [
    { key: "t1", label: "Term 1 Score", color: G.accent },
    { key: "t2", label: "Term 2 Score", color: G.accent },
    { key: "t3", label: "Term 3 Score", color: G.accent },
    { key: "att", label: "Attendance %", color: vals.att < 60 ? G.danger : vals.att < 75 ? G.warning : G.accent },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.1rem" }}>
      {sliders.map(({ key, label, color }) => (
        <div key={key}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.45rem" }}>
            <label style={{ fontSize: "0.67rem", fontFamily: "'Space Mono',monospace", letterSpacing: "1px", textTransform: "uppercase", color: G.muted }}>{label}</label>
            <span style={{ fontFamily: "'Space Mono',monospace", fontSize: "0.82rem", color, fontWeight: 700 }}>{vals[key]}</span>
          </div>
          <input type="range" min="0" max="100" value={vals[key]} onChange={(e) => update(key, e.target.value)} />
        </div>
      ))}

      <button onClick={run} disabled={loading}
        style={{
          width: "100%", padding: "0.85rem", background: loading ? "rgba(0,245,196,0.3)" : `linear-gradient(135deg, ${G.accent}, #00c9a0)`,
          color: "#000", border: "none", borderRadius: 12, fontFamily: "'Syne',sans-serif",
          fontSize: "0.92rem", fontWeight: 700, cursor: loading ? "not-allowed" : "pointer",
          transition: "all 0.3s", letterSpacing: 0.5
        }}
        onMouseEnter={(e) => !loading && (e.target.style.boxShadow = `0 8px 28px rgba(0,245,196,0.35)`)}
        onMouseLeave={(e) => (e.target.style.boxShadow = "none")}
      >
        {loading ? "Running…" : "⚡ Run Prediction"}
      </button>

      {result && (
        <div style={{
          background: G.surface2, border: `1px solid ${G.border}`, borderRadius: 12, padding: "1.1rem",
          animation: "aq-fadeUp 0.45s ease"
        }}>
          <div style={{ fontSize: "1.3rem", fontWeight: 800, color: result.passed ? G.accent : G.danger, marginBottom: "0.25rem" }}>
            {result.passed ? "✅ PASS PREDICTED" : "❌ FAIL RISK DETECTED"}
          </div>
          <div style={{ fontFamily: "'Space Mono',monospace", fontSize: "0.72rem", color: G.muted, marginBottom: "0.7rem" }}>
            Confidence: {(result.confidence * 100).toFixed(1)}%
          </div>
          <div style={{ height: 5, background: "rgba(255,255,255,0.07)", borderRadius: 10, overflow: "hidden" }}>
            <div style={{
              height: "100%", borderRadius: 10, background: `linear-gradient(90deg,${G.accent2},${G.accent})`,
              width: `${result.confidence * 100}%`, transition: "width 1s ease"
            }} />
          </div>
        </div>
      )}
    </div>
  );
}

// ─── MAIN APP ────────────────────────────────────────────────────────────────
export default function App() {
  const [students, setStudents] = useState([]);
  const [toast, setToast] = useState({ msg: "", visible: false, type: "success" });
  const [predictInit, setPredictInit] = useState(null);
  const toastTimer = useRef(null);

  useEffect(() => {
    injectFonts();
    load();
  }, []);

  const load = async () => {
    const data = await fetchStudents();
    setStudents(data);
  };

  const showToast = useCallback((msg, type = "success") => {
    clearTimeout(toastTimer.current);
    setToast({ msg, visible: true, type });
    toastTimer.current = setTimeout(() => setToast((t) => ({ ...t, visible: false })), 3500);
  }, []);

  const handlePredict = (s) => {
    setPredictInit({ t1: s.term1, t2: s.term2, t3: s.term3, att: s.attendance_percentage });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleDelete = async (id) => {
    const ok = await deleteStudent(id);
    if (ok) {
      showToast("Student removed from system", "success");
      load();
    } else {
      showToast("Failed to remove student", "error");
    }
  };

  return (
    <div style={{ background: G.bg, minHeight: "100vh", color: G.text, fontFamily: "'Syne',sans-serif" }}>
      <Grid3D />

      <div style={{ position: "relative", zIndex: 1, maxWidth: 1200, margin: "0 auto", padding: "0 2rem" }}>

        {/* HEADER */}
        <header style={{
          display: "flex", justifyContent: "space-between", alignItems: "center",
          padding: "1.4rem 0", borderBottom: `1px solid ${G.border}`
        }}>
          <div style={{ fontSize: "1.55rem", fontWeight: 800, letterSpacing: "-1px" }}>
            Academi<span style={{ color: G.accent }}>Q</span>
          </div>
          <div style={{
            display: "flex", alignItems: "center", gap: "0.5rem",
            background: "rgba(0,245,196,0.08)", border: "1px solid rgba(0,245,196,0.25)",
            padding: "0.38rem 1rem", borderRadius: 999, fontSize: "0.74rem",
            fontFamily: "'Space Mono',monospace", color: G.accent
          }}>
            <div style={{
              width: 7, height: 7, borderRadius: "50%", background: G.accent,
              boxShadow: `0 0 8px ${G.accent}`, animation: "aq-pulse 2s infinite"
            }} />
            FastAPI Live
          </div>
        </header>

        {/* HERO */}
        <div style={{ padding: "4rem 0 2.5rem" }}>
          <div style={{
            display: "inline-block", background: "rgba(123,97,255,0.12)",
            border: "1px solid rgba(123,97,255,0.3)", color: "#a78bfa", fontSize: "0.72rem",
            fontFamily: "'Space Mono',monospace", letterSpacing: "2px", textTransform: "uppercase",
            padding: "0.38rem 1.1rem", borderRadius: 4, marginBottom: "1.4rem"
          }}>
            Smart Attendance Analytics
          </div>
          <h1 style={{
            fontSize: "clamp(2.4rem,5.5vw,4rem)", fontWeight: 800, lineHeight: 1.05,
            letterSpacing: "-2px", marginBottom: "0.9rem"
          }}>
            Predict Risk.<br />Save <span style={{ color: G.accent }}>Futures.</span>
          </h1>
          <p style={{ color: G.muted, fontSize: "1rem", maxWidth: 480, lineHeight: 1.7 }}>
            Identify students at risk based on real attendance patterns and term results.
          </p>
        </div>

        {/* STAT CARDS */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(200px,1fr))", gap: "1rem", marginBottom: "1.8rem" }}>
          <StatCard label="At-Risk Students" value={students.filter(s => s.attendance_percentage < 75).length} sub="Below 75%" color={G.danger} icon="🔴" />
          <StatCard label="Critical Zone" value={students.filter(s => s.attendance_percentage < 60).length} sub="Below 60%" color={G.warning} icon="⚡" />
          <StatCard label="Loaded Items" value={students.length} sub="Connected to DB" color={G.accent} icon="📊" />
          <StatCard label="System Status" value="Online" sub="API Active" color="#a78bfa" icon="🌍" />
        </div>

        {/* MAIN GRID */}
        <div style={{
          display: "grid", gridTemplateColumns: "1fr 360px", gap: "1.4rem", marginBottom: "3rem",
          "@media(max-width:1000px)": { gridTemplateColumns: "1fr" }
        }}>
          {/* AT-RISK TABLE */}
          <Panel title="Student Risk Registry">
            <StudentTable onPredict={handlePredict} onDelete={handleDelete} students={students} />
          </Panel>

          {/* PREDICTOR */}
          <Panel title="AI Failure Predictor" badge="POST /predict/realtime">
            <Predictor initial={predictInit} toast={showToast} />
          </Panel>
        </div>

      </div>

      <Toast msg={toast.msg} type={toast.type} visible={toast.visible} />
    </div>
  );
}