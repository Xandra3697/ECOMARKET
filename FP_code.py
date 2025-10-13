"""
EcoMarket - Sistema básico de gestión de inventario (consola)
Funciones:
 - Registrar productos (CU01)
 - Registrar entrada / reposición (CU02)
 - Registrar venta / salida (CU03)
 - Consultar stock en tiempo real (CU04)
 - Reporte de bajo stock + exportar CSV (CU05)
 - Cálculo valor inventario y recargo 8% (CU06)
 - Historial de movimientos
Almacenamiento en memoria usando dicts y listas. Interacción por consola.
"""

import datetime
import csv
import os

class Inventario:
    def __init__(self):
        self.productos = {}  # Almacena los datos de los productos por código
        self.historial_movimientos = [] # Almacena un registro de todas las entradas y salidas
        self.precios_unitarios = {} # Almacena precios unitarios para CU06

    # --- Métodos Auxiliares ---
    def _registrar_movimiento(self, codigo, tipo, cantidad_afectada, cantidad_final_stock, documento=None, referencia=None, responsable=None, fecha_hora=None):
        """
        Método interno para registrar un movimiento en el historial.
        """
        if fecha_hora is None:
            fecha_hora = datetime.datetime.now()

        movimiento = {
            "fecha_hora": fecha_hora.strftime("%Y-%m-%d %H:%M:%S"),
            "codigo_producto": codigo,
            "tipo_movimiento": tipo, # Ej: "Ingreso", "Salida", "Ingreso Inicial"
            "cantidad_afectada": cantidad_afectada,
            "cantidad_final_stock": cantidad_final_stock,
            "numero_documento": documento if documento else "N/A",
            "referencia_pedido": referencia if referencia else "N/A",
            "responsable": responsable if responsable else "N/A"
        }
        self.historial_movimientos.append(movimiento)

    # --- CU01 - Registrar productos ---
    def registrar_producto(self, codigo, nombre, categoria, cantidad_inicial, ubicacion=None, precio_unitario=0.0):
        """
        Registra un nuevo producto en el inventario.

        Args:
            codigo (str): Código único del producto (obligatorio).
            nombre (str): Nombre del producto.
            categoria (str): Categoría a la que pertenece el producto.
            cantidad_inicial (int): Cantidad inicial en stock.
            ubicacion (str, optional): Ubicación del producto. Por defecto es None.
            precio_unitario (float, optional): Precio unitario del producto para cálculo de valor.

        Returns:
            dict or str: Un diccionario con el resumen del producto si el registro es exitoso,
                         o un mensaje de error si el código ya existe.
        """
        if not codigo:
            return "Error: El código de producto es obligatorio."

        if codigo in self.productos:
            return f"Error: El código de producto '{codigo}' ya está registrado."
        
        if not isinstance(cantidad_inicial, int) or cantidad_inicial < 0:
            return "Error: La cantidad inicial debe ser un número entero no negativo."
        
        if not isinstance(precio_unitario, (int, float)) or precio_unitario < 0:
            return "Error: El precio unitario debe ser un número no negativo."

        producto = {
            "nombre": nombre,
            "categoria": categoria,
            "cantidad": cantidad_inicial, # Cantidad actual en stock
            "ubicacion": ubicacion
        }
        self.productos[codigo] = producto
        self.precios_unitarios[codigo] = precio_unitario # Guardar precio unitario

        # Registrar este registro inicial como un tipo de movimiento "Ingreso Inicial"
        self._registrar_movimiento(
            codigo=codigo,
            tipo="Ingreso Inicial",
            cantidad_afectada=cantidad_inicial,
            cantidad_final_stock=cantidad_inicial,
            documento="Registro Inicial"
        )

        return {
            "mensaje": "Producto registrado exitosamente.",
            "resumen": {
                "Código": codigo,
                "Nombre": producto["nombre"],
                "Categoría": producto["categoria"],
                "Cantidad": producto["cantidad"],
                "Ubicación": producto["ubicacion"] if producto["ubicacion"] else "No especificada",
                "Precio Unitario": f"${precio_unitario:.2f}"
            }
        }

    # --- CU02 - Registrar entrada de producto (compra o reposición) ---
    def registrar_entrada_producto(self, codigo_producto, cantidad_ingresada, numero_documento=None):
        """
        Registra una entrada (compra o reposición) de un producto existente.

        Args:
            codigo_producto (str): El código del producto.
            cantidad_ingresada (int): La cantidad a añadir al stock.
            numero_documento (str, optional): Número de documento asociado a la entrada.

        Returns:
            str: Mensaje de actualización de stock y nuevo nivel, o mensaje de error.
        """
        if not codigo_producto:
            return "Error: El código de producto no puede estar vacío."
        
        if codigo_producto not in self.productos:
            return f"Error: El producto con código '{codigo_producto}' no existe en el inventario."
        
        if not isinstance(cantidad_ingresada, int) or cantidad_ingresada <= 0:
            return "Error: La cantidad ingresada debe ser un número entero positivo."

        # Obtener el producto
        producto = self.productos[codigo_producto]
        
        # Sumar cantidad al stock
        producto["cantidad"] += cantidad_ingresada
        nuevo_stock = producto["cantidad"]

        # Registrar movimiento en historial
        self._registrar_movimiento(
            codigo=codigo_producto,
            tipo="Ingreso",
            cantidad_afectada=cantidad_ingresada,
            cantidad_final_stock=nuevo_stock,
            documento=numero_documento
        )

        return (f"Stock actualizado para '{producto['nombre']}' (Código: {codigo_producto}). "
                f"Cantidad ingresada: {cantidad_ingresada}. Nuevo stock disponible: {nuevo_stock}.")

    # --- CU03 - Salida de stock (despacho/venta) ---
    def registrar_salida_producto(self, codigo_producto, cantidad_retirar, referencia_pedido=None, responsable=None):
        """
        Registra una salida de producto (despacho/venta).

        Args:
            codigo_producto (str): El código del producto a retirar.
            cantidad_retirar (int): La cantidad a retirar del stock.
            referencia_pedido (str, optional): Referencia del pedido o venta.
            responsable (str, optional): Nombre del responsable del retiro.

        Returns:
            str: Mensaje de actualización de stock y nuevo nivel, o mensaje de error por insuficiencia.
        """
        if not codigo_producto:
            return "Error: El código de producto no puede estar vacío."
        
        if codigo_producto not in self.productos:
            return f"Error: El producto con código '{codigo_producto}' no existe en el inventario."
        
        if not isinstance(cantidad_retirar, int) or cantidad_retirar <= 0:
            return "Error: La cantidad a retirar debe ser un número entero positivo."

        producto = self.productos[codigo_producto]

        # Verificar stock suficiente
        if producto["cantidad"] < cantidad_retirar:
            return (f"Error: Stock insuficiente para '{producto['nombre']}' (Código: {codigo_producto}). "
                    f"Stock actual: {producto['cantidad']}, cantidad solicitada: {cantidad_retirar}.")
        
        # Restar cantidad del stock
        producto["cantidad"] -= cantidad_retirar
        nuevo_stock = producto["cantidad"]

        # Registrar movimiento en historial
        self._registrar_movimiento(
            codigo=codigo_producto,
            tipo="Salida",
            cantidad_afectada=cantidad_retirar,
            cantidad_final_stock=nuevo_stock,
            referencia=referencia_pedido,
            responsable=responsable
        )

        return (f"Salida registrada para '{producto['nombre']}' (Código: {codigo_producto}). "
                f"Cantidad retirada: {cantidad_retirar}. Nuevo stock disponible: {nuevo_stock}.")

    # --- CU04 - Consultar stock en tiempo real ---
    def consultar_stock(self, filtro_codigo="", filtro_nombre_parcial="", filtro_categoria="", umbral_minimo_stock=5):
        """
        Consulta el stock según varios parámetros de búsqueda.

        Args:
            filtro_codigo (str): Código exacto del producto a buscar.
            filtro_nombre_parcial (str): Parte del nombre del producto a buscar (insensible a mayúsculas/minúsculas).
            filtro_categoria (str): Categoría del producto a buscar (insensible a mayúsculas/minúsculas).
            umbral_minimo_stock (int): Umbral para considerar un producto como "bajo stock".

        Returns:
            tuple: (list de productos encontrados, dict de métricas).
        """
        productos_encontrados = []
        stock_total = 0
        productos_bajo_minimo = 0

        for codigo, datos in self.productos.items():
            cumple_filtro = True

            if filtro_codigo and codigo != filtro_codigo:
                cumple_filtro = False
            
            if filtro_nombre_parcial and filtro_nombre_parcial.lower() not in datos["nombre"].lower():
                cumple_filtro = False
            
            if filtro_categoria and filtro_categoria.lower() not in datos["categoria"].lower():
                cumple_filtro = False
            
            if cumple_filtro:
                productos_encontrados.append({
                    "codigo": codigo,
                    "nombre": datos["nombre"],
                    "categoria": datos["categoria"],
                    "cantidad": datos["cantidad"],
                    "ubicacion": datos["ubicacion"] if datos["ubicacion"] else "No especificada"
                })
                stock_total += datos["cantidad"]
                if datos["cantidad"] <= umbral_minimo_stock:
                    productos_bajo_minimo += 1

        metricas = {
            "stock_total_encontrado": stock_total,
            "productos_bajo_minimo": productos_bajo_minimo
        }
        return productos_encontrados, metricas

    # --- CU05 - Reporte de bajo stock y generación de CSV ---
    def generar_reporte_completo(self, umbral_minimo_stock=5):
        """
        Genera un reporte completo de todos los productos y su estado,
        identificando aquellos con bajo stock.
        """
        print("\n--- REPORTE COMPLETO DE INVENTARIO ---")
        productos_con_bajo_stock = []
        
        if not self.productos:
            print("El inventario está vacío. No hay productos para reportar.")
            return

        for codigo, datos in self.productos.items():
            precio = self.precios_unitarios.get(codigo, 0.0)
            print(f"Código: {codigo}")
            print(f"  Nombre: {datos['nombre']}")
            print(f"  Categoría: {datos['categoria']}")
            print(f"  Stock Actual: {datos['cantidad']}")
            print(f"  Ubicación: {datos['ubicacion'] if datos['ubicacion'] else 'No especificada'}")
            print(f"  Precio Unitario: ${precio:.2f}")

            if datos['cantidad'] <= umbral_minimo_stock:
                print("  *** ¡ATENCIÓN: BAJO STOCK! ***")
                productos_con_bajo_stock.append(codigo)
            print("-" * 30)
        
        print("\n--- Resumen del Reporte ---")
        print(f"Total de productos registrados: {len(self.productos)}")
        print(f"Productos con bajo stock (<= {umbral_minimo_stock}): {len(productos_con_bajo_stock)}")
        if productos_con_bajo_stock:
            print(f"  Códigos: {', '.join(productos_con_bajo_stock)}")
        print("-----------------------------\n")

    def exportar_reporte_csv(self, filename="reporte_inventario.csv"):
        """
        Exporta el reporte completo del inventario y su historial de movimientos a un archivo CSV.
        """
        if not self.productos and not self.historial_movimientos:
            print("No hay datos en el inventario o historial para exportar.")
            return

        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)

                # Encabezado del reporte de productos
                writer.writerow(["--- PRODUCTOS EN INVENTARIO ---"])
                writer.writerow(["Código", "Nombre", "Categoría", "Cantidad", "Ubicación", "Precio Unitario"])
                for codigo, datos in self.productos.items():
                    precio = self.precios_unitarios.get(codigo, 0.0)
                    writer.writerow([
                        codigo,
                        datos['nombre'],
                        datos['categoria'],
                        datos['cantidad'],
                        datos['ubicacion'] if datos['ubicacion'] else "N/A",
                        f"{precio:.2f}"
                    ])
                
                writer.writerow([]) # Línea en blanco para separar

                # Encabezado del reporte de movimientos
                writer.writerow(["--- HISTORIAL DE MOVIMIENTOS ---"])
                writer.writerow([
                    "Fecha/Hora", "Código Producto", "Tipo Movimiento",
                    "Cantidad Afectada", "Stock Final", "Número Documento",
                    "Referencia Pedido", "Responsable"
                ])
                for mov in self.historial_movimientos:
                    writer.writerow([
                        mov['fecha_hora'],
                        mov['codigo_producto'],
                        mov['tipo_movimiento'],
                        mov['cantidad_afectada'],
                        mov['cantidad_final_stock'],
                        mov['numero_documento'],
                        mov['referencia_pedido'],
                        mov['responsable']
                    ])
            print(f"Reporte exportado exitosamente a '{filename}'")
        except IOError as e:
            print(f"Error al exportar el reporte a CSV: {e}")

    # --- CU06 - Control de inventario y cálculo de valor total ---
    def calcular_valor_total_inventario(self, umbral_valor=10000.0, recargo_porcentaje=0.08):
        """
        Calcula el valor total del inventario y aplica un recargo si supera un umbral.

        Args:
            umbral_valor (float): El umbral a partir del cual se aplica el recargo.
            recargo_porcentaje (float): El porcentaje de recargo a aplicar (ej. 0.08 para 8%).

        Returns:
            str: Mensaje con el valor total y si se aplicó recargo.
        """
        valor_total_sin_recargo = 0.0
        
        if not self.productos:
            return "El inventario está vacío, no se puede calcular el valor total."

        for codigo, datos in self.productos.items():
            precio = self.precios_unitarios.get(codigo, 0.0)
            cantidad = datos["cantidad"]
            subtotal = precio * cantidad
            valor_total_sin_recargo += subtotal
        
        valor_final = valor_total_sin_recargo
        mensaje_recargo = "No se aplicó recargo."

        if valor_total_sin_recargo > umbral_valor:
            recargo = valor_total_sin_recargo * recargo_porcentaje
            valor_final += recargo
            mensaje_recargo = f"¡Se aplicó un recargo del {recargo_porcentaje*100:.0f}% (${recargo:.2f}) porque el valor supera el umbral de ${umbral_valor:.2f}!"

        return (f"--- CÁLCULO DE VALOR TOTAL DEL INVENTARIO ---\n"
                f"Valor total del inventario (sin recargo): ${valor_total_sin_recargo:.2f}\n"
                f"{mensaje_recargo}\n"
                f"Valor total final del inventario: ${valor_final:.2f}")

    # --- Métodos de visualización (del CU01 y CU02 original) ---
    def mostrar_inventario(self):
        """Muestra todos los productos actualmente en el inventario."""
        if not self.productos:
            print("\nEl inventario está vacío. No hay productos registrados.")
            return

        print("\n--- Inventario Actual ---")
        for codigo, datos in self.productos.items():
            precio = self.precios_unitarios.get(codigo, 0.0)
            print(f"Código: {codigo}")
            print(f"  Nombre: {datos['nombre']}")
            print(f"  Categoría: {datos['categoria']}")
            print(f"  Cantidad: {datos['cantidad']}")
            print(f"  Ubicación: {datos['ubicacion'] if datos['ubicacion'] else 'No especificada'}")
            print(f"  Precio Unitario: ${precio:.2f}")
            print("-" * 20)
        print("-------------------------\n")

    def mostrar_historial_movimientos(self):
        """Muestra el historial completo de movimientos del inventario."""
        if not self.historial_movimientos:
            print("\nNo hay movimientos registrados en el historial.")
            return

        print("\n--- Historial de Movimientos ---")
        for mov in self.historial_movimientos:
            print(f"Fecha/Hora: {mov['fecha_hora']}")
            print(f"  Producto: {mov['codigo_producto']}")
            print(f"  Tipo: {mov['tipo_movimiento']}")
            print(f"  Cantidad afectada: {mov['cantidad_afectada']}")
            print(f"  Stock Final: {mov['cantidad_final_stock']}")
            print(f"  Documento: {mov['numero_documento']}")
            print(f"  Referencia: {mov['referencia_pedido']}")
            print(f"  Responsable: {mov['responsable']}")
            print("-------------------------")
        print("-------------------------\n")


# --- Funciones para interactuar con el usuario (Front-end) ---

def solicitar_datos_producto():
    """Solicita al usuario los datos para registrar un nuevo producto."""
    print("\n--- CU01: Registrar Nuevo Producto ---")
    codigo = input("Ingrese el código del producto (obligatorio): ").strip()
    nombre = input("Ingrese el nombre del producto: ").strip()
    categoria = input("Ingrese la categoría del producto: ").strip()
    
    while True:
        try:
            cantidad_inicial_str = input("Ingrese la cantidad inicial: ").strip()
            cantidad_inicial = int(cantidad_inicial_str)
            if cantidad_inicial < 0:
                print("La cantidad inicial no puede ser negativa. Intente de nuevo.")
            else:
                break
        except ValueError:
            print("Cantidad inicial inválida. Por favor, ingrese un número entero.")

    while True:
        try:
            precio_unitario_str = input("Ingrese el precio unitario del producto (ej. 19.99): ").strip()
            precio_unitario = float(precio_unitario_str)
            if precio_unitario < 0:
                print("El precio unitario no puede ser negativo. Intente de nuevo.")
            else:
                break
        except ValueError:
            print("Precio unitario inválido. Por favor, ingrese un número.")

    ubicacion = input("Ingrese la ubicación del producto (opcional, deje en blanco si no aplica): ").strip()
    if not ubicacion:
        ubicacion = None

    return codigo, nombre, categoria, cantidad_inicial, ubicacion, precio_unitario

def solicitar_datos_entrada_producto():
    """Solicita al usuario los datos para registrar una entrada de producto."""
    print("\n--- CU02: Registrar Entrada de Producto ---")
    codigo_producto = input("Ingrese el código del producto a ingresar: ").strip()
    
    while True:
        try:
            cantidad_ingresada_str = input("Ingrese la cantidad a ingresar: ").strip()
            cantidad_ingresada = int(cantidad_ingresada_str)
            if cantidad_ingresada <= 0:
                print("La cantidad a ingresar debe ser un número entero positivo. Intente de nuevo.")
            else:
                break
        except ValueError:
            print("Cantidad ingresada inválida. Por favor, ingrese un número entero.")
            
    numero_documento = input("Ingrese el número de documento (opcional, deje en blanco si no aplica): ").strip()
    if not numero_documento:
        numero_documento = None
        
    return codigo_producto, cantidad_ingresada, numero_documento

def solicitar_datos_salida_producto():
    """Solicita al usuario los datos para registrar una salida de producto."""
    print("\n--- CU03: Registrar Salida de Stock ---")
    codigo_producto = input("Ingrese el código del producto a retirar: ").strip()
    
    while True:
        try:
            cantidad_retirar_str = input("Ingrese la cantidad a retirar: ").strip()
            cantidad_retirar = int(cantidad_retirar_str)
            if cantidad_retirar <= 0:
                print("La cantidad a retirar debe ser un número entero positivo. Intente de nuevo.")
            else:
                break
        except ValueError:
            print("Cantidad a retirar inválida. Por favor, ingrese un número entero.")
            
    referencia_pedido = input("Ingrese la referencia del pedido (opcional): ").strip()
    if not referencia_pedido:
        referencia_pedido = None
        
    responsable = input("Ingrese el nombre del responsable (opcional): ").strip()
    if not responsable:
        responsable = None
        
    return codigo_producto, cantidad_retirar, referencia_pedido, responsable

def solicitar_parametros_consulta_stock():
    """Solicita al usuario los parámetros para consultar stock."""
    print("\n--- CU04: Consultar Stock en Tiempo Real ---")
    filtro_codigo = input("Filtrar por Código exacto (deje en blanco para omitir): ").strip()
    filtro_nombre_parcial = input("Filtrar por Nombre parcial (deje en blanco para omitir): ").strip()
    filtro_categoria = input("Filtrar por Categoría (deje en blanco para omitir): ").strip()
    
    umbral_minimo_str = input("Definir umbral de bajo stock (ej. 5, por defecto): ").strip()
    try:
        umbral_minimo_stock = int(umbral_minimo_str) if umbral_minimo_str else 5
        if umbral_minimo_stock < 0:
             print("El umbral no puede ser negativo, se usará el valor por defecto (5).")
             umbral_minimo_stock = 5
    except ValueError:
        print("Umbral inválido, se usará el valor por defecto (5).")
        umbral_minimo_stock = 5

    return filtro_codigo, filtro_nombre_parcial, filtro_categoria, umbral_minimo_stock

def ejecutar_inventario_interactivo():
    """Ejecuta el sistema de inventario de forma interactiva."""
    inventario = Inventario()

    while True:
        print("\n--- Sistema de Gestión de Inventario ECOMARKET (Menú Principal) ---")
        print("1. CU01 - Registrar nuevo producto")
        print("2. CU02 - Registrar entrada de producto (compra/reposición)")
        print("3. CU03 - Registrar salida de stock (despacho/venta)")
        print("4. CU04 - Consultar stock en tiempo real")
        print("5. CU05 - Reporte de bajo stock y generación de CSV")
        print("6. CU06 - Control de inventario y cálculo de valor total")
        print("7. Ver Inventario Actual completo") # Conveniencia
        print("8. Ver Historial de Movimientos completo") # Conveniencia
        print("9. Salir del programa")
        
        opcion = input("Seleccione una opción: ").strip()

        if opcion == '1':
            codigo, nombre, categoria, cantidad_inicial, ubicacion, precio_unitario = solicitar_datos_producto()
            resultado = inventario.registrar_producto(codigo, nombre, categoria, cantidad_inicial, ubicacion, precio_unitario)
            
            if isinstance(resultado, dict) and "resumen" in resultado:
                print(resultado["mensaje"])
                print("--- Resumen del Producto Creado ---")
                for key, value in resultado["resumen"].items():
                    print(f"{key}: {value}")
            else:
                print(resultado)
        
        elif opcion == '2':
            codigo_prod, cantidad_ing, num_doc = solicitar_datos_entrada_producto()
            mensaje = inventario.registrar_entrada_producto(codigo_prod, cantidad_ing, num_doc)
            print(mensaje)

        elif opcion == '3':
            codigo_prod, cantidad_ret, ref_ped, resp = solicitar_datos_salida_producto()
            mensaje = inventario.registrar_salida_producto(codigo_prod, cantidad_ret, ref_ped, resp)
            print(mensaje)
        
        elif opcion == '4':
            filtro_cod, filtro_nom, filtro_cat, umbral_min = solicitar_parametros_consulta_stock()
            productos_hallados, metricas_consulta = inventario.consultar_stock(
                filtro_codigo=filtro_cod,
                filtro_nombre_parcial=filtro_nom,
                filtro_categoria=filtro_cat,
                umbral_minimo_stock=umbral_min
            )
            print("\n--- Resultados de la Consulta ---")
            if productos_hallados:
                for prod in productos_hallados:
                    print(f"  Código: {prod['codigo']}, Nombre: {prod['nombre']}, Cantidad: {prod['cantidad']}, Ubicación: {prod['ubicacion']}")
                print(f"\nTotal de productos encontrados: {len(productos_hallados)}")
                print(f"Stock total de los productos encontrados: {metricas_consulta['stock_total_encontrado']}")
                print(f"Productos bajo el umbral de bajo stock ({umbral_min}): {metricas_consulta['productos_bajo_minimo']}")
            else:
                print("No se encontraron productos que coincidan con los filtros.")
            print("---------------------------------\n")

        elif opcion == '5':
            inventario.generar_reporte_completo()
            exportar = input("¿Desea exportar el reporte a un archivo CSV? (s/n): ").strip().lower()
            if exportar == 's':
                filename = input("Ingrese el nombre del archivo CSV (ej. mi_reporte.csv): ").strip()
                if not filename: filename = "reporte_inventario.csv"
                inventario.exportar_reporte_csv(filename)
            
        elif opcion == '6':
            umbral_str = input("Ingrese el umbral de valor para el recargo (ej. 10000, por defecto): ").strip()
            try:
                umbral = float(umbral_str) if umbral_str else 10000.0
                if umbral < 0:
                    print("El umbral no puede ser negativo, se usará el valor por defecto (10000.0).")
                    umbral = 10000.0
            except ValueError:
                print("Umbral inválido, se usará el valor por defecto (10000.0).")
                umbral = 10000.0

            recargo_str = input("Ingrese el porcentaje de recargo (ej. 8 para 8%, por defecto): ").strip()
            try:
                recargo_porcentaje = float(recargo_str) / 100 if recargo_str else 0.08
                if not (0 <= recargo_porcentaje <= 1):
                     print("El porcentaje de recargo debe estar entre 0 y 100, se usará el valor por defecto (8%).")
                     recargo_porcentaje = 0.08
            except ValueError:
                print("Porcentaje de recargo inválido, se usará el valor por defecto (8%).")
                recargo_porcentaje = 0.08

            print(inventario.calcular_valor_total_inventario(umbral_valor=umbral, recargo_porcentaje=recargo_porcentaje))

        elif opcion == '7':
            inventario.mostrar_inventario()

        elif opcion == '8':
            inventario.mostrar_historial_movimientos()
        
        elif opcion == '9':
            print("Saliendo del sistema de inventario. ¡Hasta luego!")
            break
        
        else:
            print("Opción no válida. Por favor, seleccione una opción del menú.")

# --- Iniciar el sistema interactivo ---
if __name__ == "__main__":
    ejecutar_inventario_interactivo()
