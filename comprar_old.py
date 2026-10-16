# pip install playwright pandas openpyxl
# playwright install

from playwright.sync_api import sync_playwright
import pandas as pd
import time

def seleccionar_usuario():
    print("¿Qué usuario querés usar?")
    print("1 - EMATEVEZ")
    print("2 - MHIBALO")
    opcion = input("Ingresá 1 o 2: ").strip()
    if opcion == "2":
        return ("EMATEVEZ", "7Wmundial1")
    elif opcion == "1":
        return ("MHIBALO", "Cotn3021")
    else:
        print("Opción no válida. Usando EMATEVEZ por defecto.")
        return ("EMATEVEZ", "7Wmundial1")

def login_comprar(cuit: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Paso 1: Login inicial
        page.goto("https://comprar.gob.ar/Login.aspx")
        page.fill('input[id="txtUsername_txtTextBox"]', cuit)
        page.click('a#lnkConfirmar')
        page.wait_for_load_state('networkidle')

        # usuario, contrasena = seleccionar_usuario()
        usuario, contrasena = "EMATEVEZ", "7Wmundial1"
        page.fill('input[placeholder="Usuario/Cuil/Cuit"]', usuario)
        page.fill('input[placeholder="Contraseña"]', contrasena)
        page.keyboard.press("Enter")
        page.wait_for_load_state('networkidle')
        print("✅ Login completado.")

        # Paso 2: Clic en botón Acceder
        try:
            page.wait_for_selector('#z9GQt', timeout=5000)
            page.click('#z9GQt')
            print("✅ Accediste al Escritorio del Comprador.")
        except:
            print("⚠️ No se encontró el botón 'Acceder'. ¿Ya estás logueado?")

        # Paso 3: Ir al escritorio directamente
        page.goto("https://comprar.gob.ar/CORE/DefaultEscritorioComprador.aspx")
        page.wait_for_load_state('networkidle')

        # Paso 4: Ir a Buscar Proceso
        page.goto("https://comprar.gob.ar/PLIEGO/BusquedaAvanzadaProcesos.aspx")
        page.wait_for_load_state('networkidle')

        # Paso 5: Completar filtros
        page.fill('input[id="ctl00_CPH1_dxeDteFechaDesde_I"]', "01/03/2025")
        page.fill('input[id="ctl00_CPH1_dxeDteFechaHasta_I"]', "03/07/2025")

        page.select_option('select[id="ctl00_CPH1_ddlTipoProceso"]', '2')  # LPR
        page.select_option('select[id="ctl00_CPH1_ddlJurisdiccionUOA"]', '949')  # Armada
        page.select_option('select[id="ctl00_CPH1_ddlUnidadOperativaAdquisiciones"]', '1055')  # 38/18

        # Paso 6: Buscar
        page.click('a[id="ctl00_CPH1_btnBuscar"]')
        print("🕒 Esperando a que cargue la tabla...")

        try:
            page.wait_for_selector('a[id*="lnkNumeroProceso"]', timeout=15000)
            print("✅ Tabla de resultados cargada correctamente.")
        except:
            print("⚠️ No se cargó la tabla con los resultados. Revisá si los filtros devolvieron algo.")
            browser.close()
            return

        # Paso 7: Extraer tabla
        table = page.query_selector('#ctl00_CPH1_gridResultado')
        rows = table.query_selector_all('tr')

        print(f"⚙️ Se encontraron {len(rows)} filas totales (incluyendo cabecera).")

        data = []
        for i, row in enumerate(rows[1:], start=1):  # saltar encabezado
            cols = row.query_selector_all('td')
            print(f"➡️ Fila {i}: {len(cols)} columnas")  # depuración

            if len(cols) >= 6:
                numero = cols[0].inner_text().strip()
                expediente = cols[1].inner_text().strip()
                nombre = cols[2].inner_text().strip()
                unidad = cols[3].inner_text().strip()
                estado = cols[4].inner_text().strip()
                fecha = cols[5].inner_text().strip()

                data.append({
                    'Número de proceso': numero,
                    'Expediente': expediente,
                    'Nombre de proceso': nombre,
                    'Unidad': unidad,
                    'Estado': estado,
                    'Fecha de creación': fecha
                })

        print(f"✅ Total registros extraídos: {len(data)}")

        # Paso 8: Guardar en Excel
        if data:
            df = pd.DataFrame(data)
            nombre_excel = os.environ.get("NOMBRE_EXCEL", "procesos_armada.xlsx")
            df.to_excel(nombre_excel, index=False)

            print("📁 Guardado exitosamente en procesos_armada.xlsx")
        else:
            print("⚠️ No se extrajo ningún dato. Revisá los filtros o el selector.")

        browser.close()

# Ejecutar
if __name__ == "__main__":
    login_comprar("20315217750")
