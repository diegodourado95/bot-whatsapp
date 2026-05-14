from flask import Flask, request, jsonify
import requests
import threading
import time

app = Flask(__name__)

# ── CONFIG Z-API ──────────────────────────────────────────────────────────────
INSTANCE_ID  = "3F0F6581B6415168D1C6261BBD342883"
TOKEN        = "F8EEBAB3ECDAABD6B1D83FA4"
CLIENT_TOKEN = "F4b2486bf327b4b5e8307e82b483052b6S"
BASE_URL     = f"https://api.z-api.io/instances/{INSTANCE_ID}/token/{TOKEN}"
HEADERS      = {"Client-Token": CLIENT_TOKEN, "Content-Type": "application/json"}

# ── CONFIGURAÇÕES ─────────────────────────────────────────────────────────────
DELAY_SEGUNDOS = 90

RESPOSTA = """Oi! 👋 Que bom que você veio aqui!

Vou te dar um presente por isso 🎨 Vou liberar o Pacote Completo pra você por apenas R$12,90, desconto especial só pra quem chegou até mim pelo WhatsApp.

São 300 dinâmicas, 50 técnicas, 30 projetos, apostila completa e todos os downloads prontos pra imprimir.

👉 https://pay.wiapy.com/txzQTZuLA

Qualquer dúvida é só falar aqui 😊"""

# Gatilhos EXCLUSIVOS de artes — não dispara para alfabetização ou outras ofertas
PALAVRAS_CHAVE_ARTES = [
    "dinâmicas de arte infantil",
    "dinamicas de arte infantil",
    "300 dinâmicas de arte",
    "300 dinamicas de arte",
    "interessada nas dinâmicas de arte",
    "interessada nas dinamicas de arte",
]

# Palavras que BLOQUEIAM a resposta
PALAVRAS_BLOQUEIO = [
    "reembolso",
    "cancelar",
    "cancelamento",
    "devolver",
    "devolução",
    "estorno",
    "alfabetização",
    "alfabetizacao",
]

# Mensagens muito curtas (menos de 15 caracteres) são ignoradas
TAMANHO_MINIMO = 15

ja_respondidos = set()

def deve_responder(mensagem):
    msg_lower = mensagem.lower()

    # Ignora mensagens curtas
    if len(mensagem.strip()) < TAMANHO_MINIMO:
        return False

    # Ignora mensagens com palavras de bloqueio
    if any(p in msg_lower for p in PALAVRAS_BLOQUEIO):
        return False

    # Só responde se tiver gatilho de artes
    return any(p in msg_lower for p in PALAVRAS_CHAVE_ARTES)

def enviar_mensagem(telefone, mensagem):
    url = f"{BASE_URL}/send-text"
    payload = {"phone": telefone, "message": mensagem}
    try:
        resp = requests.post(url, json=payload, headers=HEADERS, timeout=15)
        return resp.status_code
    except Exception as e:
        print(f"Erro ao enviar: {e}")
        return 0

def responder_com_delay(telefone):
    time.sleep(DELAY_SEGUNDOS)
    status = enviar_mensagem(telefone, RESPOSTA)
    if status == 200:
        print(f"✅ [ARTES] Respondido: {telefone}")
    else:
        print(f"❌ [ARTES] Erro ao responder {telefone}: {status}")

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json
        print(f"Webhook recebido: {data}")

        # Ignora mensagens enviadas por mim
        if data.get("fromMe"):
            return jsonify({"status": "ignored"}), 200

        telefone = data.get("phone", "")
        texto = data.get("text", {}).get("message", "") if isinstance(data.get("text"), dict) else ""

        if not telefone or not texto:
            return jsonify({"status": "no_data"}), 200

        # Já respondeu esse número
        if telefone in ja_respondidos:
            return jsonify({"status": "already_replied"}), 200

        if deve_responder(texto):
            ja_respondidos.add(telefone)
            t = threading.Thread(target=responder_com_delay, args=(telefone,))
            t.daemon = True
            t.start()
            print(f"⏳ [ARTES] Resposta agendada para {telefone} em {DELAY_SEGUNDOS}s")

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print(f"Erro no webhook: {e}")
        return jsonify({"status": "error"}), 500

@app.route("/", methods=["GET"])
def home():
    return "Bot Artes ativo 🎨", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
