from flask import Flask, request
from openai import OpenAI
from twilio.rest import Client
import cloudinary
import cloudinary.uploader
from gtts import gTTS
import os
import traceback

app = Flask(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

import json
HISTORY_FILE = "conversas.json"
def carregar_historico():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def salvar_historico(historico):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)

historico_conversas = carregar_historico()

user_language_choice = {}

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    try:
        print("🔵 Requisição recebida no /whatsapp")

        incoming_msg = request.form.get("Body", "").strip().lower()
        from_number = request.form.get("From")
        num_media = int(request.form.get("NumMedia", 0))
        if not incoming_msg and num_media > 0:
            media_url = request.form.get("MediaUrl0")
            media_type = request.form.get("MediaContentType0")
            print(f"🎙️ Áudio recebido: {media_url} ({media_type})")
            from requests.auth import HTTPBasicAuth
            import requests
            audio_response = requests.get(media_url, auth=HTTPBasicAuth(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN")))
            with open("/tmp/input.ogg", "wb") as f:
                f.write(audio_response.content)
            from pydub import AudioSegment
            AudioSegment.from_file("/tmp/input.ogg").export("/tmp/input.mp3", format="mp3")
            import openai
            with open("/tmp/input.mp3", "rb") as f:
                transcript = openai.audio.transcriptions.create(model="whisper-1", file=f)
            incoming_msg = transcript.text.strip().lower()
            print(f"📝 Transcrição do áudio: {incoming_msg}")

        print(f"📥 Mensagem recebida: {incoming_msg}")
        print(f"📱 De: {from_number}")
        if not incoming_msg:
            print("⚠️ Mensagem vazia recebida, ignorando.")
            return "Mensagem vazia recebida", 200

        if incoming_msg in ["english", "french", "spanish"]:
            lang_code = {"english": "en", "french": "fr", "spanish": "es"}[incoming_msg]
            user_language_choice[from_number] = lang_code

            welcome_msgs = {
                "en": "Great! Let's continue practicing English!",
                "fr": "Génial ! Continuons à pratiquer le français !",
                "es": "¡Genial! ¡Sigamos practicando español!"
            }
            resposta_texto = welcome_msgs[lang_code]

            tts = gTTS(text=resposta_texto, lang=lang_code)
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
                media_url=[audio_url]
            )
            return "Idioma salvo com sucesso."

        if from_number not in user_language_choice:
            texto = (
                "Olá! Por favor escolha o idioma que deseja praticar:\n"
                "- Digite 'english' para Inglês 🇺🇸\n"
                "- Digite 'french' para Francês 🇫🇷\n"
                "- Digite 'spanish' para Espanhol 🇪🇸\n"
            )
            tts = gTTS(text=texto, lang="pt")
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
                media_url=[audio_url]
            )
            return "Aguardando escolha de idioma."

        idioma = user_language_choice[from_number]
        system_lang = {"en": "English", "fr": "French", "es": "Spanish"}[idioma]

        historico = historico_conversas.get(from_number, [])
        historico.append({"role": "user", "content": incoming_msg})
        mensagens = [{"role": "system", "content": (
            f"You are a native {system_lang} teacher having a casual conversation with a student. "
            f"Always respond ONLY in {system_lang}, in a natural and informal tone. "
            f"Continue the conversation, do not repeat your previous message, and respond with a new idea or question."
        )}] + historico
        response = client.chat.completions.create(
        )
        resposta_texto = response.choices[0].message.content.strip()
        print(f"🧠 Resposta do GPT: {resposta_texto}")

        tts = gTTS(text=resposta_texto, lang=idioma)
        audio_path = "/tmp/resposta.mp3"
        tts.save(audio_path)
        print("✅ Áudio gerado com gTTS com sucesso")

        uploaded = cloudinary.uploader.upload(audio_path, resource_type="raw")
        audio_url = uploaded.get("secure_url")
        print(f"🌐 Áudio disponível em: {audio_url}")

        Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        ).messages.create(
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
            to=from_number,
            media_url=[audio_url]
        )

        print("📤 Mensagem de voz enviada com sucesso via Twilio")
        return "Mensagem processada com sucesso"

    except Exception as e:
        print("❌ Erro no processamento:")
        traceback.print_exc()
        return "Erro no processamento", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
