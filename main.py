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

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    try:
        print("🔵 Requisição recebida no /whatsapp")

        incoming_msg = request.form.get("Body", "").strip()
        from_number = request.form.get("From")

        print(f"📥 Mensagem recebida: {incoming_msg}")
        print(f"📱 De: {from_number}")

        idioma = "en"
        system_lang = "English"
        if "francês" in incoming_msg.lower():
            idioma = "fr"
            system_lang = "French"
        elif "espanhol" in incoming_msg.lower():
            idioma = "es"
            system_lang = "Spanish"

        # System prompt atualizado com contexto e idioma correto
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a native {system_lang} teacher. "
                        f"You are chatting with a student. "
                        f"Always respond ONLY in {system_lang}, informally, as if you're speaking. "
                        f"Never repeat the student's question. Continue the conversation naturally, even across multiple messages. "
                        f"Correct mistakes subtly as you go."
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

        # Gerar áudio com gTTS
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
