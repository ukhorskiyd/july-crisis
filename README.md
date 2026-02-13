# July Crisis 1914 — A Historical Strategy Game

A CLI strategy game where you control Austria-Hungary during the July Crisis of 1914. Navigate 5 turns (July 23–28) balancing internal factions and external diplomacy, with AI-driven responses from Serbia, Russia, and Germany powered by DeepSeek V3 via OpenRouter.

## Setup

### Requirements

- Python 3.10+
- `requests` library

### Install

```bash
pip install requests
```

### API Key

1. Get an API key from [OpenRouter](https://openrouter.ai/)
2. Edit `config.json` and replace `YOUR_OPENROUTER_API_KEY_HERE` with your key

```json
{
    "openrouter_api_key": "sk-or-v1-your-key-here",
    "model": "deepseek/deepseek-chat-v3",
    "api_url": "https://openrouter.ai/api/v1/chat/completions",
    "max_tokens": 512,
    "temperature": 0.8
}
```

The game works without an API key in offline mode using example responses.

## Play

```bash
python game.py
```

Type your diplomatic action each turn, then press Enter on a blank line to submit. Type `quit` to save and exit.

## How It Works

### Turn Structure

Each of the 5 turns:

1. **Situation Report** — AI-generated briefing on the current state of the crisis
2. **Your Decision** — Write a diplomatic action, military order, or message
3. **Country Responses** — Serbia, Russia, and Germany react via AI
4. **Faction Reactions** — Hawks and Moderates within Austria-Hungary shift loyalty
5. **State Update** — All changes applied, win/lose conditions checked

### Game State

| Metric | Range | Meaning |
|---|---|---|
| Hawks loyalty | 0–100 | War Party confidence in your leadership |
| Moderates loyalty | 0–100 | Peace Party confidence in your leadership |
| Serbia compliance | 0–100 | How much Serbia yields to your demands |
| Russia mobilization | 0–100 | How close Russia is to general mobilization |
| Germany support | 0–100 | Berlin's willingness to back your actions |

### Win Conditions

- **Best**: Serbia compliance >= 70, Russia < 50, both factions >= 50
- **Good**: Russia < 50, both factions >= 40
- **Acceptable**: Serbia >= 50, Russia < 80

### Lose Conditions

- Russia mobilization >= 80 (general war)
- Any faction loyalty < 30 (internal collapse)

## Example Actions

Strong hawk-leaning actions:
- "Order partial mobilization along the Serbian border as a show of force"
- "Demand Serbia accept all ultimatum terms without modification within 24 hours"

Moderate/diplomatic actions:
- "Send a private back-channel message to Sazonov proposing a great-power conference"
- "Instruct our ambassador to extend the deadline and signal willingness to negotiate on points 5 and 6"

Balanced actions:
- "Publicly insist on the ultimatum terms while privately telling Berlin we would accept Serbian compliance on 8 of 10 points"
- "Leak to the press that Austria is mobilizing, while secretly telling Russia this is defensive only"

## Files

| File | Purpose |
|---|---|
| `game.py` | Main game loop and CLI interface |
| `game_state.py` | State management, persistence, win/lose checks |
| `ai_personalities.py` | DeepSeek prompt templates for each country/narrator |
| `config.json` | API configuration (add your key here) |

## Cost

DeepSeek V3 via OpenRouter is very inexpensive. A full 5-turn game typically uses ~25 API calls and costs under $0.01.
