from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from rembg import remove
from PIL import Image
import os
from werkzeug.utils import secure_filename
import time

app = Flask(__name__)
CORS(app)

# Yüklenen dosyaların kaydedileceği klasör
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Klasörleri oluştur
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def cleanup_old_files():
    """24 saatten eski dosyaları temizle"""
    current_time = time.time()
    for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
        for filename in os.listdir(folder):
            filepath = os.path.join(folder, filename)
            if os.path.getmtime(filepath) < current_time - 86400:  # 24 saat
                os.remove(filepath)

# Her istekte temizlik yap
@app.before_request
def before_request():
    cleanup_old_files()

@app.route('/remove-background', methods=['POST'])
def remove_background():
    try:
        # Dosya kontrolü
        if 'image' not in request.files:
            return jsonify({'error': 'Dosya yüklenmedi'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'Dosya seçilmedi'}), 400
            
        if not allowed_file(file.filename):
            return jsonify({'error': 'Geçersiz dosya formatı'}), 400

        # Dosyayı güvenli bir şekilde kaydet
        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        output_filename = f"removed_{filename.rsplit('.', 1)[0]}.png"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        file.save(input_path)

        # Arka planı kaldır
        input_image = Image.open(input_path)
        output_image = remove(input_image)
        output_image.save(output_path)

        # Dosya yollarını temizle
        os.remove(input_path)  # Input dosyasını sil

        # Sonuç URL'sini döndür
        result_url = f"/get-image/{output_filename}"
        return jsonify({
            'success': True,
            'message': 'Arka plan başarıyla kaldırıldı',
            'image_url': result_url
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get-image/<filename>')
def get_image(filename):
    try:
        return send_file(os.path.join(OUTPUT_FOLDER, filename))
    except Exception as e:
        return jsonify({'error': str(e)}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)