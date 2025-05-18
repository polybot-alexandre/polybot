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

# Mapeamento de número para idioma
language_map = {
    "+5527988418585": "fr"  # Altere para seu número e idioma desejado
}

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    try:
        print("🔵 Requisição recebida no /whatsapp")

        incoming_msg = request.form.get("Body", "").strip()
        from_number = request.form.get("From")

        print(f"📥 Mensagem recebida: {incoming_msg}")
        print(f"📱 De: {from_number}")

        # Detectar idioma baseado no número
        idioma = language_map.get(from_number, "en")
        system_lang = {
            "en": "English",
            "fr": "French",
            "es": "Spanish"
        }.get(idioma, "English")

        # Caso o número não esteja mapeado, pedir escolha de idioma
        if from_number not in language_map:
            texto = (
                "Hello! Please reply with the language you want to practice:\n"
                "- Type 'english' for English 🇺🇸\n"
                "- Type 'french' for French 🇫🇷\n"
                "- Type 'spanish' for Spanish 🇪🇸"
            )
            tts = gTTS(text=texto, lang="en")
            audio_path = "/tmp/resposta.mp3"
            tts.save(audio_path)
            uploaded = cloudinary.uploader.upload(audio_path, resource_type="raw")
            audio_url = uploaded.get("secure_url")

            client_twilio = Client(
                os.getenv("TWILIO_ACCOUNT_SID"),
                os.getenv("TWILIO_AUTH_TOKEN")
            )

            client_twilio.messages.create(
                from_=os.getenv("TWILIO_PHONE_NUMBER"),
                to=from_number,
                media_url=[audio_url]
            )
            return "Idioma não definido. Mensagem de orientação enviada."

        # System prompt refinado com idioma garantido
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a native {system_lang} teacher. "
                        f"Respond ONLY in {system_lang}, in a natural, informal, conversational tone. "
                        f"Don't repeat the student's input. Just keep the conversation going."
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

        # gTTS com idioma certo
        tts = gTTS(text=resposta_texto, lang=idioma)
        audio_path = "/tmp/resposta.mp3"
        tts.save(audio_path)
        print("✅ Áudio gerado com gTTS com sucesso")

        uploaded = cloudinary.uploader.upload(audio_path, resource_type="raw")
        audio_url = uploaded.get("secure_url")
        print(f"🌐 Áudio disponível em: {audio_url}")

        client_twilio = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )

        client_twilio.messages.create(
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
