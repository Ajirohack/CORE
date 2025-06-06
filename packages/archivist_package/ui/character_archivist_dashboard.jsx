import React, { useState } from "react";

// Add token support for authenticated API calls
function getToken() {
  return localStorage.getItem("token"); // Or use context/provider
}

export default function CharacterArchivistDashboard() {
  const [chatLog, setChatLog] = useState("");
  const [stage, setStage] = useState("initial");
  const [profile, setProfile] = useState(null);
  const [fmt, setFmt] = useState(null);
  const [report, setReport] = useState("");

  async function fetchProfile() {
    const res = await fetch("/api/character-archivist/profile", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${getToken()}`,
      },
      body: JSON.stringify({ chat_log: chatLog }),
    });
    setProfile(await res.json());
  }

  async function fetchFmt() {
    const res = await fetch("/api/character-archivist/fmt", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${getToken()}`,
      },
      body: JSON.stringify({ chat_log: chatLog, stage }),
    });
    setFmt(await res.json());
  }

  async function fetchReport() {
    const res = await fetch("/api/character-archivist/report", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${getToken()}`,
      },
      body: JSON.stringify({ chat_log: chatLog }),
    });
    const data = await res.json();
    setReport(data.report);
  }

  return (
    <div style={{ maxWidth: 800, margin: "auto", padding: 24 }}>
      <h2>Character Archivist Dashboard</h2>
      <textarea
        rows={10}
        style={{ width: "100%" }}
        placeholder="Paste chat log here..."
        value={chatLog}
        onChange={(e) => setChatLog(e.target.value)}
      />
      <div style={{ margin: "12px 0" }}>
        <label>Stage: </label>
        <input value={stage} onChange={(e) => setStage(e.target.value)} />
      </div>
      <button onClick={fetchProfile}>Analyze Profile</button>
      <button onClick={fetchFmt} style={{ marginLeft: 8 }}>
        Recommend FMT
      </button>
      <button onClick={fetchReport} style={{ marginLeft: 8 }}>
        Generate Report
      </button>
      <div style={{ marginTop: 24 }}>
        {profile && (
          <div>
            <h3>Profile</h3>
            <pre>{JSON.stringify(profile, null, 2)}</pre>
          </div>
        )}
        {fmt && (
          <div>
            <h3>Recommended FMT</h3>
            <pre>{JSON.stringify(fmt, null, 2)}</pre>
          </div>
        )}
        {report && (
          <div>
            <h3>Review Report</h3>
            <pre>{report}</pre>
          </div>
        )}
      </div>
    </div>
  );
}
