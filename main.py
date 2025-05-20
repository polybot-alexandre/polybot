
from flask import Flask, request
import os
import traceback
import json
import requests
from pydub import AudioSegment
from openai import OpenAI
from twilio.rest import Client
import cloudinary.uploader
from requests.auth import HTTPBasicAuth

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

HISTORY_FILE = "conversas.json"
def carregar_historico():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def salvar_historico(hist):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(hist, f, ensure_ascii=False, indent=2)

historico_conversas = carregar_historico()
user_language_choice = {}

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    try:
        print("🔵 Requisição recebida no /whatsapp")
        incoming_msg = request.form.get("Body", "").strip().lower()
        from_number = request.form.get("From")
        num_media = int(request.form.get("NumMedia", 0))

        print(f"📥 Mensagem recebida: {incoming_msg}")
        print(f"📱 De: {from_number}")

        if incoming_msg in ["english", "french", "spanish"]:
            user_language_choice[from_number] = incoming_msg
            return send_text_message(from_number, f"Idioma selecionado: {incoming_msg.capitalize()} ✔️")

        if incoming_msg == "nova conversa":
            historico_conversas[from_number] = []
            salvar_historico(historico_conversas)
            return send_text_message(from_number, "🔄 Conversa reiniciada. Pode começar a falar!")

        if from_number not in user_language_choice:
            return send_text_message(from_number,
                "Olá! Por favor, escolha o idioma que deseja praticar:\n"
                "1️⃣ Digite ou fale 'english' para Inglês 🇺🇸\n"
                "2️⃣ 'french' para Francês 🇫🇷\n"
                "3️⃣ 'spanish' para Espanhol 🇪🇸"
            )

        if not incoming_msg and num_media > 0:
            media_url = request.form.get("MediaUrl0")
            audio_response = requests.get(media_url, auth=HTTPBasicAuth(
                os.getenv("TWILIO_ACCOUNT_SID"),
                os.getenv("TWILIO_AUTH_TOKEN")
            ))
            with open("/tmp/input.ogg", "wb") as f:
                f.write(audio_response.content)
            AudioSegment.from_file("/tmp/input.ogg").export("/tmp/input.mp3", format="mp3")
            with open("/tmp/input.mp3", "rb") as f:
                transcript = client.audio.transcriptions.create(model="whisper-1", file=f)
            incoming_msg = transcript.text.strip().lower()
            print(f"📝 Transcrição do áudio: {incoming_msg}")

        if not incoming_msg:
            return "Mensagem vazia recebida", 200

        idioma = user_language_choice.get(from_number, "english")
        historico = historico_conversas.get(from_number, [])
        historico.append({"role": "user", "content": incoming_msg})

        mensagens = [{"role": "system", "content": (
            f"You are a native {idioma} teacher having a casual conversation with a student. "
            f"Always respond ONLY in {idioma}, in a natural and informal tone. "
            f"Continue the conversation, do not repeat your previous message, and respond with a new idea or question."
        )}] + historico

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=mensagens
        )
        resposta_texto = response.choices[0].message.content.strip()
        print(f"🧠 Resposta do GPT: {resposta_texto}")
        historico.append({"role": "assistant", "content": resposta_texto})
        historico_conversas[from_number] = historico
        salvar_historico(historico_conversas)

        from gtts import gTTS
        tts = gTTS(text=resposta_texto, lang=idioma[:2])
        audio_path = "/tmp/resposta.mp3"
        tts.save(audio_path)
        uploaded = cloudinary.uploader.upload(audio_path, resource_type="raw")
        audio_url = uploaded.get("secure_url")

        Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        ).messages.create(
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
            to=from_number,
            body="🗣️ Aqui está sua resposta por áudio:",
            media_url=[audio_url]
        )

        return "Mensagem processada com sucesso"

    except Exception as e:
        print("❌ Erro no processamento:")
        traceback.print_exc()
        return "Erro no processamento", 500

def send_text_message(to, text):
    Client(
        os.getenv("TWILIO_ACCOUNT_SID"),
        os.getenv("TWILIO_AUTH_TOKEN")
    ).messages.create(
        from_=os.getenv("TWILIO_PHONE_NUMBER"),
        to=to,
        body=text
    )
    return "Mensagem de texto enviada"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
