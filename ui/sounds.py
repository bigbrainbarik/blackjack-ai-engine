"""
JavaScript-based sound-effects system.

Sounds are tiny base64-encoded audio blips generated procedurally so we don't
need external asset files — works on Streamlit Community Cloud out of the box.

Each ``play_*`` function returns an HTML snippet with an inline ``<script>``
that plays the sound via the Web Audio API.
"""


def _audio_context_js() -> str:
    """Reusable AudioContext initializer."""
    return """
    (function(){
      if(!window._bjAudioCtx){
        window._bjAudioCtx = new (window.AudioContext || window.webkitAudioContext)();
      }
    })();
    """


def _synth_beep(freq: float, duration: float, type_: str = "sine",
                volume: float = 0.3, attack: float = 0.01,
                decay: float = 0.1) -> str:
    """Generate JS to play a synthesized beep via Web Audio API."""
    return f"""
    (function(){{
      const ctx = window._bjAudioCtx;
      if(!ctx) return;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = '{type_}';
      osc.frequency.value = {freq};
      gain.gain.setValueAtTime(0, ctx.currentTime);
      gain.gain.linearRampToValueAtTime({volume}, ctx.currentTime + {attack});
      gain.gain.linearRampToValueAtTime(0, ctx.currentTime + {duration});
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + {duration} + 0.05);
    }})();"""


def _noise_burst(duration: float = 0.05, volume: float = 0.15) -> str:
    """Short white-noise burst (card snap / chip click)."""
    # Use a buffer of random samples
    sample_rate = 22050
    n_samples = int(sample_rate * duration)
    return f"""
    (function(){{
      const ctx = window._bjAudioCtx;
      if(!ctx) return;
      const buf = ctx.createBuffer(1, {n_samples}, {sample_rate});
      const data = buf.getChannelData(0);
      for(let i=0;i<{n_samples};i++) data[i]=(Math.random()*2-1)*{volume};
      // Apply quick fade-out
      for(let i=Math.floor({n_samples}*0.6);i<{n_samples};i++)
        data[i]*=1-(i-{n_samples}*0.6)/({n_samples}*0.4);
      const src = ctx.createBufferSource();
      src.buffer = buf;
      const gain=ctx.createGain();
      gain.gain.value={volume};
      src.connect(gain);
      gain.connect(ctx.destination);
      src.start();
    }})();"""


def sound_html(event: str, enabled: bool = True, volume: float = 0.5) -> str:
    """
    Return an HTML snippet that plays a sound for the given event.

    Events: card_deal, card_flip, chip_place, win, lose, blackjack, bust, button_click
    """
    if not enabled:
        return ""

    vol = max(0.05, min(1.0, volume))

    sound_map = {
        "card_deal":    _noise_burst(0.04, 0.12 * vol),
        "card_flip":    _noise_burst(0.06, 0.10 * vol),
        "chip_place":   _noise_burst(0.03, 0.15 * vol),
        "button_click": _synth_beep(800, 0.08, "sine", 0.1 * vol),
        "win":          (_synth_beep(523, 0.15, "sine", 0.2 * vol) +
                         _synth_beep(659, 0.15, "sine", 0.2 * vol) +
                         _synth_beep(784, 0.25, "sine", 0.25 * vol)),
        "lose":         _synth_beep(220, 0.4, "sawtooth", 0.15 * vol, decay=0.3),
        "blackjack":    (_synth_beep(523, 0.12, "sine", 0.25 * vol) +
                         _synth_beep(659, 0.12, "sine", 0.25 * vol) +
                         _synth_beep(784, 0.12, "sine", 0.25 * vol) +
                         _synth_beep(1047, 0.3, "sine", 0.3 * vol)),
        "bust":         (_synth_beep(300, 0.2, "square", 0.15 * vol) +
                         _synth_beep(200, 0.3, "square", 0.12 * vol)),
    }

    js_code = sound_map.get(event, "")
    if not js_code:
        return ""

    return f"""<div style="display:none;">
    <script>
    {_audio_context_js()}
    {js_code}
    </script>
    </div>"""
