# Discord AI Bot

Lightweight Discord helper that turns mention-based prompts and uploads into Ollama-powered responses with per-user state, model choice, file handling, and rich messaging.

## Features
- Answer prompts only when the bot is mentioned so it stays silent outside focused conversations.
- Persist up to eight turns of chat history per user while still enforcing the system prompt that asks for pure JSON responses with code block hygiene.
- Accept attachments (images, text, HEIC photos) by saving them under `uploads/<user-id>` and feeding their content or encoded image to the Ollama chat API; HEIC uploads are converted to JPEG automatically.
- Provide slash commands to clear state (`/clear`), list and choose Ollama models (`/models`), and show the current default (`/current`).
- Convert Ollama JSON output into Discord messages with embeds, buttons, and long-response protection via `bot.messaging`.

## Prerequisites
- Python 3.10+ and `pip` installed.
- A running Ollama server accessible by the `OLLAMA_CHAT` and `OLLAMA_TAGS` endpoints (default `http://localhost:11434`).
- A Discord bot token with Message Content Intent enabled so slash commands can sync automatically across joined guilds.

## Setup
1. `pip install -r requirements.txt`
2. Copy the YAML template: `cp config.example.yaml config.yaml` (or `copy config.example.yaml config.yaml` on Windows).
3. Populate `DISCORD_TOKEN` and any overrides directly inside `config.yaml`.
4. Adjust optional values such as `DEFAULT_MODEL`, `LOG_LEVEL`, `UPLOAD_ROOT`, and `OLLAMA_PARALLELISM`.

## Running
`python main.py`

The entry point in `main.py` wires the bot handlers defined in `bot/handlers/handlers.py`, configures logging, checks for a `DISCORD_TOKEN`, and launches the Discord client.

## Configuration
The bot reads configuration from `config.yaml` at the project root (values can still be overridden via environment variables if necessary).
| Variable | Description |
| --- | --- |
| `DISCORD_TOKEN` | Required bot token.
| `OLLAMA_CHAT` | Ollama chat endpoint (used for prompt/response exchange).
| `OLLAMA_TAGS` | Ollama tags endpoint (returns model names used by `/models`).
| `DEFAULT_MODEL` | Fallback Ollama model when the user has no selection.
| `LOG_LEVEL` | Controls logging verbosity for `bot.logger`.
| `UPLOAD_ROOT` | Root folder for persisting attachments that accompany prompts.
| `OLLAMA_PARALLELISM` | Maximum concurrent requests to the Ollama API (default `1` to serialize calls).
| `OLLAMA_PARALLELISM` | Maximum concurrent requests to the Ollama API (default `1` to serialize calls).

## Usage
- Mention the bot in any channel (e.g., `@Bot Hello`). The handler strips the mention, saves attachments, and relays the prompt plus context to Ollama.
- Attachments larger than the configured limit are truncated: text files contribute up to ~4KB, while images are base64-encoded and sent on their own.
- `/clear` removes the user’s chat history and deletes their upload folder via `bot.services.attachments.delete_user_uploads`.
- `/models` fetches available Ollama models (`bot.services.ollama.get_models`) and lets the user switch with a dropdown; `/current` reports their choice.
- Requests to Ollama are serialized. If a prompt arrives while another is being handled, the bot replies with a queue message (e.g., “Queue #2”), and that message is deleted once the request is served.
- Responses quote the triggering message so users can see which exchange the bot is addressing.
- The bot builds Discord responses with embeds, buttons, and custom views when the Ollama response contains `components` or `embeds`.

## Architecture Highlights
- `bot/config.py` loads configuration from `config.yaml` (with environment-variable overrides) so operational parameters stay in one place.
- `bot/services/ollama.py` keeps chat history per user, appends the `SYSTEM_PROMPT`, merges uploaded files, handles HEIC conversion (`bot/files/heic_converter.py`), and posts to the configured Ollama endpoint with a semaphore governed by `OLLAMA_PARALLELISM` so the Ollama server is never hit in parallel more than needed.
- `bot/messaging.py` parses Ollama JSON with `bot.utils.safe_json_parse`, adds fenced code blocks (`fix_codeblocks`), and maps component buttons to Discord UI elements.
- `bot/events/message_handler.py` serializes mention handling through a queue and calls `ask_ollama` while quoting the triggering message.
`bot/events/command_handlers.py` exposes slash commands, view dropdowns, and sync logic that iterates over every guild the bot is a member of at startup.
- `bot/state.py` tracks chat history and per-user model selections, and `bot.utils` sanitizes output, maps button styles, and recovers JSON from imperfect model text.

## Project Layout
- `bot` – Application package with configuration, client, logging, event handlers, services, and utilities.
- `bot/events` – Event modules that register Discord listeners and commands on import so `bot.app` can dynamically load them.
- `bot/services` – Ollama/world-specific helpers such as attachment storage, Ollama client wrappers, and file conversion utilities.
- `bot/files` – Thin helpers such as `heic_converter.py` that interact with external libraries.
- `tests` – pytest-based unit tests for helpers and services.

## Testing
`pytest`
Current tests cover attachment cleanup (`tests/test_attachments.py`) and utility helpers (`tests/test_utils.py`).

## Logging & Troubleshooting
`bot.logger.configure_logging` sets a consistent `%(asctime)s | %(levelname)s | %(message)s` format. Problems include missing `DISCORD_TOKEN`, Ollama timeouts (handled with a 1-hour timeout), and failures reading uploads (logged at error level).

## Deployment & Operations
### Docker
1. Build a container based on `python:3.12-slim`, copy the project, install `requirements.txt`, and create a volume for `uploads`. Example:
   ```dockerfile
   FROM python:3.12-slim
   WORKDIR /app
   COPY . .
   RUN pip install --no-cache-dir -r requirements.txt
   CMD ["python", "main.py"]
   ```
2. Mount `config.yaml` from the host (`-v "$(pwd)/config.yaml:/app/config.yaml:ro"`) so secrets stay outside the image.
3. Expose ports if you need to access logs remotely or supervise health checks; Discord interactions run outbound so no public ports are required.

### CI/CD
- Run `pytest` on every push or pull request to guard helpers such as `bot.services.attachments` and the new `bot.services.ollama` coverage.
- Lint Python files, rebuild Docker images, and publish artifacts only when configuration variables (Discord token, Ollama endpoints) are provided as secrets.
- Keep `config.yaml` in CI as a templated file or use environment variables to override without checking credentials into the repo.

### Hosted Ollama Instances
- Point `OLLAMA_CHAT` / `OLLAMA_TAGS` at your hosted model endpoint (TLS, auth, or a load balancer is supported).
- Ensure the machine running Ollama is reachable from wherever the bot is hosted, or set up a secure tunnel if the instance is behind a firewall.
- Monitor `bot.logger` output for request latency; adjust `OLLAMA_PARALLELISM` and retries when the hosted API rates-limit or throttles requests.

## Next Steps
1. Add more tests for `bot.services.ollama` to verify payload handling and HEIC conversions.
2. Expand documentation for deploying the bot (Docker, CI, or hosted Ollama instances).
