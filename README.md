# Steam Integration for Unfolded Circle Remote Two/3

This integration displays your currently playing Steam game and online friends information on your Unfolded Circle Remote Two/Three.

**Developer:** Meir Miyara :smiley:

## Features

- **Currently Playing Game Display**
  - Game title and Steam artwork
  - Real-time game detection
  - Playing status indicator
  - Steam game cover art display

- **Online Friends List**
  - Count of friends currently online
  - Real-time friend status updates
  - Privacy-friendly (respects Steam profile settings)

- **Automatic Updates**
  - 30-second refresh intervals
  - Survives Remote reboots
  - Graceful error handling
  - Battery-optimized polling

## Performance & Caching

The Steam integration includes intelligent caching to provide a smooth, reliable experience:

### **Smart Error Recovery**
- **Handles Steam server issues**: When Steam API returns 502/503 errors, the integration uses cached data to prevent flickering
- **Maintains stable display**: Your currently playing game and friends count stay visible during temporary API outages
- **Graceful degradation**: Falls back to last known good state instead of showing errors

### **Artwork Caching**
- **Game images cached**: Once a game's artwork is loaded, it's cached to reduce API calls
- **High-resolution Steam logo**: Friends entity uses Steam's official high-quality SVG logo instead of tiny favicon
- **Faster loading**: Repeated views of the same games load instantly from cache

### **API Optimization**
- **Intelligent throttling**: Respects Steam's 1 request/second limit with built-in throttling
- **Reduced flickering**: Cached responses prevent rapid state changes during API hiccups
- **Battery efficient**: Optimized polling reduces unnecessary network requests

### **Cache Benefits**
- **Stable user experience** during temporary Steam server issues
- **Faster response times** for previously seen games
- **Reduced network usage** on your Remote device
- **Professional appearance** with high-quality Steam branding

## Prerequisites

1. Unfolded Circle Remote Two/3
2. Steam account with public profile (recommended)
3. **Steam Web API Key** (see setup below)
4. **Your Steam ID** (see setup below)

## Steam API Setup

**IMPORTANT:** Before installing this integration, you must obtain your Steam Web API Key and Steam ID.

### Step 1: Get Your Steam Web API Key

1. Go to [Steam Web API Key](https://steamcommunity.com/dev/apikey)
2. Sign in with your Steam account
3. Enter any domain name (e.g., `localhost` or `example.com`)
4. Click **"Register"**
5. Copy your **Steam Web API Key** (keep this secure!)

### Step 2: Find Your Steam ID

**Method 1: Steam ID Finder (Easiest)**
1. Go to [SteamID.io](https://steamid.io/)
2. Enter your Steam profile URL or username
3. Copy your **steamID64** (17-digit number starting with 765...)

**Method 2: Steam Client**
1. Open Steam → View → Settings → Interface
2. Check "Display Steam URL address when available"
3. Go to your Steam profile
4. Your Steam ID is the number in the profile URL

### Step 3: Profile Privacy Settings

For the friends list feature to work properly:
1. Go to Steam → Profile → Edit Profile → Privacy Settings
2. Set **"Game details"** to **Public** or **Friends Only**
3. Set **"Friends list"** to **Public** or **Friends Only**
4. Click **"Save"**

**Note:** Private profiles will show game information but no friends data.

## Installation

### Method 1: Pre-built Release (Recommended)
1. Download the latest `.tar.gz` file from the [Releases](https://github.com/mase1981/uc-intg-steam/releases) page
2. Upload to your Remote Two via the web configurator
3. Follow the setup process

### Method 2: Docker Deployment

Run the Steam integration as a Docker container on any host machine (server, NAS, Raspberry Pi, etc.). The Remote will automatically discover it via zeroconf/mDNS.

#### Quick Start (Single Command)
```bash
docker run -d --name uc-intg-steam --network host --restart unless-stopped -v uc-steam-config:/config mase1981/uc-intg-steam:latest
```

#### Docker Compose (Recommended)

1. **Create docker-compose.yml:**
   ```yaml
   version: '3.8'
   services:
     uc-intg-steam:
       build: .
       container_name: uc-intg-steam
       restart: unless-stopped
       network_mode: host
       environment:
         - UC_INTEGRATION_HTTP_PORT=9090
         - UC_CONFIG_HOME=/config
       volumes:
         - ./config:/config
   ```

2. **Clone and start:**
   ```bash
   git clone https://github.com/mase1981/uc-intg-steam.git
   cd uc-intg-steam
   docker-compose up -d
   ```

3. **Check logs:**
   ```bash
   docker-compose logs -f uc-intg-steam
   ```

#### Docker Configuration

- **Auto-discovery**: The container will be automatically discovered by your Remote
- **Port**: Uses port 9090 (ensure it's not in use)
- **Network**: Uses host networking for proper mDNS discovery
- **Config**: All settings configured through the Remote's web interface
- **Persistence**: Configuration stored in `/config` volume

#### Docker Troubleshooting

1. **Integration not discovered**: Ensure Remote and Docker host are on same network
2. **Port conflicts**: Change `UC_INTEGRATION_HTTP_PORT` to different port
3. **Check logs**: `docker logs uc-intg-steam` for error details

### Method 3: Development Installation
1. Clone this repository
2. Set up your development environment (see Development section)

## Setup Process

### During Integration Setup:

1. **Steam Credentials Page:**
   - **Steam Web API Key:** Enter your API key from the Steam developer portal
   - **Steam ID (64-bit):** Enter your 17-digit Steam ID
   - Click **Next**

2. **Validation:**
   - The integration will test your Steam API credentials
   - Verify your Steam profile is accessible
   - Click **Finish**

3. **Completion:**
   - Two entities will be created:
     - **Steam - Now Playing** (Media Player entity)
     - **Steam - Friends** (Media Player entity)

## Usage

### Currently Playing Entity
- Shows game title and artwork when you're playing
- Displays "No game detected" when idle
- Updates every 30 seconds automatically
- Press **ON** button to manually refresh

### Friends Entity
- Shows count of online friends
- Updates every 30 seconds automatically
- Press **ON** button to manually refresh
- Respects Steam privacy settings

## Troubleshooting

### Common Issues

1. **"Invalid API key" error:**
   - Verify you entered the correct Steam Web API Key
   - Check for extra spaces or characters
   - Ensure the API key is active

2. **"Access denied" error:**
   - Check your Steam profile privacy settings
   - Ensure "Game details" is not set to Private
   - Verify your Steam ID is correct

3. **No friends data:**
   - Check that "Friends list" privacy is not set to Private
   - Verify you have friends who are currently online
   - Some Steam profiles may restrict API access

4. **No game information:**
   - Make sure Steam is running and you're playing a game
   - Check that your profile's "Game details" is public
   - Verify Steam is not in offline mode

### Setup Issues

1. **Invalid Steam ID:**
   - Ensure you're using the 64-bit Steam ID (17 digits)
   - Don't use your Steam username or profile name
   - Verify the Steam ID format starts with 765...

2. **Connection Issues:**
   - Check your internet connection
   - Verify Steam servers are operational
   - Ensure no firewall is blocking the integration

### Debug Information

Check the Remote logs for detailed information:
- Steam API connection status
- Authentication issues
- Rate limiting messages
- Game detection events

## Development

### Setup Development Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/mase1981/uc-intg-steam.git
   cd uc-intg-steam
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run in development mode:**
   ```bash
   python uc_intg_steam/driver.py
   ```

### Project Structure

```
uc-intg-steam/
├── uc_intg_steam/
│   ├── __init__.py
│   ├── driver.py          # Main integration driver
│   ├── client.py          # Steam API client with caching
│   ├── config.py          # Configuration management
│   ├── setup.py           # Setup handler
│   ├── media_player.py    # Media player entities
│   └── remote.py          # Remote entity (placeholder)
├── .vscode/
│   └── launch.json        # VSCode debug configuration
├── .github/
│   └── workflows/
│       └── build.yml      # GitHub Actions build
├── driver.json            # Integration metadata
├── config.json            # Runtime configuration (created during setup)
├── pyproject.toml         # Python project configuration
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker image configuration
├── docker-compose.yml     # Docker Compose configuration
└── README.md
```

### Debugging

Use VSCode with the provided `launch.json` configuration:
1. Open the project in VSCode
2. Go to Run and Debug (Ctrl+Shift+D)
3. Select "Python: Steam Integration"
4. Press F5 to start debugging

### Key Implementation Notes

1. **Rate Limiting**: Respects Steam's API limits with 1 request per second throttling
2. **Error Handling**: Advanced caching system prevents flickering during Steam API outages
3. **Privacy Aware**: Handles private Steam profiles without crashing
4. **Persistent**: Survives Remote Two reboots and network outages
5. **Battery Friendly**: Optimized polling intervals with intelligent caching

## API Rate Limiting

The integration respects Steam's API rate limits:
- **1 request per second maximum**
- **30-second update intervals** for real-time data
- **Automatic throttling** to prevent API abuse
- **Batch processing** for friend lists

## Technical Details

### Steam Web API Endpoints Used
- `ISteamUser/GetPlayerSummaries/v0002/` - Player info and currently playing
- `ISteamUser/GetFriendList/v0001/` - Friends list (if public)

### Data Sources
- **Game artwork**: Steam CDN header images
- **Game information**: Steam Web API player summaries
- **Friend status**: Steam Web API friend summaries

### Caching & Performance
- **Artwork caching**: Game images cached by title to reduce API calls
- **Data persistence**: API responses cached during temporary server errors
- **High-quality assets**: Uses Steam's official SVG logo for crisp display
- **Smart fallbacks**: Maintains last known state during API disruptions

### Security & Privacy
- **Your Steam API key stays on your device**
- **No credentials shared with the integration author**
- **Respects Steam privacy settings**
- **Local configuration storage only**
- **No telemetry or data collection**

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly with your own Steam account
5. Submit a pull request

**Please test with both public and private Steam profiles!**

## License

This project is licensed under the Mozilla Public License 2.0 - see the LICENSE file for details.

## Legal Disclaimers

### Third-Party Service Integration
This integration is an independent, unofficial project that interfaces with Steam's publicly available Web API. This project is:

- **NOT sponsored, endorsed, or affiliated** with Valve Corporation or Steam
- **NOT an official Steam product** or service
- Developed independently using Steam's public Web API documentation

### Intellectual Property
- **Steam** is a trademark of Valve Corporation
- All Steam-related trademarks, service marks, and logos are the property of Valve Corporation
- This project claims no ownership of Steam's intellectual property
- Game artwork and information accessed through the API remain the property of their respective copyright holders

### API Usage and Terms
- Users must comply with [Steam's Web API Terms of Use](https://steamcommunity.com/dev/apiterms)
- This integration requires users to obtain their own Steam Web API Key
- Usage is subject to Steam's rate limiting and API policies
- Users are responsible for their own API key security

### User Responsibilities
By using this integration, you acknowledge that:

- You are responsible for obtaining and securing your own Steam Web API key
- You are responsible for complying with Steam's terms of service
- You use this software at your own risk
- The developer is not liable for any account restrictions or consequences
- You must respect other users' privacy settings

### Data and Privacy
- This integration does not store, collect, or transmit personal data beyond what is necessary for API functionality
- Steam API keys are stored locally on your device
- No user data is shared with third parties
- Configuration remains on your local device
- Users should review Steam's privacy policy for information about data handled by Steam's services

**For questions about Steam's services, terms, or policies, please contact Valve Corporation directly.**

## Support

- GitHub Issues: [Report bugs and request features](https://github.com/mase1981/uc-intg-steam/issues)
- Unfolded Circle Community: [Get help from the community](https://unfoldedcircle.com/community)

## Acknowledgments

- Unfolded Circle for the Remote Two/3 and integration API
- Valve Corporation for Steam and the Steam Web API
- The UC community for testing and feedback
- All Steam users who helped test this integration

---

**Enjoy your Steam integration! Happy gaming! 🎮**

**- Meir Miyara**