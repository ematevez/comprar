"""
servidor_dashboard.py
Servidor HTTP que sirve el dashboard y expone endpoints para:
- Descartar/Reactivar procesos
- Ejecutar scripts comprar.py y detalle_proceso.py
- Consultar registro de gestión
- Gestión de emails para reportes
- Integración con middleware de seguridad
"""
import json
import os
import sys
import time
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
import pandas as pd
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Importar funciones del generador
from generar_dashboard import (
    generar_dashboard, 
    descartar_proceso, 
    reactivar_proceso,
    cargar_cronograma,
    ejecutar_script,
    estado_ejecucion,
    cargar_notas,
    agregar_nota,
    marcar_nota,
    eliminar_nota,
    registrar_impresion,
    resetear_datos,
    buscar_expediente_en_pdfs,
    EXCEL_GESTION
)

# Importar middleware de seguridad
from middleware_seguridad import (
    verificar_ip_permitida,
    verificar_rate_limit,
    registrar_intento_login,
    crear_token,
    verificar_token,
    verificar_credenciales,
    log_seguridad
)

# Importar API de emails
from api_emails import cargar_emails, agregar_email, eliminar_email, enviar_test

from urllib.parse import urlparse, parse_qs
from licencia import verificar_licencia, renovar_licencia

# Cada cuánto se FIJA si toca correr algo (en minutos)
INTERVALO_CHEQUEO_MINUTOS = 60


def scheduler_automatico():
    print(f"⏱️  Scheduler automático activo: revisa cada {INTERVALO_CHEQUEO_MINUTOS} min")
    while True:
        try:
            r1 = ejecutar_script('comprar')
            if r1.get('ok'):
                for _ in range(600):
                    time.sleep(1)
                    if not estado_ejecucion('comprar')['corriendo']:
                        break
                ejecutar_script('detalle')
        except Exception as e:
            print(f"⚠️ Error en el scheduler automático: {e}")
        time.sleep(INTERVALO_CHEQUEO_MINUTOS * 60)


class DashboardHandler(SimpleHTTPRequestHandler):
    
    def _get_client_ip(self):
        """Obtiene la IP real del cliente (detrás de proxy si aplica)."""
        forwarded = self.headers.get('X-Forwarded-For')
        if forwarded:
            return forwarded.split(',')[0].strip()
        return self.client_address[0]
    
    def _check_auth(self):
        """Verifica autenticación por token en header."""
        auth_header = self.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            return verificar_token(token)
        # También aceptar cookie de sesión
        cookie = self.headers.get('Cookie', '')
        if 'session=' in cookie:
            token = cookie.split('session=')[1].split(';')[0]
            return verificar_token(token)
        return False
    
    def do_GET(self):
        client_ip = self._get_client_ip()
        
        # Verificar IP permitida
        if not verificar_ip_permitida(client_ip):
            log_seguridad("ACCESO_DENEGADO_IP", client_ip)
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b'{"error": "IP no autorizada"}')
            return
        
        if self.path == '/' or self.path == '/dashboard.html':
            lic = verificar_licencia()
            if not lic['ok']:
                self._servir_pantalla_licencia(lic)
                return
            generar_dashboard()
            self.path = '/dashboard.html'
            return super().do_GET()
        
        # Endpoint de login
        if self.path == '/api/login':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'ok': True, 'message': 'Login endpoint'}).encode())
            return
        
        parsed = urlparse(self.path)
        
        if parsed.path == '/api/estado':
            qs = parse_qs(parsed.query)
            script_name = qs.get('script', [''])[0]
            resultado = estado_ejecucion(script_name)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(resultado, ensure_ascii=False).encode())
            return

        if self.path == '/api/notas':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'notas': cargar_notas()}, ensure_ascii=False).encode())
            return

        if self.path == '/api/gestion':
            if os.path.exists(EXCEL_GESTION):
                df = pd.read_excel(EXCEL_GESTION)
                rows = df.to_dict(orient='records')
            else:
                rows = []
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'rows': rows}, ensure_ascii=False).encode())
            return
        
        # Endpoint para obtener lista de emails
        if self.path == '/api/emails':
            if not self._check_auth():
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'No autorizado'}).encode())
                return
            emails = cargar_emails()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(emails, ensure_ascii=False).encode())
            return
        
        return super().do_GET()

    def _servir_pantalla_licencia(self, lic):
        html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<title>Licencia</title>
<style>
  body {{ font-family: -apple-system, 'Segoe UI', Arial, sans-serif; background: #F4F6F9;
         display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
  .box {{ background: white; border: 1px solid #E4E8EF; border-radius: 12px; padding: 32px;
          max-width: 420px; box-shadow: 0 8px 24px rgba(20,33,61,0.12); }}
  h1 {{ color: #14213D; font-size: 18px; margin: 0 0 12px; }}
  p {{ color: #5B6B82; font-size: 13.5px; line-height: 1.5; margin: 0 0 18px; }}
  input {{ width: 100%; padding: 10px 12px; border: 1px solid #E4E8EF; border-radius: 6px;
           font-size: 13px; margin-bottom: 12px; box-sizing: border-box; }}
  button {{ width: 100%; padding: 10px; border: 0; border-radius: 6px; background: #14213D;
            color: white; font-weight: 700; font-size: 13px; cursor: pointer; }}
  #msg {{ margin-top: 12px; font-size: 12.5px; }}
</style></head>
<body>
  <div class="box">
    <h1>Dashboard de Licitaciones</h1>
    <p>{lic['motivo']}</p>
    <input type='password' id='clave' placeholder='Clave o código de renovación'>
    <button onclick='renovar()'>Renovar</button>
    <div id="msg"></div>
  </div>
  <script>
    async function renovar() {{
      const clave = document.getElementById('clave').value;
      const resp = await fetch('/api/licencia/renovar', {{
        method: 'POST', headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{clave}})
      }});
      const data = await resp.json();
      const msg = document.getElementById('msg');
      if (data.ok) {{
        msg.style.color = '#059669';
        msg.textContent = data.mensaje + ' Recargando...';
        setTimeout(() => location.reload(), 1200);
      }} else {{
        msg.style.color = '#DC2626';
        msg.textContent = data.error;
      }}
    }}
  </script>
</body></html>"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def do_POST(self):
        client_ip = self._get_client_ip()
        
        # Verificar IP permitida
        if not verificar_ip_permitida(client_ip):
            log_seguridad("ACCESO_DENEGADO_IP", client_ip)
            self.send_response(403)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'IP no autorizada'}).encode())
            return
        
        # Rate limiting
        allowed, msg = verificar_rate_limit(client_ip)
        if not allowed:
            log_seguridad("RATE_LIMIT_EXCEDIDO", client_ip, msg)
            self.send_response(429)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': msg}).encode())
            return
        
        content_length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(content_length).decode('utf-8')) if content_length else {}

        # LOGIN
        if self.path == '/api/login':
            username = body.get('username', '')
            password = body.get('password', '')
            valido, error = verificar_credenciales(username, password)
            if valido:
                registrar_intento_login(client_ip, exitoso=True)
                token = crear_token(username)
                log_seguridad("LOGIN_EXITOSO", client_ip, f"Usuario: {username}")
                resultado = {'ok': True, 'token': token}
            else:
                registrar_intento_login(client_ip, exitoso=False)
                log_seguridad("LOGIN_FALLIDO", client_ip, error)
                resultado = {'ok': False, 'error': error}
        
        elif self.path == '/api/descartar':
            resultado = descartar_proceso(body.get('numero', ''), body.get('motivo', ''))
        elif self.path == '/api/reactivar':
            resultado = reactivar_proceso(body.get('numero', ''))
        elif self.path == '/api/ejecutar':
            resultado = ejecutar_script(body.get('script', ''), forzar=bool(body.get('forzar', False)))
        elif self.path == '/api/notas/agregar':
            resultado = agregar_nota(body.get('texto', ''))
        elif self.path == '/api/notas/marcar':
            resultado = marcar_nota(body.get('id'), body.get('hecha', True))
        elif self.path == '/api/notas/eliminar':
            resultado = eliminar_nota(body.get('id'))
        elif self.path == '/api/registrar_impresion':
            resultado = registrar_impresion(body.get('numero', ''))
        elif self.path == '/api/resetear':
            resultado = resetear_datos()
        elif self.path == '/api/expediente':
            resultado = buscar_expediente_en_pdfs(body.get('numero', ''))
        elif self.path == '/api/licencia/renovar':
            resultado = renovar_licencia(body.get('clave', ''))
        
        # EMAILS (requiere auth)
        elif self.path == '/api/emails/agregar':
            if not self._check_auth():
                resultado = {'ok': False, 'error': 'No autorizado'}
            else:
                resultado = agregar_email(body.get('email', ''))
        elif self.path == '/api/emails/eliminar':
            if not self._check_auth():
                resultado = {'ok': False, 'error': 'No autorizado'}
            else:
                resultado = eliminar_email(body.get('email', ''))
        elif self.path == '/api/emails/test':
            if not self._check_auth():
                resultado = {'ok': False, 'error': 'No autorizado'}
            else:
                resultado = enviar_test(body.get('email', ''))
        
        else:
            resultado = {'ok': False, 'error': 'Endpoint desconocido'}

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(resultado, ensure_ascii=False).encode())

    def log_message(self, format, *args):
        pass


def main():
    puerto = int(os.environ.get("PUERTO", "8765"))
    print("="*60)
    print("🚀 Dashboard de Licitaciones")
    print("="*60)

    lic = verificar_licencia()
    if lic['ok']:
        print(f"🔑 Licencia: {lic['motivo']}")
    else:
        print(f"🔒 Licencia BLOQUEADA: {lic['motivo']}")
    print("="*60)

    print(f"📍 Accedé a: http://0.0.0.0:{puerto}")
    print(f"⏱️  Scheduler automático: revisa cada {INTERVALO_CHEQUEO_MINUTOS} min")
    print("="*60)
    print("Presioná Ctrl+C para detener el servidor")
    print("="*60)
    
    generar_dashboard()
    threading.Thread(target=scheduler_automatico, daemon=True).start()

    # Escuchar en 0.0.0.0 para acceso desde la red
    server = HTTPServer(('0.0.0.0', puerto), DashboardHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Servidor detenido")
        server.shutdown()


if __name__ == "__main__":
    main()
