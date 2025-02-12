from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from rembg import remove
from PIL import Image, ImageOps, ImageFilter
import os
import base64
import requests
from io import BytesIO
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid
import threading
import time
from functools import wraps

app = Flask(__name__)
CORS(app)

# Varsayılan klasör yollarını tanımla
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'

# Klasörleri oluştur
try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
except Exception as e:
    print(f"Klasör oluşturma hatası: {e}")

def get_folders():
    """Request context'inde çalışacak şekilde klasör yollarını belirle"""
    if request and 'pythonanywhere.com' in request.host_url:
        return '/home/muratbaba/mysite/uploads', '/home/muratbaba/mysite/outputs'
    return UPLOAD_FOLDER, OUTPUT_FOLDER

# Temizleme süresi (15 dakika = 900 saniye)
CLEANUP_INTERVAL = 900

def cleanup_old_files():
    while True:
        try:
            current_time = datetime.now().timestamp()
            upload_folder, output_folder = UPLOAD_FOLDER, OUTPUT_FOLDER
            for folder in [upload_folder, output_folder]:
                if os.path.exists(folder):
                    for filename in os.listdir(folder):
                        file_path = os.path.join(folder, filename)
                        if os.path.exists(file_path):
                            creation_time = os.path.getctime(file_path)
                            if current_time - creation_time > CLEANUP_INTERVAL:
                                os.remove(file_path)
        except Exception as e:
            print(f"Temizleme hatası: {e}")
        time.sleep(CLEANUP_INTERVAL)

# Temizleme thread'ini başlat
cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_base64_image(base64_string):
    # Base64 başlığını kaldır
    if 'base64,' in base64_string:
        base64_string = base64_string.split('base64,')[1]
    image_data = base64.b64decode(base64_string)
    return Image.open(BytesIO(image_data))

def process_url_image(url):
    response = requests.get(url)
    return Image.open(BytesIO(response.content))

def add_shadow(image, offset=(40,40), shadow_blur=15, shadow_color='black', shadow_opacity=128):
    # Görüntünün boyutlarını al
    width, height = image.size
    
    # Gölge için yeni bir görüntü oluştur
    shadow = Image.new('RGBA', (width + abs(offset[0]), height + abs(offset[1])), (0,0,0,0))
    
    # Orijinal görüntüyü siyaha çevir (gölge için)
    shadow_image = Image.new('RGBA', image.size, shadow_color)
    shadow_image.putalpha(image.getchannel('A'))
    
    # Gölgeyi bulanıklaştır
    shadow_image = shadow_image.filter(ImageFilter.GaussianBlur(shadow_blur))
    
    # Gölge opaklığını ayarla - doğrudan sayısal değer kullan
    alpha = shadow_image.getchannel('A')
    alpha = alpha.point(lambda x: int(x * shadow_opacity/255))
    shadow_image.putalpha(alpha)
    
    # Yeni bir görüntü oluştur
    result = Image.new('RGBA', (width + abs(offset[0]), height + abs(offset[1])), (0,0,0,0))
    
    # Gölgeyi yerleştir
    result.paste(shadow_image, (offset[0] if offset[0] > 0 else 0, offset[1] if offset[1] > 0 else 0))
    
    # Orijinal görüntüyü yerleştir
    result.paste(image, (0 if offset[0] < 0 else 0, 0 if offset[1] < 0 else 0), image)
    
    return result

# API anahtarı kontrolü için decorator
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-RapidAPI-Proxy-Secret')
        if api_key != 'b4ae3340-d79c-11ef-8554-298f2e5b056d':
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Invalid or missing API key'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return jsonify({'status': 'running'})

@app.route('/remove-background', methods=['POST'])
@require_api_key
def remove_background():
    try:
        # Her request için doğru klasör yollarını al
        upload_folder, output_folder = get_folders()

        input_image = None
        original_filename = None

        # Content type kontrolü
        content_type = request.headers.get('Content-Type', '')

        if 'multipart/form-data' in content_type:
            if 'image' not in request.files:
                return jsonify({'error': 'Dosya yüklenmedi'}), 400

            file = request.files['image']
            if file.filename == '':
                return jsonify({'error': 'Dosya seçilmedi'}), 400
            if not allowed_file(file.filename):
                return jsonify({'error': 'Geçersiz dosya formatı'}), 400

            original_filename = secure_filename(file.filename)
            input_image = Image.open(file)

        elif 'application/json' in content_type:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Geçersiz JSON verisi'}), 400

            if 'base64' in data:
                input_image = process_base64_image(data['base64'])
                original_filename = 'image_from_base64.png'
            elif 'base64_image' in data:
                input_image = process_base64_image(data['base64_image'])
                original_filename = 'image_from_base64.png'
            elif 'image_url' in data:
                input_image = process_url_image(data['image_url'])
                original_filename = 'image_from_url.png'
            else:
                return jsonify({'error': 'JSON içinde base64, base64_image veya image_url bulunamadı'}), 400
        else:
            return jsonify({'error': 'Desteklenmeyen Content-Type. multipart/form-data veya application/json kullanın'}), 415

        if input_image is None:
            return jsonify({'error': 'Görsel işlenemedi'}), 400

        # Benzersiz dosya adı oluştur
        unique_filename = f"{uuid.uuid4()}_{original_filename}"

        # Gölge parametrelerini JSON'dan al
        shadow_params = {}
        is_shadow = False
        if 'application/json' in content_type:
            data = request.get_json()
            is_shadow = data.get('isShadow', False)  # Varsayılan olarak False
            shadow_params = {
                'offset': tuple(data.get('shadow_offset', (40, 40))),
                'shadow_blur': data.get('shadow_blur', 15),
                'shadow_color': data.get('shadow_color', 'black'),
                'shadow_opacity': data.get('shadow_opacity', 128)
            }
        elif 'multipart/form-data' in content_type:
            is_shadow = request.form.get('isShadow', 'false').lower() == 'true'
            if is_shadow:
                shadow_params = {
                    'offset': tuple(map(int, request.form.get('shadow_offset', '40,40').split(','))),
                    'shadow_blur': int(request.form.get('shadow_blur', 15)),
                    'shadow_color': request.form.get('shadow_color', 'black'),
                    'shadow_opacity': int(request.form.get('shadow_opacity', 128))
                }

        # Arka planı kaldır ve isShadow true ise gölge ekle
        output_image = remove(input_image)
        if is_shadow:
            output_image = add_shadow(output_image, **shadow_params)

        # Dosyayı kaydet
        output_filename = f"removed_{unique_filename}"
        output_path = os.path.join(output_folder, output_filename)
        output_image.save(output_path, format="PNG")

        # Base64 dönüşümü
        buffered = BytesIO()
        output_image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        # URL oluştur
        image_url = f"{request.host_url.rstrip('/')}/get-image/{output_filename}"

        return jsonify({
            'success': True,
            'message': 'Success',
            'image_base64': f'data:image/png;base64,{img_str}',
            'image_url': image_url,
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/remove-background-free-for-muratbaba', methods=['POST'])
def remove_background_free():
    try:
        # Sunucu URL'sini belirle
        is_production = 'pythonanywhere.com' in request.host_url
        base_url = 'https://muratbaba.pythonanywhere.com' if is_production else request.host_url.rstrip('/')

        input_image = None
        original_filename = None

        # Content type kontrolü
        content_type = request.headers.get('Content-Type', '')

        if 'multipart/form-data' in content_type:
            if 'image' not in request.files:
                return jsonify({'error': 'Dosya yüklenmedi'}), 400

            file = request.files['image']
            if file.filename == '':
                return jsonify({'error': 'Dosya seçilmedi'}), 400
            if not allowed_file(file.filename):
                return jsonify({'error': 'Geçersiz dosya formatı'}), 400

            original_filename = secure_filename(file.filename)
            input_image = Image.open(file)

        elif 'application/json' in content_type:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Geçersiz JSON verisi'}), 400

            if 'base64' in data:
                input_image = process_base64_image(data['base64'])
                original_filename = 'image_from_base64.png'
            elif 'base64_image' in data:
                input_image = process_base64_image(data['base64_image'])
                original_filename = 'image_from_base64.png'
            elif 'image_url' in data:
                input_image = process_url_image(data['image_url'])
                original_filename = 'image_from_url.png'
            else:
                return jsonify({'error': 'JSON içinde base64, base64_image veya image_url bulunamadı'}), 400
        else:
            return jsonify({'error': 'Desteklenmeyen Content-Type. multipart/form-data veya application/json kullanın'}), 415

        if input_image is None:
            return jsonify({'error': 'Görsel işlenemedi'}), 400

        # Benzersiz dosya adı oluştur
        unique_filename = f"{uuid.uuid4()}_{original_filename}"

        # Gölge parametrelerini JSON'dan al
        shadow_params = {}
        if 'application/json' in content_type:
            data = request.get_json()
            shadow_params = {
                'offset': tuple(data.get('shadow_offset', (40, 40))),
                'shadow_blur': data.get('shadow_blur', 15),
                'shadow_color': data.get('shadow_color', 'black'),
                'shadow_opacity': data.get('shadow_opacity', 128)
            }

        # Arka planı kaldır ve gölge ekle
        output_image = remove(input_image)
        #output_image = add_shadow(output_image, **shadow_params)

        # Dosyayı kaydet
        output_filename = f"removed_{unique_filename}"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        output_image.save(output_path, format="PNG")

        # Base64 dönüşümü
        buffered = BytesIO()
        output_image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        # URL oluştur
        image_url = f"{base_url}/get-image/{output_filename}"

        return jsonify({
            'image_url': image_url,
            'success': True,
            'message': 'Success',
            'image_base64': f'data:image/png;base64,{img_str}',

        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Get-image endpoint'ini geri ekleyelim
@app.route('/get-image/<filename>')
def get_image(filename):
    try:
        _, output_folder = get_folders()
        return send_file(os.path.join(output_folder, filename))
    except Exception as e:
        return jsonify({'error': str(e)}), 404


if __name__ == '__main__':
    app.run(debug=True)