from flask import Flask, request, jsonify
from escpos.printer import Usb
import logging
import os

app = Flask(__name__)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='printer_client.log', 
                    filemode='a')

# --- IMPORTANTE: Reemplaza estos valores con los de tu impresora ---
# Cómo obtener idVendor y idProduct:
# 1. Conecta la impresora USB a tu máquina Windows 10.
# 2. Abre el "Administrador de Dispositivos" (clic derecho en el botón de Inicio -> Administrador de Dispositivos).
# 3. Busca tu impresora. Podría estar bajo "Controladoras de bus serie universal",
#    "Dispositivos de interfaz de usuario" o "Impresoras".
#    Si no la encuentras fácilmente por su nombre, busca un dispositivo USB que aparezca cuando la conectas/desconectas.
# 4. Haz clic derecho en el dispositivo de tu impresora y selecciona "Propiedades".
# 5. Ve a la pestaña "Detalles".
# 6. En el menú desplegable "Propiedad", selecciona "Id. de hardware".
# 7. Verás una cadena como "USB\VID_XXXX&PID_YYYY&MI_ZZ".
#    "XXXX" es tu idVendor (Vendor ID) y "YYYY" es tu idProduct (Product ID).
#    Asegúrate de copiar solo los valores hexadecimales (sin el '0x' inicial), y luego agrégales '0x' en el código.
# Ejemplo: si es USB\VID_04B8&PID_0E1F, entonces idVendor=0x04B8, idProduct=0x0E1F
PRINTER_VENDOR_ID = 0x28E9  
PRINTER_PRODUCT_ID = 0x0289 
# -----------------------------------------------------------------

@app.route('/imprimir_comanda', methods=['POST'])
def imprimir_comanda():
    data = request.get_json()
    
    if not data:
        logging.warning("Received empty print data.")
        return jsonify({"error": "No se recibieron datos para imprimir."}), 400

    try:
        p = Usb(PRINTER_VENDOR_ID, PRINTER_PRODUCT_ID)
        logging.info("Impresora USB conectada exitosamente.")

        # --- ID del pedido (centrado, grande) ---
        p.set(align='center', custom_size=True, width=3, height=3)
        p.text(f"ID: {data['numero_pedido']}\n\n")

        # --- Lista de productos (alineado a la izquierda, tamaño medio) ---
        p.set(align='left', custom_size=True, width=2, height=2)
        for prod in data['productos_detalle']:
            cantidad = int(prod['cantidad_producto'])
            nombre = prod['nombre_producto']
            p.text(f"{cantidad} {nombre}\n")
        p.text("\n")

        # --- Hora de retiro (centrado, tamaño medio) ---
        p.set(align='center', custom_size=True, width=2, height=2)
        p.text(f"{data['para_hora']}\n\n")

        # --- Nombre del cliente (pequeño, alineado a la izquierda) ---
        #p.set(align='left', font='a', custom_size=True, width=1, height=1)
        #p.text(f"{data['cliente']}\n")

        p.cut()
        p.close()
        
        logging.info("Comanda impresa exitosamente.")
        return jsonify({"message": "Comanda impresa exitosamente"}), 200

    except Exception as e:
        error_message = f"Error al imprimir comanda: {e}"
        logging.error(error_message, exc_info=True) 
        return jsonify({"error": error_message}), 500

if __name__ == '__main__':
    # Obtener la IP fija de la máquina de la rotisería si es posible,
    # o usar '0.0.0.0' para escuchar en todas las interfaces (menos seguro si no hay firewall).
    # Ajusta el puerto si es necesario.
    host_ip = os.environ.get('PRINTER_CLIENT_HOST', '0.0.0.0') # Puede leerse de una variable de entorno
    port = int(os.environ.get('PRINTER_CLIENT_PORT', 5000)) # Puede leerse de una variable de entorno
    
    logging.info(f"Cliente impresor iniciado en http://{host_ip}:{port}")
    #app.run(host=host_ip, port=port)
    app.run(host='192.168.1.16', port=5000, debug=True)
