
import React, { useEffect, useState } from "react";

const Dashboard: React.FC = () => {
  const [claims, setClaims] = useState<any[]>([]);
  const [selectedClaim, setSelectedClaim] = useState<any | null>(null);

  useEffect(() => {
    fetch(`/api/claims`)
      .then((res) => {
        if (!res.ok) {
          console.error('Fetch failed:', res.status, res.statusText);
          return [];
        }
        return res.json();
      })
      .then(setClaims)
      .catch((err) => {
        console.error('Fetch error:', err);
        setClaims([]);
      });
  }, []);

  const total = claims.length;
  // If state is not present, do not filter
  const violated = claims.filter((c) => c.state === "violated").length;
  const conflicted = claims.filter((c) => c.state === "conflicted").length;

  if (selectedClaim) {
    return (
      <div style={{ padding: 32 }}>
        <button onClick={() => setSelectedClaim(null)} style={{ marginBottom: 16 }}>&larr; Back</button>
        <h2>Claim Detail</h2>
        {Object.entries(selectedClaim).map(([key, value]) => (
          <div key={key}><b>{key}:</b> {String(value)}</div>
        ))}
      </div>
    );
  }

  return (
    <div style={{ padding: 32, fontFamily: "sans-serif" }}>
      <h1>Control Point</h1>
      <div style={{ display: "flex", gap: 24, marginBottom: 32 }}>
        <CountCard label="Total claims" count={total} />
        <CountCard label="Violated claims" count={violated} />
        <CountCard label="Conflicted claims" count={conflicted} />
      </div>
      <div style={{ marginBottom: 24 }}>
        <b>Public API:</b> &nbsp;
        <a href="#" onClick={e => { e.preventDefault(); window.dispatchEvent(new CustomEvent('nav', { detail: 'gate' })); }}>Gate Check</a> | &nbsp;
        <a href="#" onClick={e => { e.preventDefault(); window.dispatchEvent(new CustomEvent('nav', { detail: 'register' })); }}>Register Claim</a> | &nbsp;
        <a href="#" onClick={e => { e.preventDefault(); window.dispatchEvent(new CustomEvent('nav', { detail: 'import' })); }}>Import Claims</a> | &nbsp;
        <a href="#" onClick={e => { e.preventDefault(); window.dispatchEvent(new CustomEvent('nav', { detail: 'arbitrate' })); }}>Arbitrate</a>
      </div>
      <h2>Claims</h2>
      <pre style={{ background: '#f0f0f0', padding: 16, borderRadius: 8, marginBottom: 16 }}>
        {JSON.stringify(claims, null, 2)}
      </pre>
      {claims.length > 0 ? (
        <table style={{ borderCollapse: "collapse", width: "100%" }}>
          <thead>
            <tr>
              {Object.keys(claims[0]).map((key) => (
                <th key={key} style={{ textAlign: "left", padding: 8 }}>{key}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {claims.map((claim, idx) => (
              <tr key={claim.claim_id || idx} style={{ cursor: "pointer" }} onClick={() => setSelectedClaim(claim)}>
                {Object.values(claim).map((value, i) => (
                  <td key={i} style={{ padding: 8 }}>{String(value)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div>No claims found.</div>
      )}
    </div>
  );
};

const CountCard: React.FC<{ label: string; count: number }> = ({ label, count }) => (
  <div style={{ minWidth: 220, background: "#f5f5f5", borderRadius: 8, padding: 24, textAlign: "center" }}>
    <div style={{ fontSize: 48, fontWeight: 700 }}>{count}</div>
    <div style={{ fontSize: 16, color: "#333", marginTop: 8 }}>{label}</div>
  </div>
);

export default Dashboard;
