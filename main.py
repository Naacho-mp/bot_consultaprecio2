from flask import Flask, request
import requests
import telebot
import json
from bs4 import BeautifulSoup

import os

TOKEN_TELEGRAM = os.environ.get("TOKEN_TELEGRAM")

webhook_activado = False

bot = telebot.TeleBot(TOKEN_TELEGRAM)

app = Flask(__name__)

@bot.message_handler(commands=["start"])
def bienvenida(message):
    bot.reply_to(message, "Hola!, Usa /precio1 o /precio2 para buscar precios.")


@app.route("/", methods=["GET"])
def indice():
    return "Bot Activo", 200


@bot.message_handler(commands=["precio1", "precio2"])
def enviar_precio(message):
    bot.reply_to(message, "Buscando el precio, por favor espera...")

    if message.text == "/precio1":
        url_producto = "https://simple.ripley.cl/notebook-gamer-asus-tuf-a15-fa506nc-hn002w-amd-ryzen-5-8gb-ram-512gb-ssd-nvidia-rtx3050-156-2000405435436p?color_80=negro&s=mdco"
    
    elif message.text == "/precio2":
        url_producto = "https://simple.ripley.cl/notebook-asus-vivobook-15-m1502ya-nj741w-amd-ryzen-7-16gb-ram-512gb-ssd-156-2000405435962p?color_80=azul-marino&sein=asus%20vivobook%2015&s=mdco"
    
    else:
        bot.reply_to(message, "Comando no reconocido.")
        return

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
    }

    try:
        response = requests.get(url_producto, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        script_json = soup.find("script", type="application/ld+json")

        if script_json:
            datos = json.loads(script_json.string)
            producto = datos.get("description", "Producto sin nombre")
            precio_internet = datos.get("offers", {}).get("sale_price", None)

            if precio_internet:
                precio_formateado = f"${precio_internet:,}"
                bot.reply_to(message, f"*Producto:* {producto}\n*Precio:* ✨{precio_formateado}✨", parse_mode="Markdown")
            else:
                bot.reply_to(message, "No se pudo encontrar el precio.")
        else:
            bot.reply_to(message, "No se encontró la información del producto en el sitio.")

    except Exception as e:

        print("Error al hacer la busqueda:", e)
        bot.reply_to(message, "Ocurrió un error al obtener el precio.")


@app.route("/" + TOKEN_TELEGRAM, methods = ["POST"])
def webhook():
    json_str = request.stream.read().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "¡OK!", 200

@app.after_request
def activar_webhook(response):
    global webhook_activado
    if not webhook_activado:
        render_hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
        if render_hostname:
            url_webhook = f"https://{render_hostname}/{TOKEN_TELEGRAM}"
            bot.remove_webhook()
            bot.set_webhook(url=url_webhook)
            print(f"✅ Webhook activado: {url_webhook}")
            webhook_activado = True
        else:
            print("⚠️ RENDER_EXTERNAL_HOSTNAME no está definido.")
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
   