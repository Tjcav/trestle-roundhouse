import React, { useState } from "react";

const Arbitrate: React.FC = () => {
  const [arbitration, setArbitration] = useState({ conflict_id: "", decision: "" });
  const [result, setResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setArbitration({ ...arbitration, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`/api/control-point/arbitrate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(arbitration),
      });
      if (!res.ok) throw new Error(await res.text());
      setResult(await res.json());
    } catch (err: any) {
      setError(err.message || String(err));
    }
  };

  return (
    <div style={{ padding: 32 }}>
      <h2>Arbitrate Conflict</h2>
      <form onSubmit={handleSubmit} style={{ marginBottom: 16 }}>
        <input name="conflict_id" placeholder="conflict_id" value={arbitration.conflict_id} onChange={handleChange} style={{ marginRight: 8 }} />
        <input name="decision" placeholder="decision (e.g. reject, allow_once)" value={arbitration.decision} onChange={handleChange} style={{ marginRight: 8 }} />
        <button type="submit">Submit Arbitration</button>
      </form>
      {error && <div style={{ color: "red" }}>{error}</div>}
      {result && (
        <pre style={{ background: '#f0f0f0', padding: 16, borderRadius: 8 }}>{JSON.stringify(result, null, 2)}</pre>
      )}
    </div>
  );
};

export default Arbitrate;
