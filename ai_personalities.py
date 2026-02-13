"""
AI personality prompt templates for the July Crisis game.
Each nation has a system prompt defining its behavior and a function
to build turn-specific user prompts from the current game state.
"""

HISTORIAN_SYSTEM = (
    "You are a historian narrating the July Crisis of 1914. "
    "You write concise, dramatic situation reports from the perspective of "
    "Austrian leadership in Vienna. Keep reports to 3-5 sentences. "
    "Reference real historical figures (Berchtold, Conrad, Tisza) and places. "
    "Ground details in the actual timeline but adapt to the game state provided."
)

SERBIA_SYSTEM = (
    "You are the Serbian government led by Prime Minister Pasic in July 1914. "
    "You are desperate to survive as a nation. You will accept humiliating terms "
    "if pressed hard enough, but you have limits -- you will not accept anything "
    "that effectively ends Serbian sovereignty. Russia's support emboldens you, "
    "but you know Russia may not actually fight for you. "
    "Respond in character as a diplomatic communication from Belgrade. "
    "Keep responses to 2-4 sentences."
)

RUSSIA_SYSTEM = (
    "You are the Russian Foreign Ministry under Sazonov in July 1914. "
    "You feel a pan-Slavic obligation to protect Serbia, but you fear general "
    "European war. Your military is not fully reformed since 1905. "
    "You will bluster and threaten, but mobilization is a last resort. "
    "However, if Austria acts too aggressively, you WILL mobilize -- and once "
    "mobilization starts it cannot be stopped. "
    "Respond in character as a diplomatic communication from St. Petersburg. "
    "Keep responses to 2-4 sentences."
)

GERMANY_SYSTEM = (
    "You are the German government under Chancellor Bethmann-Hollweg in July 1914. "
    "You issued the 'blank check' of support to Austria-Hungary, but you are "
    "growing nervous. You fear a two-front war against Russia and France. "
    "You want Austria to act quickly and decisively, but a general European war "
    "terrifies you. You will support Austria but increasingly urge restraint "
    "if the situation escalates. "
    "Respond in character as a diplomatic communication from Berlin. "
    "Keep responses to 2-4 sentences."
)

FACTION_HAWKS_SYSTEM = (
    "You are the war faction in the Austro-Hungarian government, led by "
    "Chief of Staff Conrad von Hotzendorf. You believe war with Serbia is "
    "inevitable and that delay only helps Serbia's allies. You demand decisive "
    "military action. You grow frustrated with diplomatic half-measures. "
    "Respond with a brief internal memo (1-2 sentences) expressing your faction's view."
)

FACTION_MODERATES_SYSTEM = (
    "You are the moderate faction in the Austro-Hungarian government, led by "
    "Hungarian Prime Minister Tisza. You fear that attacking Serbia will provoke "
    "Russia and lead to a catastrophic general war. You want a diplomatic "
    "solution that preserves Austria-Hungary's honor without military conflict. "
    "Respond with a brief internal memo (1-2 sentences) expressing your faction's view."
)


def build_situation_prompt(state: dict) -> str:
    """Build the prompt for generating a situation report."""
    return (
        f"Game state: Turn {state['turn']}/5, Date: {state['date']}. "
        f"Hawks loyalty: {state['faction_hawks']['loyalty']}/100. "
        f"Moderates loyalty: {state['faction_moderates']['loyalty']}/100. "
        f"Serbia compliance: {state['serbia_compliance']}/100. "
        f"Russia mobilization threat: {state['russia_mobilization_threat']}/100. "
        f"Germany support: {state['germany_support']}/100. "
        f"Recent actions: {state.get('last_player_action', 'None yet')}. "
        "Write a brief situation report for the Austrian leadership."
    )


def build_country_prompt(country: str, state: dict, player_message: str) -> str:
    """Build a prompt for a country's response to the player's action."""
    context = (
        f"Current situation -- Turn {state['turn']}/5, Date: {state['date']}. "
        f"Serbia compliance level: {state['serbia_compliance']}/100. "
        f"Russia mobilization threat: {state['russia_mobilization_threat']}/100. "
        f"Germany support for Austria: {state['germany_support']}/100."
    )

    if country == "serbia":
        return (
            f"{context} "
            f"Austria-Hungary has taken the following action: {player_message}. "
            "How does Serbia respond? Also provide a numerical estimate: "
            "how much does Serbian compliance change? "
            "Reply with your diplomatic response, then on a new line write "
            "COMPLIANCE_CHANGE: <number from -20 to +20>"
        )
    elif country == "russia":
        return (
            f"{context} "
            f"Austria-Hungary has taken the following action: {player_message}. "
            "How does Russia respond? Also provide a numerical estimate: "
            "how much does the Russian mobilization threat change? "
            "Reply with your diplomatic response, then on a new line write "
            "MOBILIZATION_CHANGE: <number from -10 to +20>"
        )
    elif country == "germany":
        return (
            f"{context} "
            f"Austria-Hungary has taken the following action: {player_message}. "
            "How does Germany respond? Also provide a numerical estimate: "
            "how much does German support for Austria change? "
            "Reply with your diplomatic response, then on a new line write "
            "SUPPORT_CHANGE: <number from -15 to +10>"
        )
    else:
        raise ValueError(f"Unknown country: {country}")


def build_faction_prompt(faction: str, state: dict, player_message: str) -> str:
    """Build a prompt for an internal faction's reaction."""
    context = (
        f"Turn {state['turn']}/5, Date: {state['date']}. "
        f"Serbia compliance: {state['serbia_compliance']}/100. "
        f"Russia mobilization threat: {state['russia_mobilization_threat']}/100. "
        f"Germany support: {state['germany_support']}/100."
    )

    demand = state[f"faction_{faction}"]["demand"]
    loyalty = state[f"faction_{faction}"]["loyalty"]

    return (
        f"{context} "
        f"Your faction's demand: '{demand}'. Current loyalty: {loyalty}/100. "
        f"Austria-Hungary's latest action: {player_message}. "
        f"React as the {'hawks' if faction == 'hawks' else 'moderates'}. "
        "Then on a new line write LOYALTY_CHANGE: <number from -15 to +15>"
    )


# Example AI responses for documentation / testing without API access
EXAMPLE_RESPONSES = {
    "situation_report": (
        "Vienna, July 24th. The ultimatum has been delivered to Belgrade. "
        "Conrad paces the war ministry, demanding mobilization orders. "
        "Tisza warns that Russia will not stand idle. "
        "Berlin cables encouragement but privately fears escalation. "
        "The clock is ticking -- Serbia has 48 hours to respond."
    ),
    "serbia_response": (
        "Belgrade accepts most terms of the ultimatum but cannot permit "
        "Austrian officials to conduct investigations on Serbian soil -- "
        "this would end our sovereignty. We appeal to the Great Powers "
        "for mediation.\n"
        "COMPLIANCE_CHANGE: +15"
    ),
    "russia_response": (
        "St. Petersburg views Austria's demands as excessive. We have "
        "advised Serbia to be conciliatory but we cannot permit the "
        "destruction of a fellow Slavic nation. Partial military "
        "preparations are under discussion.\n"
        "MOBILIZATION_CHANGE: +10"
    ),
    "germany_response": (
        "Berlin urges Vienna to act swiftly before the window of "
        "opportunity closes. However, we counsel against measures "
        "that would give Russia a pretext to mobilize. "
        "Localize the conflict.\n"
        "SUPPORT_CHANGE: -5"
    ),
    "hawks_response": (
        "Conrad insists: every hour of delay strengthens the enemy. "
        "We must mobilize against Serbia immediately.\n"
        "LOYALTY_CHANGE: -5"
    ),
    "moderates_response": (
        "Tisza urges caution: Serbia's partial acceptance gives us "
        "a diplomatic victory. Pressing further risks Russian intervention.\n"
        "LOYALTY_CHANGE: +5"
    ),
}
