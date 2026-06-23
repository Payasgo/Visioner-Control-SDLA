// static/js/main.js

(function () {
    "use strict";

    var POLL_INTERVAL = 5000; // ms

    function updateDashboard() {
        fetch("/api/telemetry")
            .then(function (res) {
                if (!res.ok) {
                    throw new Error("HTTP " + res.status);
                }
                return res.json();
            })
            .then(function (data) {
                // --- Skill badge ---
                var skillEl = document.getElementById("skill");
                if (skillEl && data.skill) {
                    skillEl.textContent = data.skill;
                    skillEl.className = "badge badge--" + data.skill.toLowerCase();
                }

                // --- Driving tip ---
                var tipEl = document.getElementById("tip");
                if (tipEl && data.tip) {
                    tipEl.textContent = data.tip;
                }

                // --- Progress table ---
                var tableEl = document.getElementById("progress-table");
                if (tableEl && data.progress) {
                    var rows = "";
                    Object.keys(data.progress).forEach(function (key) {
                        rows +=
                            "<tr><td><strong>" +
                            escapeHtml(key) +
                            "</strong></td><td>" +
                            escapeHtml(String(data.progress[key])) +
                            "</td></tr>";
                    });
                    tableEl.innerHTML = rows;
                }
            })
            .catch(function (err) {
                console.error("Failed to fetch telemetry:", err);
            });
    }

    /** Minimal HTML escaping to prevent XSS from server-returned strings. */
    function escapeHtml(str) {
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }

    // Kick off polling once the DOM is ready
    document.addEventListener("DOMContentLoaded", function () {
        setInterval(updateDashboard, POLL_INTERVAL);
    });
})();
