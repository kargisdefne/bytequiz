# ByteQuiz - Render deployment

Bu klasör Flask uygulamasının Render'a hazırlanmış halidir.

## Klasör yapısı

app.py
requirements.txt
render.yaml
templates/
static/
  uploads/

## Eksik bırakılan dosyalar

Mevcut konuşmada HTML dosyalarının içerikleri erişilebilir değildi.
Bu nedenle mevcut tasarımını bozacak şekilde yeni HTML dosyaları oluşturulmadı.

Aşağıdaki mevcut dosyalarını `templates/` klasörüne koy:
- index.html
- quiz.html
- siniflandirma.html
- sonuc.html

Ayrıca varsa CSS/JS/görsellerini `static/` içine koy.

## Render ayarları

Build Command:
pip install -r requirements.txt

Start Command:
gunicorn app:app

Python:
3.10.14

Not:
ImageAI 3.0.3 PyTorch backend kullanır ve resmi dokümantasyonu Python 3.7-3.10 aralığını belirtir.
Render Free web service 512 MB RAM ile sınırlıdır. TinyYOLOv3 + PyTorch bu sınırı aşabilir; bu nedenle deploy başarılı olsa bile modelin çalışma sırasında bellek sınırına takılıp takılmadığını Render loglarında kontrol etmek gerekir.
