#!/usr/bin/env python3
"""
IRONGRIP WhatsApp AI Agent
Responde automáticamente a mensajes de clientes en español
Captura reservas con S/10 de pre-venta
Guarda datos en CSV para exportar a Google Sheet
"""

from flask import Flask, request
from twilio.rest import Client
import os
import json
import csv
from datetime import datetime

# Configuración de Twilio
ACCOUNT_SID = "AC50e23fd6ae7013a5b4d0bc50b681e7a3"
AUTH_TOKEN = "d4fafb37ec1eb8168abb893f6c0cdcfc9"
TWILIO_WHATSAPP_NUMBER = "whatsapp:+1415523886"  # Número de Twilio
YOUR_WHATSAPP_NUMBER = "whatsapp:+51946867808"   # Tu número para recibir mensajes
PLIN_NUMBER = "991993723"
CSV_FILE = "irongrip_reservas.csv"

client = Client(ACCOUNT_SID, AUTH_TOKEN)
app = Flask(__name__)

# Base de datos simple para guardar reservas
reservas = {}

# Estados de conversación
ESTADOS = {
    "INICIO": 0,
    "ESPERANDO_NOMBRE": 1,
    "ESPERANDO_UBICACION": 2,
    "ESPERANDO_DNI": 3,
    "CONFIRMADO": 4
}

def inicializar_csv():
    """Crea el archivo CSV si no existe"""
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Número de Seguimiento',
                'Nombre',
                'DNI',
                'Ubicación',
                'Monto Pagado (S/)',
                'Fecha de Pago',
                'Estado'
            ])

def obtener_proximo_numero_seguimiento():
    """Genera el próximo número de seguimiento (IRONGRIP-001, IRONGRIP-002, etc.)"""
    inicializar_csv()
    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            lineas = list(reader)
            numero = len(lineas) + 1
            return f"IRONGRIP-{numero:03d}"
    except:
        return "IRONGRIP-001"

def guardar_reserva_csv(nombre, dni, ubicacion):
    """Guarda la reserva en CSV"""
    inicializar_csv()
    numero_seguimiento = obtener_proximo_numero_seguimiento()
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            numero_seguimiento,
            nombre,
            dni if dni else "Pendiente",
            ubicacion,
            "10.00",
            fecha,
            "Pendiente de Pago"
        ])
    
    return numero_seguimiento

def obtener_estado_cliente(numero):
    """Obtiene el estado actual de un cliente"""
    if numero not in reservas:
        reservas[numero] = {
            "estado": ESTADOS["INICIO"],
            "nombre": None,
            "dni": None,
            "ubicacion": None,
            "timestamp": datetime.now().isoformat()
        }
    return reservas[numero]

def responder_whatsapp(numero_cliente, mensaje):
    """Envía respuesta a cliente por WhatsApp"""
    try:
        message = client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body=mensaje,
            to=numero_cliente
        )
        print(f"Mensaje enviado a {numero_cliente}: {message.sid}")
        return True
    except Exception as e:
        print(f"Error enviando mensaje: {e}")
        return False

def generar_respuesta_ia(texto_cliente, estado_cliente):
    """Genera respuesta automática basada en el estado de la conversación"""
    
    numero = estado_cliente.get("numero")
    estado = estado_cliente.get("estado")
    
    # ESTADO 0: Primer mensaje - Bienvenida
    if estado == ESTADOS["INICIO"]:
        estado_cliente["estado"] = ESTADOS["ESPERANDO_NOMBRE"]
        return """Hola 👋

¡Gracias por tu interés en IRONGRIP! 💪

IMPORTANTE: El PRIMER LOTE se agotó 😅

PERO: Puedes RESERVAR el tuyo AHORA con solo S/10 soles 🦵

📦 CRONOGRAMA:
✅ El segundo lote llega en: 2 SEMANAS
💳 Puedes pagar hasta: 13 DÍAS antes que llegue
🎁 Serás de los PRIMEROS en recibirlo

💰 Pre-venta: S/49.90 (Después subirá a S/69.90)

📝 Para reservar, confirma tu:
• Nombre y Apellido
• DNI
• Ubicación (Tu distrito)

¿Cuál es tu nombre? 👇"""
    
    # ESTADO 1: Esperando nombre
    elif estado == ESTADOS["ESPERANDO_NOMBRE"]:
        estado_cliente["nombre"] = texto_cliente
        estado_cliente["estado"] = ESTADOS["ESPERANDO_DNI"]
        return f"""Gracias {texto_cliente} 😊

¿Cuál es tu DNI? 📝"""
    
    # ESTADO 2: Esperando DNI
    elif estado == ESTADOS["ESPERANDO_DNI"]:
        estado_cliente["dni"] = texto_cliente
        estado_cliente["estado"] = ESTADOS["ESPERANDO_UBICACION"]
        return f"""Perfecto 👍

¿De qué distrito eres? 📍
(Ejemplo: Lima, San Isidro, Surco, Quillabamba, etc.)"""
    
    # ESTADO 3: Esperando ubicación
    elif estado == ESTADOS["ESPERANDO_UBICACION"]:
        estado_cliente["ubicacion"] = texto_cliente
        estado_cliente["estado"] = ESTADOS["CONFIRMADO"]
        
        nombre = estado_cliente.get("nombre", "Cliente")
        dni = estado_cliente.get("dni", "No especificado")
        ubicacion = texto_cliente
        
        # Guardar en CSV y obtener número de seguimiento
        numero_seguimiento = guardar_reserva_csv(nombre, dni, ubicacion)
        
        return f"""¡PERFECTO {nombre.upper()}! ✅

Tu reserva está CONFIRMADA 📋

🆔 Número de Seguimiento: {numero_seguimiento}

📌 Detalles de tu Reserva:
• Nombre: {nombre}
• DNI: {dni}
• Ubicación: {ubicacion}
• Monto de reserva: S/10 soles
• Precio final: S/49.90 (pre-venta)

⏰ IMPORTANTE - Cronograma:
📦 El segundo lote llega en: 2 SEMANAS
💳 Puedes hacer el pago hasta: 13 DÍAS antes que llegue
✅ Serás de los PRIMEROS en recibirlo

💸 PAGA TU RESERVA (S/10) POR PLIN:
👉 {PLIN_NUMBER}

📸 Después de pagar, responde con foto del comprobante.

Usa tu número de seguimiento: {numero_seguimiento}

¡Gracias por tu confianza {nombre}! 🦵💪"""
    
    # ESTADO 4: Confirmado
    else:
        nombre = estado_cliente.get('nombre', 'amigo')
        numero_seguimiento = estado_cliente.get('numero_seguimiento', 'IRONGRIP-XXX')
        return f"""Gracias {nombre} 🙌

Estamos esperando tu comprobante de pago en PLIN.

Tu número de seguimiento: {numero_seguimiento}

Cuando confirmes el pago, recibirás:
✅ Confirmación de reserva
✅ Fecha exacta de entrega
✅ Soporte personalizado

¿Algo más en lo que pueda ayudarte? 💪"""

@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    """Webhook que recibe mensajes de WhatsApp"""
    
    try:
        # Obtener datos del mensaje
        incoming_msg = request.values.get("Body", "").strip()
        sender_number = request.values.get("From", "")
        
        print(f"Mensaje recibido de {sender_number}: {incoming_msg}")
        
        # Obtener estado del cliente
        estado_cliente = obtener_estado_cliente(sender_number)
        estado_cliente["numero"] = sender_number
        
        # Generar respuesta
        respuesta = generar_respuesta_ia(incoming_msg, estado_cliente)
        
        # Enviar respuesta
        responder_whatsapp(sender_number, respuesta)
        
        # Guardar reserva
        with open("reservas.json", "a") as f:
            f.write(json.dumps({
                "numero": sender_number,
                "datos": estado_cliente,
                "timestamp": datetime.now().isoformat()
            }) + "\n")
        
        return ("", 200)
    
    except Exception as e:
        print(f"Error en webhook: {e}")
        return ("Error", 500)

@app.route("/", methods=["GET"])
def health():
    """Health check"""
    inicializar_csv()
    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            num_reservas = len(list(reader))
    except:
        num_reservas = 0
    
    return {
        "status": "AI WhatsApp Agent IRONGRIP activo ✅",
        "account": ACCOUNT_SID[:10] + "...",
        "archivo_csv": CSV_FILE,
        "total_reservas": num_reservas,
        "instrucciones": "Descarga irongrip_reservas.csv y sube a Google Sheet"
    }

@app.route("/reservas", methods=["GET"])
def ver_reservas():
    """Ver todas las reservas en CSV"""
    try:
        inicializar_csv()
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            contenido = f.read()
        return {
            "status": "✅ Reservas guardadas",
            "archivo": CSV_FILE,
            "datos": contenido
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════╗
    ║   IRONGRIP WhatsApp AI Agent      ║
    ║   Status: 🟢 ACTIVO               ║
    ║                                    ║
    ║   Account: AC50e23fd6ae7...       ║
    ║   Número: +51946867808            ║
    ║   Plin: 991993723                 ║
    ╚════════════════════════════════════╝
    """)
    
    # Ejecutar en puerto 5000
    app.run(debug=True, port=5000)
