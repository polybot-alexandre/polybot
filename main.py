from flask import Flask, request
from openai import OpenAI
import requests
import os
import traceback

app = Flask(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
eleven_api_key = os.getenv("ELEVENLABS_API_KEY")
twilio_number = os.getenv("TWILIO_PHONE_NUMBER")

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    try:
        print("🔵 Requisição recebida no /whatsapp")

        incoming_msg = request.form.get("Body")
        from_number = request.form.get("From")

        print(f"📥 Mensagem recebida: {incoming_msg}")
        print(f"📱 De: {from_number}")

        idioma = "english"
        if "francês" in incoming_msg.lower():
            idioma = "french"
        elif "espanhol" in incoming_msg.lower():
            idioma = "spanish"

        prompt = f"Você é um professor nativo de {idioma}. Corrija e continue esta conversa: {incoming_msg}"
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        resposta_texto = response.choices[0].message.content

        print(f"🧠 Resposta do GPT: {resposta_texto}")

        voice_id = {
            "english": "EXAVITQu4vr4xnSDxMaL",
            "french": "TxGEqnHWrfWFTfGW9XjX",
            "spanish": "MF3mGyEYCl7XYWbV9V6O"
        }[idioma]

        audio_response = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={
                "xi-api-key": eleven_api_key,
                "Content-Type": "application/json"
            },
            json={
                "text": resposta_texto,
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
            }
        )

        audio_path = f"/tmp/resposta_{idioma}.mp3"
        with open(audio_path, "wb") as f:
            f.write(audio_response.content)

        print("✅ Áudio gerado com sucesso")

        return "Mensagem processada com sucesso"
    except Exception as e:
        print("❌ Erro no processamento:")
        traceback.print_exc()
        return "Erro no processamento", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
