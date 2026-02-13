"""
Game state management for the July Crisis game.
Handles initialization, persistence, updates, and win/lose checks.
"""

import json
import os
from pathlib import Path

SAVE_FILE = Path(__file__).parent / "savegame.json"

DATES = {
    1: "July 23, 1914",
    2: "July 24, 1914",
    3: "July 25, 1914",
    4: "July 27, 1914",
    5: "July 28, 1914",
}


def new_game() -> dict:
    """Create a fresh game state."""
    return {
        "turn": 1,
        "date": DATES[1],
        "faction_hawks": {
            "loyalty": 60,
            "demand": "Crush Serbia",
        },
        "faction_moderates": {
            "loyalty": 50,
            "demand": "Avoid general war",
        },
        "serbia_compliance": 0,
        "russia_mobilization_threat": 20,
        "germany_support": 70,
        "player_messages": [],
        "last_player_action": None,
        "api_usage": {
            "total_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_cost_usd": 0.0,
            "api_calls": 0,
        },
    }


def save_game(state: dict) -> None:
    """Save game state to JSON file."""
    with open(SAVE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def load_game() -> dict | None:
    """Load game state from JSON file, or return None if no save exists."""
    if not SAVE_FILE.exists():
        return None
    with open(SAVE_FILE) as f:
        return json.load(f)


def delete_save() -> None:
    """Remove the save file."""
    if SAVE_FILE.exists():
        os.remove(SAVE_FILE)


def advance_turn(state: dict) -> dict:
    """Advance to the next turn."""
    state["turn"] += 1
    if state["turn"] <= 5:
        state["date"] = DATES[state["turn"]]
    return state


def clamp(value: int, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, value))


def apply_state_changes(
    state: dict,
    compliance_delta: int = 0,
    mobilization_delta: int = 0,
    support_delta: int = 0,
    hawks_loyalty_delta: int = 0,
    moderates_loyalty_delta: int = 0,
) -> dict:
    """Apply numeric deltas to the game state, clamping to 0-100."""
    state["serbia_compliance"] = clamp(
        state["serbia_compliance"] + compliance_delta
    )
    state["russia_mobilization_threat"] = clamp(
        state["russia_mobilization_threat"] + mobilization_delta
    )
    state["germany_support"] = clamp(
        state["germany_support"] + support_delta
    )
    state["faction_hawks"]["loyalty"] = clamp(
        state["faction_hawks"]["loyalty"] + hawks_loyalty_delta
    )
    state["faction_moderates"]["loyalty"] = clamp(
        state["faction_moderates"]["loyalty"] + moderates_loyalty_delta
    )
    return state


def track_api_usage(state: dict, usage: dict) -> dict:
    """Accumulate API token/cost tracking."""
    u = state["api_usage"]
    u["prompt_tokens"] += usage.get("prompt_tokens", 0)
    u["completion_tokens"] += usage.get("completion_tokens", 0)
    u["total_tokens"] += usage.get("total_tokens", 0)
    u["api_calls"] += 1
    # DeepSeek V3 via OpenRouter: ~$0.27/M input, ~$1.10/M output
    prompt_cost = usage.get("prompt_tokens", 0) * 0.27 / 1_000_000
    completion_cost = usage.get("completion_tokens", 0) * 1.10 / 1_000_000
    u["total_cost_usd"] += prompt_cost + completion_cost
    return state


class GameOutcome:
    PLAYING = "playing"
    # Win outcomes
    BEST_WIN = "best_win"
    GOOD_WIN = "good_win"
    ACCEPTABLE_WIN = "acceptable_win"
    # Lose outcomes
    RUSSIA_MOBILIZES = "russia_mobilizes"
    FACTION_COLLAPSE = "faction_collapse"


def check_outcome(state: dict) -> tuple[str, str]:
    """
    Check win/lose conditions. Returns (outcome, description).
    Only triggers at end of turn or on threshold breach.
    """
    # Lose: Russia mobilization
    if state["russia_mobilization_threat"] >= 80:
        return (
            GameOutcome.RUSSIA_MOBILIZES,
            "DEFEAT -- Russia has ordered general mobilization. "
            "The alliance system activates. France mobilizes in support of Russia. "
            "Germany invokes the Schlieffen Plan. General European war is now inevitable. "
            "The July Crisis has become the Great War.",
        )

    # Lose: Faction collapse
    if state["faction_hawks"]["loyalty"] < 30:
        return (
            GameOutcome.FACTION_COLLAPSE,
            "DEFEAT -- The war party has lost confidence in your leadership. "
            "Conrad and the military establishment move to sideline you. "
            "Austria-Hungary descends into internal political crisis, "
            "paralyzed at the worst possible moment.",
        )
    if state["faction_moderates"]["loyalty"] < 30:
        return (
            GameOutcome.FACTION_COLLAPSE,
            "DEFEAT -- The moderates have broken with you. "
            "Tisza withdraws Hungarian support, threatening the Dual Monarchy's unity. "
            "Without Hungarian cooperation, Austria-Hungary cannot act coherently. "
            "The Empire's internal contradictions consume it.",
        )

    # Win checks only on turn 5 completion
    if state["turn"] > 5:
        hawks_ok = state["faction_hawks"]["loyalty"] >= 50
        moderates_ok = state["faction_moderates"]["loyalty"] >= 50
        low_mob = state["russia_mobilization_threat"] < 40
        high_compliance = state["serbia_compliance"] >= 60

        if high_compliance and hawks_ok and moderates_ok and low_mob:
            return (
                GameOutcome.BEST_WIN,
                "TRIUMPH -- Serbia capitulates to your demands. Russia backs down. "
                "Both factions in Vienna are satisfied. You have achieved the impossible: "
                "a complete diplomatic victory that averts general war while preserving "
                "Austria-Hungary's prestige. History will remember your statesmanship.",
            )
        elif high_compliance and low_mob:
            return (
                GameOutcome.GOOD_WIN,
                "VICTORY -- The crisis is resolved peacefully. Serbia has largely complied, "
                "and Russia has not mobilized. However, not all factions in Vienna are "
                "satisfied. Political tensions simmer, but war has been averted. "
                "A respectable outcome for the Dual Monarchy.",
            )
        elif state["russia_mobilization_threat"] < 60:
            return (
                GameOutcome.ACCEPTABLE_WIN,
                "PYRRHIC VICTORY -- War with Serbia is localized. Russia protests but "
                "does not mobilize fully. The conflict remains contained to the Balkans. "
                "Austria-Hungary pays a heavy price but avoids the nightmare of general "
                "European war. History may judge this the least bad option.",
            )
        else:
            return (
                GameOutcome.RUSSIA_MOBILIZES,
                "DEFEAT -- Despite your efforts, the crisis has spiraled. "
                "Russia's mobilization threat is too high. The Great Powers slide "
                "toward war as diplomacy fails. The old world dies in August 1914.",
            )

    return (GameOutcome.PLAYING, "")


def format_status_bar(state: dict) -> str:
    """Format a compact status bar for display each turn."""
    lines = [
        f"{'=' * 60}",
        f"  TURN {state['turn']}/5  |  {state['date']}",
        f"{'=' * 60}",
        f"  Hawks loyalty:    {_bar(state['faction_hawks']['loyalty'])} "
        f"{state['faction_hawks']['loyalty']}%",
        f"  Moderates loyalty:{_bar(state['faction_moderates']['loyalty'])} "
        f"{state['faction_moderates']['loyalty']}%",
        f"  Serbia compliance:{_bar(state['serbia_compliance'])} "
        f"{state['serbia_compliance']}%",
        f"  Russia mob threat:{_bar(state['russia_mobilization_threat'])} "
        f"{state['russia_mobilization_threat']}%",
        f"  Germany support:  {_bar(state['germany_support'])} "
        f"{state['germany_support']}%",
        f"{'=' * 60}",
    ]
    return "\n".join(lines)


def _bar(value: int, width: int = 20) -> str:
    """Render a simple ASCII progress bar."""
    filled = round(value / 100 * width)
    return "[" + "#" * filled + "." * (width - filled) + "]"
