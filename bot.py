import discord
from discord.ext import commands
import os
import logging
from datetime import timedelta
import qbittorrentapi

logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN', 'YOUR_DISCORD_BOT_TOKEN')
QBITTORRENT_URL = os.getenv('QBITTORRENT_URL', 'YOUR_QBITTORRENT_URL')
QBITTORRENT_USERNAME = os.getenv('QBITTORRENT_USERNAME', 'YOUR_USERNAME')
QBITTORRENT_PASSWORD = os.getenv('QBITTORRENT_PASSWORD', 'YOUR_PASSWORD')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')


class QBittorrentBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        self.qb_client: qbittorrentapi.Client | None = None

    async def setup_hook(self):
        """Called when the bot is starting up"""
        self.connect_qbittorrent()

    def connect_qbittorrent(self) -> bool:
        """Connect to qBittorrent Web API"""
        try:
            url_parts = QBITTORRENT_URL.replace('http://', '').replace('https://', '')
            if ':' in url_parts:
                host, port = url_parts.split(':')
                port = int(port)
            else:
                host = url_parts
                port = 8080

            self.qb_client = qbittorrentapi.Client(
                host=host,
                port=port,
                username=QBITTORRENT_USERNAME,
                password=QBITTORRENT_PASSWORD,
                VERIFY_WEBUI_CERTIFICATE=False,
                REQUESTS_ARGS={'timeout': (10, 30)}
            )

            self.qb_client.auth_log_in()

            version = self.qb_client.app.version
            logger.info(f"✅ Connected to qBittorrent v{version}")
            return True

        except qbittorrentapi.LoginFailed:
            logger.error("❌ qBittorrent login failed - check username/password")
            return False
        except qbittorrentapi.APIConnectionError as e:
            logger.error(f"❌ Cannot connect to qBittorrent Web API: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error connecting to qBittorrent: {e}")
            return False

    def get_torrents(self):
        """Get all torrents from qBittorrent"""
        try:
            if not self.qb_client:
                self.connect_qbittorrent()

            torrents = self.qb_client.torrents_info()
            return torrents
        except Exception as e:
            logger.error(f"Error getting torrents: {e}")
            if self.connect_qbittorrent():
                try:
                    torrents = self.qb_client.torrents_info()
                    return torrents
                except Exception as retry_error:
                    logger.error(f"Retry failed: {retry_error}")
            return None

    def format_size(self, size_bytes):
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f} {size_names[i]}"

    def format_speed(self, speed_bytes):
        if speed_bytes == 0:
            return "0 B/s"
        return f"{self.format_size(speed_bytes)}/s"

    def format_eta(self, eta_seconds):
        if eta_seconds == 8640000:
            return "∞"
        if eta_seconds <= 0:
            return "Unknown"

        eta_delta = timedelta(seconds=eta_seconds)
        days = eta_delta.days
        hours, remainder = divmod(eta_delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    def get_state_emoji(self, state):
        state_emojis = {
            'downloading': '⬇️',
            'uploading': '⬆️',
            'stalledDL': '⏸️',
            'stalledUP': '⏸️',
            'queuedDL': '⏳',
            'queuedUP': '⏳',
            'pausedDL': '⏸️',
            'pausedUP': '⏸️',
            'completedDL': '✅',
            'completedUP': '✅',
            'checkingDL': '🔍',
            'checkingUP': '🔍',
            'error': '❌',
            'missingFiles': '❌',
            'allocating': '📦'
        }
        return state_emojis.get(state, '❓')


bot = QBittorrentBot()


@bot.event
async def on_ready():
    logger.info(f'🤖 {bot.user} is now online!')
    logger.info(f'📡 Connected to {len(bot.guilds)} server(s)')
    print(f'🤖 {bot.user} is now online!')
    print(f'📡 Connected to {len(bot.guilds)} server(s)')


@bot.command(name='status')
async def torrent_status(ctx, *, movie_name: str = None):
    if not movie_name:
        await ctx.send("❌ Please provide a movie/show name: `!status movie name`")
        return

    if not bot.qb_client:
        await ctx.send("❌ Not connected to qBittorrent. Trying to connect...")
        if not bot.connect_qbittorrent():
            await ctx.send("❌ Failed to connect to qBittorrent Web API")
            return

    torrents = bot.get_torrents()
    if torrents is None:
        await ctx.send("❌ Failed to get torrent list from qBittorrent")
        return

    movie_name_lower = movie_name.lower()
    matching_torrents = [
        torrent for torrent in torrents
        if movie_name_lower in torrent.name.lower()
    ]

    if not matching_torrents:
        await ctx.send(f"❌ No torrents found matching: `{movie_name}`")
        return

    for torrent in matching_torrents[:3]:
        embed = discord.Embed(
            title=f"{bot.get_state_emoji(torrent.state)} {torrent.name[:100]}",
            color=0x00ff00 if torrent.progress == 1 else 0xff9900
        )

        progress_percent = torrent.progress * 100
        progress_bar = "█" * int(progress_percent / 5) + "░" * (20 - int(progress_percent / 5))

        embed.add_field(name="📊 Progress", value=f"`{progress_bar}` {progress_percent:.1f}%", inline=False)
        embed.add_field(name="💾 Size", value=f"{bot.format_size(torrent.downloaded)} / {bot.format_size(torrent.size)}", inline=True)
        embed.add_field(name="🚀 Speed", value=f"⬇️ {bot.format_speed(torrent.dlspeed)}\n⬆️ {bot.format_speed(torrent.upspeed)}", inline=True)
        embed.add_field(name="⏰ ETA", value=bot.format_eta(torrent.eta), inline=True)
        embed.add_field(name="📈 Ratio", value=f"{torrent.ratio:.2f}", inline=True)
        embed.add_field(name="👥 Seeds/Peers", value=f"{torrent.num_seeds} / {torrent.num_leechs}", inline=True)
        embed.add_field(name="🔧 State", value=torrent.state.title(), inline=True)
        embed.set_footer(text=f"Hash: {torrent.hash[:8]}...")

        await ctx.send(embed=embed)


@bot.command(name='list')
async def list_active_downloads(ctx):
    if not bot.qb_client:
        await ctx.send("❌ Not connected to qBittorrent. Trying to connect...")
        if not bot.connect_qbittorrent():
            await ctx.send("❌ Failed to connect to qBittorrent Web API")
            return

    torrents = bot.get_torrents()
    if torrents is None:
        await ctx.send("❌ Failed to get torrent list from qBittorrent")
        return

    active_downloads = [
        t for t in torrents if t.state in [
            "downloading", "stalledDL", "queuedDL", "checkingDL", "forcedDL"
        ]
    ]

    if not active_downloads:
        await ctx.send("📭 No active downloads found")
        return

    embed = discord.Embed(title="⬇️ Active Downloads", color=0x0099ff)

    torrent_list = []
    for i, torrent in enumerate(active_downloads[:10]):
        progress = torrent.progress * 100
        state_emoji = bot.get_state_emoji(torrent.state)
        name = torrent.name[:50] + "..." if len(torrent.name) > 50 else torrent.name
        torrent_list.append(f"{state_emoji} **{name}** - {progress:.1f}%")

    embed.description = "\n".join(torrent_list)

    if len(active_downloads) > 10:
        embed.set_footer(text=f"Showing 10 of {len(active_downloads)} active downloads")

    await ctx.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Missing required argument. Use `!help` for usage information.")
    elif isinstance(error, commands.CommandNotFound):
        return
    else:
        await ctx.send(f"❌ An error occurred: {str(error)}")
        logger.error(f"Command error: {error}")


if __name__ == "__main__":
    logger.info("🚀 Starting Discord qBittorrent Bot...")
    print("🚀 Starting Discord qBittorrent Bot...")
    print("📋 Available commands:")
    print("  !status <movie_name> - Get download status for a specific torrent")
    print("  !list - List all active torrents")
    print("\n⚙️  Configuration:")
    print(f"  Discord Token: {'Set' if DISCORD_TOKEN != 'YOUR_DISCORD_BOT_TOKEN' else 'NOT SET'}")
    print(f"  qBittorrent URL: {QBITTORRENT_URL}")
    print(f"  qBittorrent User: {QBITTORRENT_USERNAME}")
    print(f"  Log Level: {LOG_LEVEL}")

    if DISCORD_TOKEN == 'YOUR_DISCORD_BOT_TOKEN':
        logger.error("❌ Discord token not set! Please set the DISCORD_TOKEN environment variable.")
        print("❌ Discord token not set! Please set the DISCORD_TOKEN environment variable.")
        exit(1)

    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        print(f"❌ Failed to start bot: {e}")
