from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import torch
from diffusers import StableDiffusionPipeline
import os
import uuid
from PIL import Image
import io
import atexit
import signal

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"]
    }
})

# Çıktı klasörü oluştur
OUTPUT_FOLDER = "generated_images"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Daha hafif model kullan
model_id = "CompVis/stable-diffusion-v1-4"  # Daha küçük model
pipe = None

def load_model():
    global pipe
    pipe = StableDiffusionPipeline.from_pretrained(
        model_id,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        safety_checker=None,  # Güvenlik kontrolünü devre dışı bırak
        requires_safety_checking=False
    )
    if torch.cuda.is_available():
        pipe = pipe.to("cuda")
        pipe.enable_attention_slicing()  # Bellek kullanımını optimize et
        pipe.enable_vae_slicing()       # VAE bellek kullanımını optimize et
    
    # Hızlandırma için önbelleğe al
    pipe(prompt="warmup", num_inference_steps=1)

def cleanup():
    global pipe
    if pipe is not None:
        try:
            del pipe
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except:
            pass

# Uygulama başlangıcında modeli yükle
if not os.environ.get('WERKZEUG_RUN_MAIN'):
    load_model()

# Temiz kapatma için handler'lar
atexit.register(cleanup)
signal.signal(signal.SIGTERM, lambda s, f: cleanup())
signal.signal(signal.SIGINT, lambda s, f: cleanup())

@app.route('/generate', methods=['POST'])
def generate_image():
    try:
        data = request.get_json()
        
        if 'prompt' not in data:
            return jsonify({'error': 'Prompt gerekli'}), 400
        
        prompt = data['prompt']
        
        # Görsel oluştur - daha az adımla
        with torch.no_grad():
            image = pipe(
                prompt,
                num_inference_steps=50,    # Adım sayısını azalt (varsayılan 50)
                guidance_scale=7.5,        # Guidance scale'i düşür
                height=512,                # Daha küçük boyut
                width=512
            ).images[0]
        
        # Benzersiz dosya adı oluştur
        filename = f"{uuid.uuid4()}.png"
        output_path = os.path.join(OUTPUT_FOLDER, filename)
        
        # Görseli kaydet
        image.save(output_path)
        
        # Hafızayı temizle
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        return jsonify({
            'success': True,
            'image_url': f'/images/{filename}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/images/<filename>')
def serve_image(filename):
    try:
        return send_file(os.path.join(OUTPUT_FOLDER, filename))
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/test-image', methods=['GET'])
def test_generate_image():
    try:
        test_prompt = "A beautiful sunset over mountains with purple and orange sky, digital art style"
        
        # Görsel oluştur
        with torch.no_grad():
            image = pipe(
                test_prompt,
                num_inference_steps=50,
                guidance_scale=7.5,
                height=512,
                width=512
            ).images[0]
        
        # Benzersiz dosya adı oluştur
        filename = f"test_{uuid.uuid4()}.png"
        output_path = os.path.join(OUTPUT_FOLDER, filename)
        
        # Görseli kaydet
        image.save(output_path)
        
        # Hafızayı temizle
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        return jsonify({
            'success': True,
            'message': 'Test görsel oluşturuldu',
            'image_url': f'/images/{filename}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/combine-images', methods=['POST', 'OPTIONS'])
def combine_images():
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        return response

    try:
        if 'user_image' not in request.files:
            return jsonify({'error': 'Kullanıcı görseli gerekli'}), 400
            
        user_image_file = request.files['user_image']
        
        if user_image_file.filename == '':
            return jsonify({'error': 'Dosya seçilmedi'}), 400
            
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
        if not '.' in user_image_file.filename or \
           user_image_file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            return jsonify({'error': 'Geçersiz dosya türü'}), 400

        prompt = request.form.get('prompt', "A beautiful sunset over mountains with purple and orange sky, digital art style")
        
        # AI ile arka plan görseli oluştur
        with torch.no_grad():
            background = pipe(
                prompt,
                num_inference_steps=50,
                guidance_scale=7.5,
                height=512,
                width=512
            ).images[0]
        
        # Arka planı RGBA'ya dönüştür
        background = background.convert('RGBA')
        
        # Kullanıcı görselini yükle
        user_image = Image.open(user_image_file)
        user_image = user_image.convert('RGBA')
        
        # Kullanıcı görselinin boyutunu ayarla (oranı koruyarak)
        base_width = 300  # Kullanıcı görselinin genişliği
        w_percent = (base_width / float(user_image.size[0]))
        h_size = int((float(user_image.size[1]) * float(w_percent)))
        user_image = user_image.resize((base_width, h_size), Image.Resampling.LANCZOS)
        
        # Kullanıcı görselini arka planın ortasına yerleştir
        # Pozisyonu hesapla
        position = (
            (background.width - user_image.width) // 2,
            (background.height - user_image.height) // 2
        )
        
        # Yeni bir kompozit görsel oluştur
        composite = Image.new('RGBA', background.size)
        composite.paste(background, (0, 0))
        
        # Kullanıcı görselini yerleştir
        composite.paste(user_image, position, user_image)
        
        # Benzersiz dosya adı oluştur
        filename = f"composite_{uuid.uuid4()}.png"
        output_path = os.path.join(OUTPUT_FOLDER, filename)
        
        # Kompozit görseli kaydet
        composite.save(output_path, 'PNG')
        
        # Hafızayı temizle
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        return jsonify({
            'success': True,
            'message': 'Görseller başarıyla birleştirildi',
            'image_url': f'/images/{filename}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == '__main__':
    # Flask'ı tek işlem modunda çalıştır
    app.run(debug=False, threaded=False)
