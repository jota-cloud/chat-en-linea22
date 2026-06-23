from flask import Flask, render_template_string
from flask_socketio import SocketIO, send
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import os
import threading
import asyncio

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chat123'
socketio = SocketIO(app, cors_allowed_origins="*")

# ============================================
# HTML del chat web (tu diseño original)
# ============================================

HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chatroom Pro</title>
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
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">💬 Chatroom Pro 🤖</div>
        <div id="welcomeScreen" class="welcome-screen">
            <h3>¿Cuál es tu nombre?</h3>
            <p>Ingresa un apodo para empezar a chatear</p>
            <input type="text" id="nombre" class="ux-input" placeholder="Ingresa tu nombre o un apodo" autofocus onkeypress="if(event.key === 'Enter') ingresarAlChat()">
            <button class="ux-btn" onclick="ingresarAlChat()">Continuar</button>
        </div>
        <div id="chatView" class="chat-view">
            <div id="chat" class="chat-messages"></div>
            <div class="chat-input-area">
                <input type="text" id="mensaje" placeholder="Escribe un mensaje..." onkeypress="if(event.key === 'Enter') enviar()">
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

# ============================================
# VARIABLES GLOBALES DEL BOT
# ============================================

TOKEN = "8295340694:AAF320uTXJvsCIfJN2t3PLBneoGakHRKSPo"
CHAT_ID = "6496673921"  # <-- REEMPLAZA CON TU ID DE TELEGRAM

# Variable global para la aplicación del bot
telegram_app = None

carritos = {}

# ============================================
# FUNCIONES DEL BOT DE TELEGRAM
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nombre = update.message.from_user.first_name
    mensaje = f"""
🤖 *¡Bienvenido a tu Chat, {nombre}!*

Usa los botones de abajo para navegar:

💬 *Soporte* - Atención personalizada
🛒 *Carrito* - Ver tu carrito
💰 *Precios* - Lista de precios
📞 *Contacto* - Información de contacto
🆘 *Ayuda* - Comandos disponibles
"""
    keyboard = [
        [InlineKeyboardButton("💬 Soporte", callback_data="soporte")],
        [InlineKeyboardButton("🛒 Carrito", callback_data="carrito")],
        [InlineKeyboardButton("💰 Precios", callback_data="precios")],
        [InlineKeyboardButton("📞 Contacto", callback_data="contacto")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(mensaje, reply_markup=reply_markup, parse_mode='Markdown')

async def soporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = """
💬 *Soporte Personalizado*

📌 Chatea con nosotros en tiempo real:
🔗 https://chat-en-linea22.onrender.com

📱 WhatsApp: +591 77777777
"""
    await update.message.reply_text(mensaje, parse_mode='Markdown')

async def carrito(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    carrito = carritos.get(user_id, [])
    if not carrito:
        await update.message.reply_text("🛒 Tu carrito está vacío.")
        return
    mensaje = "🛒 *Tu Carrito:*\n\n"
    for item in carrito:
        mensaje += f"• {item}\n"
    await update.message.reply_text(mensaje, parse_mode='Markdown')

async def precios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = """
💰 *Lista de Precios:*

• Producto A: Bs 10.00
• Producto B: Bs 15.00
• Producto C: Bs 20.00
"""
    await update.message.reply_text(mensaje, parse_mode='Markdown')

async def contacto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = """
📞 *Contacto:*

📱 WhatsApp: +591 77777777
📧 Email: contacto@chat.com
🌐 Web: https://chat-en-linea22.onrender.com
"""
    await update.message.reply_text(mensaje, parse_mode='Markdown')

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = """
📖 *Comandos disponibles:*

/start - Menú principal
/soporte - Atención personalizada
/carrito - Ver carrito
/precios - Lista de precios
/contacto - Información de contacto
/ayuda - Mostrar esta ayuda
"""
    await update.message.reply_text(mensaje, parse_mode='Markdown')

async def manejar_mensaje_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cuando alguien escribe un mensaje al bot (no comando), lo reenvía al chat web."""
    texto = update.message.text
    nombre = update.message.from_user.first_name
    msg_para_chat = f"🤖 Bot ({nombre}): {texto}"
    # Emitir al chat web vía SocketIO
    socketio.emit('message', msg_para_chat, broadcast=True)
    await update.message.reply_text("✅ Tu mensaje fue enviado al chat web.")

async def botones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "soporte":
        await soporte(update, context)
    elif data == "carrito":
        await carrito(update, context)
    elif data == "precios":
        await precios(update, context)
    elif data == "contacto":
        await contacto(update, context)

# ============================================
# FUNCIÓN PARA ENVIAR MENSAJE DEL CHAT WEB AL BOT
# ============================================

def enviar_a_telegram(mensaje):
    """Envía un mensaje desde el chat web al bot (a un chat de Telegram específico)."""
    if telegram_app is None or CHAT_ID == "TU_CHAT_ID":
        print("⚠️ Bot no iniciado o CHAT_ID no configurado.")
        return
    try:
        # Crear una tarea asíncrona para no bloquear
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(telegram_app.bot.send_message(chat_id=CHAT_ID, text=f"📱 Chat Web: {mensaje}"))
        loop.close()
    except Exception as e:
        print(f"Error al enviar a Telegram: {e}")

# ============================================
# MANEJADOR DE MENSAJES DEL CHAT WEB
# ============================================

@socketio.on("message")
def handle_message(msg):
    print(f"Mensaje en chat web: {msg}")
    # Reenviar al bot de Telegram si no es un mensaje del propio bot
    if not msg.startswith("🤖 Bot:"):
        enviar_a_telegram(msg)
    # Retransmitir a todos los clientes del chat web
    send(msg, broadcast=True)

# ============================================
# INICIO DEL BOT DE TELEGRAM (en hilo separado)
# ============================================

def run_telegram():
    global telegram_app
    try:
        application = Application.builder().token(TOKEN).build()
        telegram_app = application

        # Comandos
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("soporte", soporte))
        application.add_handler(CommandHandler("carrito", carrito))
        application.add_handler(CommandHandler("precios", precios))
        application.add_handler(CommandHandler("contacto", contacto))
        application.add_handler(CommandHandler("ayuda", ayuda))

        # Manejador de mensajes de texto (no comandos)
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje_telegram))

        # Manejador de botones (callbacks)
        application.add_handler(CallbackQueryHandler(botones))

        print("🤖 Bot de Telegram iniciando...")
        # Ejecutar el polling de forma síncrona (bloquea el hilo)
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        print(f"❌ Error en Telegram: {e}")

# ============================================
# PUNTO DE ENTRADA PRINCIPAL
# ============================================

if __name__ == "__main__":
    # Iniciar bot en un hilo separado
    telegram_thread = threading.Thread(target=run_telegram, daemon=True)
    telegram_thread.start()

    # Iniciar servidor web (Flask + SocketIO)
    port = int(os.environ.get("PORT", 5000))
    socketio.run(
        app,
        host="0.0.0.0",
        port=port,
        debug=False,
        allow_unsafe_werkzeug=True
    )