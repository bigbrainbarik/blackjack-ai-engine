"""
Result celebration / impact visual effects.

Each function returns an HTML snippet to inject via ``st.components.html()``.
Uses lightweight inline JS — no external libraries.
"""


def confetti_html(duration_ms: int = 3000) -> str:
    """Canvas-based confetti burst for Blackjack wins."""
    return f"""
    <canvas id="confetti-canvas" style="position:fixed;top:0;left:0;width:100%;height:100%;
        pointer-events:none;z-index:99999;"></canvas>
    <script>
    (function() {{
        const C = document.getElementById('confetti-canvas');
        if (!C) return;
        const ctx = C.getContext('2d');
        C.width = window.innerWidth;
        C.height = window.innerHeight;
        const colors = ['#ffd700','#ff6b6b','#48bb78','#4299e1','#ed64a6','#ecc94b','#fff'];
        const pieces = [];
        for (let i = 0; i < 150; i++) {{
            pieces.push({{
                x: C.width * 0.5 + (Math.random() - 0.5) * 200,
                y: C.height * 0.4,
                vx: (Math.random() - 0.5) * 16,
                vy: -Math.random() * 18 - 4,
                w: Math.random() * 10 + 4,
                h: Math.random() * 6 + 3,
                color: colors[Math.floor(Math.random() * colors.length)],
                rot: Math.random() * 360,
                rotV: (Math.random() - 0.5) * 12,
                gravity: 0.25 + Math.random() * 0.15,
                alpha: 1
            }});
        }}
        const start = performance.now();
        function frame(ts) {{
            const elapsed = ts - start;
            if (elapsed > {duration_ms}) {{ C.remove(); return; }}
            ctx.clearRect(0, 0, C.width, C.height);
            const fade = elapsed > {duration_ms * 0.7} ? 1 - (elapsed - {duration_ms * 0.7}) / {duration_ms * 0.3} : 1;
            pieces.forEach(p => {{
                p.vy += p.gravity;
                p.x += p.vx;
                p.y += p.vy;
                p.rot += p.rotV;
                p.vx *= 0.99;
                ctx.save();
                ctx.translate(p.x, p.y);
                ctx.rotate(p.rot * Math.PI / 180);
                ctx.globalAlpha = fade * p.alpha;
                ctx.fillStyle = p.color;
                ctx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h);
                ctx.restore();
            }});
            requestAnimationFrame(frame);
        }}
        requestAnimationFrame(frame);
    }})();
    </script>"""


def win_glow_html() -> str:
    """Pulsing green glow overlay for wins."""
    return """
    <div style="position:fixed;top:0;left:0;width:100%;height:100%;
        pointer-events:none;z-index:99998;
        animation: winGlow 1.2s ease-out forwards;">
    </div>
    <style>
    @keyframes winGlow {
        0%   { background: rgba(74, 222, 128, 0.15); }
        50%  { background: rgba(74, 222, 128, 0.06); }
        100% { background: transparent; }
    }
    </style>"""


def bust_flash_html() -> str:
    """Red flash for bust."""
    return """
    <div style="position:fixed;top:0;left:0;width:100%;height:100%;
        pointer-events:none;z-index:99998;
        animation: bustFlash 0.6s ease-out forwards;">
    </div>
    <style>
    @keyframes bustFlash {
        0%   { background: rgba(248, 113, 113, 0.2); }
        30%  { background: rgba(248, 113, 113, 0.08); }
        100% { background: transparent; }
    }
    </style>"""


def push_pulse_html() -> str:
    """Yellow pulse for push."""
    return """
    <div style="position:fixed;top:0;left:0;width:100%;height:100%;
        pointer-events:none;z-index:99998;
        animation: pushPulse 1s ease-out forwards;">
    </div>
    <style>
    @keyframes pushPulse {
        0%   { background: rgba(251, 191, 36, 0.12); }
        100% { background: transparent; }
    }
    </style>"""


def surrender_fade_html() -> str:
    """Gray fade effect for surrender."""
    return """
    <div style="position:fixed;top:0;left:0;width:100%;height:100%;
        pointer-events:none;z-index:99998;
        animation: surrFade 1s ease-out forwards;">
    </div>
    <style>
    @keyframes surrFade {
        0%   { background: rgba(160, 160, 160, 0.15); }
        100% { background: transparent; }
    }
    </style>"""


def get_effect_for_result(result: str) -> str:
    """Return the appropriate effect HTML for a game result string."""
    effects = {
        "BLACKJACK": confetti_html(),
        "WIN":       win_glow_html(),
        "BUST":      bust_flash_html(),
        "LOSE":      bust_flash_html(),
        "PUSH":      push_pulse_html(),
        "SURRENDER": surrender_fade_html(),
    }
    return effects.get(result, "")
