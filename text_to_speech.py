import whisper
import urllib.request
import os

def download_audio(url, output_path):
    """Download audio file from URL"""
    print("Downloading audio file...")
    urllib.request.urlretrieve(url, output_path)
    print("Download completed!")

def transcribe_audio(audio_path, model_name="base"):
    """Transcribe audio file using Whisper model"""
    print(f"Loading Whisper {model_name} model...")
    model = whisper.load_model(model_name)
    
    print("Transcribing audio...")
    result = model.transcribe(audio_path)
    
    return result["text"]

def main():
    # Audio file URL and path
    audio_url = "https://storage.googleapis.com/falserverless/model_tests/whisper/dinner_conversation.mp3"
    audio_path = "dinner_conversation.mp3"
    
    # Download audio if not exists
    if not os.path.exists(audio_path):
        download_audio(audio_url, audio_path)
    
    # Transcribe audio
    transcription = transcribe_audio(audio_path)
    
    print("\nTranscription:")
    print("-" * 50)
    print(transcription)
    
    # Optionally save transcription to file
    with open("transcription.txt", "w", encoding="utf-8") as f:
        f.write(transcription)
    print("\nTranscription saved to transcription.txt")

if __name__ == "__main__":
    main()
