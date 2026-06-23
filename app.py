from flask import Flask, render_template_string
from flask_socketio import SocketIO, send
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import os
import threading
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chat123'
socketio = SocketIO(app, cors_allowed_origins="*")

# --- HTML DEL CHAT WEB (SOPORTE FARMACIA) ---
HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Farmacia Online</title>
    <style>
        :root {
            --bg-main: #0b141a;
            --bg-panel: #202c33;
            --bg-input: #2a3942;
            --accent: #00f2ff;
            --text-white: #e9edef;
            --msg-sent: #005c4b;
        }
        body { 
            margin: 0; 
            font-family: "Segoe UI", sans-serif; 
            background: var(--bg-main); 
            color: var(--text-white);
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .chat-container { 
            width: 100%;
            max-width: 450px; 
            height: 90vh; 
            display: flex; 
            flex-direction: column; 
            border-radius: 12px; 
            overflow: hidden; 
            background: var(--bg-main); 
            border: 1px solid rgba(0, 242, 255, 0.25); 
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
        }
        .chat-header { 
            background: var(--bg-panel); 
            padding: 18px; 
            text-align: center; 
            font-weight: 600; 
            color: var(--accent);
            font-size: 1.1rem;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        .welcome-screen {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            flex: 1;
            padding: 30px;
            text-align: center;
        }
        .welcome-screen p {
            color: #8696a0;
            margin-bottom: 24px;
        }
        .ux-input {
            width: 100%;
            max-width: 280px;
            padding: 14px;
            border-radius: 8px;
            border: 1px solid var(--bg-input);
            background: var(--bg-input);
            color: white;
            outline: none;
            font-size: 1rem;
            text-align: center;
            transition: border 0.3s;
        }
        .ux-input:focus {
            border-color: var(--accent);
        }
        .ux-btn {
            width: 100%;
            max-width: 280px;
            margin-top: 15px;
            padding: 14px;
            border-radius: 8px;
            border: none;
            background: var(--accent);
            color: #000;
            font-weight: bold;
            font-size: 1rem;
            cursor: pointer;
            transition: transform 0.1s, opacity 0.2s;
        }
        .ux-btn:active {
            transform: scale(0.98);
        }
        .chat-view {
            display: none;
            flex-direction: column;
            flex: 1;
            overflow: hidden;
        }
        .chat-messages { 
            flex: 1; 
            padding: 20px; 
            overflow-y: auto; 
            background-image: url('https://user-images.githubusercontent.com/15075759/28719144-86dc0f70-73b1-11e7-911d-60d70fcded21.png'); 
            background-blend-mode: overlay;
            display: flex; 
            flex-direction: column; 
        }
        .message { 
            max-width: 75%; 
            padding: 9px 14px; 
            margin: 6px 0; 
            border-radius: 12px; 
            word-wrap: break-word; 
            font-size: 0.95rem;
            line-height: 1.4;
            box-shadow: 0 1px 1px rgba(0,0,0,0.2);
        }
        .sent { 
            background: var(--msg-sent); 
            align-self: flex-end; 
            border-top-right-radius: 2px;
        }
        .received { 
            background: var(--bg-panel); 
            align-self: flex-start; 
            border-top-left-radius: 2px;
        }
        .chat-input-area { 
            display: flex; 
            padding: 12px; 
            background: var(--bg-panel); 
            align-items: center;
            gap: 10px;
        }
        .chat-input-area input { 
            flex: 1; 
            padding: 12px 16px; 
            border-radius: 24px; 
            border: none; 
            background: var(--bg-input); 
            color: white; 
            outline: none; 
            font-size: 0.95rem;
        }
        .send-btn { 
            background: var(--accent);
            border: none;
            color: #000;
            width: 44px;
            height: 44px;
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            cursor: pointer;
            transition: transform 0.2s;
            flex-shrink: 0;
        }
        .send-btn:hover {
            transform: scale(1.05);
        }
        .send-btn svg {
            width: 18px;
            height: 18px;
            fill: currentColor;
            margin-left: 2px; 
        }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-thumb { background: rgba(0, 242, 255, 0.2); border-radius: 10px; }
        .pharmacy-badge {
            background: #00b894;
            color: white;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.7rem;
            margin-left: 8px;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            💊 Farmacia Online
            <span class="pharmacy-badge">🏥 Atención 24/7</span>
        </div>
        <div id="welcomeScreen" class="welcome-screen">
            <h3>¿Cuál es tu nombre?</h3>
            <p>Ingresa tu nombre para atención personalizada</p>
            <input type="text" id="nombre" class="ux-input" placeholder="Ingresa tu nombre" autofocus onkeypress="if(event.key === 'Enter') ingresarAlChat()">
            <button class="ux-btn" onclick="ingresarAlChat()">Continuar</button>
        </div>
        <div id="chatView" class="chat-view">
            <div id="chat" class="chat-messages"></div>
            <div class="chat-input-area">
                <input type="text" id="mensaje" placeholder="Escribe tu mensaje..." onkeypress="if(event.key === 'Enter') enviar()">
                <button class="send-btn" onclick="enviar()" aria-label="Enviar mensaje">
                    <svg viewBox="0 0 24 24"><path d="M2,21L23,12L2,3V10L17,12L2,14V21Z"/></svg>
                </button>
            </div>
        </div>
    </div>
    <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
    <script>
        var socket = io();
        var miNombre = "";
        function ingresarAlChat() {
            var nombreInput = document.getElementById("nombre");
            miNombre = nombreInput.value.trim();
            if (miNombre === "") {
                nombreInput.style.border = "1px solid red"; 
                nombreInput.placeholder = "¡El nombre es obligatorio!";
                return;
            }
            document.getElementById("welcomeScreen").style.display = "none";
            document.getElementById("chatView").style.display = "flex";
            document.getElementById("mensaje").focus();
        }
        function enviar() {
            var mensajeInput = document.getElementById("mensaje");
            var mensaje = mensajeInput.value.trim();
            if (mensaje === "") return; 
            socket.emit("message", miNombre + ": " + mensaje);
            mensajeInput.value = "";
        }
        socket.on("message", function (msg) {
            var chat = document.getElementById("chat");
            var div = document.createElement("div");
            div.classList.add("message");
            if (msg.startsWith(miNombre + ":")) {
                div.classList.add("sent");
                div.innerText = msg.replace(miNombre + ":", "Tú:");
            } else {
                div.classList.add("received");
                div.innerText = msg;
            }
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight; 
        });
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

# --- Evento mensajes del chat web ---
@socketio.on("message")
def handle_message(msg):
    print("Mensaje en chat web:", msg)
    socketio.emit('message', msg, broadcast=True)

# ============================================
# 🚀 CONFIGURACIÓN DEL BOT DE TELEGRAM - FARMACIA
# ============================================

TOKEN = "8295340694:AAF320uTXJvsCIfJN2t3PLBneoGakHRKSPo"

# Base de datos del carrito
carritos = {}

# Base de datos de medicamentos (precios en Bs)
MEDICAMENTOS = {
    "paracetamol": {"nombre": "Paracetamol 500mg", "precio": 8.50, "presentacion": "Tabletas", "stock": 100},
    "ibuprofeno": {"nombre": "Ibuprofeno 400mg", "precio": 10.00, "presentacion": "Tabletas", "stock": 80},
    "aspirina": {"nombre": "Aspirina 100mg", "precio": 6.50, "presentacion": "Tabletas", "stock": 120},
    "omeprazol": {"nombre": "Omeprazol 20mg", "precio": 12.00, "presentacion": "Cápsulas", "stock": 60},
    "loratadina": {"nombre": "Loratadina 10mg", "precio": 9.00, "presentacion": "Tabletas", "stock": 90},
    "amoxicilina": {"nombre": "Amoxicilina 500mg", "precio": 15.00, "presentacion": "Cápsulas", "stock": 50},
    "metformina": {"nombre": "Metformina 850mg", "precio": 11.00, "presentacion": "Tabletas", "stock": 70},
    "vitamina_c": {"nombre": "Vitamina C 1000mg", "precio": 7.00, "presentacion": "Efervescente", "stock": 150}
}

# ============================================
# 🏠 COMANDO /start - MENÚ PRINCIPAL
# ============================================
async def start(update: Update, context):
    nombre = update.message.from_user.first_name
    mensaje = f"""
💊 *¡Bienvenido a Farmacia Plus, {nombre}!*

Tu salud es nuestra prioridad. 
Usa los botones de abajo para explorar:

🛍️ *Productos* - Ver catálogo de medicamentos
💰 *Precios* - Lista de precios actualizada
🔍 *Buscar* - Encuentra tu medicamento
🛒 *Carrito* - Ver tu carrito de compras
💬 *Soporte* - Atención personalizada
⭐ *Sugerencias* - Ayúdanos a mejorar
📞 *Contacto* - Información de contacto
🕐 *Horario* - Horario de atención
🎯 *Promociones* - Ofertas especiales
📋 *Recetas* - Información sobre recetas

*Escribe /ayuda para ver todos los comandos*
"""
    
    keyboard = [
        [InlineKeyboardButton("🛍️ Productos", callback_data="productos")],
        [InlineKeyboardButton("💰 Precios", callback_data="precios")],
        [InlineKeyboardButton("🔍 Buscar Medicamento", callback_data="buscar")],
        [InlineKeyboardButton("🛒 Mi Carrito", callback_data="ver_carrito")],
        [InlineKeyboardButton("💬 Soporte Farmacéutico", callback_data="soporte")],
        [InlineKeyboardButton("📋 Recetas Médicas", callback_data="recetas")],
        [InlineKeyboardButton("🎯 Promociones", callback_data="promociones")],
        [InlineKeyboardButton("⭐ Sugerencias", callback_data="sugerencias")],
        [InlineKeyboardButton("📞 Contacto", callback_data="contacto")],
        [InlineKeyboardButton("🕐 Horario", callback_data="horario")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(mensaje, reply_markup=reply_markup, parse_mode='Markdown')

# ============================================
# 📋 COMANDO /productos - CATÁLOGO
# ============================================
async def productos(update: Update, context):
    mensaje = """
🛍️ *CATÁLOGO DE MEDICAMENTOS* 🛍️

💊 *Medicamentos de venta libre:*
• Paracetamol 500mg - Bs 8.50
• Ibuprofeno 400mg - Bs 10.00
• Aspirina 100mg - Bs 6.50
• Loratadina 10mg - Bs 9.00
• Vitamina C 1000mg - Bs 7.00

💊 *Medicamentos con receta:*
• Omeprazol 20mg - Bs 12.00
• Amoxicilina 500mg - Bs 15.00
• Metformina 850mg - Bs 11.00

🧴 *Productos de cuidado personal:*
• Alcohol en gel - Bs 5.00
• Mascarillas KN95 - Bs 3.00
• Termómetro digital - Bs 15.00

📌 *Todos nuestros productos son 100% originales*
"""
    
    keyboard = [
        [InlineKeyboardButton("🔍 Buscar Medicamento", callback_data="buscar")],
        [InlineKeyboardButton("💰 Ver Precios", callback_data="precios")],
        [InlineKeyboardButton("🏠 Volver al Menú", callback_data="volver_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(mensaje, reply_markup=reply_markup, parse_mode='Markdown')

# ============================================
# 💰 COMANDO /precios - LISTA DE PRECIOS
# ============================================
async def precios(update: Update, context):
    mensaje = """
💰 *LISTA DE PRECIOS* 💰

-----------------------------
💊 *Medicamentos:*

• Paracetamol 500mg - Bs 8.50
• Ibuprofeno 400mg - Bs 10.00
• Aspirina 100mg - Bs 6.50
• Omeprazol 20mg - Bs 12.00
• Loratadina 10mg - Bs 9.00
• Amoxicilina 500mg - Bs 15.00
• Metformina 850mg - Bs 11.00
• Vitamina C 1000mg - Bs 7.00

🧴 *Cuidado personal:*
• Alcohol en gel - Bs 5.00
• Mascarillas KN95 - Bs 3.00
• Termómetro digital - Bs 15.00

-----------------------------
🎯 *Ofertas especiales:*
🔥 Ibuprofeno + Paracetamol = Bs 16.00
🔥 Vitamina C + Mascarillas = Bs 8.00

💳 *Métodos de pago:*
• Efectivo
• Transferencia bancaria
• Tarjeta de crédito/débito
• QR (Pago móvil)

_*Los precios pueden cambiar sin previo aviso*_
"""
    
    keyboard = [
        [InlineKeyboardButton("🛒 Agregar al Carrito", callback_data="agregar_carrito")],
        [InlineKeyboardButton("🎯 Ver Promociones", callback_data="promociones")],
        [InlineKeyboardButton("🏠 Volver al Menú", callback_data="volver_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(mensaje, reply_markup=reply_markup, parse_mode='Markdown')

# ============================================
# 🔍 COMANDO /buscar - BUSCAR MEDICAMENTO
# ============================================
async def buscar(update: Update, context):
    mensaje = """
🔍 *BUSCAR MEDICAMENTO* 🔍

Escribe el nombre del medicamento que buscas:

Ejemplo: `/buscar paracetamol`

🔎 *Medicamentos disponibles:*
• Paracetamol
• Ibuprofeno
• Aspirina
• Omeprazol
• Loratadina
• Amoxicilina
• Metformina
• Vitamina C

*También puedes escribir /productos para ver el catálogo completo*
"""
    await update.message.reply_text(mensaje, parse_mode='Markdown')

async def buscar_medicamento(update: Update, context):
    """Busca un medicamento específico"""
    nombre_buscar = " ".join(context.args).lower()
    
    if not nombre_buscar:
        await update.message.reply_text("❌ Escribe el nombre del medicamento.\nEjemplo: /buscar paracetamol")
        return
    
    encontrados = []
    for clave, medicamento in MEDICAMENTOS.items():
        if nombre_buscar in clave.lower() or nombre_buscar in medicamento["nombre"].lower():
            encontrados.append(medicamento)
    
    if not encontrados:
        await update.message.reply_text(f"❌ No encontramos '{nombre_buscar}'. Usa /productos para ver el catálogo completo.")
        return
    
    mensaje = f"🔍 *Resultados para '{nombre_buscar}':*\n\n"
    for med in encontrados:
        mensaje += f"💊 *{med['nombre']}*\n"
        mensaje += f"💰 Precio: Bs {med['precio']:.2f}\n"
        mensaje += f"📦 Presentación: {med['presentacion']}\n"
        mensaje += f"📊 Stock: {med['stock']} unidades\n\n"
    
    keyboard = [
        [InlineKeyboardButton("🛒 Agregar al Carrito", callback_data=f"agregar_{med['nombre']}")],
        [InlineKeyboardButton("🏠 Volver al Menú", callback_data="volver_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(mensaje, reply_markup=reply_markup, parse_mode='Markdown')

# ============================================
# 🛒 COMANDO /carrito - GESTIÓN DEL CARRITO
# ============================================
async def ver_carrito(update: Update, context):
    user_id = str(update.effective_user.id)
    carrito = carritos.get(user_id, [])
    
    if not carrito:
        mensaje = "🛒 *Tu carrito está vacío*\n\nUsa /precios o /productos para ver los medicamentos y agregar al carrito."
        await update.message.reply_text(mensaje, parse_mode='Markdown')
        return
    
    total = 0
    mensaje = "🛒 *TU CARRITO DE COMPRAS* 🛒\n\n"
    for i, item in enumerate(carrito, 1):
        mensaje += f"{i}. {item['nombre']} - Bs {item['precio']:.2f}\n"
        total += item['precio']
    
    mensaje += f"\n💰 *Total: Bs {total:.2f}*"
    
    keyboard = [
        [InlineKeyboardButton("🗑️ Vaciar Carrito", callback_data="vaciar_carrito")],
        [InlineKeyboardButton("💳 Comprar Ahora", callback_data="comprar")],
        [InlineKeyboardButton("🏠 Volver al Menú", callback_data="volver_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(mensaje, reply_markup=reply_markup, parse_mode='Markdown')

# ============================================
# 💬 COMANDO /soporte - ATENCIÓN PERSONALIZADA
# ============================================
async def soporte(update: Update, context):
    mensaje = """
💬 *SOPORTE FARMACÉUTICO* 💬

¿Necesitas ayuda con algún medicamento?
¿Tienes dudas sobre tu receta?
¿Quieres atención personalizada?

📌 *Chatea con nosotros en tiempo real:*
🔗 [Haz clic aquí para abrir el chat de soporte](https://chat-en-linea22.onrender.com)

⏰ *Horario de atención:*
Lunes a Viernes: 8:00 AM - 8:00 PM
Sábados: 9:00 AM - 6:00 PM
Domingos: 9:00 AM - 2:00 PM

📞 *También puedes contactarnos:*
WhatsApp: +591 77777777
Email: farmacia@plus.com

*¡Tu salud es nuestra prioridad!* 🤝
"""
    
    keyboard = [
        [InlineKeyboardButton("💬 Abrir Chat", url="https://chat-en-linea22.onrender.com")],
        [InlineKeyboardButton("📱 WhatsApp", url="https://wa.me/59177777777")],
        [InlineKeyboardButton("🏠 Volver al Menú", callback_data="volver_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(mensaje, reply_markup=reply_markup, parse_mode='Markdown')

# ============================================
# 📋 COMANDO /recetas - RECETAS MÉDICAS
# ============================================
async def recetas(update: Update, context):
    mensaje = """
📋 *INFORMACIÓN SOBRE RECETAS MÉDICAS* 📋

⚠️ *Importante:*
Algunos medicamentos requieren receta médica obligatoria.

💊 *Medicamentos que requieren receta:*
• Omeprazol 20mg
• Amoxicilina 500mg
• Metformina 850mg

📌 *¿Cómo funciona?*
1. Envía una foto de tu receta médica
2. Nuestro farmacéutico la revisará
3. Confirmaremos tu pedido
4. Puedes retirar o recibir tu medicamento

📸 *Puedes enviarnos la receta por:*
• WhatsApp: +591 77777777
• Email: farmacia@plus.com
• En el chat de soporte

*Tu salud es lo más importante* 💚
"""
    
    keyboard = [
        [InlineKeyboardButton("💬 Enviar Receta", callback_data="soporte")],
        [InlineKeyboardButton("📱 WhatsApp", url="https://wa.me/59177777777")],
        [InlineKeyboardButton("🏠 Volver al Menú", callback_data="volver_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(mensaje, reply_markup=reply_markup, parse_mode='Markdown')

# ============================================
# 🎯 COMANDO /promociones - OFERTAS ESPECIALES
# ============================================
async def promociones(update: Update, context):
    mensaje = """
🎯 *PROMOCIONES ESPECIALES* 🎯

🔥 *Ofertas de la semana:*

📦 *Kit Salud Plus*
• Paracetamol + Ibuprofeno + Vitamina C
💰 *Precio normal: Bs 25.50*
🎉 *Precio oferta: Bs 20.00*
(Ahorras Bs 5.50)

📦 *Kit Protección*
• Mascarillas KN95 (5 unidades)
• Alcohol en gel
💰 *Precio normal: Bs 20.00*
🎉 *Precio oferta: Bs 15.00*
(Ahorras Bs 5.00)

📦 *Kit Digestivo*
• Omeprazol + Metformina
💰 *Precio normal: Bs 23.00*
🎉 *Precio oferta: Bs 18.00*
(Ahorras Bs 5.00)

📅 *Válido hasta el 30 de junio de 2026*
"""
    
    keyboard = [
        [InlineKeyboardButton("🛒 Agregar Promo al Carrito", callback_data="promo_carrito")],
        [InlineKeyboardButton("💰 Ver Precios", callback_data="precios")],
        [InlineKeyboardButton("🏠 Volver al Menú", callback_data="volver_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(mensaje, reply_markup=reply_markup, parse_mode='Markdown')

# ============================================
# ⭐ COMANDO /sugerencias - SUGERENCIAS
# ============================================
async def sugerencias(update: Update, context):
    mensaje = """
⭐ *¡QUEREMOS ESCUCHARTE!* ⭐

Tus sugerencias nos ayudan a mejorar cada día.

📝 *¿Qué te gustaría que agreguemos?*
• Nuevos medicamentos
• Mejores precios
• Promociones especiales
• Mejora en el servicio
• Nuevos horarios

Escribe tu sugerencia:

Ejemplo: `/sugerencias Me gustaría que agreguen más medicamentos para ...`
"""
    await update.message.reply_text(mensaje, parse_mode='Markdown')

async def guardar_sugerencia(update: Update, context):
    sugerencia = " ".join(context.args)
    if not sugerencia:
        await update.message.reply_text("❌ Escribe tu sugerencia.\nEjemplo: /sugerencias Me gustaría ...")
        return
    
    nombre = update.message.from_user.first_name
    mensaje = f"✅ ¡Gracias por tu sugerencia, {nombre}!\n\nTu opinión es muy importante. La revisaremos y te responderemos pronto.\n\n📝 *Tu sugerencia:* {sugerencia}"
    await update.message.reply_text(mensaje, parse_mode='Markdown')

# ============================================
# 📞 COMANDO /contacto
# ============================================
async def contacto(update: Update, context):
    mensaje = """
📞 *INFORMACIÓN DE CONTACTO* 📞

🏪 *Farmacia Plus*
📍 Dirección: Av. Principal #123, La Paz, Bolivia

📱 *Teléfonos:*
• +591 77777777 (WhatsApp)
• +591 22222222 (Llamadas)

📧 *Email:*
farmacia@plus.com

🌐 *Redes Sociales:*
• Instagram: @farmaciaplus
• Facebook: /farmaciaplus

🕐 *Horario de Atención:*
Lun - Vie: 8:00 AM - 8:00 PM
Sáb: 9:00 AM - 6:00 PM
Dom: 9:00 AM - 2:00 PM

🚚 *Entregas a domicilio disponibles*
Área de cobertura: Zona Central de La Paz

*¡Estamos para cuidar tu salud!* 🙌
"""
    
    keyboard = [
        [InlineKeyboardButton("💬 Chat en Vivo", url="https://chat-en-linea22.onrender.com")],
        [InlineKeyboardButton("📱 WhatsApp", url="https://wa.me/59177777777")],
        [InlineKeyboardButton("🏠 Volver al Menú", callback_data="volver_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(mensaje, reply_markup=reply_markup, parse_mode='Markdown')

# ============================================
# 🕐 COMANDO /horario
# ============================================
async def horario(update: Update, context):
    mensaje = """
🕐 *HORARIO DE ATENCIÓN* 🕐

🏪 *Farmacia Plus*

📅 *Lunes a Viernes:*
8:00 AM - 8:00 PM

📅 *Sábados:*
9:00 AM - 6:00 PM

📅 *Domingos:*
9:00 AM - 2:00 PM

🚚 *Entregas a domicilio:*
Lun - Vie: 8:00 AM - 8:00 PM
Sáb: 9:00 AM - 6:00 PM

📌 *Emergencias las 24/7*
Llama al: +591 77777777

*¡Tu salud no espera!* 💚
"""
    
    keyboard = [
        [InlineKeyboardButton("📱 Contactar", callback_data="contacto")],
        [InlineKeyboardButton("🏠 Volver al Menú", callback_data="volver_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(mensaje, reply_markup=reply_markup, parse_mode='Markdown')

# ============================================
# 🆘 COMANDO /ayuda - LISTA DE COMANDOS
# ============================================
async def ayuda(update: Update, context):
    mensaje = """
📖 *LISTA DE COMANDOS DISPONIBLES*

🏠 /start - Menú principal
🛍️ /productos - Catálogo de medicamentos
💰 /precios - Lista de precios en Bs
🔍 /buscar [medicamento] - Buscar medicamento
🛒 /carrito - Ver mi carrito de compras
💬 /soporte - Atención personalizada
📋 /recetas - Información sobre recetas
🎯 /promociones - Ofertas especiales
⭐ /sugerencias [texto] - Enviar sugerencia
📞 /contacto - Información de contacto
🕐 /horario - Horario de atención
🆘 /ayuda - Mostrar esta ayuda

🤖 *Consejo:* Usa los botones para navegar más fácil.
"""
    await update.message.reply_text(mensaje, parse_mode='Markdown')

# ============================================
# 🔘 MANEJADOR DE BOTONES (Callbacks)
# ============================================
async def botones(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "volver_menu":
        await start(update, context)
    
    elif data == "productos":
        await productos(update, context)
    
    elif data == "precios":
        await precios(update, context)
    
    elif data == "buscar":
        await buscar(update, context)
    
    elif data == "ver_carrito":
        await ver_carrito(update, context)
    
    elif data == "soporte":
        await soporte(update, context)
    
    elif data == "recetas":
        await recetas(update, context)
    
    elif data == "promociones":
        await promociones(update, context)
    
    elif data == "sugerencias":
        await sugerencias(update, context)
    
    elif data == "contacto":
        await contacto(update, context)
    
    elif data == "horario":
        await horario(update, context)
    
    elif data == "agregar_carrito":
        user_id = str(update.effective_user.id)
        if user_id not in carritos:
            carritos[user_id] = []
        carritos[user_id].append({"nombre": "Paracetamol 500mg", "precio": 8.50})
        await query.edit_message_text("✅ Producto agregado al carrito correctamente.\n\nUsa /carrito para ver tu carrito.")
    
    elif data == "promo_carrito":
        user_id = str(update.effective_user.id)
        if user_id not in carritos:
            carritos[user_id] = []
        carritos[user_id].append({"nombre": "Kit Salud Plus (Oferta)", "precio": 20.00})
        await query.edit_message_text("✅ Kit Salud Plus agregado al carrito correctamente.\n\nUsa /carrito para ver tu carrito.")
    
    elif data == "vaciar_carrito":
        user_id = str(update.effective_user.id)
        carritos[user_id] = []
        await query.edit_message_text("🗑️ Tu carrito ha sido vaciado.")
    
    elif data == "comprar":
        user_id = str(update.effective_user.id)
        if user_id in carritos:
            total = sum(item['precio'] for item in carritos[user_id])
            carritos[user_id] = []
            await query.edit_message_text(f"🎉 ¡Gracias por tu compra!\n\nTotal: Bs {total:.2f}\n\nTe contactaremos pronto para confirmar tu pedido.\n\n¿Quieres seguir comprando? Usa /start")
        else:
            await query.edit_message_text("❌ Tu carrito está vacío.")

# ============================================
# 🚀 INICIAR EL BOT
# ============================================
def run_telegram():
    if not TOKEN or TOKEN == "TU_TOKEN_AQUI":
        print("⚠️ No hay token de Telegram configurado.")
        return
    
    try:
        app_tg = Application.builder().token(TOKEN).build()
        
        # Comandos
        app_tg.add_handler(CommandHandler("start", start))
        app_tg.add_handler(CommandHandler("productos", productos))
        app_tg.add_handler(CommandHandler("precios", precios))
        app_tg.add_handler(CommandHandler("buscar", buscar_medicamento))
        app_tg.add_handler(CommandHandler("carrito", ver_carrito))
        app_tg.add_handler(CommandHandler("soporte", soporte))
        app_tg.add_handler(CommandHandler("recetas", recetas))
        app_tg.add_handler(CommandHandler("promociones", promociones))
        app_tg.add_handler(CommandHandler("sugerencias", guardar_sugerencia))
        app_tg.add_handler(CommandHandler("contacto", contacto))
        app_tg.add_handler(CommandHandler("horario", horario))
        app_tg.add_handler(CommandHandler("ayuda", ayuda))
        
        # Botones
        app_tg.add_handler(CallbackQueryHandler(botones))
        
        print("🤖 Bot de Telegram iniciado correctamente")
        app_tg.run_polling()
    except Exception as e:
        print(f"❌ Error al iniciar Telegram: {e}")

# ============================================
# 🚀 EJECUTAR FLASK + TELEGRAM
# ============================================
if __name__ == "__main__":
    thread = threading.Thread(target=run_telegram)
    thread.daemon = True
    thread.start()
    
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port, debug=False)