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

user_language_choice = {}

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    try:
        print("🔵 Requisição recebida no /whatsapp")

        incoming_msg = request.form.get("Body", "").strip().lower()
        from_number = request.form.get("From")

        print(f"📥 Mensagem recebida: {incoming_msg}")
        print(f"📱 De: {from_number}")

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
                "- Digite 'spanish' para Espanhol 🇪🇸"
            )
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

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a native {system_lang} teacher having a casual conversation with a student. "
                        f"Always respond ONLY in {system_lang}, in a natural and informal tone. "
                        f"Continue the conversation, do not repeat your previous message, and respond with a new idea or question."
                    )
                },
                {
                    "role": "user",
                    "content": incoming_msg
                }
            ]
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

# ===== MULTILINGUE =====

from gtts import gTTS

LANGUAGE_MAP = {
    "english": "en",
    "french": "fr",
    "spanish": "es",
    "portuguese": "pt",
}

def gerar_audio_mensagem(texto, idioma_destino='en'):
    tts = gTTS(text=texto, lang=idioma_destino)
    filename = f"mensagem_{idioma_destino}.mp3"
    tts.save(filename)
    return filename
