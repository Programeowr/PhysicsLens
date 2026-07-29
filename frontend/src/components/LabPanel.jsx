import { useMemo, useState } from "react";
import ReactiveButton from "./ReactiveButton";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";
const defaultPrompt =
  "A box of mass 5kg is placed on a frictionless inclined plane with 30 degree inclination. How much force is required to keep it at rest?";

function decodeSvg(base64Text) {
  return `data:image/svg+xml;base64,${base64Text}`;
}

export default function LabPanel() {
  const [prompt, setPrompt] = useState(defaultPrompt);
  const [status, setStatus] = useState("idle");
  const [message, setMessage] = useState("Describe your problem and hit generate.");
  const [svgData, setSvgData] = useState("");
  const [details, setDetails] = useState(null);

  const detailRows = useMemo(() => {
    if (!details?.force_solution?.derived_values) {
      return [];
    }
    return Object.entries(details.force_solution.derived_values);
  }, [details]);

  async function solve() {
    if (!prompt.trim()) {
      setMessage("Add a physics question first.");
      return;
    }

    setStatus("loading");
    setMessage("Crunching vectors…");

    try {
      const response = await fetch(`${API_BASE}/solve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: prompt.trim() }),
      });

      const data = await response.json();
      if (data.status !== "ok") {
        const missing = data.missing_fields?.length ? data.missing_fields.join(", ") : "unknown values";
        setStatus("error");
        setMessage(`Need more details: ${missing}`);
        setSvgData("");
        setDetails(null);
        return;
      }

      setSvgData(decodeSvg(data.diagram_svg_base64));
      setDetails(data);
      setStatus("ready");
      setMessage("Diagram generated successfully.");
    } catch (error) {
      setStatus("error");
      setMessage("Unable to reach the API. Start FastAPI and try again.");
      setSvgData("");
      setDetails(null);
    }
  }

  return (
    <section className="lab-wrap" id="start" aria-label="Interactive solve panel">
      <div className="section-title">
        <h2>Diagram Workspace</h2>
        <p>Paste one question → get a deterministic force diagram.</p>
      </div>
      <div className="lab-grid">
        <div className="lab-input">
          <label htmlFor="prompt-box">Problem text</label>
          <textarea
            id="prompt-box"
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            spellCheck={false}
            placeholder="Describe a physics problem involving forces, inclines, pulleys, or projectiles…"
          />
          <div className="lab-actions">
            <div data-magnetic>
              <ReactiveButton onClick={solve} disabled={status === "loading"}>
                {status === "loading" ? "Solving…" : "Generate Diagram"}
              </ReactiveButton>
            </div>
            <p className={`status status-${status}`}>{message}</p>
          </div>
        </div>
        <div className="lab-output">
          {svgData ? (
            <img src={svgData} alt="Generated force diagram" />
          ) : (
            <div className="empty-state">
              <span>Your SVG diagram will appear here</span>
            </div>
          )}
          {detailRows.length > 0 && (
            <div className="derived-table" aria-label="Computed quantities">
              {detailRows.map(([key, value]) => (
                <div className="derived-row" key={key}>
                  <span>{key.replaceAll("_", " ")}</span>
                  <strong>{String(value)}</strong>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
