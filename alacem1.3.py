import json
import os
import time
from datetime import datetime, timedelta

# ==========================================
# CONFIGURACIÓN DE PERSISTENCIA Y REGLAS DE NEGOCIO
# ==========================================
ARCHIVO_INVENTARIO = "inventario.json"
ARCHIVO_HISTORIAL = "historial_ingresos.json"

# Límite máximo realista permitido por producto en el almacén
LIMITE_MAXIMO_STOCK = 250
UMBRAL_STOCK_BAJO = 5
DIAS_VENTANA_CADUCIDAD = 3
FECHA_CADUCIDAD_POR_DEFECTO = "2026-12-20"

USUARIOS_VALIDOS = {
    "admin": "1234",
    "almacen": "almacen2026",
}


# ==========================================
# UTILIDADES DE INTERFAZ Y TIEMPOS DE ESPERA
# ==========================================

def limpiar_pantalla():
    """Limpia la consola según el sistema operativo para mejorar la lectura."""
    os.system("cls" if os.name == "nt" else "clear")


def pausa_usuario(mensaje="\nPresiona [ENTER] para continuar..."):
    """Detiene el flujo hasta que el usuario presione Enter."""
    input(mensaje)


def esperar(segundos=1.2):
    """Genera una pausa temporal controlada para que el usuario lea los mensajes."""
    time.sleep(segundos)


def leer_fecha_caducidad(mensaje, fecha_por_defecto=None, permitir_vacio=False):
    """Solicita y valida una fecha en formato YYYY-MM-DD.

    Args:
        mensaje (str): Texto mostrado al solicitar la fecha.
        fecha_por_defecto (str | None): Valor devuelto si se omite la entrada.
        permitir_vacio (bool): Indica si dejar la entrada vacía es válido.

    Returns:
        str | None: Fecha válida en formato YYYY-MM-DD o fecha_por_defecto.
    """
    while True:
        entrada = input(mensaje).strip()
        if not entrada and permitir_vacio:
            return fecha_por_defecto
        try:
            datetime.strptime(entrada, "%Y-%m-%d")
            return entrada
        except ValueError:
            print("[Error] Formato inválido. Usa YYYY-MM-DD (ejemplo: 2026-12-20).")
            esperar(0.8)


# ==========================================
# MODELO DE DATOS (POO BÁSICA)
# ==========================================

class Producto:
    """Representa un ítem almacenado con su control de stock y caducidad."""

    def __init__(self, nombre, categoria, cantidad, unidad, caducidad):
        self.nombre = nombre
        self.categoria = categoria
        self.cantidad = cantidad
        self.unidad = unidad
        self.caducidad = caducidad

    def a_diccionario(self):
        """Convierte la instancia a un diccionario serializable en JSON."""
        return {
            "nombre": self.nombre,
            "categoria": self.categoria,
            "cantidad": self.cantidad,
            "unidad": self.unidad,
            "caducidad": self.caducidad,
        }


# ==========================================
# CAPA DE PERSISTENCIA (JSON / SISTEMA DE ARCHIVOS)
# ==========================================

def obtener_inventario_inicial():
    """Retorna los datos semilla iniciales del almacén."""
    return [
        {"nombre": "Carne de Res", "categoria": "Carne", "cantidad": 12, "unidad": "kg", "caducidad": FECHA_CADUCIDAD_POR_DEFECTO},
        {"nombre": "Pechuga de Pollo", "categoria": "Carne", "cantidad": 4, "unidad": "kg", "caducidad": FECHA_CADUCIDAD_POR_DEFECTO},
        {"nombre": "Lechuga", "categoria": "Verdura", "cantidad": 2, "unidad": "unidades", "caducidad": "2026-11-14"},
        {"nombre": "Tomate", "categoria": "Verdura", "cantidad": 8, "unidad": "kg", "caducidad": FECHA_CADUCIDAD_POR_DEFECTO},
        {"nombre": "Crema de Aji Artesanal", "categoria": "Crema", "cantidad": 3, "unidad": "frascos", "caducidad": FECHA_CADUCIDAD_POR_DEFECTO},
        {"nombre": "Mayonesa Casera", "categoria": "Crema", "cantidad": 1, "unidad": "frascos", "caducidad": FECHA_CADUCIDAD_POR_DEFECTO},
    ]


def cargar_datos(ruta_archivo, datos_por_defecto):
    """Carga datos desde un archivo JSON o crea uno nuevo con valores por defecto."""
    if os.path.exists(ruta_archivo):
        try:
            with open(ruta_archivo, "r", encoding="utf-8") as archivo:
                return json.load(archivo)
        except (json.JSONDecodeError, OSError):
            print(f"[Aviso] Error al leer {ruta_archivo}. Restaurando valores iniciales...")
            esperar(1.5)

    guardar_datos(ruta_archivo, datos_por_defecto)
    return datos_por_defecto


def guardar_datos(ruta_archivo, datos):
    """Guarda una estructura de datos en formato JSON con codificación UTF-8."""
    try:
        with open(ruta_archivo, "w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, indent=4, ensure_ascii=False)
    except OSError as error:
        print(f"[Error crítico] No se pudo guardar en {ruta_archivo}: {error}")
        pausa_usuario()


def reiniciar_datos_prueba():
    """Elimina los archivos JSON del disco y restaura el estado semilla limpio."""
    limpiar_pantalla()
    print("=" * 55)
    print("   ELIMINAR DATOS DE PRUEBA Y REINICIAR SISTEMA")
    print("=" * 55)
    print("Esta acción borrará permanentemente los archivos:")
    print(f" - {ARCHIVO_INVENTARIO}")
    print(f" - {ARCHIVO_HISTORIAL}\n")

    confirmacion = input("¿Estás seguro de continuar? (s/n): ").strip().lower()
    if confirmacion != "s":
        print("\nOperación cancelada. No se borró ningún dato.")
        esperar(1.2)
        return None, None

    print("\nEliminando archivos de prueba del disco...")
    esperar(1.0)

    for ruta in (ARCHIVO_INVENTARIO, ARCHIVO_HISTORIAL):
        if os.path.exists(ruta):
            os.remove(ruta)

    inventario_limpio = cargar_datos(ARCHIVO_INVENTARIO, obtener_inventario_inicial())
    historial_limpio = cargar_datos(ARCHIVO_HISTORIAL, [])

    print("[Éxito] Datos de prueba eliminados. Sistema restaurado a valores iniciales.")
    pausa_usuario("\nPresiona [ENTER] para volver al menú principal...")
    return inventario_limpio, historial_limpio


# ==========================================
# MÓDULO DE AUTENTICACIÓN
# ==========================================

def iniciar_sesion():
    """Valida credenciales de usuario con un máximo de 3 intentos."""
    limpiar_pantalla()
    print("=" * 50)
    print("   SISTEMA DE GESTIÓN DE ALMACÉN - ACCESO")
    print("=" * 50)
    print("Usuarios de prueba -> admin / 1234  |  almacen / almacen2026\n")

    intentos = 3
    while intentos > 0:
        usuario = input("Usuario: ").strip()
        clave = input("Contraseña: ").strip()

        print("\nVerificando credenciales...")
        esperar(1.0)

        if usuario in USUARIOS_VALIDOS and USUARIOS_VALIDOS[usuario] == clave:
            print(f"[Acceso concedido] Bienvenido(a), {usuario}.")
            print("Cargando base de datos del almacén...")
            esperar(1.5)
            return usuario

        intentos -= 1
        print(f"[Error] Credenciales incorrectas. Intentos restantes: {intentos}")
        esperar(1.2)
        print("-" * 50)

    print("\nSe agotaron los intentos de inicio de sesión. Cerrando sistema...")
    esperar(1.5)
    return None


# ==========================================
# RECURSIVIDAD Y ORDENAMIENTO (SESIÓN 7.1)
# ==========================================

def calcular_stock_total_recursivo(productos, indice=0):
    """Suma recursivamente las cantidades registradas en el inventario.

    Condición de parada / Caso base: cuando `indice` alcanza o supera el tamaño
    de la lista, no quedan elementos por sumar y retorna 0.
    Progreso: avanza a `indice + 1` en cada llamada recursiva.

    Args:
        productos (list[dict]): Lista de productos del inventario.
        indice (int): Posición actual evaluada en la lista.

    Returns:
        float | int: Suma acumulada de cantidades en el inventario.
    """
    if indice >= len(productos):
        return 0
    cantidad_actual = productos[indice].get("cantidad", 0)
    return cantidad_actual + calcular_stock_total_recursivo(productos, indice + 1)


def ordenar_por_cantidad_burbuja(productos, descendente=False):
    """Ordena una copia de la lista de productos mediante ordenamiento burbuja.

    Args:
        productos (list[dict]): Lista original de productos.
        descendente (bool): Si es True, ordena de mayor a menor cantidad;
            si es False, de menor a mayor.

    Returns:
        list[dict]: Nueva lista ordenada por cantidad.
    """
    lista_ordenada = productos.copy()
    total_elementos = len(lista_ordenada)

    for pasada in range(total_elementos):
        hubo_intercambio = False

        # En cada pasada, el elemento mayor/menor ya queda ubicado al final
        for actual in range(0, total_elementos - pasada - 1):
            cant_actual = lista_ordenada[actual]["cantidad"]
            cant_siguiente = lista_ordenada[actual + 1]["cantidad"]

            debe_intercambiar = (
                cant_actual < cant_siguiente if descendente else cant_actual > cant_siguiente
            )

            if debe_intercambiar:
                lista_ordenada[actual], lista_ordenada[actual + 1] = (
                    lista_ordenada[actual + 1],
                    lista_ordenada[actual],
                )
                hubo_intercambio = True

        # Corte temprano: si no hubo intercambios, la lista ya está ordenada
        if not hubo_intercambio:
            break

    return lista_ordenada


# ==========================================
# MÓDULO DE ALERTAS PERSISTENTES (REUTILIZACIÓN DRY)
# ==========================================

def _evaluar_caducidad_producto(producto, hoy, limite_vencimiento):
    """Evalúa si un producto está vencido o próximo a vencer según la ventana activa."""
    try:
        fecha_cad = datetime.strptime(producto["caducidad"], "%Y-%m-%d").date()
    except (KeyError, ValueError):
        return None

    if fecha_cad <= limite_vencimiento:
        estado = "VENCIDO" if fecha_cad < hoy else "Vence pronto"
        return (producto["nombre"], producto["caducidad"], estado)
    return None


def obtener_alertas_activas(inventario):
    """Obtiene listas de productos con stock bajo y con caducidad cercana/vencida."""
    alertas_stock = [p for p in inventario if p["cantidad"] < UMBRAL_STOCK_BAJO]

    hoy = datetime.now().date()
    limite_vencimiento = hoy + timedelta(days=DIAS_VENTANA_CADUCIDAD)
    alertas_caducidad = []

    for producto in inventario:
        alerta = _evaluar_caducidad_producto(producto, hoy, limite_vencimiento)
        if alerta is not None:
            alertas_caducidad.append(alerta)

    return alertas_stock, alertas_caducidad


def mostrar_panel_alertas_persistente(inventario):
    """Muestra en consola el resumen persistente de alertas de stock y caducidad."""
    alertas_stock, alertas_caducidad = obtener_alertas_activas(inventario)

    print("!" * 65)
    print(" PANEL DE ALERTAS PERSISTENTES DEL ALMACÉN")
    print("!" * 65)

    if alertas_stock:
        print(f" [!] STOCK BAJO ({len(alertas_stock)} producto(s)):")
        for p in alertas_stock:
            print(f"     * {p['nombre']}: {p['cantidad']} {p['unidad']}")
    else:
        print(" [OK] Niveles de stock óptimos.")

    if alertas_caducidad:
        print(f" [!] CADUCIDAD CERCANA / VENCIDOS ({len(alertas_caducidad)} producto(s)):")
        for nombre, fecha, estado in alertas_caducidad:
            print(f"     * {nombre} ({fecha}) -> {estado}")
    else:
        print(" [OK] Sin productos próximos a vencer.")
    print("!" * 65)


# ==========================================
# FUNCIONES OPERATIVAS DEL ALMACÉN
# ==========================================

def ver_inventario(inventario):
    """Muestra el inventario con opción de ordenamiento burbuja y total recursivo."""
    limpiar_pantalla()
    print("Opciones de visualización del inventario:")
    print(" 1. Orden de registro (original)")
    print(" 2. Ordenar por cantidad: menor a mayor (Burbuja)")
    print(" 3. Ordenar por cantidad: mayor a menor (Burbuja)")

    criterio = input("\nElige cómo mostrar el inventario (1-3) [Enter = 1]: ").strip() or "1"

    if criterio == "2":
        productos_a_mostrar = ordenar_por_cantidad_burbuja(inventario, descendente=False)
        etiqueta_orden = "Menor a mayor cantidad (Burbuja)"
    elif criterio == "3":
        productos_a_mostrar = ordenar_por_cantidad_burbuja(inventario, descendente=True)
        etiqueta_orden = "Mayor a menor cantidad (Burbuja)"
    else:
        productos_a_mostrar = inventario
        etiqueta_orden = "Orden original"

    esperar(0.5)
    total_unidades = calcular_stock_total_recursivo(productos_a_mostrar)

    print("\n" + "=" * 75)
    print(f"INVENTARIO GENERAL | {etiqueta_orden} | Máx: {LIMITE_MAXIMO_STOCK}")
    print("=" * 75)
    print(f"{'PRODUCTO':<25} | {'CATEGORÍA':<10} | {'CANTIDAD':<12} | {'CADUCIDAD'}")
    print("-" * 75)
    for p in productos_a_mostrar:
        cant_str = f"{p['cantidad']} {p['unidad']}"
        print(f"{p['nombre']:<25} | {p['categoria']:<10} | {cant_str:<12} | {p['caducidad']}")
    print("-" * 75)
    print(f"Total acumulado de unidades/medidas registradas (recursivo): {total_unidades}")
    print("=" * 75)
    pausa_usuario("\nPresiona [ENTER] para volver al menú principal...")


def anadir_producto(inventario, historial, usuario_actual):
    """Registra un producto nuevo o repone stock de uno existente y actualiza el historial."""
    limpiar_pantalla()
    print("=" * 55)
    print(f"AÑADIR PRODUCTO AL ALMACÉN (Límite máx: {LIMITE_MAXIMO_STOCK} unidades)")
    print("=" * 55)

    nombre = input("Nombre del producto: ").strip()
    if not nombre:
        print("\n[Error] El nombre no puede estar vacío.")
        esperar(1.3)
        return

    producto_existente = next(
        (p for p in inventario if p["nombre"].lower() == nombre.lower()), None
    )
    stock_actual = producto_existente["cantidad"] if producto_existente else 0
    espacio_disponible = LIMITE_MAXIMO_STOCK - stock_actual

    if producto_existente and espacio_disponible <= 0:
        print(
            f"\n[Bloqueado] '{producto_existente['nombre']}' ya alcanzó el límite "
            f"máximo permitido ({LIMITE_MAXIMO_STOCK} {producto_existente['unidad']})."
        )
        pausa_usuario("\nPresiona [ENTER] para volver al menú principal...")
        return

    if producto_existente:
        print(
            f"\n[Info] '{producto_existente['nombre']}' ya existe "
            f"(Stock actual: {stock_actual} {producto_existente['unidad']})."
        )
        print(
            f"[Info] Capacidad disponible para agregar: hasta "
            f"{espacio_disponible} {producto_existente['unidad']}.\n"
        )
        esperar(0.7)

    while True:
        try:
            cantidad = float(input(f"Cantidad a ingresar (1 - {espacio_disponible}): "))
            if cantidad <= 0:
                print("[Error] La cantidad debe ser mayor a cero.")
                esperar(0.8)
                continue
            if cantidad > LIMITE_MAXIMO_STOCK:
                print(
                    f"[Error] Cantidad irreal. No se permite ingresar más de "
                    f"{LIMITE_MAXIMO_STOCK} unidades por producto."
                )
                esperar(1.0)
                continue
            if (stock_actual + cantidad) > LIMITE_MAXIMO_STOCK:
                print(
                    f"[Error] Se excede la capacidad máxima del almacén "
                    f"({LIMITE_MAXIMO_STOCK}). Solo puedes agregar hasta {espacio_disponible}."
                )
                esperar(1.0)
                continue
            if cantidad.is_integer():
                cantidad = int(cantidad)
            break
        except ValueError:
            print("[Error] Debes ingresar un valor numérico válido.")
            esperar(0.8)

    if producto_existente:
        producto_existente["cantidad"] += cantidad
        producto_existente["caducidad"] = leer_fecha_caducidad(
            f"Nueva fecha de caducidad YYYY-MM-DD (Enter para mantener {producto_existente['caducidad']}): ",
            fecha_por_defecto=producto_existente["caducidad"],
            permitir_vacio=True,
        )
        categoria_reg = producto_existente["categoria"]
        unidad_reg = producto_existente["unidad"]
        caducidad_reg = producto_existente["caducidad"]
        tipo_movimiento = "REPOSICIÓN DE STOCK"
    else:
        categoria_reg = input("Categoría (Carne, Verdura, Crema, Abarrotes, etc.): ").strip() or "General"
        unidad_reg = input("Unidad de medida (kg, unidades, frascos, litros): ").strip() or "unidades"
        caducidad_reg = leer_fecha_caducidad(
            f"Fecha de caducidad (YYYY-MM-DD) [Enter para {FECHA_CADUCIDAD_POR_DEFECTO}]: ",
            fecha_por_defecto=FECHA_CADUCIDAD_POR_DEFECTO,
            permitir_vacio=True,
        )

        nuevo_prod = Producto(nombre, categoria_reg, cantidad, unidad_reg, caducidad_reg)
        inventario.append(nuevo_prod.a_diccionario())
        tipo_movimiento = "NUEVO PRODUCTO"

    registro_historial = {
        "fecha_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "usuario": usuario_actual,
        "tipo": tipo_movimiento,
        "producto": nombre,
        "categoria": categoria_reg,
        "cantidad_agregada": cantidad,
        "unidad": unidad_reg,
        "caducidad_asignada": caducidad_reg,
    }
    historial.append(registro_historial)

    print("\nGuardando cambios en inventario e historial...")
    esperar(1.0)
    guardar_datos(ARCHIVO_INVENTARIO, inventario)
    guardar_datos(ARCHIVO_HISTORIAL, historial)

    print(f"[Éxito] '{nombre}' registrado ({cantidad} {unidad_reg}) y guardado permanentemente.")
    pausa_usuario("\nPresiona [ENTER] para volver al menú principal...")


def ver_historial_ingresos(historial):
    """Muestra la bitácora de movimientos e ingresos registrados."""
    limpiar_pantalla()
    print("Consultando bitácora de ingresos...\n")
    esperar(0.7)

    print("=" * 85)
    print("HISTORIAL DE PRODUCTOS AÑADIDOS AL ALMACÉN")
    print("=" * 85)
    if not historial:
        print("Aún no se han registrado ingresos en el historial.")
    else:
        print(f"{'FECHA Y HORA':<20} | {'USUARIO':<10} | {'ACCIÓN':<19} | {'PRODUCTO':<18} | {'CANTIDAD'}")
        print("-" * 85)
        for h in historial:
            cant_str = f"+{h['cantidad_agregada']} {h['unidad']}"
            print(
                f"{h['fecha_hora']:<20} | {h['usuario']:<10} | "
                f"{h['tipo']:<19} | {h['producto']:<18} | {cant_str}"
            )
    print("=" * 85)
    pausa_usuario("\nPresiona [ENTER] para volver al menú principal...")


def mostrar_stock_bajo(inventario):
    """Muestra los productos cuya cantidad está por debajo del umbral configurado."""
    limpiar_pantalla()
    print("Analizando niveles de stock...\n")
    esperar(0.7)

    print("=" * 45)
    print(f"DETALLE DE PRODUCTOS CON STOCK BAJO (< {UMBRAL_STOCK_BAJO})")
    print("=" * 45)
    stock_bajo = [p for p in inventario if p["cantidad"] < UMBRAL_STOCK_BAJO]
    if stock_bajo:
        for p in stock_bajo:
            print(f" - {p['nombre']} ({p['categoria']}): Solo quedan {p['cantidad']} {p['unidad']}")
    else:
        print(" No hay productos con stock bajo.")
    print("=" * 45)
    pausa_usuario("\nPresiona [ENTER] para volver al menú principal...")


def mostrar_proximos_a_vencer(inventario):
    """Muestra los productos vencidos o dentro de la ventana de caducidad."""
    limpiar_pantalla()
    print("Revisando fechas de caducidad...\n")
    esperar(0.7)

    print("=" * 45)
    print(f"DETALLE DE CADUCIDAD (VENTANA DE {DIAS_VENTANA_CADUCIDAD} DÍAS)")
    print("=" * 45)
    _, alertas_caducidad = obtener_alertas_activas(inventario)

    if alertas_caducidad:
        for nombre, fecha, estado in alertas_caducidad:
            print(f" - {nombre} ({fecha}): {estado}")
    else:
        print(" Ningún producto está próximo a vencer.")
    print("=" * 45)
    pausa_usuario("\nPresiona [ENTER] para volver al menú principal...")


# ==========================================
# CONTROLADOR PRINCIPAL DEL PROGRAMA
# ==========================================

def main():
    """Coordina el flujo principal del sistema de almacén."""
    usuario_activo = iniciar_sesion()
    if not usuario_activo:
        return

    inventario = cargar_datos(ARCHIVO_INVENTARIO, obtener_inventario_inicial())
    historial = cargar_datos(ARCHIVO_HISTORIAL, [])

    while True:
        limpiar_pantalla()
        mostrar_panel_alertas_persistente(inventario)

        print(f"\n--- MENÚ DE ALMACÉN (Usuario: {usuario_activo}) ---")
        print("1. Ver Inventario General")
        print("2. Añadir producto / Reponer stock")
        print("3. Ver Historial de productos añadidos")
        print("4. Ver detalle de productos con stock bajo")
        print("5. Ver detalle de productos próximos a vencer / vencidos")
        print("6. Eliminar datos de prueba / Reiniciar sistema")
        print("7. Salir")

        opcion = input("\nSelecciona una opción (1-7): ").strip()

        if opcion == "1":
            ver_inventario(inventario)
        elif opcion == "2":
            anadir_producto(inventario, historial, usuario_activo)
        elif opcion == "3":
            ver_historial_ingresos(historial)
        elif opcion == "4":
            mostrar_stock_bajo(inventario)
        elif opcion == "5":
            mostrar_proximos_a_vencer(inventario)
        elif opcion == "6":
            inv_limpio, hist_limpio = reiniciar_datos_prueba()
            if inv_limpio is not None:
                inventario = inv_limpio
                historial = hist_limpio
        elif opcion == "7":
            print("\nGuardando estado final del almacén...")
            guardar_datos(ARCHIVO_INVENTARIO, inventario)
            guardar_datos(ARCHIVO_HISTORIAL, historial)
            esperar(1.2)
            print("Datos guardados correctamente. ¡Hasta luego!")
            esperar(1.0)
            break
        else:
            print("\n[Error] Opción no válida. Elige un número entre 1 y 7.")
            esperar(1.2)


if __name__ == "__main__":
    main()