# Discord qBittorrent Bot

A simple Discord bot that connects to a qBittorrent Web UI and exposes a couple of helpful commands to check torrent status and list active downloads.

Written in Python using `discord.py` (`discord.ext.commands`) and `qbittorrent-api`.

---

## Features

* Connects to qBittorrent Web API and reads torrent state
* `!status <name>` - look up a torrent by (partial) name and show progress, speeds, ETA, ratio, seeds/peers
* `!list` - show up to 10 currently active downloads
* Robust reconnect logic and helpful logging

<img width="643" height="315" alt="{68A3530D-478C-4969-AC1F-328331E6D3C5}" src="https://github.com/user-attachments/assets/22f26d51-74d7-4e37-9489-f4f3c584bfa3" />
<img width="616" height="142" alt="{8DEF7878-DAAE-415B-8356-EDDE3A5F0490}" src="https://github.com/user-attachments/assets/0d0b053d-4d3d-40f5-82fd-57556c5ec3ac" />

---

## Prerequisites

* Python 3.10+ (or another 3.x compatible runtime)
* A running qBittorrent instance with the Web UI enabled
* A Discord bot application + bot token with the `Message Content Intent` enabled.
* (Optional) Docker and Docker Compose if you want to run the bot in a container. **Note:** this repository already includes a `Dockerfile` and a `docker-compose.yml`. See those files directly for containerized deployment instructions.

---

## Environment variables

The bot reads configuration from environment variables. Create a `.env` file for convenience when running with Docker/Compose or locally.

| Variable               | Default | Description                                                                                                              |
| ---------------------- | ------: | ------------------------------------------------------------------------------------------------------------------------ |
| `DISCORD_TOKEN`        |  (none) | **Required.** Discord bot token.                                                                                         |
| `QBITTORRENT_URL`      |  (none) | The URL (including host and optional port) of your qBittorrent Web UI. Can be `http://host:port` or `https://host:port`. If qBittorrent and the bot are running in containers, you can also use `http://qBittorrent_container_name:port` and Docker's internal DNS will resolve to that container provided they are both on the same network. |
| `QBITTORRENT_USERNAME` |  (none) | qBittorrent web UI username                                                                                              |
| `QBITTORRENT_PASSWORD` |  (none) | qBittorrent web UI password                                                                                              |
| `LOG_LEVEL`            |  `INFO` | Python logging level (DEBUG/INFO/WARNING/ERROR)                                                                          |

**Example `.env`**

```env
DISCORD_TOKEN=your_discord_token_here
QBITTORRENT_URL=http://qbt-host:8080
QBITTORRENT_USERNAME=admin
QBITTORRENT_PASSWORD=supersecret
LOG_LEVEL=INFO
```

> **Note:** You can declare your variables in four different ways: in the `.env` file, in your `docker-compose.yml`, as environment variables supplied to the process or directly in the `bot.py` script. Use the approach that best fits your deployment. You do not need to do all four.

---

## Quickstart (local)

1. Clone the repository and change into the project directory.

2. Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip3 install -U pip
pip3 install -r requirements.txt
```

3. Export environment variables (or create `.env`) and run:

```bash
export DISCORD_TOKEN=...
export QBITTORRENT_URL=http://192.168.0.6:8080
export QBITTORRENT_USERNAME=admin
export QBITTORRENT_PASSWORD=supersecret
python3 bot.py
```

You should see logs showing the bot starting and the connection to qBittorrent.

---

## (Repository includes Dockerfiles)

This repository already contains a `Dockerfile` and `docker-compose.yml` for containerized deployment. If you prefer to run the bot in Docker, review those files in the repo and adapt environment variables / networking as needed for your environment.

---

## Discord setup

1. Create a new application at the Discord Developer Portal.
2. Add a Bot to the application and copy the bot token into your `DISCORD_TOKEN` env var.
3. Under "Bot -> Privileged Gateway Intents" enable **Message Content Intent** if you plan to use plain text commands triggered by users typing in chat.
4. Invite the bot to your server with the necessary permissions (Send Messages, Embed Links, Read Message History, etc.).

---

## Usage

Once the bot is running and connected to both Discord and qBittorrent, the following commands are available (prefix `!`):

* `!status <movie_name>` Finds torrents whose name contains `<movie_name>` (case-insensitive). Shows up to 3 matches with:

  * Progress (graph + %)
  * Downloaded size / total size
  * Download / upload speed
  * ETA
  * Ratio
  * Seeds / Peers
  * Torrent state

* `!list` Lists up to 10 active downloads (downloading/stalledDL/queuedDL/checkingDL/forcedDL) with a short one-line summary.

Examples:

```
!status The.Matrix
!list
```

---

## Logging & debugging

* The bot uses the standard Python `logging` module. Change `LOG_LEVEL` (`DEBUG` for verbose output).
* Common problems:

  * `qBittorrent login failed`  verify `QBITTORRENT_USERNAME` / `QBITTORRENT_PASSWORD`, and ensure the qBittorrent Web UI is reachable from the bot.
  * `Cannot connect to qBittorrent Web API`  network issues, wrong URL, or the Web UI is disabled.
  * `Discord token not set`  make sure `DISCORD_TOKEN` is provided; the bot exits if token is missing.

If you see certificate verification errors when connecting to qBittorrent over HTTPS with a self-signed certificate, you can either:

* Use a signed certificate for the qBittorrent Web UI, or
* Ensure the bot container/system trusts the certificate, or
* Run the service behind an HTTPS-terminating reverse proxy with a valid cert.

> The script currently configures the qBittorrent client with certificate verification disabled for convenience when using self-signed certs. Change that behavior if you require stricter security.

---

## Security considerations

* Keep `DISCORD_TOKEN` secret.
* Limit the bot's permissions in your Discord server to the minimum required.
* Be careful where you host the bot. It requires network access to qBittorrent and your Discord gateway.

---

## Extending the bot

Ideas for future enhancements:

* Add commands to pause/resume/remove torrents.
* Allow controlling categories, speed limits, labels.
* Add a configuration command or slash-command support (`discord.app_commands`) instead of message-content parsing.
* Persist user preferences (e.g. default filters) in a small database.
* If you feel like contributing feel free to submit a PR! Contributions are always welcome :)

---

## Troubleshooting tips

* If the bot reports zero guilds or isn't receiving messages, verify the bot was invited with the correct scopes and has appropriate permissions in the server and channel.
* If search results are missing or partial, confirm the bot can reach the qBittorrent Web UI and that the Web UI login did not fail.
* Enable `DEBUG` logging to see the underlying exception traces.

---

Happy torrenting!
