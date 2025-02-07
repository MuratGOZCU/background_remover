import whisper
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

def transcribe_audio(audio_path, model_name="base"):
    """Transcribe audio file using Whisper model"""
    print(f"Loading Whisper {model_name} model...")
    model = whisper.load_model(model_name)
    
    print("Transcribing audio...")
    result = model.transcribe(audio_path)
    
    return result["text"]

@app.route('/transcribe', methods=['POST'])
def handle_transcription():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    
    if audio_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    # Geçici dosya yolu oluştur
    temp_audio_path = "temp_audio_file"
    
    try:
        # Gelen dosyayı kaydet
        audio_file.save(temp_audio_path)
        
        # Transcribe işlemini gerçekleştir
        transcription = transcribe_audio(temp_audio_path)
        
        # Geçici dosyayı sil
        os.remove(temp_audio_path)
        
        return jsonify({
            'success': True,
            'transcription': transcription
        })
        
    except Exception as e:
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
