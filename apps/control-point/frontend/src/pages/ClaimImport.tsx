import React, { useState, useRef } from "react";

const ClaimImport: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [result, setResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFile(e.target.files?.[0] || null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setResult(null);
    if (!file) return setError("No file selected");
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await fetch(`/api/claims/import`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error(await res.text());
      setResult(await res.json());
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
    } catch (err: any) {
      setError(err.message || String(err));
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <div style={{ padding: 32 }}>
      <h2>Import Claims</h2>
      <form onSubmit={handleSubmit} style={{ marginBottom: 16 }}>
        <input type="file" accept=".txt,.md,.json" onChange={handleFileChange} style={{ marginRight: 8 }} ref={fileInputRef} />
        <button type="submit">Import</button>
      </form>
      {error && <div style={{ color: "red" }}>{error}</div>}
      {result && (
        <pre style={{ background: '#f0f0f0', padding: 16, borderRadius: 8 }}>{JSON.stringify(result, null, 2)}</pre>
      )}
    </div>
  );
};

export default ClaimImport;
