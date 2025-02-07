import json
from deep_translator import GoogleTranslator
import time
from deep_translator.exceptions import RequestError

def translate_tr_to_es():
    # JSON dosyasını oku
    try:
        with open('data.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        print("data.json dosyası bulunamadı!")
        return
    except json.JSONDecodeError:
        print("JSON dosyası geçerli değil!")
        return

    # Çevirmen nesnesini oluştur
    translator = GoogleTranslator(source='tr', target='nl')
    
    # TR verilerini ES'e çevir
    if "tr" in data:
        # Mevcut çevirileri kontrol et
        try:
            with open('data_with_nl.json', 'r', encoding='utf-8') as file:
                existing_data = json.load(file)
                translated_ids = {item["id"] for item in existing_data.get("nl", [])}
        except FileNotFoundError:
            translated_ids = set()
            existing_data = {"nl": []}

        for item in data["tr"]:
            if item["id"] in translated_ids:
                print(f"ID {item['id']} zaten çevrilmiş, atlanıyor...")
                continue

            retry_count = 0
            while retry_count < 3:
                try:
                    es_item = {
                        "id": item["id"],
                        "word": item["word"],
                        "correctAnswer": translator.translate(item["correctAnswer"]),
                        "options": [translator.translate(option) for option in item["options"]],
                        "example": {
                            "nl": translator.translate(item["example"]["tr"]),
                            "en": item["example"]["en"]
                        }
                    }
                    existing_data["nl"].append(es_item)
                    
                    # Her başarılı çeviriden sonra dosyayı güncelle
                    with open('data_with_nl.json', 'w', encoding='utf-8') as file:
                        json.dump(existing_data, file, ensure_ascii=False, indent=2)
                    
                    print(f"Çevrilen id: {item['id']}")
                    time.sleep(0.1)  # Normal bekleme süresi
                    break
                    
                except RequestError as e:
                    retry_count += 1
                    wait_time = retry_count * 5  # Her denemede bekleme süresini artır
                    print(f"Rate limit aşıldı. {wait_time} saniye bekleniyor... (Deneme {retry_count}/3)")
                    time.sleep(wait_time)
                    continue
                except Exception as e:
                    print(f"Hata oluştu (ID: {item['id']}): {str(e)}")
                    break

    # Sonuçları yeni bir JSON dosyasına kaydet
    try:
        with open('data_with_nl.json', 'w', encoding='utf-8') as file:
            json.dump(existing_data, file, ensure_ascii=False, indent=2)
        print("Çeviri tamamlandı! Sonuçlar data_with_nl.json dosyasına kaydedildi.")
    except Exception as e:
        print(f"Dosya kaydetme hatası: {e}")

if __name__ == "__main__":
    translate_tr_to_es()