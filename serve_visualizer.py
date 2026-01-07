"""
Simple HTTP server to view the visualizer
Run this, then open http://localhost:8000/visualizer.html
"""
import http.server
import socketserver
import webbrowser
from pathlib import Path
from generate_run_list import generate_run_list

PORT = 8000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers to allow loading local JSON files
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

def start_server():
    """Start the HTTP server."""
    # 1. GENERATE RUN LIST AUTOMATICALLY
    print("🔄 Scanning for simulation runs...")
    try:
        generate_run_list()
    except Exception as e:
        print(f"⚠️ Warning: Failed to generate run list automatically: {e}")

    # 2. Start Server
    Handler = MyHTTPRequestHandler
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        url = f"http://localhost:{PORT}/visualizer.html"
        print(f"\n{'='*60}")
        print(f"🌐 MPES Visualizer Server")
        print(f"{'='*60}")
        print(f"\nServer running at: {url}")
        print(f"\nOpen your browser and go to:")
        print(f"  {url}")
        print(f"\nPress Ctrl+C to stop the server")
        print(f"{'='*60}\n")
        
        # Try to open browser automatically
        try:
            webbrowser.open(url)
            print("✓ Browser opened automatically\n")
        except:
            print("⚠️  Could not open browser automatically")
            print(f"   Please open {url} manually\n")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n👋 Server stopped")

if __name__ == "__main__":
    start_server()
