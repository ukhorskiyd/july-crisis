#!/usr/bin/env python3
"""
The July Crisis -- A Historical Strategy Game
Player controls Austria-Hungary during July 23-28, 1914.
"""

import json
import re
import sys
import time
from pathlib import Path

import ai_personalities as ai
import game_state as gs

CONFIG_PATH = Path(__file__).parent / "config.json"


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return json.load(f)


def call_api(config: dict, system_prompt: str, user_prompt: str, state: dict) -> str:
    """Call the OpenRouter API with the given prompts. Returns the response text."""
    import urllib.request
    import urllib.error

    payload = {
        "model": config["model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": config.get("max_tokens", 500),
        "temperature": config.get("temperature", 0.8),
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config['api_key']}",
        "HTTP-Referer": "https://github.com/july-crisis-game",
        "X-Title": "July Crisis Game",
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(config["api_url"], data=data, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"\n  [API Error {e.code}]: {body}")
        return ""
    except urllib.error.URLError as e:
        print(f"\n  [Network Error]: {e.reason}")
        return ""

    # Track usage
    usage = result.get("usage", {})
    gs.track_api_usage(state, usage)

    choices = result.get("choices", [])
    if choices:
        return choices[0].get("message", {}).get("content", "")
    return ""


def parse_numeric_tag(text: str, tag: str) -> int:
    """Extract a numeric value from a tagged line like 'TAG: 5'."""
    pattern = rf"{tag}:\s*([+-]?\d+)"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 0


def strip_tag_lines(text: str) -> str:
    """Remove lines containing state-change tags from display text."""
    tags = [
        "COMPLIANCE_CHANGE",
        "MOBILIZATION_CHANGE",
        "SUPPORT_CHANGE",
        "LOYALTY_CHANGE",
    ]
    lines = text.split("\n")
    return "\n".join(
        line for line in lines if not any(tag in line.upper() for tag in tags)
    ).strip()


def print_slow(text: str, delay: float = 0.01) -> None:
    """Print text character by character for dramatic effect."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def print_section(header: str, text: str) -> None:
    """Print a labeled section."""
    print(f"\n  --- {header} ---")
    for line in text.split("\n"):
        print(f"  {line}")
    print()


def get_player_action() -> str:
    """Prompt the player for their action."""
    print("  What is your action? Options include:")
    print("    - Send diplomatic messages to Serbia, Russia, or Germany")
    print("    - Issue ultimatum demands")
    print("    - Order military preparations")
    print("    - Propose mediation or compromise")
    print("    - Address internal factions")
    print()
    print("  Describe your action (or 'quit' to save and exit):")
    print()

    lines = []
    while True:
        try:
            line = input("  > ")
        except (EOFError, KeyboardInterrupt):
            print()
            return "quit"
        if line.strip().lower() == "quit":
            return "quit"
        if line.strip() == "" and lines:
            break
        lines.append(line)

    return " ".join(lines).strip()


def run_ai_turn(config: dict, state: dict, player_action: str) -> dict:
    """Run all AI responses for a single turn and apply state changes."""

    # 1. Get country responses
    print("\n  Dispatches arriving from foreign capitals...\n")

    # Serbia
    serbia_text = call_api(
        config,
        ai.SERBIA_SYSTEM,
        ai.build_country_prompt("serbia", state, player_action),
        state,
    )
    if serbia_text:
        compliance_delta = parse_numeric_tag(serbia_text, "COMPLIANCE_CHANGE")
        print_section("DISPATCH FROM BELGRADE", strip_tag_lines(serbia_text))
    else:
        compliance_delta = 0
        print_section("DISPATCH FROM BELGRADE", "[No response received]")

    # Russia
    russia_text = call_api(
        config,
        ai.RUSSIA_SYSTEM,
        ai.build_country_prompt("russia", state, player_action),
        state,
    )
    if russia_text:
        mobilization_delta = parse_numeric_tag(russia_text, "MOBILIZATION_CHANGE")
        print_section("DISPATCH FROM ST. PETERSBURG", strip_tag_lines(russia_text))
    else:
        mobilization_delta = 0
        print_section("DISPATCH FROM ST. PETERSBURG", "[No response received]")

    # Germany
    germany_text = call_api(
        config,
        ai.GERMANY_SYSTEM,
        ai.build_country_prompt("germany", state, player_action),
        state,
    )
    if germany_text:
        support_delta = parse_numeric_tag(germany_text, "SUPPORT_CHANGE")
        print_section("DISPATCH FROM BERLIN", strip_tag_lines(germany_text))
    else:
        support_delta = 0
        print_section("DISPATCH FROM BERLIN", "[No response received]")

    # 2. Get faction reactions
    print("  Internal council reactions...\n")

    hawks_text = call_api(
        config,
        ai.FACTION_HAWKS_SYSTEM,
        ai.build_faction_prompt("hawks", state, player_action),
        state,
    )
    if hawks_text:
        hawks_delta = parse_numeric_tag(hawks_text, "LOYALTY_CHANGE")
        print_section("HAWKS (Conrad)", strip_tag_lines(hawks_text))
    else:
        hawks_delta = 0
        print_section("HAWKS (Conrad)", "[No response received]")

    moderates_text = call_api(
        config,
        ai.FACTION_MODERATES_SYSTEM,
        ai.build_faction_prompt("moderates", state, player_action),
        state,
    )
    if moderates_text:
        moderates_delta = parse_numeric_tag(moderates_text, "LOYALTY_CHANGE")
        print_section("MODERATES (Tisza)", strip_tag_lines(moderates_text))
    else:
        moderates_delta = 0
        print_section("MODERATES (Tisza)", "[No response received]")

    # 3. Apply all changes
    state = gs.apply_state_changes(
        state,
        compliance_delta=compliance_delta,
        mobilization_delta=mobilization_delta,
        support_delta=support_delta,
        hawks_loyalty_delta=hawks_delta,
        moderates_loyalty_delta=moderates_delta,
    )

    return state


def show_intro() -> None:
    """Display game introduction."""
    intro = """
    ============================================================
          THE JULY CRISIS
          A Historical Strategy Game
    ============================================================

    Vienna, July 1914.

    Archduke Franz Ferdinand is dead, assassinated in Sarajevo
    by a Bosnian Serb nationalist. The Dual Monarchy demands
    justice. But the path forward is perilous.

    You are the decision-maker for Austria-Hungary. Over five
    critical days, you must navigate between:

      - The HAWKS (Conrad, the military) who demand war
      - The MODERATES (Tisza, Hungary) who fear catastrophe
      - SERBIA, which may or may not comply with your demands
      - RUSSIA, Serbia's protector, whose mobilization means
        general European war
      - GERMANY, your ally, whose support is not unconditional

    Your goal: resolve the crisis in Austria-Hungary's favor
    without triggering a general European war or losing control
    of your own government.

    History did not manage this. Can you?

    ============================================================
    """
    print(intro)


def show_end_summary(state: dict) -> None:
    """Display end-of-game summary including API usage."""
    u = state["api_usage"]
    print(f"\n  --- API Usage Summary ---")
    print(f"  Total API calls:       {u['api_calls']}")
    print(f"  Total tokens:          {u['total_tokens']}")
    print(f"    Prompt tokens:       {u['prompt_tokens']}")
    print(f"    Completion tokens:   {u['completion_tokens']}")
    print(f"  Estimated cost:        ${u['total_cost_usd']:.4f}")
    print()


def main() -> None:
    config = load_config()

    if config["api_key"] == "YOUR_OPENROUTER_API_KEY_HERE":
        print("\n  ERROR: Please set your OpenRouter API key in config.json")
        print("  Get one at: https://openrouter.ai/keys\n")
        sys.exit(1)

    # Check for existing save
    existing = gs.load_game()
    if existing and existing["turn"] <= 5:
        print("\n  Found existing save game.")
        choice = input("  Continue? (y/n): ").strip().lower()
        if choice == "y":
            state = existing
        else:
            gs.delete_save()
            state = gs.new_game()
    else:
        gs.delete_save()
        state = gs.new_game()

    if state["turn"] == 1 and state["last_player_action"] is None:
        show_intro()
        input("  Press Enter to begin...")

    # Main game loop
    while state["turn"] <= 5:
        # Display status
        print()
        print(gs.format_status_bar(state))

        # Generate situation report
        print("\n  Generating situation report...\n")
        sitrep = call_api(
            config,
            ai.HISTORIAN_SYSTEM,
            ai.build_situation_prompt(state),
            state,
        )
        if sitrep:
            print_section("SITUATION REPORT", sitrep)
        else:
            print_section("SITUATION REPORT", "[Unable to generate report]")

        # Get player action
        player_action = get_player_action()
        if player_action == "quit":
            gs.save_game(state)
            print("\n  Game saved. Goodbye.\n")
            return

        if not player_action:
            print("  Please enter an action.")
            continue

        # Record action
        state["last_player_action"] = player_action
        state["player_messages"].append(
            {"turn": state["turn"], "action": player_action}
        )

        # Run AI turn
        state = run_ai_turn(config, state, player_action)

        # Check lose conditions (can trigger mid-game)
        outcome, description = gs.check_outcome(state)
        if outcome != gs.GameOutcome.PLAYING:
            print()
            print(gs.format_status_bar(state))
            print()
            print_slow(f"  {description}")
            show_end_summary(state)
            gs.delete_save()
            return

        # Advance turn
        state = gs.advance_turn(state)
        gs.save_game(state)

    # Game complete -- check final outcome
    outcome, description = gs.check_outcome(state)
    print()
    print(gs.format_status_bar(state))
    print()
    print_slow(f"  {description}")
    show_end_summary(state)
    gs.delete_save()


if __name__ == "__main__":
    main()
