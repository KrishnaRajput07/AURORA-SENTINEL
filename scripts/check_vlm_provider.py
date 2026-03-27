#!/usr/bin/env python3
import argparse
import base64
import json
import os
import sys
import time
from io import BytesIO
from pathlib import Path


LOG_PATH = Path("/home/anon/PROJECTS/aurora/AURORA-SENTINEL-1/.cursor/debug-57135e.log")
SESSION_ID = "57135e"
LOCATION = "scripts/check_vlm_provider.py"


def ndjson_log(run_id: str, hypothesis_id: str, message: str, data: dict) -> None:
    payload = {
        "sessionId": SESSION_ID,
        "id": f"log_{int(time.time() * 1000)}_{os.getpid()}",
        "timestamp": int(time.time() * 1000),
        "runId": run_id,
        "hypothesisId": hypothesis_id,
        "location": LOCATION,
        "message": message,
        "data": data,
    }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")


def make_dummy_image_pil() -> "object":
    # Keep image tiny so encode+transfer stays fast.
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (96, 96), color=(10, 10, 10))
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, 80, 80], outline=(240, 240, 240), width=3)
    draw.line([0, 96, 96, 0], fill=(80, 200, 255), width=3)
    return img


def pil_to_data_url_jpeg_b64(img) -> str:
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def safe_get_status(tracker, model_name: str):
    try:
        return tracker.get_status(model_name)
    except Exception:
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Runtime check of VLM provider/model + fallback behavior.")
    parser.add_argument("--runs", type=int, default=3, help="How many analyze_image calls to make (same process).")
    parser.add_argument("--mlScore", type=int, default=85, help="ML score to force deeper analysis.")
    parser.add_argument("--cameraId", type=str, default="TEST_CAMERA")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))

    # Import router with the exact same config resolution it uses at runtime.
    ai_layer_dir = repo_root / "ai-intelligence-layer"
    sys.path.insert(0, str(ai_layer_dir))
    try:
        import aiRouter_enhanced
    except Exception as e:
        print(f"Failed to import aiRouter_enhanced: {e}")
        raise

    try:
        import config as app_config
    except Exception:
        app_config = None

    expected_model_tag = getattr(app_config, "OLLAMA_CLOUD_MODEL", "qwen3-vl:235b-cloud") if app_config else "qwen3-vl:235b-cloud"

    resolved = {
        "env_PRIMARY_VLM_PROVIDER": os.getenv("PRIMARY_VLM_PROVIDER"),
        "env_OLLAMA_CLOUD_MODEL": os.getenv("OLLAMA_CLOUD_MODEL"),
        "config_PRIMARY_VLM_PROVIDER": getattr(app_config, "PRIMARY_VLM_PROVIDER", None) if app_config else None,
        "config_OLLAMA_CLOUD_MODEL": getattr(app_config, "OLLAMA_CLOUD_MODEL", None) if app_config else None,
        "router_PRIMARY_PROVIDER": getattr(aiRouter_enhanced, "PRIMARY_PROVIDER", None),
        "router_OLLAMA_MODEL": getattr(aiRouter_enhanced, "OLLAMA_MODEL", None),
        "router_QWEN2VL_MODEL": getattr(aiRouter_enhanced, "QWEN2VL_MODEL", None),
        "expected_ollama_model_tag": expected_model_tag,
    }
    print("Resolved provider/model configuration:")
    print(json.dumps(resolved, indent=2, sort_keys=True))
    ndjson_log(
        run_id="precheck",
        hypothesis_id="H3_or_H4",
        message="Resolved PRIMARY_PROVIDER and model tags",
        data=resolved,
    )

    # Check that Ollama is available and that the expected tag exists in the running Ollama instance.
    ollama_check = {"ollama_importable": False, "ollama_list_return_shape": None, "expected_present": None}
    try:
        import ollama  # type: ignore

        ollama_check["ollama_importable"] = True
        models_resp = ollama.list()
        ollama_check["models_resp_type"] = type(models_resp).__name__
        models = None
        if isinstance(models_resp, dict) and "models" in models_resp:
            models = models_resp.get("models")
            ollama_check["ollama_list_return_shape"] = "dict.models"
        elif isinstance(models_resp, list):
            models = models_resp
            ollama_check["ollama_list_return_shape"] = "list"

        found = False
        model_names = []
        if isinstance(models, list):
            for m in models:
                name = m.get("name") if isinstance(m, dict) else None
                if name:
                    model_names.append(name)
                if name == expected_model_tag:
                    found = True

        ollama_check["expected_present"] = found
        ollama_check["matching_model_names_sample"] = model_names[:20]

        # Also attempt show() for more concrete evidence (best-effort).
        try:
            ollama_check["show_expected_model_ok"] = True if ollama.show(expected_model_tag) else True
        except Exception as e:
            ollama_check["show_expected_model_ok"] = False
            ollama_check["show_expected_model_error"] = str(e)

    except Exception as e:
        ollama_check["ollama_importable"] = False
        ollama_check["error"] = str(e)

    print("\nOllama instance model check (expected tag presence):")
    print(json.dumps(ollama_check, indent=2, sort_keys=True))
    ndjson_log(
        run_id="precheck",
        hypothesis_id="H4",
        message="Checked Ollama instance for expected model tag",
        data=ollama_check,
    )

    # Build dummy image and call the same main routing function as the server does.
    image = make_dummy_image_pil()
    image_data = pil_to_data_url_jpeg_b64(image)
    ml_score = int(args.mlScore)
    ml_factors = {}

    # Access the same availability tracker used for circuit-breaking.
    tracker = getattr(aiRouter_enhanced, "_availability_tracker", None)
    initial_tracker_status = safe_get_status(tracker, "ollama") if tracker else None
    print("\nInitial availability tracker status (ollama):")
    print(json.dumps(initial_tracker_status, indent=2, sort_keys=True))
    ndjson_log(
        run_id="precheck",
        hypothesis_id="H5",
        message="Initial ollama availability status",
        data={"ollama_status": initial_tracker_status, "cooldown_seconds_hint": getattr(tracker, "COOLDOWN_SECONDS", None)},
    )

    for i in range(1, args.runs + 1):
        run_id = f"analyze_image_run_{i}"
        before = safe_get_status(tracker, "ollama") if tracker else None
        print(f"\n=== analyze_image call {i}/{args.runs} ===")
        print("Tracker status before call (ollama):")
        print(json.dumps(before, indent=2, sort_keys=True))

        t0 = time.time()
        result = aiRouter_enhanced.analyze_image(image_data, ml_score, ml_factors, args.cameraId)
        dt = time.time() - t0

        after = safe_get_status(tracker, "ollama") if tracker else None

        # Reduce noise in the console but keep the deciding fields.
        compact = {
            "provider": result.get("provider"),
            "aiScore": result.get("aiScore"),
            "sceneType": result.get("sceneType"),
            "confidence": result.get("confidence"),
            "latency_metrics": result.get("latency_metrics"),
            "errors": result.get("errors"),
            "elapsed_sec": round(dt, 3),
            "tracker_ollama_before": before,
            "tracker_ollama_after": after,
        }
        print("Result (compact):")
        print(json.dumps(compact, indent=2, sort_keys=True))

        hypothesis_id = "H1_if_ollama_succeeds_else_H2"
        ndjson_log(
            run_id=run_id,
            hypothesis_id=hypothesis_id,
            message="analyze_image result + provider/fallback evidence",
            data=compact,
        )


if __name__ == "__main__":
    main()

