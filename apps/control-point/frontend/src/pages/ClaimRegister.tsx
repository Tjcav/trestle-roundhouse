import React, { useState } from "react";

const ClaimRegister: React.FC = () => {
  const [form, setForm] = useState({
    claim_id: "",
    title: "",
    scope_types: "",
    assertion: "",
    severity: "block",
    owner: "",
    introduced_by: "",
    rationale: "",
    category: "requirement",
  });
  const [result, setResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setResult(null);
    try {
      const payload = { ...form, scope_types: form.scope_types.split(",").map(s => s.trim()) };
      const res = await fetch(`/api/claims/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(await res.text());
      setResult(await res.json());
    } catch (err: any) {
      setError(err.message || String(err));
    }
  };

  return (
    <div style={{ padding: 32 }}>
      <h2>Register Claim</h2>
      <form onSubmit={handleSubmit} style={{ marginBottom: 16 }}>
        <input name="claim_id" placeholder="claim_id" value={form.claim_id} onChange={handleChange} style={{ marginRight: 8 }} />
        <input name="title" placeholder="title" value={form.title} onChange={handleChange} style={{ marginRight: 8 }} />
        <input name="scope_types" placeholder="scope_types (comma separated)" value={form.scope_types} onChange={handleChange} style={{ marginRight: 8 }} />
        <input name="assertion" placeholder="assertion" value={form.assertion} onChange={handleChange} style={{ marginRight: 8 }} />
        <select name="severity" value={form.severity} onChange={handleChange} style={{ marginRight: 8 }}>
          <option value="block">block</option>
          <option value="warn">warn</option>
        </select>
        <input name="owner" placeholder="owner" value={form.owner} onChange={handleChange} style={{ marginRight: 8 }} />
        <input name="introduced_by" placeholder="introduced_by" value={form.introduced_by} onChange={handleChange} style={{ marginRight: 8 }} />
        <input name="rationale" placeholder="rationale" value={form.rationale} onChange={handleChange} style={{ marginRight: 8 }} />
        <input name="category" placeholder="category" value={form.category} onChange={handleChange} style={{ marginRight: 8 }} />
        <button type="submit">Register</button>
      </form>
      {error && <div style={{ color: "red" }}>{error}</div>}
      {result && (
        <pre style={{ background: '#f0f0f0', padding: 16, borderRadius: 8 }}>{JSON.stringify(result, null, 2)}</pre>
      )}
    </div>
  );
};

export default ClaimRegister;
