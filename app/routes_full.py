# app/routes_full.py
"""
Feature 27 – REST API   (Basic → Full)
Feature 28 – Dashboard  (Basic → Full live dashboard)

Registers all routes on the Flask app:
  GET  /                         – live HTML dashboard
  GET  /api/telemetry            – current telemetry + skill + tip
  GET  /api/violations           – recent violation log (JSON)
  GET  /api/violations/stats     – aggregated stats for charts
  GET  /api/health               – health check
  POST /api/violations           – manually log a violation
  GET  /api/session              – current session summary
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, render_template_string, request

from app.behavior.classifier import DriverClassifier
from app.behavior.lesson_tracker import LessonTracker
from app.behavior.voice_coach import VoiceCoach
from app.telemetry.simulator_interface import TelemetrySimulator
from app.enforcement.evidence import ViolationLogger

# ─────────────────────────────────────────────────────────────────────────────
# Dashboard HTML (single-file, Chart.js)
# ─────────────────────────────────────────────────────────────────────────────

_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Visioner-Control SDLA</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
:root{--bg:#0d1117;--surf:#161b22;--brd:#30363d;--acc:#238636;--red:#da3633;
      --warn:#d29922;--text:#e6edf3;--muted:#8b949e;--blue:#1f6feb;}
*{box-sizing:border-box;margin:0;padding:0;}
body{background:var(--bg);color:var(--text);font-family:'Segoe UI',system-ui,sans-serif;}
header{background:var(--surf);border-bottom:1px solid var(--brd);
       padding:14px 24px;display:flex;align-items:center;gap:10px;}
header h1{font-size:1.15rem;font-weight:600;}
.dot{width:8px;height:8px;border-radius:50%;background:var(--acc);
     box-shadow:0 0 6px var(--acc);animation:pulse 1.5s infinite;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
.upd{margin-left:auto;font-size:.75rem;color:var(--muted);}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
      gap:14px;padding:20px 24px;}
.kpi{background:var(--surf);border:1px solid var(--brd);border-radius:8px;
     padding:14px;text-align:center;}
.kpi .v{font-size:1.8rem;font-weight:700;}
.kpi .l{font-size:.72rem;color:var(--muted);margin-top:4px;}
.kpi.r .v{color:var(--red)}.kpi.w .v{color:var(--warn)}.kpi.g .v{color:var(--acc)}
.kpi.b .v{color:var(--blue)}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;padding:0 24px 24px;}
@media(max-width:780px){.grid{grid-template-columns:1fr;}}
.card{background:var(--surf);border:1px solid var(--brd);border-radius:8px;padding:14px;}
.card h2{font-size:.8rem;color:var(--muted);text-transform:uppercase;
         letter-spacing:.05em;margin-bottom:10px;}
canvas{max-height:200px;}
.wide{grid-column:1/-1;}
.tip{font-size:.95rem;padding:10px;background:#161b2288;border-radius:6px;
     border-left:3px solid var(--acc);}
.skill{display:inline-block;padding:4px 14px;border-radius:20px;font-weight:700;
       font-size:1.1rem;}
.skill.Beginner{background:#da363322;color:#da3633;}
.skill.Medium{background:#d2992222;color:#d29922;}
.skill.Pro{background:#23863622;color:#3fb950;}
table{width:100%;border-collapse:collapse;font-size:.8rem;}
th{color:var(--muted);padding:5px 7px;text-align:left;border-bottom:1px solid var(--brd);}
td{padding:5px 7px;border-bottom:1px solid var(--brd);}
.badge{display:inline-block;padding:2px 7px;border-radius:10px;font-size:.68rem;font-weight:600;}
</style>
</head>
<body>
<header>
  <div class="dot"></div>
  <h1>🚗 Visioner-Control SDLA – Live Dashboard</h1>
  <span class="upd" id="upd">Connecting…</span>
</header>

<div class="kpis">
  <div class="kpi g"><div class="v" id="kSkill">–</div><div class="l">Skill Level</div></div>
  <div class="kpi b"><div class="v" id="kSpeed">–</div><div class="l">Speed (km/h)</div></div>
  <div class="kpi w"><div class="v" id="kScore">–</div><div class="l">Session Score</div></div>
  <div class="kpi r"><div class="v" id="kViol">–</div><div class="l">Total Violations</div></div>
</div>

<div class="grid">
  <div class="card">
    <h2>Driver Skill</h2>
    <span class="skill" id="skillBadge">–</span>
  </div>
  <div class="card">
    <h2>Coaching Tip</h2>
    <p class="tip" id="tip">–</p>
  </div>
  <div class="card"><h2>Violations by Type</h2><canvas id="cType"></canvas></div>
  <div class="card"><h2>Lesson Progress</h2><canvas id="cProg"></canvas></div>
  <div class="card wide">
    <h2>Recent Violations</h2>
    <table>
      <thead><tr><th>Time</th><th>Type</th><th>Plate</th><th>Speed</th></tr></thead>
      <tbody id="vtbl"><tr><td colspan="4" style="color:var(--muted)">No violations yet.</td></tr></tbody>
    </table>
  </div>
</div>

<script>
const C=['#da3633','#d29922','#238636','#1f6feb','#8957e5','#ffa657','#56d364'];
function mk(id,type,data,opts={}){
  return new Chart(document.getElementById(id).getContext('2d'),{type,data,options:{
    responsive:true,maintainAspectRatio:true,
    plugins:{legend:{labels:{color:'#e6edf3',font:{size:11}}}},
    scales:['pie','doughnut'].includes(type)?undefined:{
      x:{ticks:{color:'#8b949e'},grid:{color:'#21262d'}},
      y:{ticks:{color:'#8b949e'},grid:{color:'#21262d'}}
    },...opts}});
}
const charts={
  type: mk('cType','doughnut',{labels:[],datasets:[{data:[],backgroundColor:C}]}),
  prog: mk('cProg','bar',{labels:['Duration (min)','Mistakes'],
           datasets:[{label:'Value',data:[0,0],backgroundColor:['#238636','#da3633']}]},
           {plugins:{legend:{display:false}}})
};

async function refresh(){
  try{
    const [tel,vio]=await Promise.all([
      fetch('/api/telemetry').then(r=>r.json()),
      fetch('/api/violations/stats').then(r=>r.json()),
    ]);
    // KPIs
    document.getElementById('kSkill').textContent=tel.skill;
    document.getElementById('kSpeed').textContent=tel.telemetry?.speed?.toFixed(0)||'–';
    document.getElementById('kScore').textContent=tel.progress?.Score??'–';
    document.getElementById('kViol').textContent=vio.total||0;
    // Skill badge
    const sb=document.getElementById('skillBadge');
    sb.textContent=tel.skill; sb.className='skill '+tel.skill;
    // Tip
    document.getElementById('tip').textContent=tel.tip||'Drive safely!';
    // Progress chart
    const p=tel.progress||{};
    charts.prog.data.datasets[0].data=[p['Duration (min)']||0,p['Mistakes']||0];
    charts.prog.update();
    // Violation type chart
    const bt=vio.by_type||{};
    charts.type.data.labels=Object.keys(bt);
    charts.type.data.datasets[0].data=Object.values(bt);
    charts.type.update();
    // Recent table
    const tbody=document.getElementById('vtbl');
    const rows=vio.recent||[];
    if(!rows.length){
      tbody.innerHTML='<tr><td colspan="4" style="color:var(--muted)">No violations yet.</td></tr>';
    }else{
      tbody.innerHTML=rows.map(r=>`<tr>
        <td>${r.timestamp}</td>
        <td><span class="badge" style="background:#da363322;color:#da3633">${r.violation_type}</span></td>
        <td>${r.license_plate}</td>
        <td>${r.speed_kmh||'–'}</td>
      </tr>`).join('');
    }
    document.getElementById('upd').textContent='Updated: '+new Date().toLocaleTimeString();
  }catch(e){
    document.getElementById('upd').textContent='Connection error';
  }
}
refresh();
setInterval(refresh,4000);
</script>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# Route registration
# ─────────────────────────────────────────────────────────────────────────────

def register_routes(app: Flask) -> None:
    """Registers all API + dashboard routes on *app*."""

    simulator  = TelemetrySimulator()
    classifier = DriverClassifier()
    tracker    = LessonTracker()
    coach      = VoiceCoach()
    vlogger    = ViolationLogger()

    # ── HTML Dashboard ────────────────────────────────────────────────
    @app.route("/")
    def dashboard():
        return render_template_string(_DASHBOARD_HTML)

    # ── Telemetry + skill API ─────────────────────────────────────────
    @app.route("/api/telemetry")
    def api_telemetry():
        data  = simulator.get_data()
        skill = classifier.classify(data)
        tracker.update(data)
        return jsonify({
            "telemetry": data,
            "skill":     skill,
            "tip":       coach.get_tip(skill),
            "progress":  tracker.get_summary(),
        })

    # ── Violations – list ─────────────────────────────────────────────
    @app.route("/api/violations", methods=["GET"])
    def api_violations_get():
        n = request.args.get("n", 20, type=int)
        return jsonify(vlogger.get_recent(n))

    # ── Violations – manual POST ──────────────────────────────────────
    @app.route("/api/violations", methods=["POST"])
    def api_violations_post():
        body = request.get_json(force=True, silent=True) or {}
        record = vlogger.log(
            violation_type  = body.get("violation_type", "MANUAL"),
            license_plate   = body.get("license_plate", "UNKNOWN"),
            speed_kmh       = body.get("speed_kmh"),
            confidence      = body.get("confidence", 1.0),
            evidence_path   = body.get("evidence_path", ""),
            location        = body.get("location", "N/A"),
            timestamp       = datetime.now(),
        )
        return jsonify(record), 201

    # ── Violations – aggregated stats ─────────────────────────────────
    @app.route("/api/violations/stats")
    def api_violations_stats():
        all_v   = vlogger.get_all()
        by_type: dict[str, int] = {}
        for row in all_v:
            vt = row.get("violation_type", "UNKNOWN")
            by_type[vt] = by_type.get(vt, 0) + 1
        return jsonify({
            "total":    len(all_v),
            "by_type":  by_type,
            "recent":   all_v[-20:],
        })

    # ── Session summary ───────────────────────────────────────────────
    @app.route("/api/session")
    def api_session():
        data  = simulator.get_data()
        skill = classifier.classify(data)
        return jsonify({
            "skill":    skill,
            "progress": tracker.get_summary(),
            "tip":      coach.get_tip(skill),
        })

    # ── Health check ──────────────────────────────────────────────────
    @app.route("/api/health")
    def api_health():
        return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})
