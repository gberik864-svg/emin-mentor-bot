from gtts import gTTS

async def voice_handler(update, context):

    voice = update.message.voice

    file = await voice.get_file()

    path = "voice.ogg"

    await file.download_to_drive(path)

    await update.message.reply_text("🎤 Голос получен")

    tts = gTTS(
        text="Ваш голос принят",
        lang="ru"
    )

    tts.save("answer.mp3")

    await update.message.reply_voice(
        voice=open("answer.mp3","rb")
    )