# Copyright (c) 2025 devgagan : https://github.com/devgaganin.
# Licensed under the GNU General Public License v3.0.
# See LICENSE file in the repository root for full license text.

import asyncio
import importlib
import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from shared_client import start_client

# ------------------------------
# ✅ Step 1: Add a Health Check Server
# ------------------------------
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()

def run_health_server():
    server = HTTPServer(("0.0.0.0", 8080), HealthCheckHandler)
    print("✅ Health server running on port 8080")
    server.serve_forever()

# Start the health check server in a separate thread
threading.Thread(target=run_health_server, daemon=True).start()

# ------------------------------
# ✅ Step 2: Load and Run Plugins
# ------------------------------
async def load_and_run_plugins():
    await start_client()
    plugin_dir = "plugins"
    plugins = [f[:-3] for f in os.listdir(plugin_dir) if f.endswith(".py") and f != "__init__.py"]

    for plugin in plugins:
        module = importlib.import_module(f"plugins.{plugin}")
        if hasattr(module, f"run_{plugin}_plugin"):
            print(f"🚀 Running {plugin} plugin...")
            await getattr(module, f"run_{plugin}_plugin")()

# ------------------------------
# ✅ Step 3: Keep Bot Running
# ------------------------------
async def main():
    await load_and_run_plugins()
    await asyncio.Event().wait()  # Keeps the bot alive indefinitely

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Event loop is closed")
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        print("🔄 Starting clients ...")

    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("🛑 Shutting down...")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        try:
            loop.close()
        except Exception:
            pass
