import asyncio
import importlib
import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from shared_client import start_client

# ------------------------------
# Step 1: Add a Health Check Server
# ------------------------------
# Use an environment variable for the port (default is 8080)
HEALTH_CHECK_PORT = int(os.getenv("HEALTH_CHECK_PORT", "8080"))

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
    try:
        server = HTTPServer(("0.0.0.0", HEALTH_CHECK_PORT), HealthCheckHandler)
        print(f"✅ Health server running on port {HEALTH_CHECK_PORT}")
        server.serve_forever()
    except OSError as e:
        # If the port is already in use, log the error
        print(f"❌ Could not start health server on port {HEALTH_CHECK_PORT}: {e}")

# Start the health check server in a separate daemon thread.
health_thread = threading.Thread(target=run_health_server, daemon=True)
health_thread.start()

# ------------------------------
# Step 2: Load and Run Plugins
# ------------------------------
async def load_and_run_plugins():
    plugin_dir = "plugins"
    if not os.path.isdir(plugin_dir):
        print("❌ Plugins directory not found")
        return

    plugins = [f[:-3] for f in os.listdir(plugin_dir)
               if f.endswith(".py") and f != "__init__.py"]

    if not plugins:
        print("⚠️ No plugins found in the plugins directory.")

    for plugin in plugins:
        try:
            module = importlib.import_module(f"plugins.{plugin}")
        except Exception as e:
            print(f"❌ Failed to import plugin '{plugin}': {e}")
            continue

        func_name = f"run_{plugin}_plugin"
        if hasattr(module, func_name):
            print(f"🚀 Running {plugin} plugin...")
            try:
                await getattr(module, func_name)()
            except Exception as e:
                print(f"❌ Error running plugin '{plugin}': {e}")
        else:
            print(f"⚠️ Function '{func_name}' not found in plugin '{plugin}'. Skipping...")

# ------------------------------
# Step 3: Run the Bot Client and Plugins Concurrently
# ------------------------------
async def main():
    print("🔄 Starting bot client and plugins concurrently...")
    # Run start_client and load_and_run_plugins concurrently.
    await asyncio.gather(
        start_client(),
        load_and_run_plugins(),
        asyncio.Event().wait()  # Keeps the process running indefinitely.
    )

if __name__ == "__main__":
    try:
        # Create and set a new event loop explicitly.
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("🛑 Shutting down...")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        loop.close()
