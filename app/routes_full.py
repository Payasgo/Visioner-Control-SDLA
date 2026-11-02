"""Full dashboard and API routes."""

from __future__ import annotations

from datetime import datetime, timezone

from flask import Flask, jsonify, render_template_string, request

from app.behavior.classifier import DriverClassifier
from app.behavior.lesson_tracker import LessonTracker
from app.behavior.voice_coach import VoiceCoach
from app.enforcement.evidence import ViolationLogger
from app.telemetry.simulator_interface import TelemetrySimulator

_DASHBOARD_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Visioner-Control SDLA</title>
<style>
:root{color-scheme:dark;--bg:#0d1117;--panel:#161b22;--line:#30363d;--text:#e6edf3;--muted:#8b949e;--accent:#58a6ff}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:15px system-ui,sans-serif}
header{padding:22px max(20px,calc((100vw - 1100px)/2));border-bottom:1px solid var(--line);background:var(--panel)}
main{max-width:1100px;margin:24px auto;padding:0 18px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:18px}.label{color:var(--muted);font-size:.82rem}
.value{font-size:2rem;font-weight:700;margin-top:8px}.wide{grid-column:1/-1}.tip{border-left:3px solid var(--accent);padding:12px;background:#1f2937;border-radius:6px}
table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:10px;border-bottom:1px solid var(--line)}
.status{color:#3fb950}.error{color:#f85149}@media(max-width:600px){header{padding:18px}}
</style></head>
<body><header><h1>Visioner-Control SDLA</h1><div class="label">Driver coaching and safety telemetry dashboard</div></header>
<main><section class="grid">
<div class="card"><div class="label">Driver skill</div><div id="skill" class="value">Loading…</div></div>
<div class="card"><div class="label">Vehicle speed</div><div id="speed" class="value">—</div></div>
<div class="card"><div class="label">Lesson duration</div><div id="duration" class="value">—</div></div>
<div class="card"><div class="label">Mistakes recorded</div><div id="mistakes" class="value">—</div></div>
<div class="card wide"><div class="label">Coaching tip</div><p id="tip" class="tip">Connecting to telemetry…</p><p id="connection" class="label">Connecting…</p></div>
<div class="card wide"><h2>Recent violations</h2><table><thead><tr><th>Time</th><th>Type</th><th>Plate</th><th>Speed</th></tr></thead><tbody id="violations"><tr><td colspan="4">No events loaded.</td></tr></tbody></table></div>
</section></main>
<script>
'use strict';
const setText=(id,value)=>{document.getElementById(id).textContent=String(value)};
async function refresh(){
 try{
  const responses=await Promise.all([
   fetch('/api/telemetry',{headers:{Accept:'application/json'}}),
   fetch('/api/violations/stats',{headers:{Accept:'application/json'}})
  ]);
  if(responses.some(r=>!r.ok))throw new Error('API request failed ('+responses.map(r=>r.status).join('/')+')');
  const tel=await responses[0].json(),vio=await responses[1].json(),p=tel.progress||{};
  setText('skill',tel.skill||'Unknown');
  const speed=Number(tel.telemetry&&tel.telemetry.speed);
  setText('speed',Number.isFinite(speed)?speed.toFixed(1)+' km/h':'—');
  setText('duration',(p['Duration (min)']??0)+' min');
  setText('mistakes',p.Mistakes??0);
  setText('tip',tel.tip||'Maintain a safe following distance.');
  const tbody=document.getElementById('violations');tbody.replaceChildren();
  for(const item of (vio.recent||[]).slice(-20).reverse()){
   const tr=document.createElement('tr');
   [item.timestamp,item.violation_type,item.license_plate,item.speed_kmh??'—'].forEach(value=>{
    const td=document.createElement('td');td.textContent=String(value??'—');tr.appendChild(td);
   });
   tbody.appendChild(tr);
  }
  if(!tbody.children.length){const tr=document.createElement('tr'),td=document.createElement('td');td.colSpan=4;td.textContent='No violations recorded.';tr.appendChild(td);tbody.appendChild(tr)}
  setText('connection','Live · updated '+new Date().toLocaleTimeString());
  document.getElementById('connection').className='label status';
 }catch(error){
  setText('connection','Dashboard API unavailable: '+error.message);
  document.getElementById('connection').className='label error';
 }
}
refresh();setInterval(refresh,5000);
</script></body></html>"""


def register_routes(app: Flask) -> None:
    """Register the dashboard and JSON API endpoints."""
    simulator = TelemetrySimulator()
    classifier = DriverClassifier()
    tracker = LessonTracker()
    coach = VoiceCoach()
    vlogger = ViolationLogger()

    @app.get("/")
    def dashboard():
        return render_template_string(_DASHBOARD_HTML)

    @app.get("/api/telemetry")
    def api_telemetry():
        data = simulator.get_data()
        skill = classifier.classify(data)
        tracker.update(data)
        return jsonify(
            telemetry=data,
            skill=skill,
            tip=coach.get_tip(skill),
            progress=tracker.get_summary(),
        )

    @app.get("/api/violations")
    def api_violations_get():
        limit = request.args.get("n", default=20, type=int)
        if limit is None or not 1 <= limit <= 200:
            return jsonify(error="n must be an integer between 1 and 200"), 400
        return jsonify(vlogger.get_recent(limit))

    @app.post("/api/violations")
    def api_violations_post():
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            return jsonify(error="Request body must be a JSON object"), 400

        violation_type = body.get("violation_type", "MANUAL")
        plate = body.get("license_plate", "UNKNOWN")
        if not isinstance(violation_type, str) or not 1 <= len(violation_type.strip()) <= 64:
            return jsonify(error="violation_type must be a string of 1–64 characters"), 400
        if not isinstance(plate, str) or len(plate) > 32:
            return jsonify(error="license_plate must be a string of at most 32 characters"), 400

        speed = body.get("speed_kmh")
        confidence = body.get("confidence", 1.0)
        if speed is not None and (
            isinstance(speed, bool) or not isinstance(speed, (int, float)) or not 0 <= speed <= 500
        ):
            return jsonify(error="speed_kmh must be between 0 and 500"), 400
        if (
            isinstance(confidence, bool)
            or not isinstance(confidence, (int, float))
            or not 0 <= confidence <= 1
        ):
            return jsonify(error="confidence must be between 0 and 1"), 400
        for key in ("evidence_path", "location"):
            if key in body and (not isinstance(body[key], str) or len(body[key]) > 512):
                return jsonify(error=f"{key} must be a string of at most 512 characters"), 400

        record = vlogger.log(
            violation_type=violation_type.strip(),
            license_plate=plate.strip() or "UNKNOWN",
            speed_kmh=speed,
            confidence=float(confidence),
            evidence_path=body.get("evidence_path", ""),
            location=body.get("location", "N/A"),
            timestamp=datetime.now(timezone.utc),
        )
        return jsonify(record), 201

    @app.get("/api/violations/stats")
    def api_violations_stats():
        all_violations = vlogger.get_all()
        by_type: dict[str, int] = {}
        for row in all_violations:
            kind = str(row.get("violation_type", "UNKNOWN"))[:64]
            by_type[kind] = by_type.get(kind, 0) + 1
        return jsonify(total=len(all_violations), by_type=by_type, recent=all_violations[-20:])

    @app.get("/api/session")
    def api_session():
        data = simulator.get_data()
        skill = classifier.classify(data)
        return jsonify(skill=skill, progress=tracker.get_summary(), tip=coach.get_tip(skill))

    @app.get("/api/health")
    def api_health():
        return jsonify(status="ok", timestamp=datetime.now(timezone.utc).isoformat())
