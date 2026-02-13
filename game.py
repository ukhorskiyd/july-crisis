#!/usr/bin/env python3
"""
July Crisis 1914 — A Historical Strategy Game
Player controls Austria-Hungary during the July Crisis (5 turns, July 23-28).
AI plays Serbia, Russia, and Germany via DeepSeek V3 on OpenRouter.
"""

import sys
import time

import requests

import ai_personalities as ai
import game_state as gs

API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-chat-v3"
MAX_TOKENS = 512
TEMPERATURE = 0.8

# DeepSeek V3 pricing (per million tokens, via OpenRouter)
COST_PER_M_INPUT = 0.5
COST_PER_M_OUTPUT = 1.0


def call_ai(api_key: str, system_prompt: str, user_prompt: str,
            state: dict) -> str:
    """Call DeepSeek V3 via OpenRouter and return the response text."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
    }

    try:
        resp = requests.post(
            API_URL, headers=headers, json=payload, timeout=30
        )
        resp.raise_for_status()
        data = resp.json()

        # Track usage
        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total = prompt_tokens + completion_tokens
        cost = (prompt_tokens * COST_PER_M_INPUT + completion_tokens * COST_PER_M_OUTPUT) / 1_000_000

        state["api_usage"]["total_tokens"] += total
        state["api_usage"]["total_calls"] += 1
        state["api_usage"]["estimated_cost_usd"] += cost

        return data["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        print(f"\n  [API Error: {e}]")
        print("  Falling back to example responses.\n")
        return None


def print_slow(text: str, delay: float = 0.01) -> None:
    """Print text with a slight delay for dramatic effect."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def print_section(title: str, text: str) -> None:
    """Print a titled section."""
    print(f"\n  --- {title} ---")
    # Indent the text and strip any shift markers for display
    for line in text.strip().split("\n"):
        stripped = line.strip()
        # Hide the machine-readable shift lines from the player
        if any(stripped.startswith(tag) for tag in [
            "COMPLIANCE_SHIFT:", "MOBILIZATION_SHIFT:",
            "GERMANY_SUPPORT_SHIFT:", "HAWKS_SHIFT:", "MODERATES_SHIFT:"
        ]):
            continue
        print(f"  {line}")
    print()


def get_player_action() -> str:
    """Get the player's action for this turn."""
    print("  YOUR DECISION")
    print("  Write your diplomatic action, message, or order.")
    print("  Examples:")
    print("    - 'Demand Serbia accept all terms within 48 hours or face consequences'")
    print("    - 'Send a private message to Russia proposing a conference'")
    print("    - 'Order partial mobilization along the Serbian border'")
    print("    - 'Instruct ambassador to extend the deadline by 24 hours'")
    print()
    lines = []
    print("  > ", end="", flush=True)
    while True:
        line = input()
        if line.strip() == "":
            if lines:
                break
            print("  > ", end="", flush=True)
            continue
        lines.append(line)
        print("  > ", end="", flush=True)
    return " ".join(lines)


def play_turn(state: dict, api_key: str | None) -> dict:
    """Execute one full turn of the game."""
    offline = api_key is None

    # 1. Display status
    print(gs.format_full_status(state))

    # 2. Situation report
    sys_prompt, usr_prompt = ai.situation_report_prompt(state)
    if offline:
        sitrep = ai.EXAMPLE_RESPONSES["situation_report"]
    else:
        sitrep = call_ai(api_key, sys_prompt, usr_prompt, state)
        if sitrep is None:
            sitrep = ai.EXAMPLE_RESPONSES["situation_report"]
    print_section("SITUATION REPORT", sitrep)

    # 3. Check for lose conditions before player acts
    loss = gs.check_lose_conditions(state)
    if loss:
        return state  # Will be caught in main loop

    # 4. Get player action
    action = get_player_action()
    state["player_messages"].append(f"Turn {state['turn']}: {action}")

    print("\n  Dispatching orders... Awaiting responses from the capitals of Europe...\n")
    if not offline:
        time.sleep(1)

    # 5. Get AI responses from each country
    # Serbia
    sys_p, usr_p = ai.serbia_response_prompt(state, action)
    if offline:
        serbia_resp = ai.EXAMPLE_RESPONSES["serbia"]
    else:
        serbia_resp = call_ai(api_key, sys_p, usr_p, state)
        if serbia_resp is None:
            serbia_resp = ai.EXAMPLE_RESPONSES["serbia"]
    print_section("SERBIA (Nikola Pasic)", serbia_resp)

    # Russia
    sys_p, usr_p = ai.russia_response_prompt(state, action)
    if offline:
        russia_resp = ai.EXAMPLE_RESPONSES["russia"]
    else:
        russia_resp = call_ai(api_key, sys_p, usr_p, state)
        if russia_resp is None:
            russia_resp = ai.EXAMPLE_RESPONSES["russia"]
    print_section("RUSSIA (Sergei Sazonov)", russia_resp)

    # Germany
    sys_p, usr_p = ai.germany_response_prompt(state, action)
    if offline:
        germany_resp = ai.EXAMPLE_RESPONSES["germany"]
    else:
        germany_resp = call_ai(api_key, sys_p, usr_p, state)
        if germany_resp is None:
            germany_resp = ai.EXAMPLE_RESPONSES["germany"]
    print_section("GERMANY (Bethmann-Hollweg)", germany_resp)

    # Internal factions
    sys_p, usr_p = ai.faction_update_prompt(state, action)
    if offline:
        faction_resp = ai.EXAMPLE_RESPONSES["factions"]
    else:
        faction_resp = call_ai(api_key, sys_p, usr_p, state)
        if faction_resp is None:
            faction_resp = ai.EXAMPLE_RESPONSES["factions"]
    print_section("INTERNAL FACTIONS", faction_resp)

    # 6. Apply state changes
    state = gs.apply_shifts(state, serbia_resp, russia_resp, germany_resp, faction_resp)

    # 7. Advance turn
    state = gs.advance_turn(state)

    # 8. Save
    gs.save_game(state)

    return state


def main() -> None:
    """Main game loop."""
    print("\n")
    print_slow("  ╔══════════════════════════════════════════════════════════╗")
    print_slow("  ║           JULY CRISIS 1914                              ║")
    print_slow("  ║           A Historical Strategy Game                    ║")
    print_slow("  ╠══════════════════════════════════════════════════════════╣")
    print_slow("  ║  You are the decision-maker for Austria-Hungary.        ║")
    print_slow("  ║  Navigate the July Crisis in 5 turns (July 23-28).      ║")
    print_slow("  ║                                                         ║")
    print_slow("  ║  Balance hawks and moderates at home.                   ║")
    print_slow("  ║  Manage Serbia, Russia, and Germany abroad.             ║")
    print_slow("  ║  Avoid general war — or win one.                        ║")
    print_slow("  ╚══════════════════════════════════════════════════════════╝")
    print()

    # Prompt for API key
    print("  Enter your OpenRouter API key (or press Enter for offline mode):")
    api_key_input = input("  > ").strip()
    if api_key_input:
        api_key = api_key_input
        print("  API key set. AI responses powered by DeepSeek V3.\n")
    else:
        api_key = None
        print("  Running in OFFLINE mode with example responses.\n")

    # Check for existing save
    existing = gs.load_game()
    if existing and existing["turn"] <= 5:
        print(f"  Found saved game at Turn {existing['turn']}.")
        choice = input("  Continue? (y/n): ").strip().lower()
        if choice == "y":
            state = existing
        else:
            gs.delete_save()
            state = gs.new_game()
    else:
        gs.delete_save()
        state = gs.new_game()

    print("\n  Press Enter after typing your action (blank line to submit).")
    print("  Type 'quit' to save and exit. Type 'status' for detailed view.\n")

    # Main game loop
    while state["turn"] <= 5:
        # Check lose before turn
        loss = gs.check_lose_conditions(state)
        if loss:
            print(gs.format_full_status(state))
            print(f"\n  {'*' * 50}")
            print_slow(f"  {loss}")
            print(f"  {'*' * 50}\n")
            gs.delete_save()
            break

        state = play_turn(state, api_key)

        # Check lose after turn
        loss = gs.check_lose_conditions(state)
        if loss:
            print(gs.format_full_status(state))
            print(f"\n  {'*' * 50}")
            print_slow(f"  {loss}")
            print(f"  {'*' * 50}\n")
            gs.delete_save()
            break
    else:
        # All 5 turns complete — check win conditions
        win = gs.check_win_conditions(state)
        if win:
            print(gs.format_full_status(state))
            print(f"\n  {'*' * 50}")
            print_slow(f"  {win}")
            print(f"  {'*' * 50}\n")
            gs.delete_save()

    # Final API usage summary
    print(f"\n  API Usage Summary:")
    print(f"    Total calls: {state['api_usage']['total_calls']}")
    print(f"    Total tokens: {state['api_usage']['total_tokens']}")
    print(f"    Estimated cost: ${state['api_usage']['estimated_cost_usd']:.4f}")
    print()


if __name__ == "__main__":
    main()
