import React, { useState } from "react";

const GateCheck: React.FC = () => {
  const [scope, setScope] = useState({ repo: "", subsystem: "", api: "", ui: "" });
  const [result, setResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setScope({ ...scope, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`/api/gate/check`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(scope),
      });
      if (!res.ok) throw new Error(await res.text());
      setResult(await res.json());
    } catch (err: any) {
      setError(err.message || String(err));
    }
  };

  return (
    <div style={{ padding: 32 }}>
      <h2>Gate Check</h2>
      <form onSubmit={handleSubmit} style={{ marginBottom: 16 }}>
        <input name="repo" placeholder="repo" value={scope.repo} onChange={handleChange} style={{ marginRight: 8 }} />
        <input name="subsystem" placeholder="subsystem" value={scope.subsystem} onChange={handleChange} style={{ marginRight: 8 }} />
        <input name="api" placeholder="api" value={scope.api} onChange={handleChange} style={{ marginRight: 8 }} />
        <input name="ui" placeholder="ui" value={scope.ui} onChange={handleChange} style={{ marginRight: 8 }} />
        <button type="submit">Check Gate</button>
      </form>
      {error && <div style={{ color: "red" }}>{error}</div>}
      {result && (
        <pre style={{ background: '#f0f0f0', padding: 16, borderRadius: 8 }}>{JSON.stringify(result, null, 2)}</pre>
      )}
    </div>
  );
};

export default GateCheck;
