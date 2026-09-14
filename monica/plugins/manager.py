"""
Safe Local Plugin Loader & Lifecycle Manager for M.O.N.I.C.A.
Dynamically imports local plugin packages, isolates errors so broken plugins never crash
the assistant, and supports runtime plugin reloading.
"""

import importlib
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from monica.core.router import CommandRouter
from monica.plugins.base import BasePlugin

logger = logging.getLogger("Monica.PluginManager")


class PluginManager:
    def __init__(self, router: CommandRouter, app_context: Dict[str, Any], plugins_dir: Optional[Path] = None):
        self.router = router
        self.app_context = app_context
        if plugins_dir is None:
            self.plugins_dir = Path(__file__).resolve().parent
        else:
            self.plugins_dir = Path(plugins_dir)

        self._loaded_plugins: Dict[str, BasePlugin] = {}

    async def load_all(self):
        """Discovers and initializes all local plugins."""
        logger.info(f"Scanning for local plugins in {self.plugins_dir}...")
        for item in self.plugins_dir.iterdir():
            if item.is_dir() and not item.name.startswith(("_", ".")):
                await self.load_plugin(item.name)

    async def load_plugin(self, plugin_name: str) -> bool:
        """Loads and activates an individual plugin module."""
        try:
            module_path = f"monica.plugins.{plugin_name}"
            module = importlib.import_module(module_path)

            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, BasePlugin) and attr is not BasePlugin:
                    plugin_class = attr
                    break

            if not plugin_class:
                logger.warning(f"No BasePlugin subclass discovered in {module_path}")
                return False

            instance: BasePlugin = plugin_class(self.router, self.app_context)
            await instance.on_load()
            self._loaded_plugins[plugin_name] = instance
            logger.info(f"Loaded plugin: {instance.name} v{instance.version} ({plugin_name})")
            return True
        except Exception as e:
            logger.error(f"Failed to load plugin '{plugin_name}': {e}", exc_info=True)
            return False

    async def unload_plugin(self, plugin_name: str) -> bool:
        """Unloads an active plugin."""
        if plugin_name in self._loaded_plugins:
            try:
                await self._loaded_plugins[plugin_name].on_unload()
                self._loaded_plugins.pop(plugin_name, None)
                logger.info(f"Unloaded plugin: {plugin_name}")
                return True
            except Exception as e:
                logger.error(f"Error unloading plugin '{plugin_name}': {e}", exc_info=True)
        return False

    async def reload_plugin(self, plugin_name: str) -> bool:
        """Reloads a plugin from disk."""
        await self.unload_plugin(plugin_name)
        return await self.load_plugin(plugin_name)

    def list_plugins(self) -> List[Dict[str, Any]]:
        """Returns details on all loaded plugins."""
        return [
            {
                "id": pid,
                "name": p.name,
                "version": p.version,
                "description": p.description,
                "category": p.category,
                "author": p.author,
            }
            for pid, p in self._loaded_plugins.items()
        ]
