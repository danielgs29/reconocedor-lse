"""Servidor local para probar la web, sin caché (así los cambios se ven al recargar)."""
import functools
import http.server
import socketserver


class SinCache(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, max-age=0")
        super().end_headers()


Handler = functools.partial(SinCache, directory="web")
socketserver.ThreadingTCPServer.allow_reuse_address = True
with socketserver.ThreadingTCPServer(("", 8000), Handler) as s:
    print("Servidor en http://localhost:8000 (sin caché)")
    s.serve_forever()
