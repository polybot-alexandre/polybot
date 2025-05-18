from flask import Flask, request
import openai
import requests
import os

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")
eleven_api_key = os.getenv("ELEVENLABS_API_KEY")
twilio_number = os.getenv("TWILIO_PHONE_NUMBER")

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    incoming_msg = request.form.get("Body")
    from_number = request.form.get("From")

    idioma = "english"
    if "francês" in incoming_msg.lower():
        idioma = "french"
    elif "espanhol" in incoming_msg.lower():
        idioma = "spanish"

    prompt = f"Você é um professor nativo de {idioma}. Corrija e continue esta conversa: {incoming_msg}"
    gpt_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    resposta_texto = gpt_response.choices[0].message.content

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

    return "Mensagem recebida"
