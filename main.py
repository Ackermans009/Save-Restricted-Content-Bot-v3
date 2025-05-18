import asyncio
import importlib
import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from shared_client import start_client

# ------------------------------
# ✅ Step 1: Health Check Server
# ------------------------------
HEALTH_CHECK_PORT = 8080  # Must match your deployment health check settings

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
    server = HTTPServer(("0.0.0.0", HEALTH_CHECK_PORT), HealthCheckHandler)
    print(f"✅ Health server running on port {HEALTH_CHECK_PORT}")
    server.serve_forever()

# Run the health check in a separate daemon thread.
threading.Thread(target=run_health_server, daemon=True).start()


# ------------------------------
# ✅ Step 2: Load and Run Plugins
# ------------------------------
async def load_plugins():
    plugin_dir = "plugins"
    if not os.path.exists(plugin_dir):
        print("❌ Plugins directory does not exist.")
        return

    plugins = [f[:-3] for f in os.listdir(plugin_dir) if f.endswith(".py") and f != "__init__.py"]
    if not plugins:
        print("⚠️ No plugins found in the plugins directory.")
    for plugin in plugins:
        try:
            module = importlib.import_module(f"plugins.{plugin}")
            func_name = f"run_{plugin}_plugin"
            if hasattr(module, func_name):
                print(f"🚀 Running {plugin} plugin...")
                await getattr(module, func_name)()
            else:
                print(f"⚠️ Function '{func_name}' not found in plugin '{plugin}'.")
        except Exception as e:
            print(f"❌ Error loading plugin '{plugin}': {e}")


# ------------------------------
# ✅ Step 3: Start the Bot
# ------------------------------
async def main():
    # Start the bot client and plugin loader concurrently.
    asyncio.create_task(start_client())
    asyncio.create_task(load_plugins())
    print("🔄 Bot client and plugins started. Awaiting events...")

    # Keep the event loop running indefinitely.
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        # Set up and start the new event loop.
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        print("🔄 Starting main bot execution...")
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("🛑 Shutting down...")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
    finally:
        try:
            loop.close()
        except Exception:
            pass
