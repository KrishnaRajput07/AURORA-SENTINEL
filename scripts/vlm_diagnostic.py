"""
AURORA-SENTINEL VLM Diagnostic Script
======================================
Checks whether the primary VLM provider is truly Ollama -> qwen3-vl:235b-cloud
OR whether fallbacks are silently happening.

Run from the project root:
    python scripts/vlm_diagnostic.py

Output is written to: scripts/vlm_report.txt
"""

import os, sys, io, time, json, re, textwrap

# ── stdout: force UTF-8 so emojis work on Windows terminals ───────────────────
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "ai-intelligence-layer"))

lines = []   # collected output for the report file

def p(*args):
    txt = " ".join(str(a) for a in args)
    print(txt)
    lines.append(txt)

def hdr(t):
    p(); p("=" * 64); p(f"  {t}"); p("=" * 64)
def ok(t):   p(f"  [OK]   {t}")
def fail(t): p(f"  [FAIL] {t}")
def warn(t): p(f"  [WARN] {t}")
def info(t): p(f"  [INFO] {t}")

# ══════════════════════════════════════════════════════════════════════════════
# 1. CONFIG AUDIT
# ══════════════════════════════════════════════════════════════════════════════
hdr("1. CONFIG AUDIT  (all files that touch PRIMARY_VLM_PROVIDER / OLLAMA_CLOUD_MODEL)")

env_provider = os.getenv("PRIMARY_VLM_PROVIDER", "<NOT SET>")
env_model    = os.getenv("OLLAMA_CLOUD_MODEL",   "<NOT SET>")
info(f"Env PRIMARY_VLM_PROVIDER = {env_provider}")
info(f"Env OLLAMA_CLOUD_MODEL   = {env_model}")

try:
    import config as app_config
    cfg_provider = getattr(app_config, "PRIMARY_VLM_PROVIDER", "MISSING")
    cfg_model    = getattr(app_config, "OLLAMA_CLOUD_MODEL",   "MISSING")
    ok(f"config.py  PRIMARY_VLM_PROVIDER = {cfg_provider}")
    ok(f"config.py  OLLAMA_CLOUD_MODEL   = {cfg_model}")
except ImportError as e:
    fail(f"Could not import config.py: {e}")
    cfg_provider = "qwen2vl_local"
    cfg_model    = "qwen3-vl:235b-cloud"
    app_config   = None

# What aiRouter_enhanced.py sees at module level
router_provider = getattr(app_config, "PRIMARY_VLM_PROVIDER", "qwen2vl_local") if app_config else cfg_provider
router_model    = getattr(app_config, "OLLAMA_CLOUD_MODEL",   "qwen3-vl:235b-cloud") if app_config else cfg_model
info(f"aiRouter_enhanced.py will see PRIMARY_PROVIDER = {router_provider}")
info(f"aiRouter_enhanced.py will see OLLAMA_MODEL     = {router_model}")

target_model_tag = cfg_model

if router_provider == "ollama_cloud":
    ok("PRIMARY_PROVIDER = 'ollama_cloud'  ->  Ollama IS the intended primary VLM")
else:
    warn(f"PRIMARY_PROVIDER = '{router_provider}'  ->  Ollama is NOT the primary VLM")

if router_model == "qwen3-vl:235b-cloud":
    ok(f"Model tag is correct: {router_model}")
else:
    warn(f"Model tag is '{router_model}' -- not the expected 'qwen3-vl:235b-cloud'")

# ══════════════════════════════════════════════════════════════════════════════
# 2. OLLAMA SERVICE CHECK
# ══════════════════════════════════════════════════════════════════════════════
hdr("2. OLLAMA SERVICE CHECK")

ollama_running = False
model_found    = False
_ollama_lib    = None

try:
    import ollama as _ollama_lib
    ok("ollama Python package installed")
except ImportError:
    fail("ollama Python package NOT installed  ->  pip install ollama")

if _ollama_lib:
    try:
        t0 = time.time()
        model_list  = _ollama_lib.list()
        elapsed_ms  = int((time.time() - t0) * 1000)
        ollama_running = True
        ok(f"Ollama service is reachable  ({elapsed_ms} ms)")

        models = getattr(model_list, "models", model_list)
        if not isinstance(models, list):
            models = list(models)

        info(f"Models available locally: {len(models)}")
        for m in models:
            name     = getattr(m, "model", None) or getattr(m, "name", str(m))
            size     = getattr(m, "size", None)
            size_str = f"  ({size / 1e9:.1f} GB)" if size else ""
            p(f"       - {name}{size_str}")
            if name == target_model_tag or target_model_tag in name:
                model_found = True

        if model_found:
            ok(f"Target model '{target_model_tag}' is present in Ollama")
        else:
            fail(f"Target model '{target_model_tag}' NOT found in Ollama")
            warn("  -> Every call to this model will raise an exception -> fallback occurs")
            warn(f"  Fix:  ollama pull {target_model_tag}")

    except Exception as e:
        fail(f"Ollama service NOT reachable: {e}")
        warn("  -> Every ollama_cloud call will fail -> fallback will occur silently")

# ══════════════════════════════════════════════════════════════════════════════
# 3. LIVE CALL  --  exact replica of analyze_with_ollama() in aiRouter_enhanced.py
# ══════════════════════════════════════════════════════════════════════════════
hdr("3. LIVE CALL  ->  ollama.chat(model='" + target_model_tag + "')")

# Build a 100x100 synthetic grey test image
test_img_bytes = None
try:
    from PIL import Image as PILImage
    synthetic_img  = PILImage.new("RGB", (100, 100), color=(100, 100, 100))
    buf            = io.BytesIO()
    synthetic_img.save(buf, format="JPEG")
    test_img_bytes = buf.getvalue()
    ok("Synthetic test image created (100x100 grey frame)")
except Exception as e:
    fail(f"Could not create test image (Pillow missing?): {e}")

# Exact structured prompt used by the system when ml_score > STRUCTURED_PROMPT_THRESHOLD
STRUCTURED_PROMPT = (
    "Analyze this image for violence or fighting in a PUBLIC SURVEILLANCE context.\n\n"
    "Classify as ONE of these categories:\n"
    "1. REAL_FIGHT: Physical aggression, assault, or attack (NO protective gear)\n"
    "2. ORGANIZED_SPORT: Boxing/martial arts WITH protective gear AND referee/ring\n"
    "3. SUSPICIOUS: Crowd surrounding people OR unknown items in suspicious contexts\n"
    "4. NORMAL: Safe activity, no threats\n\n"
    "Risk scoring:\n"
    "- REAL_FIGHT with heavy fighting: 80-95\n"
    "- REAL_FIGHT without heavy indicators: 75-90\n"
    "- ORGANIZED_SPORT: 20-35\n"
    "- SUSPICIOUS: 60-75\n"
    "- NORMAL: 10-25\n\n"
    "Respond in JSON: "
    '{"aiScore": <0-100>, "sceneType": "<real_fight|organized_sport|suspicious|normal>", '
    '"explanation": "<what you see>", "confidence": <0.0-1.0>}'
)

call_result = {
    "provider_used":   None,
    "model_name":      None,
    "response_raw":    None,
    "latency_ms":      None,
    "success":         False,
    "error":           None,
    "fallback_reason": None,
}

if _ollama_lib and ollama_running and test_img_bytes:
    info(f"Sending request to ollama.chat(model='{target_model_tag}') ...")
    t_start = time.time()
    try:
        response = _ollama_lib.chat(
            model=target_model_tag,
            messages=[{
                "role":    "user",
                "content": STRUCTURED_PROMPT,
                "images":  [test_img_bytes],
            }]
        )
        latency_ms    = int((time.time() - t_start) * 1000)
        response_text = response["message"]["content"]

        call_result.update({
            "provider_used": "ollama",
            "model_name":    target_model_tag,
            "response_raw":  response_text,
            "latency_ms":    latency_ms,
            "success":       True,
        })
        ok(f"Ollama responded in {latency_ms} ms")
        p()
        p("  --- Raw response ---")
        for line in textwrap.wrap(response_text, width=70):
            p(f"  {line}")
        p("  -------------------")

    except Exception as e:
        latency_ms = int((time.time() - t_start) * 1000)
        call_result.update({
            "error":           str(e),
            "latency_ms":      latency_ms,
            "fallback_reason": f"ollama.chat raised: {e}",
        })
        fail(f"Ollama call FAILED after {latency_ms} ms")
        fail(f"  Exception: {e}")
        warn("  System would now fall back to Qwen2-VL local")

elif not _ollama_lib:
    call_result["fallback_reason"] = "ollama package not installed"
    fail("Skipping live call -- ollama package not installed")
elif not ollama_running:
    call_result["fallback_reason"] = "Ollama service not reachable"
    fail("Skipping live call -- Ollama service is down")
else:
    call_result["fallback_reason"] = "test image could not be built"
    fail("Skipping live call -- test image build failed")

# ══════════════════════════════════════════════════════════════════════════════
# 4. RESPONSE ANALYSIS  (same parse logic as aiRouter_enhanced.py)
# ══════════════════════════════════════════════════════════════════════════════
hdr("4. RESPONSE ANALYSIS")

if call_result["success"] and call_result["response_raw"]:
    response_text = call_result["response_raw"]
    json_match    = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
    parsed_ok     = False

    if json_match:
        try:
            parsed     = json.loads(json_match.group())
            ai_score   = int(parsed.get("aiScore", -1))
            scene_type = parsed.get("sceneType", "N/A")
            confidence = float(parsed.get("confidence", 0.0))
            explanation= parsed.get("explanation", "")
            ok("Response contains valid JSON  ->  model followed structured format")
            info(f"  aiScore    = {ai_score}")
            info(f"  sceneType  = {scene_type}")
            info(f"  confidence = {confidence}")
            info(f"  explanation= {explanation[:150]}")
            parsed_ok = True
        except Exception as je:
            warn(f"JSON block found but failed to parse: {je}")

    if not parsed_ok:
        warn("No valid JSON in response -- system would use keyword-based fallback parser")
        lower      = response_text.lower()
        has_fight  = any(k in lower for k in ["fight","violence","assault","attack","punch","aggressive"])
        has_sport  = any(k in lower for k in ["boxing","martial arts","referee","gloves","headgear"])
        has_normal = any(k in lower for k in ["normal","safe","walking","standing","peaceful"])
        info(f"  Keyword hits -> fight={has_fight}, sport={has_sport}, normal={has_normal}")

    lt = call_result["latency_ms"]
    if lt is not None:
        timeout_ms = int(getattr(app_config, "AI_TOTAL_TIMEOUT", 5.0) * 1000) if app_config else 5000
        if lt < timeout_ms:
            ok(f"Latency OK: {lt} ms < AI_TOTAL_TIMEOUT {timeout_ms} ms")
        else:
            warn(f"Latency {lt} ms EXCEEDS AI_TOTAL_TIMEOUT {timeout_ms} ms -- response would be cut off!")
else:
    warn("No response to analyse")

# ══════════════════════════════════════════════════════════════════════════════
# 5. FALLBACK CHAIN TRACE
# ══════════════════════════════════════════════════════════════════════════════
hdr("5. FALLBACK CHAIN TRACE  (analyze_image() in aiRouter_enhanced.py:528)")

p()
p("  Step 1: PRIMARY_PROVIDER == 'ollama_cloud'?")
if cfg_provider == "ollama_cloud":
    ok(      "  YES  -> system calls analyze_with_ollama() first")
    p()
    p("  Step 2: analyze_with_ollama() succeeds?")
    if call_result["success"]:
        ok(  "  YES  -> result returned. NO fallback triggered. Ollama is live!")
        final_verdict = "OLLAMA_CLOUD_PRIMARY_WORKING"
    else:
        fail(f"  NO   -> {call_result['error'] or call_result['fallback_reason']}")
        warn("  System logs 'Primary Ollama failed, falling back to Local (Qwen2-VL)'")
        p()
        p("  Step 3: analyze_with_qwen2vl() available?")
        try:
            from qwen2vl_integration import Qwen2VLAnalyzer  # noqa: F401
            warn("  Qwen2-VL importable -- but needs ~4 GB VRAM to load")
            final_verdict = "OLLAMA_FAILED__QWEN2VL_FALLBACK_POSSIBLE"
        except ImportError:
            fail("  qwen2vl_integration not importable -> Qwen2-VL would also fail")
            p()
            p("  Step 4: fallback_analysis() -> uses raw ML score (confidence=0.3)")
            warn("  FULL FALLBACK: no VLM is running -- ML-only scoring active")
            final_verdict = "FULL_ML_FALLBACK"
else:
    warn(f"  PRIMARY_PROVIDER = '{cfg_provider}'  ->  Ollama is NOT configured as primary")
    info("  System goes directly to analyze_with_qwen2vl() instead")
    final_verdict = "OLLAMA_NOT_PRIMARY"

# ══════════════════════════════════════════════════════════════════════════════
# 6. FINAL VERDICT
# ══════════════════════════════════════════════════════════════════════════════
hdr("6. FINAL VERDICT")

verdicts = {
    "OLLAMA_CLOUD_PRIMARY_WORKING": (
        "[PASS]",
        f"Ollama is primary AND is responding with '{target_model_tag}'.",
        "No fallbacks are occurring. System is working as intended."
    ),
    "OLLAMA_FAILED__QWEN2VL_FALLBACK_POSSIBLE": (
        "[WARN]",
        f"'{target_model_tag}' is configured as primary but NOT responding.",
        "Every analysis call is silently falling back to local Qwen2-VL.\n"
        f"  Fix: make sure Ollama is running and run:  ollama pull {target_model_tag}"
    ),
    "FULL_ML_FALLBACK": (
        "[CRIT]",
        "CRITICAL: Both Ollama AND Qwen2-VL are unavailable.",
        "System is running on ML-only scoring (confidence=0.3).\n"
        "  AI scene understanding is COMPLETELY DISABLED."
    ),
    "OLLAMA_NOT_PRIMARY": (
        "[WARN]",
        f"PRIMARY_VLM_PROVIDER='{cfg_provider}' -- Ollama is not the primary VLM.",
        "Check .env or config.py if you intended ollama_cloud to be primary."
    ),
}

label, summary, detail = verdicts.get(final_verdict, ("[UNKN]", "Unexpected state", ""))
p()
p(f"  {label}  {summary}")
p()
for line in detail.split("\n"):
    p(f"  {line}")
p()
p("  Action items:")
if not (_ollama_lib and ollama_running):
    p("  -> Start Ollama service:  ollama serve")
if ollama_running and not model_found:
    p(f"  -> Pull the model:        ollama pull {target_model_tag}")
if final_verdict == "OLLAMA_CLOUD_PRIMARY_WORKING":
    p("  -> None. Everything is working correctly.")
p()

# ══════════════════════════════════════════════════════════════════════════════
# Save report
# ══════════════════════════════════════════════════════════════════════════════
report_path = os.path.join(ROOT, "scripts", "vlm_report.txt")
with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"\n  Report saved: {report_path}")
