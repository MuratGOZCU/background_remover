import cv2
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from rembg import remove

class WatermarkRemover:
    def __init__(self):
        self.debug = False

    def remove_watermark(self, image_path, output_path):
        # Görüntüyü oku
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Görüntü okunamadı")

        # Görüntüyü gri tonlamaya çevir
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Watermark bölgesini tespit et
        _, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
        
        # Morfolojik işlemler
        kernel = np.ones((3,3), np.uint8)
        mask = cv2.dilate(binary, kernel, iterations=2)
        
        # Inpainting uygula
        radius = 3
        result = cv2.inpaint(image, mask, radius, cv2.INPAINT_TELEA)
        
        # Görüntüyü iyileştir
        result = cv2.fastNlMeansDenoisingColored(result, None, 10, 10, 7, 21)
        
        # Sonucu kaydet
        cv2.imwrite(output_path, result)
        
        # Görselleştir
        self.visualize_results(image_path, output_path, mask)

    def visualize_results(self, input_path, output_path, mask):
        original = cv2.imread(input_path)
        cleaned = cv2.imread(output_path)
        
        # BGR'den RGB'ye dönüştür
        original = cv2.cvtColor(original, cv2.COLOR_BGR2RGB)
        cleaned = cv2.cvtColor(cleaned, cv2.COLOR_BGR2RGB)
        
        plt.figure(figsize=(15, 5))
        
        plt.subplot(131)
        plt.imshow(original)
        plt.title('Orijinal Görüntü')
        plt.axis('off')
        
        plt.subplot(132)
        plt.imshow(mask, cmap='gray')
        plt.title('Watermark Maskesi')
        plt.axis('off')
        
        plt.subplot(133)
        plt.imshow(cleaned)
        plt.title('Watermark Temizlenmiş')
        plt.axis('off')
        
        plt.tight_layout()
        plt.show()

def main():
    try:
        remover = WatermarkRemover()
        input_path = "watermark_image.jpg"
        output_path = "cleaned_image.jpg"
        remover.remove_watermark(input_path, output_path)
        print(f"Watermark başarıyla temizlendi. Sonuç {output_path} olarak kaydedildi.")
    except Exception as e:
        print(f"Hata oluştu: {str(e)}")

if __name__ == "__main__":
    main()
