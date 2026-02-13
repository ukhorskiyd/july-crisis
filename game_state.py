"""
Game state management for the July Crisis game.
Handles creation, persistence, updates, and win/lose condition checks.
"""

import json
import os
import re
from pathlib import Path

SAVE_FILE = Path(__file__).parent / "savegame.json"

DATES = {
    1: "July 23, 1914",
    2: "July 24, 1914",
    3: "July 25, 1914",
    4: "July 26, 1914",
    5: "July 28, 1914",
}


def new_game() -> dict:
    """Create a fresh game state."""
    return {
        "turn": 1,
        "date": DATES[1],
        "faction_hawks": {"loyalty": 60, "demand": "Crush Serbia"},
        "faction_moderates": {"loyalty": 50, "demand": "Avoid general war"},
        "serbia_compliance": 0,
        "russia_mobilization_threat": 20,
        "germany_support": 70,
        "player_messages": [],
        "api_usage": {"total_tokens": 0, "total_calls": 0, "estimated_cost_usd": 0.0},
    }


def save_game(state: dict) -> None:
    """Save game state to JSON file."""
    with open(SAVE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def load_game() -> dict | None:
    """Load game state from JSON file, or None if no save exists."""
    if SAVE_FILE.exists():
        with open(SAVE_FILE) as f:
            return json.load(f)
    return None


def delete_save() -> None:
    """Delete the save file."""
    if SAVE_FILE.exists():
        os.remove(SAVE_FILE)


def clamp(value: int, lo: int = 0, hi: int = 100) -> int:
    """Clamp an integer to [lo, hi]."""
    return max(lo, min(hi, value))


def parse_shift(text: str, label: str) -> int:
    """Extract a numeric shift value from AI response text.

    Looks for patterns like 'LABEL: +5' or 'LABEL: -10'.
    Returns 0 if not found.
    """
    pattern = rf"{label}:\s*([+-]?\d+)"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 0


def apply_shifts(state: dict, serbia_text: str, russia_text: str,
                 germany_text: str, faction_text: str) -> dict:
    """Parse AI responses and apply all shifts to game state."""
    compliance_shift = parse_shift(serbia_text, "COMPLIANCE_SHIFT")
    mobilization_shift = parse_shift(russia_text, "MOBILIZATION_SHIFT")
    support_shift = parse_shift(germany_text, "GERMANY_SUPPORT_SHIFT")
    hawks_shift = parse_shift(faction_text, "HAWKS_SHIFT")
    moderates_shift = parse_shift(faction_text, "MODERATES_SHIFT")

    state["serbia_compliance"] = clamp(state["serbia_compliance"] + compliance_shift)
    state["russia_mobilization_threat"] = clamp(state["russia_mobilization_threat"] + mobilization_shift)
    state["germany_support"] = clamp(state["germany_support"] + support_shift)
    state["faction_hawks"]["loyalty"] = clamp(state["faction_hawks"]["loyalty"] + hawks_shift)
    state["faction_moderates"]["loyalty"] = clamp(state["faction_moderates"]["loyalty"] + moderates_shift)

    return state


def advance_turn(state: dict) -> dict:
    """Move to the next turn."""
    state["turn"] += 1
    if state["turn"] <= 5:
        state["date"] = DATES[state["turn"]]
    return state


def check_lose_conditions(state: dict) -> str | None:
    """Check if any lose condition is met. Returns a description or None."""
    if state["russia_mobilization_threat"] >= 80:
        return (
            "DEFEAT — GENERAL WAR\n"
            "Russia has ordered general mobilization. Germany activates the Schlieffen Plan. "
            "France mobilizes. Britain wavers but will soon join. The Great War has begun.\n"
            "Austria-Hungary will be ground down in a multi-front war it cannot win. "
            "The Monarchy's days are numbered."
        )
    if state["faction_hawks"]["loyalty"] < 30:
        return (
            "DEFEAT — INTERNAL COLLAPSE (Hawks)\n"
            "The War Party has lost all confidence in your leadership. Conrad von Hotzendorf "
            "has gone directly to the Emperor, demanding your removal. The military establishment "
            "refuses to follow your orders. You are dismissed in disgrace."
        )
    if state["faction_moderates"]["loyalty"] < 30:
        return (
            "DEFEAT — INTERNAL COLLAPSE (Moderates)\n"
            "Count Tisza and the Hungarian delegation have withdrawn their support. "
            "Without Hungary, the Dual Monarchy cannot function. The Emperor is forced "
            "to dismiss you to prevent the constitutional crisis from deepening."
        )
    return None


def check_win_conditions(state: dict) -> str | None:
    """Check win conditions at end of game (turn 5 complete). Returns description or None."""
    if state["turn"] > 5:
        s = state["serbia_compliance"]
        r = state["russia_mobilization_threat"]
        hawks = state["faction_hawks"]["loyalty"]
        moderates = state["faction_moderates"]["loyalty"]

        if s >= 70 and r < 50 and hawks >= 50 and moderates >= 50:
            return (
                "BEST OUTCOME — DIPLOMATIC TRIUMPH\n"
                "Serbia has substantially capitulated to your demands. Russia, finding no "
                "pretext for intervention, stands down. Both the hawks and moderates are "
                "satisfied with your leadership. The Dual Monarchy emerges stronger.\n"
                "History will remember this as Austria-Hungary's finest diplomatic hour."
            )
        if r < 50 and hawks >= 40 and moderates >= 40:
            return (
                "GOOD OUTCOME — PEACE PRESERVED\n"
                "The crisis has been resolved without a general European war. Not everyone "
                "is fully satisfied — some grumble that you were too soft, others that you "
                "were too reckless — but the Monarchy endures and the continent breathes.\n"
                "Perhaps this peace will hold. Perhaps not."
            )
        if s >= 50 and r < 80:
            return (
                "ACCEPTABLE OUTCOME — LOCALIZED CONFLICT\n"
                "Serbia has been sufficiently humbled, and while tensions with Russia remain "
                "high, a general war has been averted — for now. Austria-Hungary's prestige "
                "is intact, though the underlying tensions in Europe remain unresolved.\n"
                "The powder keg still has its fuse."
            )
        return (
            "MIXED OUTCOME — UNEASY STALEMATE\n"
            "The crisis has passed its acute phase, but nothing is truly resolved. Serbia "
            "remains defiant, Russia is suspicious, and your own government is fractured. "
            "You have avoided catastrophe, but the Monarchy's position has weakened.\n"
            "The next crisis may not end so ambiguously."
        )
    return None


def format_status_bar(state: dict) -> str:
    """Format a compact status bar for display."""
    return (
        f"{'=' * 60}\n"
        f" Turn {state['turn']}/5 | {state['date']}\n"
        f" Hawks: {state['faction_hawks']['loyalty']}  "
        f"Moderates: {state['faction_moderates']['loyalty']}  "
        f"Serbia: {state['serbia_compliance']}  "
        f"Russia: {state['russia_mobilization_threat']}  "
        f"Germany: {state['germany_support']}\n"
        f"{'=' * 60}"
    )


def format_full_status(state: dict) -> str:
    """Format detailed status display."""
    return (
        f"\n{'=' * 60}\n"
        f"  JULY CRISIS 1914 — Turn {state['turn']}/5 — {state['date']}\n"
        f"{'=' * 60}\n"
        f"  INTERNAL FACTIONS:\n"
        f"    Hawks (War Party):     loyalty {state['faction_hawks']['loyalty']}/100\n"
        f"      Demand: {state['faction_hawks']['demand']}\n"
        f"    Moderates (Peace):     loyalty {state['faction_moderates']['loyalty']}/100\n"
        f"      Demand: {state['faction_moderates']['demand']}\n"
        f"  EXTERNAL SITUATION:\n"
        f"    Serbia compliance:     {state['serbia_compliance']}/100\n"
        f"    Russia mobilization:   {state['russia_mobilization_threat']}/100"
        f"{'  *** DANGER ***' if state['russia_mobilization_threat'] >= 60 else ''}\n"
        f"    Germany support:       {state['germany_support']}/100\n"
        f"  API USAGE:\n"
        f"    Calls: {state['api_usage']['total_calls']}  "
        f"Tokens: {state['api_usage']['total_tokens']}  "
        f"Est. cost: ${state['api_usage']['estimated_cost_usd']:.4f}\n"
        f"{'=' * 60}\n"
    )
