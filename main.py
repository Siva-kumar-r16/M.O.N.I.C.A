"""
M.O.N.I.C.A. — Multimodal Operational Neural Intelligence & Conversational Assistant
Main Application Entry Point.
"""

import asyncio
import logging
import signal
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from monica.config import config
from monica.db import DatabaseEngine, MigrationManager, Repository
from monica.core import ContactManager, TelegramClientWrapper, default_router
from monica.memory import MemoryManager
from monica.persona import PersonaLoader
from monica.ai import OllamaProvider, MonicaAIManager
from monica.scheduler import SchedulerEngine
from monica.plugins import PluginManager
from monica.core.pipeline import MessagePipeline


def setup_logging():
    log_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(getattr(logging, config.LOG_LEVEL, logging.INFO))

    file_handler = RotatingFileHandler(
        config.LOG_FILE,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.DEBUG)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Silence noisy dependencies
    logging.getLogger("telethon").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


async def main():
    setup_logging()
    logger = logging.getLogger("Monica.Main")

    print("=" * 65)
    print("   M.O.N.I.C.A. — AI Telegram Personal Manager & Userbot")
    print("=" * 65)

    # 1. Configuration Validation
    errors = config.validate()
    if errors:
        logger.error("Configuration validation failed:")
        for err in errors:
            logger.error(f"  • {err}")
        print("\n[!] Check your .env file or copy from .env.example.\n")
        # In headless test environments we don't hard-exit if mock mode
        if not ("--test" in sys.argv or "--mock" in sys.argv):
            return

    logger.info(f"API_ID: {config.API_ID} | API_HASH: {config.mask_secret(config.API_HASH)}")
    logger.info(f"Ollama Model: {config.OLLAMA_MODEL} at {config.OLLAMA_HOST}")
    logger.info(f"Auto-Reply: {'Enabled' if config.AUTO_REPLY else 'Disabled'} (Mode: {config.AUTO_REPLY_MODE})")

    # 2. Database & Migrations
    db_engine = DatabaseEngine(config.DATABASE_PATH)
    migrator = MigrationManager(db_engine)
    await migrator.run_migrations()
    repository = Repository(db_engine)

    # 3. Contacts Subsystem
    legacy_contacts = config.DATA_DIR / "trusted_contacts.json"
    contacts_mgr = ContactManager(repository, legacy_json_path=legacy_contacts)
    await contacts_mgr.init_from_legacy_if_needed()

    # 4. Persona Loader
    persona_loader = PersonaLoader()

    # 5. AI Client & Memory Manager
    ollama_provider = OllamaProvider(
        host=config.OLLAMA_HOST,
        model=config.OLLAMA_MODEL,
    )
    memory_mgr = MemoryManager(
        repository=repository,
        ai_client=ollama_provider,
        debounce_seconds=config.MESSAGE_DEBOUNCE_SECONDS,
    )

    # Verify Ollama connectivity asynchronously
    asyncio.create_task(_verify_ollama(ollama_provider, logger))

    ai_manager = MonicaAIManager(
        provider=ollama_provider,
        persona_loader=persona_loader,
        memory_manager=memory_mgr,
    )

    # 6. Telegram Client
    tg_client = TelegramClientWrapper(
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        session_string=config.SESSION_STRING,
    )

    # 7. Persistent Scheduler
    scheduler = SchedulerEngine(repository=repository)
    scheduler.set_dispatcher(
        lambda chat_id, text: tg_client.send_message(chat_id, text)
    )
    await scheduler.start()

    # 8. Command Router & Plugins
    app_context = {
        "config": config,
        "repository": repository,
        "contacts": contacts_mgr,
        "persona": persona_loader,
        "memory": memory_mgr,
        "ollama": ollama_provider,
        "ai_manager": ai_manager,
        "client": tg_client,
        "scheduler": scheduler,
    }
    plugin_manager = PluginManager(default_router, app_context)
    await plugin_manager.load_all()
    app_context["plugin_manager"] = plugin_manager

    # 9. Unified Message Processing Pipeline
    pipeline = MessagePipeline(
        config=config,
        client=tg_client,
        repository=repository,
        contacts=contacts_mgr,
        memory=memory_mgr,
        persona=persona_loader,
        ai_manager=ai_manager,
        router=default_router,
        scheduler=scheduler,
    )

    # Register Telegram listeners
    tg_client.register_message_listener(pipeline.handle_event)

    # 10. Start Telegram Client
    stop_event = asyncio.Event()

    def _on_signal():
        logger.info("Shutdown signal received. Closing M.O.N.I.C.A...")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _on_signal)
        except NotImplementedError:
            pass  # Windows or certain runtimes

    try:
        if config.API_ID and config.SESSION_STRING:
            await tg_client.start()
            logger.info("🎉 M.O.N.I.C.A. is active and listening for messages!")
        else:
            logger.warning("Telegram credentials not fully configured. Running in background worker mode.")

        await stop_event.wait()
    except Exception as e:
        logger.critical(f"Fatal error in main event loop: {e}", exc_info=True)
    finally:
        logger.info("Shutting down scheduler and Telegram client...")
        await scheduler.stop()
        await tg_client.stop()
        logger.info("M.O.N.I.C.A. shutdown complete.")


async def _verify_ollama(provider: OllamaProvider, logger: logging.Logger):
    is_online = await provider.check_connection()
    if is_online:
        logger.info("Ollama AI backend is online and accessible.")
    else:
        logger.warning(
            f"Ollama backend ({provider.host}) is currently unreachable. "
            "Ensure Ollama is running: 'ollama serve' and 'ollama run qwen2.5-coder:7b'"
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
