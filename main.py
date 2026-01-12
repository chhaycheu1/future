import threading
import logging
from src.web.app import app, db_manager
from src.core.bot import TradingBot
from config.settings import Config

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("Main")

def start_bot():
    try:
        logger.info("Initializing Trading Bot...")
        bot = TradingBot(Config, db_manager)
        bot.start() # This calls run_loop which has a while loop, but run_loop is called inside start? 
        # Wait, in my bot.py, start() calls db update then run_loop() which blocks if not threaded inside bot.
        # My bot.py start() calls run_loop() directly at the end. 
        # So bot.start() IS blocking. That's fine for this thread.
    except Exception as e:
        logger.error(f"Bot thread crashed: {e}")

if __name__ == "__main__":
    logger.info("Starting Application...")
    
    # Start Bot in background thread
    bot_thread = threading.Thread(target=start_bot, name="BotThread")
    bot_thread.daemon = True # Daemon thread exits when main thread exits
    bot_thread.start()

    # Start Flask Web Server
    # use_reloader=False is important when traversing threads to avoid duplicates
    logger.info("Starting Web Server on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
