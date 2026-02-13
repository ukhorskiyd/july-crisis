# The July Crisis -- A Historical Strategy Game

Control Austria-Hungary during the five critical days of July 23-28, 1914. Navigate between war hawks, cautious moderates, a defiant Serbia, a threatening Russia, and a nervous Germany. Can you resolve the crisis without triggering the Great War?

## Setup

1. **Python 3.10+** required (no external dependencies -- uses only stdlib).

2. **Get an OpenRouter API key** at [openrouter.ai/keys](https://openrouter.ai/keys).

3. **Configure** -- edit `config.json` and replace the placeholder:
   ```json
   {
       "api_key": "sk-or-v1-your-key-here",
       "model": "deepseek/deepseek-chat-v3",
       "api_url": "https://openrouter.ai/api/v1/chat/completions",
       "max_tokens": 500,
       "temperature": 0.8
   }
   ```

4. **Run**:
   ```bash
   python game.py
   ```

## How to Play

Each turn you see a status dashboard and situation report, then choose an action:

- Send diplomatic messages to Serbia, Russia, or Germany
- Issue ultimatum demands
- Order military preparations or stand down
- Propose mediation or compromise
- Address internal factions directly

Type your action as free text. Press Enter on an empty line to submit. Type `quit` to save and exit mid-game.

## Win/Lose Conditions

**Win:**
- **Best:** Serbia backs down, both factions satisfied, Russia stays calm
- **Good:** Crisis resolved peacefully, some faction unhappy
- **Acceptable:** Localized war with Serbia, no general European war

**Lose:**
- Russia mobilization threat reaches 80+ (general war)
- Any faction loyalty drops below 30 (internal collapse)

## Game State

The game tracks five key metrics (0-100 scale):

| Metric | Starts | Danger Zone |
|---|---|---|
| Hawks loyalty | 60 | Below 30 = defeat |
| Moderates loyalty | 50 | Below 30 = defeat |
| Serbia compliance | 0 | Higher is better |
| Russia mob. threat | 20 | 80+ = defeat |
| Germany support | 70 | Low = less leverage |

## Strategy Tips

- Aggressive moves please hawks but alarm moderates and Russia
- Conciliatory moves please moderates but frustrate hawks
- Germany's support erodes if the crisis escalates toward general war
- Serbia will comply under enough pressure, but Russia reacts to that pressure too
- There is no perfect move -- every action has trade-offs

## Files

| File | Purpose |
|---|---|
| `game.py` | Main game loop and CLI interface |
| `game_state.py` | State management, persistence, win/lose checks |
| `ai_personalities.py` | DeepSeek prompt templates and example responses |
| `config.json` | API configuration |
| `savegame.json` | Auto-generated save file (created at runtime) |

## Cost

Uses DeepSeek V3 via OpenRouter (~$0.27/M input tokens, ~$1.10/M output tokens). A full 5-turn game typically costs less than $0.01. Token usage is displayed at game end.

## Example Gameplay

```
> Deliver the ultimatum to Serbia with a 48-hour deadline. Demand full
  compliance with all points including Austrian participation in the
  investigation. Privately reassure Germany this is meant to be rejected.

  --- DISPATCH FROM BELGRADE ---
  Belgrade accepts most terms of the ultimatum but cannot permit
  Austrian officials to conduct investigations on Serbian soil --
  this would end our sovereignty. We appeal to the Great Powers
  for mediation.

  --- DISPATCH FROM ST. PETERSBURG ---
  St. Petersburg views Austria's demands as excessive. We have
  advised Serbia to be conciliatory but we cannot permit the
  destruction of a fellow Slavic nation. Partial military
  preparations are under discussion.

  --- DISPATCH FROM BERLIN ---
  Berlin urges Vienna to act swiftly before the window of
  opportunity closes. However, we counsel against measures
  that would give Russia a pretext to mobilize.
  Localize the conflict.

  --- HAWKS (Conrad) ---
  Conrad insists: every hour of delay strengthens the enemy.
  We must mobilize against Serbia immediately.

  --- MODERATES (Tisza) ---
  Tisza urges caution: Serbia's partial acceptance gives us
  a diplomatic victory. Pressing further risks Russian intervention.
```
