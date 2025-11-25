# src/scheduling/gemini_mcp.py
import os
import json
from google import genai as genai
from typing import Any, Dict, List
import logging

class GeminiMCP:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Set GEMINI_API_KEY environment variable")
        # Attempt to configure the genai client for a variety of library versions.
        # If configuration or model creation fails, fall back to a lightweight
        # heuristic implementation so the app stays usable without the API.
        self._use_genai = False
        self.model = None
        try:
            if hasattr(genai, "configure"):
                genai.configure(api_key=api_key)
            elif hasattr(genai, "Client"):
                # recent variants may use a Client class
                try:
                    genai.client = genai.Client(api_key=api_key)
                except Exception:
                    # best-effort: set environment variables recognised by some builds
                    os.environ.setdefault("GOOGLE_API_KEY", api_key)
            else:
                # Set common env vars used by alternative entrypoints
                os.environ.setdefault("GOOGLE_API_KEY", api_key)
                os.environ.setdefault("GENAI_API_KEY", api_key)

            # Try to create the high-level model object if available
            if hasattr(genai, "GenerativeModel"):
                try:
                    self.model = genai.GenerativeModel(
                        model_name="gemini-1.5-flash",
                        generation_config={
                            "temperature": 0.2,
                            "response_mime_type": "application/json",
                        }
                    )
                    self._use_genai = True
                except Exception:
                    logging.info("genai.GenerativeModel exists but failed to instantiate; falling back to heuristics")
            else:
                logging.info("genai.GenerativeModel not available in this genai build; using heuristics")

        except AttributeError as e:
            # Older/newer genai builds may not expose configure; proceed with heuristics
            logging.info(f"genai configuration not available: {e}; using heuristics")
        except Exception as e:
            logging.warning(f"Unexpected error initializing genai client: {e}; using heuristics")

    def estimate_duration(self, task_name: str, description: str) -> float:
        prompt = f"""
You are an expert project manager and time estimator.
Estimate how long the following task will realistically take for an experienced professional (in minutes, as a number only).

Examples:
Task: "Review PR for feature X"
Description: "Check logic, run tests, confirm documentation updated"
→ 90

Task: "Answer customer emails"
Description: "Reply to 15 pending support tickets"
→ 120

Task: "{task_name}"
Description: "{description}"

Return ONLY a JSON object: {{"estimated_minutes": <number>}}
"""
        # If genai is configured and model available, try to use it, otherwise
        # fall back to a local heuristic estimator so the app remains functional.
        if self._use_genai and self.model is not None:
            try:
                response = self.model.generate_content(prompt)
                data = json.loads(response.text)
                return float(data["estimated_minutes"])
            except Exception as e:
                logging.warning(f"Gemini call failed for estimate_duration: {e}; falling back to heuristic")

        # Heuristic fallback: base estimate on description length and task name
        word_count = len((task_name + " " + description).split())
        # base: 15 minutes + 0.5 minute per word, clamped
        estimated = max(10.0, min(8 * 60.0, 15.0 + 0.5 * word_count))
        return estimated

    def detect_distractions(self, task: Dict[str, Any], open_items: List[str]) -> Dict[str, Any]:
        task_name = task["name"]
        attached = task.get("attached_apps", [])
        attached_str = ", ".join(attached) if attached else "none specified"

        open_str = "\n".join([f"- {item}" for item in open_items])

        prompt = f"""
You are a strict focus coach. The user is working on this task:

Task: {task_name}
Required/attached applications: {attached_str}

Currently open applications/tabs:
{open_str}

Identify any items that are VERY LIKELY to be distractions (social media, streaming, games, unrelated news, etc.).
Ignore IDEs, terminals, browsers open to documentation, or tools explicitly attached to the task.

Return JSON exactly like this:
{{
  "distractions": ["firefox: youtube.com/watch?v=funnycats", "vlc.exe"],
  "rationale": "YouTube and VLC are entertainment platforms not required for report writing.",
  "suggestion": "Close these tabs/apps or take a proper break later."
}}

If no clear distractions, return empty list and "No distractions detected." as rationale.
"""
        # Use genai if available, otherwise perform a heuristic detection.
        if self._use_genai and self.model is not None:
            try:
                response = self.model.generate_content(prompt)
                return json.loads(response.text)
            except Exception as e:
                logging.warning(f"Gemini call failed for detect_distractions: {e}; falling back to heuristic")

        # Heuristic fallback: flag obvious entertainment/social apps/tabs
        lower_open = [s.lower() for s in open_items]
        distractions = []
        distract_keywords = ["youtube", "vimeo", "netflix", "tiktok", "spotify", "vlc", "steam", "reddit", "facebook", "twitter", "instagram"]
        for item in lower_open:
            for kw in distract_keywords:
                if kw in item:
                    distractions.append(item)
                    break

        # Remove any attached apps from distractions if they match by name
        attached_lower = [a.lower() for a in attached]
        filtered = [d for d in distractions if not any(a in d for a in attached_lower)]

        if not filtered:
            return {"distractions": [], "rationale": "No distractions detected.", "suggestion": ""}

        rationale = "The following open apps/tabs appear entertainment or social in nature and are unlikely required for the current task."
        suggestion = "Close these tabs/apps or save them for a scheduled break."
        return {"distractions": filtered, "rationale": rationale, "suggestion": suggestion}