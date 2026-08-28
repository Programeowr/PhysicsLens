"""PhysicsLens parser evaluation harness.

Scores a labeled eval set (JSONL) against the real pipeline end-to-end and
compares parsing modes.

Usage (from repo root):
    python eval/run_eval.py --parser deterministic
    python eval/run_eval.py --parser llm            # hybrid: deterministic first,
                                                    # Ollama qwen2.5:7b fallback
    python eval/run_eval.py --parser llm --resume   # skip cases already scored

Eval set format (one JSON object per line):
    {
      "id": "incline_001",
      "category": "incline",
      "text": "...",
      "expected_status": "ok" | "needs_clarification" | "unsupported_scenario",
      "expected_scenario": "inclined_plane" | null,
      "expected_masses_kg": [5.0],
      "expected_scalars": {"incline_angle_deg": 30.0, ...},
      "expected_applied_force_magnitudes_n": [100.0],
      "expected_missing": ["mass_kg"]
    }
All expectation fields except id/category/text/expected_status are optional;
only the ones present are scored.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from physics_diagram.pipeline import solve_and_render  # noqa: E402

# ── Scoring ───────────────────────────────────────────────────────────────────

ANGLE_KEYS = ("incline_angle_deg", "projectile_angle_deg")
SCALAR_KEYS = ANGLE_KEYS + ("initial_speed_ms", "mu")


def close(pred: float | None, exp: float) -> bool:
    """Numeric match tolerant of rounding (regex extracts exact decimals)."""
    if pred is None:
        return False
    return abs(pred - exp) <= 0.05 + 1e-3 * abs(exp)


def score_case(case: dict, parse_result, status: str) -> dict:
    """Compare one pipeline result against its ground truth."""
    checks: list[tuple[str, bool]] = []

    checks.append(("status", status == case["expected_status"]))

    if case.get("expected_scenario"):
        checks.append(("scenario", parse_result.scenario_type == case["expected_scenario"]))

    pred_masses = sorted(o.mass_kg for o in parse_result.objects if o.mass_kg is not None)
    exp_masses = sorted(case.get("expected_masses_kg") or [])
    if exp_masses:
        ok = len(pred_masses) == len(exp_masses) and all(
            close(p, e) for p, e in zip(pred_masses, exp_masses)
        )
        checks.append(("masses", ok))

    g = parse_result.geometry
    pred_scalars = {
        "incline_angle_deg": g.incline_angle_deg,
        "projectile_angle_deg": g.projectile_angle_deg,
        "initial_speed_ms": g.initial_speed_ms,
        "mu": parse_result.mu,
    }
    for key, exp in (case.get("expected_scalars") or {}).items():
        if exp is None or key not in SCALAR_KEYS:
            continue
        checks.append((key, close(pred_scalars[key], float(exp))))

    exp_forces = case.get("expected_applied_force_magnitudes_n") or []
    if exp_forces:
        pred_forces = sorted(f.magnitude_n for f in parse_result.applied_forces)
        remaining = list(pred_forces)
        for e in exp_forces:
            match = next((i for i, p in enumerate(remaining) if close(p, e)), None)
            if match is not None:
                remaining.pop(match)
        checks.append(("applied_forces", len(remaining) == len(pred_forces) - len(exp_forces)))

    if "expected_missing" in case:
        got = sorted(parse_result.missing_required)
        want = sorted(case["expected_missing"])
        checks.append(("missing_exact", got == want))

    return {
        "id": case["id"],
        "category": case["category"],
        "checks": {name: ok for name, ok in checks},
        "passed": all(ok for _, ok in checks),
        "predicted_status": status,
        "predicted_scenario": parse_result.scenario_type,
        "predicted_masses_kg": pred_masses,
        "predicted_missing": sorted(parse_result.missing_required),
    }


# ── Runner ────────────────────────────────────────────────────────────────────

def load_cases(path: Path) -> list[dict]:
    cases = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
        line = line.strip()
        if not line or line.startswith("//"):
            continue
        try:
            cases.append(json.loads(line))
        except json.JSONDecodeError as exc:
            sys.exit(f"{path}:{i + 1}: invalid JSON ({exc})")
    ids = [c["id"] for c in cases]
    dupes = {x for x in ids if ids.count(x) > 1}
    if dupes:
        sys.exit(f"Duplicate ids in eval set: {sorted(dupes)}")
    return cases


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--parser", choices=("deterministic", "llm"), default="deterministic")
    ap.add_argument("--set", dest="eval_set", type=Path, default=Path(__file__).parent / "eval_set.jsonl")
    ap.add_argument("--results-dir", type=Path, default=Path(__file__).parent / "results")
    ap.add_argument("--tag", default=None, help="name for result files (default: parser name)")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--ids", default=None, help="comma-separated subset of case ids")
    ap.add_argument("--resume", action="store_true", help="skip ids already present in results file")
    args = ap.parse_args()

    tag = args.tag or args.parser
    results_dir = args.results_dir
    results_dir.mkdir(parents=True, exist_ok=True)
    results_path = results_dir / f"{tag}_results.jsonl"

    cases = load_cases(args.eval_set)
    if args.ids:
        wanted = {x.strip() for x in args.ids.split(",")}
        cases = [c for c in cases if c["id"] in wanted]
    if args.limit:
        cases = cases[: args.limit]

    done: dict[str, dict] = {}
    if args.resume and results_path.exists():
        for line in results_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                done[r["id"]] = r
        print(f"[resume] {len(done)} cases already scored")

    # Count actual Ollama invocations when running hybrid mode.
    llm_calls = {"n": 0}
    if args.parser == "llm":
        import physics_diagram.llm_parser as llm_parser

        original = llm_parser._call_ollama

        def counting(text: str):
            llm_calls["n"] += 1
            return original(text)

        llm_parser._call_ollama = counting  # type: ignore[method-assign]

    pending = [c for c in cases if c["id"] not in done]
    rows: list[dict] = list(done.values())
    with tempfile.TemporaryDirectory(prefix="pl_eval_") as tmpdir:
        svg_path = str(Path(tmpdir) / "out.svg")
        t_start = time.perf_counter()
        for i, case in enumerate(pending, 1):
            t0 = time.perf_counter()
            try:
                out = solve_and_render(case["text"], svg_path, parser=args.parser)
                latency = time.perf_counter() - t0
                row = score_case(case, out["parse_result"], out["status"])
            except Exception as exc:  # noqa: BLE001 — a crash is a failed case, not a dead run
                latency = time.perf_counter() - t0
                row = {
                    "id": case["id"], "category": case["category"], "checks": {},
                    "passed": False, "predicted_status": f"ERROR: {exc}",
                    "predicted_scenario": None, "predicted_masses_kg": [],
                    "predicted_missing": [],
                }
            row["latency_s"] = round(latency, 3)
            rows.append(row)
            flag = "PASS" if row["passed"] else "FAIL"
            print(f"[{i}/{len(pending)}] {flag} {row['id']} "
                  f"(status={row['predicted_status']}, {row['latency_s']}s)")
            with results_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    wall = time.perf_counter() - t_start

    summary = summarize(rows, tag, wall, llm_calls["n"] if args.parser == "llm" else None)
    (results_dir / f"{tag}_summary.json").write_text(
        json.dumps(summary["overall"], indent=2), encoding="utf-8"
    )
    (results_dir / f"{tag}_report.md").write_text(summary["markdown"], encoding="utf-8")
    print(summary["text"])
    print(f"\nArtifacts: {results_path}, {results_dir / (tag + '_report.md')}")


def summarize(rows: list[dict], tag: str, wall_s: float, llm_calls: int | None) -> dict:
    total = len(rows)
    latencies = [r["latency_s"] for r in rows]

    check_names = sorted({k for r in rows for k in r.get("checks", {})})
    check_stats = {
        name: {
            "passed": sum(1 for r in rows if r.get("checks", {}).get(name) is True),
            "total": sum(1 for r in rows if name in r.get("checks", {})),
        }
        for name in check_names
    }

    def pct(p, n):
        return round(100 * p / n, 1) if n else None

    overall = {
        "mode": tag,
        "cases": total,
        "case_pass_rate_pct": pct(sum(r["passed"] for r in rows), total),
        "check_accuracy_pct": {
            k: pct(v["passed"], v["total"]) for k, v in check_stats.items()
        },
        "latency_s": {
            "mean": round(statistics.mean(latencies), 3) if latencies else None,
            "median": round(statistics.median(latencies), 3) if latencies else None,
            "max": round(max(latencies), 3) if latencies else None,
            "wall": round(wall_s, 1),
        },
        "llm_fallback_calls": llm_calls,
    }

    lines = [
        f"EVAL RESULTS [{tag}] ({total} cases)",
        "-" * 56,
        f"case pass rate      : {overall['case_pass_rate_pct']}%",
    ]
    for k, v in overall["check_accuracy_pct"].items():
        stat = check_stats[k]
        lines.append(f"  {k:<18}: {v}%  ({stat['passed']}/{stat['total']})")
    if llm_calls is not None:
        lines.append(f"Ollama fallback calls: {llm_calls}")
    lines.append(
        f"latency mean/med/max : {overall['latency_s']['mean']}/"
        f"{overall['latency_s']['median']}/{overall['latency_s']['max']} s"
    )

    cats = sorted({r["category"] for r in rows})
    cat_lines, cat_rows = [], []
    for c in cats:
        sub = [r for r in rows if r["category"] == c]
        entry = {
            "category": c,
            "cases": len(sub),
            "pass_rate_pct": pct(sum(r["passed"] for r in sub), len(sub)),
        }
        cat_rows.append(entry)
        cat_lines.append(f"  {c:<12}: {entry['pass_rate_pct']}%  ({entry['cases']} cases)")

    lines.append("by category:")
    lines.extend(cat_lines)

    fails = [r for r in rows if not r["passed"]]
    if fails:
        lines.append(f"\nFAILED CASES ({len(fails)}):")
        for r in fails[:40]:
            bad = [k for k, v in r.get("checks", {}).items() if v is not True]
            lines.append(
                f"  {r['id']:<16} [{','.join(bad)}] status={r['predicted_status']} "
                f"scenario={r['predicted_scenario']} masses={r['predicted_masses_kg']} "
                f"missing={r['predicted_missing']}"
            )
    text = "\n".join(lines)

    md = [
        f"# Eval report — `{tag}`",
        "",
        "| metric | value |", "|---|---|",
        f"| cases | {total} |",
        f"| case pass rate | {overall['case_pass_rate_pct']}% |",
        *[f"| {k} accuracy | {v}% |" for k, v in overall["check_accuracy_pct"].items()],
        f"| Ollama fallback calls | {llm_calls if llm_calls is not None else '—'} |",
        f"| latency mean/median/max (s) | {overall['latency_s']['mean']} / "
        f"{overall['latency_s']['median']} / {overall['latency_s']['max']} |",
        "",
        "## By category", "", "| category | cases | pass rate |", "|---|---|---|",
        *[f"| {c['category']} | {c['cases']} | {c['pass_rate_pct']}% |" for c in cat_rows],
    ]
    return {"overall": overall, "text": text, "markdown": "\n".join(md)}


if __name__ == "__main__":
    main()
