from gtts import gTTS
import os
from io import BytesIO
import base64
from flask import Flask, request, send_file, url_for
from flask_cors import CORS
import uuid
import edge_tts
import asyncio
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import threading
import time
import glob

app = Flask(__name__)
CORS(app)

# Get the absolute path of the current directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VOICE_DIR = os.path.join(BASE_DIR, "voice")

# Available voices
VOICE_OPTIONS = {
    "tr": {
        "male": "tr-TR-AhmetNeural",      # Türkçe erkek
        "female": "tr-TR-EmelNeural"      # Türkçe kadın
    },
    "en": {
        "male": "en-US-ChristopherNeural", # İngilizce erkek
        "female": "en-US-JennyNeural"      # İngilizce kadın
    },
    "ar": {
        "male": "ar-SA-HamedNeural",      # Arapça erkek
        "female": "ar-SA-ZariyahNeural"   # Arapça kadın
    },
    "es": {
        "male": "es-ES-AlvaroNeural",     # İspanyolca erkek
        "female": "es-ES-ElviraNeural"    # İspanyolca kadın
    },
    "fr": {
        "male": "fr-FR-HenriNeural",      # Fransızca erkek
        "female": "fr-FR-DeniseNeural"    # Fransızca kadın
    },
    "de": {
        "male": "de-DE-ConradNeural",     # Almanca erkek
        "female": "de-DE-KatjaNeural"     # Almanca kadın
    },
    "it": {
        "male": "it-IT-DiegoNeural",      # İtalyanca erkek
        "female": "it-IT-ElsaNeural"      # İtalyanca kadın
    },
    "ja": {
        "male": "ja-JP-KeitaNeural",      # Japonca erkek
        "female": "ja-JP-NanamiNeural"    # Japonca kadın
    },
    "ko": {
        "male": "ko-KR-InJoonNeural",     # Korece erkek
        "female": "ko-KR-SunHiNeural"     # Korece kadın
    },
    "ru": {
        "male": "ru-RU-DmitryNeural",     # Rusça erkek
        "female": "ru-RU-SvetlanaNeural"  # Rusça kadın
    },
    "zh": {
        "male": "zh-CN-YunxiNeural",      # Çince erkek
        "female": "zh-CN-XiaoxiaoNeural"  # Çince kadın
    },
    "hi": {
        "male": "hi-IN-MadhurNeural",     # Hintçe erkek
        "female": "hi-IN-SwaraNeural"     # Hintçe kadın
    },
    "pt": {
        "male": "pt-BR-AntonioNeural",    # Portekizce erkek
        "female": "pt-BR-FranciscaNeural" # Portekizce kadın
    },
    "nl": {
        "male": "nl-NL-MaartenNeural",    # Hollandaca erkek
        "female": "nl-NL-ColetteNeural"   # Hollandaca kadın
    },
    "pl": {
        "male": "pl-PL-MarekNeural",      # Lehçe erkek
        "female": "pl-PL-ZofiaNeural"     # Lehçe kadın
    },
    "uk": {
        "male": "uk-UA-OstapNeural",      # Ukraynaca erkek
        "female": "uk-UA-PolinaNeural"    # Ukraynaca kadın
    },
    "cs": {
        "male": "cs-CZ-AntoninNeural",    # Çekçe erkek
        "female": "cs-CZ-VlastaNeural"    # Çekçe kadın
    },
    "el": {
        "male": "el-GR-NestorasNeural",   # Yunanca erkek
        "female": "el-GR-AthinaNeural"    # Yunanca kadın
    },
    "hu": {
        "male": "hu-HU-TamasNeural",      # Macarca erkek
        "female": "hu-HU-NoemiNeural"     # Macarca kadın
    },
    "ro": {
        "male": "ro-RO-EmilNeural",       # Romence erkek
        "female": "ro-RO-AlinaNeural"     # Romence kadın
    },
    "sk": {
        "male": "sk-SK-LukasNeural",      # Slovakça erkek
        "female": "sk-SK-ViktoriaNeural"  # Slovakça kadın
    },
    "da": {
        "male": "da-DK-JeppeNeural",      # Danca erkek
        "female": "da-DK-ChristelNeural"  # Danca kadın
    },
    "fi": {
        "male": "fi-FI-HarriNeural",      # Fince erkek
        "female": "fi-FI-NooraNeural"     # Fince kadın
    },
    "no": {
        "male": "nb-NO-FinnNeural",       # Norveççe erkek
        "female": "nb-NO-IselinNeural"    # Norveççe kadın
    },
    "sv": {
        "male": "sv-SE-MattiasNeural",    # İsveççe erkek
        "female": "sv-SE-SofieNeural"     # İsveççe kadın
    },
    "bg": {
        "male": "bg-BG-BorislavNeural",   # Bulgarca erkek
        "female": "bg-BG-KalinaNeural"    # Bulgarca kadın
    },
    "id": {
        "male": "id-ID-ArdiNeural",       # Endonezce erkek
        "female": "id-ID-GadisNeural"     # Endonezce kadın
    },
    "ms": {
        "male": "ms-MY-OsmanNeural",      # Malayca erkek
        "female": "ms-MY-YasminNeural"    # Malayca kadın
    },
    "vi": {
        "male": "vi-VN-NamMinhNeural",    # Vietnamca erkek
        "female": "vi-VN-HoaiMyNeural"    # Vietnamca kadın
    },
    "th": {
        "male": "th-TH-PremwadeeNeural",  # Tayca erkek
        "female": "th-TH-NiwatNeural"     # Tayca kadın
    },
    "he": {
        "male": "he-IL-AvriNeural",       # İbranice erkek
        "female": "he-IL-HilaNeural"      # İbranice kadın
    },
    "bn": {
        "male": "bn-IN-BashkarNeural",    # Bengalce erkek
        "female": "bn-IN-TanishaaNeural"  # Bengalce kadın
    },
    "fa": {
        "male": "fa-IR-FaridNeural",      # Farsça erkek
        "female": "fa-IR-DilaraNeural"    # Farsça kadın
    },
    "af": {
        "male": "af-ZA-WillemNeural",     # Afrikaanca erkek
        "female": "af-ZA-AdriNeural"      # Afrikaanca kadın
    },
    "am": {
        "male": "am-ET-AmehaNeural",      # Amharca erkek
        "female": "am-ET-MekdesNeural"    # Amharca kadın
    },
    "az": {
        "male": "az-AZ-BabekNeural",      # Azerice erkek
        "female": "az-AZ-BanuNeural"      # Azerice kadın
    },
    "bs": {
        "male": "bs-BA-GoranNeural",      # Boşnakça erkek
        "female": "bs-BA-VesnaNeural"     # Boşnakça kadın
    },
    "ca": {
        "male": "ca-ES-EnricNeural",      # Katalanca erkek
        "female": "ca-ES-JoanaNeural"     # Katalanca kadın
    },
    "cy": {
        "male": "cy-GB-AledNeural",       # Galce erkek
        "female": "cy-GB-NiaNeural"       # Galce kadın
    },
    "et": {
        "male": "et-EE-KertNeural",       # Estonca erkek
        "female": "et-EE-AnuNeural"       # Estonca kadın
    },
    "eu": {
        "male": "eu-ES-AitorNeural",      # Baskça erkek
        "female": "eu-ES-AinhoaNeural"    # Baskça kadın
    },
    "fil": {
        "male": "fil-PH-AngeloNeural",    # Filipince erkek
        "female": "fil-PH-BlessicaNeural" # Filipince kadın
    },
    "gl": {
        "male": "gl-ES-RoiNeural",        # Galiçyaca erkek
        "female": "gl-ES-SabelaNeural"    # Galiçyaca kadın
    },
    "ka": {
        "male": "ka-GE-GiorgiNeural",     # Gürcüce erkek
        "female": "ka-GE-EkaNeural"       # Gürcüce kadın
    },
    "kk": {
        "male": "kk-KZ-DauletNeural",     # Kazakça erkek
        "female": "kk-KZ-AigulNeural"     # Kazakça kadın
    },
    "km": {
        "male": "km-KH-PisethNeural",     # Kmerce erkek
        "female": "km-KH-SreymomNeural"   # Kmerce kadın
    },
    "ky": {
        "male": "ky-KG-AsanNeural",       # Kırgızca erkek
        "female": "ky-KG-BegaimNeural"    # Kırgızca kadın
    },
    "lv": {
        "male": "lv-LV-NilsNeural",       # Letonca erkek
        "female": "lv-LV-EveritaNeural"   # Letonca kadın
    },
    "lt": {
        "male": "lt-LT-LeonasNeural",     # Litvanca erkek
        "female": "lt-LT-OnaNeural"       # Litvanca kadın
    },
    "mk": {
        "male": "mk-MK-AleksandarNeural", # Makedonca erkek
        "female": "mk-MK-MarijaNeural"    # Makedonca kadın
    },
    "mt": {
        "male": "mt-MT-JosephNeural",     # Maltaca erkek
        "female": "mt-MT-GraceNeural"     # Maltaca kadın
    },
    "mn": {
        "male": "mn-MN-BataaNeural",      # Moğolca erkek
        "female": "mn-MN-YesuiNeural"     # Moğolca kadın
    },
    "sr": {
        "male": "sr-RS-NicholasNeural",   # Sırpça erkek
        "female": "sr-RS-SophieNeural"    # Sırpça kadın
    },
    "si": {
        "male": "si-LK-SameeraNeural",    # Seylanca erkek
        "female": "si-LK-ThiliniNeural"   # Seylanca kadın
    },
    "sw": {
        "male": "sw-KE-RafikiNeural",     # Svahili erkek
        "female": "sw-KE-ZuriNeural"      # Svahili kadın
    },
    "ta": {
        "male": "ta-IN-ValluvarNeural",   # Tamilce erkek
        "female": "ta-IN-PallaviNeural"   # Tamilce kadın
    },
    "te": {
        "male": "te-IN-MohanNeural",      # Telugu erkek
        "female": "te-IN-ShrutiNeural"    # Telugu kadın
    },
    "ur": {
        "male": "ur-PK-AsadNeural",       # Urduca erkek
        "female": "ur-PK-UzmaNeural"      # Urduca kadın
    },
    "uz": {
        "male": "uz-UZ-SardorNeural",     # Özbekçe erkek
        "female": "uz-UZ-MadinaNeural"    # Özbekçe kadın
    }
}

# Create voice directory if it doesn't exist
if not os.path.exists(VOICE_DIR):
    try:
        os.makedirs(VOICE_DIR, exist_ok=True)
        print(f"Created voice directory at: {VOICE_DIR}")
    except Exception as e:
        print(f"Error creating voice directory: {e}")

async def edge_tts_generate(text, voice_name):
    """Generate speech using edge-tts"""
    communicate = edge_tts.Communicate(text, voice_name)
    filename = f"speech_{uuid.uuid4()}.mp3"
    filepath = os.path.join(VOICE_DIR, filename)
    await communicate.save(filepath)
    return filename

def get_supported_languages():
    """Get list of supported languages with their codes"""
    return {
        "tr": "Turkish",
        "en": "English",
        "ar": "Arabic",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "it": "Italian",
        "ja": "Japanese",
        "ko": "Korean",
        "ru": "Russian",
        "zh": "Chinese",
        "hi": "Hindi",
        "pt": "Portuguese",
        "nl": "Dutch",
        "pl": "Polish",
        "uk": "Ukrainian",
        "cs": "Czech",
        "el": "Greek",
        "hu": "Hungarian",
        "ro": "Romanian",
        "sk": "Slovak",
        "da": "Danish",
        "fi": "Finnish",
        "no": "Norwegian",
        "sv": "Swedish",
        "bg": "Bulgarian",
        "id": "Indonesian",
        "ms": "Malay",
        "vi": "Vietnamese",
        "th": "Thai",
        "he": "Hebrew",
        "bn": "Bengali",
        "fa": "Persian",
        "af": "Afrikaans",
        "am": "Amharic",
        "az": "Azerbaijani",
        "bs": "Bosnian",
        "ca": "Catalan",
        "cy": "Welsh",
        "et": "Estonian",
        "eu": "Basque",
        "fil": "Filipino",
        "gl": "Galician",
        "ka": "Georgian",
        "kk": "Kazakh",
        "km": "Khmer",
        "ky": "Kyrgyz",
        "lv": "Latvian",
        "lt": "Lithuanian",
        "mk": "Macedonian",
        "mt": "Maltese",
        "mn": "Mongolian",
        "sr": "Serbian",
        "si": "Sinhala",
        "sw": "Swahili",
        "ta": "Tamil",
        "te": "Telugu",
        "ur": "Urdu",
        "uz": "Uzbek"
    }

# Add new endpoint to get supported languages
@app.route('/api/supported-languages', methods=['GET'])
def supported_languages():
    """Return list of supported languages"""
    return {
        "status": "success",
        "languages": get_supported_languages(),
        "message": "Supported languages retrieved successfully"
    }

# Initialize limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per minute"]  # Örnek limit
)

def cleanup_old_files(filepath, delay=600):  # 600 seconds = 10 minutes
    """Delete the audio file after specified delay"""
    def delete_file():
        time.sleep(delay)
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"Deleted file: {filepath}")
        except Exception as e:
            print(f"Error deleting file {filepath}: {e}")

    # Start deletion thread
    thread = threading.Thread(target=delete_file)
    thread.daemon = True
    thread.start()

def text_to_speech(text, voice="en", gender="female"):
    """
    Convert text to speech using Edge TTS
    
    Args:
        text (str): Text to convert to speech
        voice (str): Language code (e.g., 'en', 'tr', 'ar', 'es', etc.)
        gender (str): Voice gender ('male' or 'female')
    
    Returns:
        dict: Response containing audio URL and status
    """
    try:
        # Get voice based on language and gender
        voice_name = VOICE_OPTIONS.get(voice, {}).get(gender)
        if not voice_name:
            # If language not found, fallback to English
            voice_name = VOICE_OPTIONS["en"]["female"]
            print(f"Warning: Voice not found for language '{voice}' and gender '{gender}'. Using default English voice.")

        # Generate unique filename and run edge-tts
        filename = asyncio.run(edge_tts_generate(text, voice_name))
        filepath = os.path.join(VOICE_DIR, filename)

        # Verify file was created
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Failed to create audio file at {filepath}")

        # Schedule file cleanup after 10 minutes
        cleanup_old_files(filepath)

        file_url = request.host_url + f"voice/{filename}"
        return {
            "status": "success",
            "audio_url": file_url,
            "message": "Audio generated successfully",
            "language": voice,
            "gender": gender
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error generating audio: {str(e)}"
        }

@app.route('/voice/<filename>')
def serve_audio(filename):
    """Serve audio files from voice directory"""
    try:
        file_path = os.path.join(VOICE_DIR, filename)
        if not os.path.exists(file_path):
            return {"error": "Audio file not found"}, 404
        return send_file(file_path, mimetype="audio/mpeg")
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/api/text-to-speech', methods=['POST', 'OPTIONS'])
@limiter.limit("200 per minute")  # Her IP için dakikada 200 istek
def generate_speech():
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response

    try:
        data = request.get_json()
        if not data:
            return {
                "status": "error",
                "message": "No JSON data received"
            }, 400
            
        text = data.get('text', '')
        if not text:
            return {
                "status": "error",
                "message": "Text field is required"
            }, 400
            
        voice = data.get('voice', 'en')
        gender = data.get('gender', 'female')  # default to female voice
        
        return text_to_speech(text=text, voice=voice, gender=gender)
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error processing request: {str(e)}"
        }, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
