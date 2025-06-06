import React from "react";

export default function ProfileViewer({ profile }) {
  if (!profile) return <div>No profile loaded.</div>;
  return (
    <div style={{ background: "#f9f9f9", padding: 16, borderRadius: 8 }}>
      <h3>Core Identity</h3>
      <pre>{JSON.stringify(profile.core_identity, null, 2)}</pre>
      <h3>Traits</h3>
      <pre>{JSON.stringify(profile.traits, null, 2)}</pre>
      <h3>Habits</h3>
      <pre>{JSON.stringify(profile.habits, null, 2)}</pre>
      <h3>Relationships</h3>
      <pre>{JSON.stringify(profile.relationships, null, 2)}</pre>
      <h3>Vulnerability</h3>
      <pre>{JSON.stringify(profile.vulnerability, null, 2)}</pre>
    </div>
  );
}
