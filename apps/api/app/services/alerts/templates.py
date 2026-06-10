"""
Email templates for scan summary alerts.
Returns both HTML and plain-text versions.
"""
from datetime import date
from dataclasses import dataclass


@dataclass
class CandidateSummary:
    symbol: str
    score: float
    confidence: str
    entry: float
    stop: float
    target1: float
    rr_ratio: float
    technical_setup: str | None


def _confidence_color(c: str) -> str:
    return {"HIGH": "#4ade80", "MEDIUM": "#facc15", "LOW": "#f87171"}.get(c, "#94a3b8")


def _breakout_note(setup: str | None) -> str:
    if not setup:
        return "—"
    if "Above 20-day high" in setup:
        return "🚀 Breakout"
    import re
    m = re.search(r"([\d.]+)% from", setup)
    if m:
        return f"{m.group(1)}% from high"
    return "—"


def _rel_vol_note(setup: str | None) -> str:
    if not setup:
        return "—"
    import re
    m = re.search(r"Rel vol ([\d.]+)x", setup)
    return f"{m.group(1)}×" if m else "—"


def render_scan_summary(
    candidates: list[CandidateSummary],
    run_date: date,
    tickers_scanned: int,
    regime: str | None,
) -> tuple[str, str]:
    """Returns (html, plain_text)."""

    regime_label = {"BULLISH": "🟢 Bullish", "NEUTRAL": "🟡 Neutral", "RISK_OFF": "🔴 Risk-Off"}.get(regime or "", "—")
    date_str = run_date.strftime("%A, %B %-d, %Y")

    # ── HTML ────────────────────────────────────────────────────────────────
    rows_html = ""
    for c in candidates[:10]:
        conf_color = _confidence_color(c.confidence)
        rows_html += f"""
        <tr style="border-bottom:1px solid #1e293b">
          <td style="padding:10px 12px;font-weight:600;font-size:14px">{c.symbol}</td>
          <td style="padding:10px 12px;font-size:14px;color:{conf_color};font-weight:700">{c.score:.1f}</td>
          <td style="padding:10px 12px;font-size:12px;color:{conf_color}">{c.confidence}</td>
          <td style="padding:10px 12px;font-size:13px">${c.entry:.2f}</td>
          <td style="padding:10px 12px;font-size:13px;color:#f87171">${c.stop:.2f}</td>
          <td style="padding:10px 12px;font-size:13px;color:#4ade80">${c.target1:.2f}</td>
          <td style="padding:10px 12px;font-size:13px">{c.rr_ratio:.1f}:1</td>
          <td style="padding:10px 12px;font-size:12px;color:#94a3b8">{_rel_vol_note(c.technical_setup)}</td>
          <td style="padding:10px 12px;font-size:12px;color:#94a3b8">{_breakout_note(c.technical_setup)}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"/></head>
<body style="margin:0;padding:0;background:#0f172a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#f1f5f9">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0f172a">
    <tr><td align="center" style="padding:32px 16px">
      <table width="640" cellpadding="0" cellspacing="0" style="max-width:640px;width:100%">

        <!-- Header -->
        <tr>
          <td style="padding:0 0 24px">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td>
                  <div style="display:inline-flex;align-items:center;gap:8px">
                    <span style="background:#166534;color:#4ade80;padding:4px 8px;border-radius:6px;font-size:13px;font-weight:700">📈 SwingScope</span>
                  </div>
                  <h1 style="margin:12px 0 4px;font-size:22px;font-weight:700">Daily Scan Summary</h1>
                  <p style="margin:0;color:#94a3b8;font-size:14px">{date_str}</p>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Stats bar -->
        <tr>
          <td style="padding:0 0 24px">
            <table width="100%" cellpadding="0" cellspacing="0" style="background:#1e293b;border-radius:8px">
              <tr>
                <td style="padding:16px 20px;border-right:1px solid #334155;text-align:center">
                  <div style="font-size:24px;font-weight:700;color:#4ade80">{len(candidates)}</div>
                  <div style="font-size:12px;color:#94a3b8;margin-top:2px">Candidates</div>
                </td>
                <td style="padding:16px 20px;border-right:1px solid #334155;text-align:center">
                  <div style="font-size:24px;font-weight:700">{tickers_scanned}</div>
                  <div style="font-size:12px;color:#94a3b8;margin-top:2px">Scanned</div>
                </td>
                <td style="padding:16px 20px;text-align:center">
                  <div style="font-size:16px;font-weight:600">{regime_label}</div>
                  <div style="font-size:12px;color:#94a3b8;margin-top:2px">Market Regime</div>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Candidates table -->
        <tr>
          <td>
            <table width="100%" cellpadding="0" cellspacing="0" style="background:#1e293b;border-radius:8px;overflow:hidden">
              <thead>
                <tr style="background:#0f172a">
                  <th style="padding:10px 12px;text-align:left;font-size:11px;font-weight:500;color:#64748b;text-transform:uppercase;letter-spacing:0.05em">Symbol</th>
                  <th style="padding:10px 12px;text-align:left;font-size:11px;font-weight:500;color:#64748b;text-transform:uppercase;letter-spacing:0.05em">Score</th>
                  <th style="padding:10px 12px;text-align:left;font-size:11px;font-weight:500;color:#64748b;text-transform:uppercase;letter-spacing:0.05em">Conf</th>
                  <th style="padding:10px 12px;text-align:left;font-size:11px;font-weight:500;color:#64748b;text-transform:uppercase;letter-spacing:0.05em">Entry</th>
                  <th style="padding:10px 12px;text-align:left;font-size:11px;font-weight:500;color:#64748b;text-transform:uppercase;letter-spacing:0.05em">Stop</th>
                  <th style="padding:10px 12px;text-align:left;font-size:11px;font-weight:500;color:#64748b;text-transform:uppercase;letter-spacing:0.05em">Target</th>
                  <th style="padding:10px 12px;text-align:left;font-size:11px;font-weight:500;color:#64748b;text-transform:uppercase;letter-spacing:0.05em">R/R</th>
                  <th style="padding:10px 12px;text-align:left;font-size:11px;font-weight:500;color:#64748b;text-transform:uppercase;letter-spacing:0.05em">Vol</th>
                  <th style="padding:10px 12px;text-align:left;font-size:11px;font-weight:500;color:#64748b;text-transform:uppercase;letter-spacing:0.05em">Breakout</th>
                </tr>
              </thead>
              <tbody>{rows_html}</tbody>
            </table>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="padding:24px 0 0">
            <p style="margin:0;font-size:11px;color:#475569;text-align:center;line-height:1.6">
              ⚠️ SwingScope is for informational purposes only. Nothing here is financial advice.<br/>
              Past performance does not guarantee future results. Trading involves risk of loss.
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""

    # ── Plain text ───────────────────────────────────────────────────────────
    lines = [
        f"SwingScope — Daily Scan Summary",
        f"{date_str}",
        f"Regime: {regime_label}  |  Scanned: {tickers_scanned}  |  Candidates: {len(candidates)}",
        "",
        f"{'SYMBOL':<8} {'SCORE':>6} {'CONF':<7} {'ENTRY':>8} {'STOP':>8} {'TARGET':>8} {'R/R':>5} {'VOL':>6} BREAKOUT",
        "-" * 78,
    ]
    for c in candidates[:10]:
        lines.append(
            f"{c.symbol:<8} {c.score:>6.1f} {c.confidence:<7} ${c.entry:>7.2f} ${c.stop:>7.2f} ${c.target1:>7.2f} {c.rr_ratio:>4.1f}:1 {_rel_vol_note(c.technical_setup):>5} {_breakout_note(c.technical_setup)}"
        )
    lines += [
        "",
        "---",
        "For informational purposes only. Not financial advice.",
    ]
    text = "\n".join(lines)

    return html, text
