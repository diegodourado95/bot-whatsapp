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
TAMANHO_MINIMO = 15

# ── OFERTA ARTES ──────────────────────────────────────────────────────────────
RESPOSTA_ARTES = """Oi! 👋 Que bom que você veio aqui!

Vou te dar um presente por isso 🎨 Vou liberar o Pacote Completo pra você por apenas R$12,90, desconto especial só pra quem chegou até mim pelo WhatsApp.

São 300 dinâmicas, 50 técnicas, 30 projetos, apostila completa e todos os downloads prontos pra imprimir.

👉 https://pay.wiapy.com/txzQTZuLA

Qualquer dúvida é só falar aqui 😊"""

GATILHOS_ARTES = [
    "dinâmicas de arte infantil",
    "dinamicas de arte infantil",
    "300 dinâmicas de arte",
    "300 dinamicas de arte",
    "interessada nas dinâmicas de arte",
    "interessada nas dinamicas de arte",
]

# ── OFERTA ALFABETIZAÇÃO ──────────────────────────────────────────────────────
RESPOSTA_ALFABETIZACAO = """Oi! 👋 Já que você veio até mim, vou liberar o Pacote Completo por R$12,90, desconto especial só pra você.

São +200 dinâmicas de alfabetização + 3 bônus, tudo pronto pra imprimir e aplicar.

Garante aqui: https://pay.wiapy.com/8izCCV4HH 😊"""

GATILHOS_ALFABETIZACAO = [
    "dinâmicas de alfabetização",
    "dinamicas de alfabetizacao",
    "interessada nas dinâmicas de alfabetização",
    "interessada nas dinamicas de alfabetizacao",
]

# ── PALAVRAS QUE BLOQUEIAM QUALQUER RESPOSTA ──────────────────────────────────
PALAVRAS_BLOQUEIO = [
    "reembolso",
    "cancelar",
    "cancelamento",
    "devolver",
    "devolução",
    "estorno",
]

# ── CONTROLE DE JÁ RESPONDIDOS (por oferta) ───────────────────────────────────
ja_respondidos_artes = set()
ja_respondidos_alfabetizacao = set()

# ── FUNÇÕES ───────────────────────────────────────────────────────────────────
def tem_bloqueio(msg_lower):
    return any(p in msg_lower for p in PALAVRAS_BLOQUEIO)

def detectar_oferta(mensagem):
    """Retorna 'artes', 'alfabetizacao' ou None"""
    msg_lower = mensagem.lower()

    if len(mensagem.strip()) < TAMANHO_MINIMO:
        return None

    if tem_bloqueio(msg_lower):
        return None

    if any(p in msg_lower for p in GATILHOS_ARTES):
        return "artes"

    if any(p in msg_lower for p in GATILHOS_ALFABETIZACAO):
        return "alfabetizacao"

    return None

def enviar_mensagem(telefone, mensagem):
    url = f"{BASE_URL}/send-text"
    payload = {"phone": telefone, "message": mensagem}
    try:
        resp = requests.post(url, json=payload, headers=HEADERS, timeout=15)
        return resp.status_code
    except Exception as e:
        print(f"Erro ao enviar: {e}")
        return 0

def responder_com_delay(telefone, oferta):
    time.sleep(DELAY_SEGUNDOS)
    resposta = RESPOSTA_ARTES if oferta == "artes" else RESPOSTA_ALFABETIZACAO
    status = enviar_mensagem(telefone, resposta)
    if status == 200:
        print(f"✅ [{oferta.upper()}] Respondido: {telefone}")
    else:
        print(f"❌ [{oferta.upper()}] Erro ao responder {telefone}: {status}")

# ── WEBHOOK ───────────────────────────────────────────────────────────────────
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json
        print(f"Webhook recebido: {data}")

        if data.get("fromMe"):
            return jsonify({"status": "ignored"}), 200

        telefone = data.get("phone", "")
        texto = data.get("text", {}).get("message", "") if isinstance(data.get("text"), dict) else ""

        if not telefone or not texto:
            return jsonify({"status": "no_data"}), 200

        oferta = detectar_oferta(texto)

        if oferta == "artes":
            if telefone in ja_respondidos_artes:
                return jsonify({"status": "already_replied"}), 200
            ja_respondidos_artes.add(telefone)
            t = threading.Thread(target=responder_com_delay, args=(telefone, "artes"))
            t.daemon = True
            t.start()
            print(f"⏳ [ARTES] Resposta agendada para {telefone} em {DELAY_SEGUNDOS}s")

        elif oferta == "alfabetizacao":
            if telefone in ja_respondidos_alfabetizacao:
                return jsonify({"status": "already_replied"}), 200
            ja_respondidos_alfabetizacao.add(telefone)
            t = threading.Thread(target=responder_com_delay, args=(telefone, "alfabetizacao"))
            t.daemon = True
            t.start()
            print(f"⏳ [ALFABETIZAÇÃO] Resposta agendada para {telefone} em {DELAY_SEGUNDOS}s")

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print(f"Erro no webhook: {e}")
        return jsonify({"status": "error"}), 500

@app.route("/", methods=["GET"])
def home():
    return "Bot ativo 🤖", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
