================================================================================
                    YaMusicLyrics Discord Status
          Display Yandex Music lyrics in Discord in real-time
================================================================================

📋 REQUIREMENTS:
  • Windows 10/11
  • Python 3.12+ (https://www.python.org/downloads/)
  • Yandex Music desktop application
  • Discord desktop app

================================================================================
🚀 QUICK START GUIDE:

1. INSTALL PYTHON
   Download from python.org
   ⚠️ IMPORTANT: Check "Add Python to PATH" during installation

2. RUN INSTALLER
   Double-click "CLICK_INSTALL.bat"
   Wait for installation (1-2 minutes)

3. GET DISCORD TOKEN
   • Open Discord → Press Ctrl+Shift+I
   • Go to "Network" tab
   • Click any channel
   • Find "discord.com/api" request
   • Click it → "Headers" tab
   • Copy "Authorization" value (starts with MT...)

4. CONFIGURE
   Paste your token into config.json:
   "discord_token": "YOUR_TOKEN_HERE"
   Save and close

5. LAUNCH
   Run "CLICK_INSTALL.bat" again
   Minimize the window (don't close!)
   Play music in Yandex Music app
   Lyrics will appear in Discord! 🎵

================================================================================
🔁 DAILY USE:
   Double-click "Start.bat"

================================================================================
⚠️ NOTES:
   • Keep the console window minimized (not closed)
   • Works with Yandex Music desktop app only
   • Lyrics availability depends on lrclib.net database
   • Never share your Discord token!
   • User token usage may violate Discord ToS

================================================================================
🔧 TROUBLESHOOTING:

   Python not found → Install Python and add to PATH
   Invalid token (401) → Get a new token from Discord
   No lyrics found → Song not available on lrclib.net
   No music detected → Use desktop app, not web version

================================================================================
📦 FILES:
   CLICK_INSTALL.bat - First-time setup & launcher
   Start.bat - Quick launch
   main.py - Program source
   config.json - Your settings (PRIVATE!)
   requirements.txt - Dependencies

================================================================================

Enjoy! 🎧