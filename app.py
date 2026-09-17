import os
from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from werkzeug.utils import secure_filename
from PIL import Image
import numpy as np

# ImageAI TinyYOLOv3 nesne tespit modeli
from imageai.Detection import ObjectDetection

app = Flask(__name__)

# Session kullanabilmek için anahtar
app.secret_key = "quiz_anahtari"

# Veritabanı bağlantısı
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///quiz.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Sınıflandırılacak görseli yükleme
UPLOAD_FOLDER = os.path.join(
    app.root_path,
    "static",
    "uploads"
)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ImageAI TinyYOLOv3 modelini yükle
MODEL_PATH = os.path.join(
    app.root_path,
    "tiny-yolov3.pt"
)

detector = ObjectDetection()
detector.setModelTypeAsTinyYOLOv3()
detector.setModelPath(MODEL_PATH)
detector.loadModel()


# Dosyanın uygun uzantıya sahip olup olmadığını kontrol eder
def allowed_file(filename):
    if "." not in filename:
        return False
    uzanti = filename.rsplit(".", 1)[1].lower()
    return uzanti in ALLOWED_EXTENSIONS


class KullaniciSkor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kullanici_adi = db.Column(
        db.String(100),
        nullable=False
    )
    puan = db.Column(
        db.Integer,
        nullable=False
    )

# Veritabanı oluşturma
with app.app_context():
    db.create_all()

sinav_sorulari = [
    # Discord.py
    {
        "id": 1, "kategori": "Discord.py", "zorluk": "Kolay",
        "soru": "Botun istemcisini (client) ve arka plandaki asenkron olay döngüsünü (event loop) başlatan ana komut hangisidir?",
        "secenekler": ["bot.execute('TOKEN')", "bot.start('TOKEN')", "bot.run('TOKEN')", "bot.connect('TOKEN')"],
        "dogru_cevap": "bot.run('TOKEN')",        
        "ipucu": "Kodun en alt satırında motoru ateşleyen metottur.",
        "aciklama": "bot.run() metodu, event loop'u oluşturur, botu başlatır ve işlem bitene kadar çalışmasını sağlar."
    },
    {
        "id": 2, "kategori": "Discord.py", "zorluk": "Orta",
        "soru": "Bir fonksiyonu bota komut olarak tanımlamak için kullanılan belirteç (decorator) hangisidir?",
        "secenekler": ["@bot.event", "@bot.command", "@bot.action", "@bot.register"],
        "dogru_cevap": "@bot.command",
        "ipucu": "Cevap sorunun içerisinde saklı.",
        "aciklama": "@bot.command() belirteci ile fonksiyonlarınızı kullanıcıların çağırabileceği komutlara dönüştürürsünüz."
    },
    {
        "id": 3, "kategori": "Discord.py", "zorluk": "Zor",
        "soru": "Botun sunucudaki üyelerin mesaj içeriklerini okuyabilmesi için hangi özelliği aktif etmesi zorunludur?",
        "secenekler": ["Administrator Permissions", "Message Content Intent", "Webhook Integration", "Oauth2 Scopes"],
        "dogru_cevap": "Message Content Intent",
        "ipucu": "Gizlilik politikaları gereği, botun verilere erişebilmesi için verilmesi gereken özel yetkilerden biridir.",
        "aciklama": "Discord API v2'den itibaren mesaj içeriklerini okumak için 'Message Content Intent' özelliğinin hem kodda hem de geliştirici portalında aktif edilmesi gerekir."
    },
    # Flask
    {
        "id": 4, "kategori": "Flask", "zorluk": "Kolay",
        "soru": "Flask uygulamasının varsayılan olarak çalıştığı port numarası hangisidir?",
        "secenekler": ["80", "8080", "3000", "5000"],
        "dogru_cevap": "5000",
        "ipucu": "Genellikle http://localhost:XXXX/ adresinde test edilir.",
        "aciklama": "Flask uygulamaları geliştirme ortamında varsayılan olarak 5000 numaralı port üzerinden yayın yapar."
    },
    {
        "id": 5, "kategori": "Flask", "zorluk": "Orta",
        "soru": "Flask kütüphanesinde HTML dosyalarını ekranda göstermek için hangi fonksiyon kullanılır?",
        "secenekler": ["show_html()", "render_template()", "display()", "return_page()"],
        "dogru_cevap": "render_template()",
        "ipucu": "HTML şablonlarını sunmak için kullanılır.",
        "aciklama": "render_template() fonksiyonu, templates klasöründeki HTML dosyalarını Jinja2 motoruyla derleyerek tarayıcıya sunar."
    },
    {
        "id": 6, "kategori": "Flask", "zorluk": "Zor",
        "soru": "Kullanıcının form üzerinden gönderdiği POST verilerini güvenli bir şekilde yakalamak için hangisi kullanılır?",
        "secenekler": ["request.form", "request.args", "request.data", "request.get"],
        "dogru_cevap": "request.form",
        "ipucu": "URL parametreleri (GET) için `.args` kullanılırken, HTTP gövdesindeki (POST) anahtar-değer çiftlerini okumak için bu nesne kullanılır.",
        "aciklama": "HTML formlarından (POST metodu ile) gelen veriler Flask'ta request.form sözlüğü kullanılarak alınır."
    },
    # Yapay Zeka
    {
        "id": 7, "kategori": "Yapay Zeka", "zorluk": "Kolay",
        "soru": "Etiketli veriler kullanılarak modelin eğitilmesi yöntemine ne ad verilir?",
        "secenekler": ["Gözetimsiz Öğrenme", "Gözetimli Öğrenme", "Takviyeli Öğrenme", "Derin Öğrenme"],
        "dogru_cevap": "Gözetimli Öğrenme",
        "ipucu": "Modele hem girdilerin (X) hem de bunlara karşılık gelen doğru çıktıların (y) birlikte sunulduğu makine öğrenmesi yaklaşımıdır.",
        "aciklama": "Girdilerin hedeflenen çıktılarla eşleştirilerek öğretilmesine Gözetimli Öğrenme denir."
    },
    {
        "id": 8, "kategori": "Yapay Zeka", "zorluk": "Orta",
        "soru": "Modelin eğitim verilerini ezberlemesi ve yeni/görülmemiş verilerde başarısız olması durumuna ne ad verilir?",
        "secenekler": ["Underfitting", "Overfitting", "Optimization", "Normalization"],
        "dogru_cevap": "Overfitting",
        "ipucu": "Eğitim verisetinde başarım %99 iken test/doğrulama verisetinde başarımın aniden düşmesi durumudur.",
        "aciklama": "Overfitting, modelin genel kuralları öğrenmek yerine sadece eğitim verisindeki gürültüleri ve istisnaları ezberlemesidir."
    },
    {
        "id": 9, "kategori": "Yapay Zeka", "zorluk": "Zor",
        "soru": "Yapay sinir ağlarının en temel yapı taşı olan ve ağırlıklı toplamı aktivasyon fonksiyonundan geçiren yapı hangisidir?",
        "secenekler": ["Katman (Layer)", "Nöron (Perseptron)", "Tensor", "Matris"],
        "dogru_cevap": "Nöron (Perseptron)",
        "ipucu": "Biyolojik beyindeki bilgi iletim noktalarının yapay sinir ağlarındaki en küçük matematiksel karşılığıdır.",
        "aciklama": "Perseptron (Yapay Nöron), yapay sinir ağlarındaki bilgi işleyen en küçük matematiksel birimdir."
    },
    # Bilgisayar Görüşü
    {
        "id": 10, "kategori": "Bilgisayar Görüşü", "zorluk": "Kolay",
        "soru": "Dijital bir görüntünün oluşturulabileceği, kontrol edilebilen en küçük renkli noktaya ne ad verilir?",
        "secenekler": ["Vektör", "Piksel", "Katman", "Kanal"],
        "dogru_cevap": "Piksel",
        "ipucu": "Görüntü matrislerinin her bir hücresini temsil eder ve genellikle RGB değer kümesini barındırır.",
        "aciklama": "Ekranda görüntüyü oluşturan noktalara piksel denir."
    },
    {
        "id": 11, "kategori": "Bilgisayar Görüşü", "zorluk": "Orta",
        "soru": "Python'da görüntü işleme için kullanılan, resimleri BGR renk formatında okuyan en popüler kütüphane hangisidir?",
        "secenekler": ["NumPy", "OpenCV", "Matplotlib", "Pillow"],
        "dogru_cevap": "OpenCV",
        "ipucu": "Standart RGB yerine BGR sıralamasını kullanmasıyla bilinen ve C++ tabanlı altyapısıyla çok hızlı çalışan açık kaynaklı kütüphanedir.",
        "aciklama": "OpenCV, görüntü işleme ve gerçek zamanlı bilgisayar görüşü projelerinde endüstri standardı haline gelmiştir."
    },
    {
        "id": 12, "kategori": "Bilgisayar Görüşü", "zorluk": "Zor",
        "soru": "Bir görüntüdeki nesnelerin sınırlarını piksel düzeyinde tam olarak belirleme işlemine ne ad verilir?",
        "secenekler": ["Filtreleme", "Nesne Tespiti", "Segmentasyon", "Döndürme"],
        "dogru_cevap": "Segmentasyon",
        "ipucu": "Nesnenin etrafına sadece dikdörtgen çizmek yerine, nesneye ait olan her bir pikseli tek tek etiketleme işlemidir.",
        "aciklama": "Nesne tespiti sadece çerçeve çizerken, segmentasyon her bir pikselin hangi nesneye ait olduğunu sınırlarıyla bulur."
    },
    # Doğal Dil İşleme (NLP)
    {
        "id": 13, "kategori": "NLP", "zorluk": "Kolay",
        "soru": "Bir metnin olumlu, olumsuz veya nötr olduğunu tespit etmek için yapılan çalışmaya ne ad verilir?",
        "secenekler": ["Metin Özetleme", "Duygu Analizi", "Konuşma Tanıma", "Kelime Bulutları"],
        "dogru_cevap": "Duygu Analizi",
        "ipucu": "Metnin içerdiği polariteyi (öznel yargı, tutum veya his) sayısal veya kategorik değerlere dönüştüren sınıflandırmadır.",
        "aciklama": "Müşteri yorumları veya tweetlerin taşıdığı hissiyatı sınıflandırma işlemine Duygu Analizi denir."
    },
    {
        "id": 14, "kategori": "NLP", "zorluk": "Orta",
        "soru": "Bir metindeki 've, veya, ama, de' gibi tek başına anlam ifade etmeyen kelimelere ne ad verilir?",
        "secenekler": ["Keywords", "Stop Words", "Tokens", "Verbs"],
        "dogru_cevap": "Stop Words",
        "ipucu": "Metin ön işleme aşamasında verinin boyutunu küçültmek ve modele ayırt edici bilgi sağlamayan kelimeleri ayıklamak için listeden çıkarılırlar.",
        "aciklama": "Model eğitimini yavaşlatmamak ve gürültüyü azaltmak için temizlik aşamasında silinen kelimelere Stop Words denir."
    },
    {
        "id": 15, "kategori": "NLP", "zorluk": "Zor",
        "soru": "Kelimeleri eklerinden arındırarak sözlükteki gerçek kök haline getirme (ör: 'gözlükçü' -> 'gözlük') işlemine ne ad verilir?",
        "secenekler": ["Lemmatization", "Tokenization", "Parsing", "Stemming"],
        "dogru_cevap": "Lemmatization",
        "ipucu": "Kelimeleri rastgele budamak yerine dilbilgisi kurallarına uyarak anlamlı temel biçimine dönüştürür.",
        "aciklama": "Lemmatization, kelimeleri morfolojik analizden geçirerek sözlükteki temel formuna çevirir."
    }
]

# http://127.0.0.1:5000 sayfasının index.htmli açması
@app.route("/")
def ana_sayfa():
    return render_template("index.html")

# http://127.0.0.1:5000/gorsel_siniflandirma sayfasının içeriği
@app.route("/gorsel_siniflandirma", methods=["GET", "POST"])
def gorsel_siniflandirma():

    dosya_yolu = None
    tahminler = []
    analiz_yapildi = False
    eslesme_mesaji = None

    # Form gönderildiyse
    if request.method == "POST":

        # Dosya gönderildi mi kontrolü
        if "dosya" not in request.files:
            return redirect(request.url)

        file = request.files["dosya"]
        if file.filename == "":
            return redirect(request.url)

        # Dosya uzantısı kontrolü
        if file and allowed_file(file.filename):

            filename = secure_filename(file.filename)
            tam_yol = os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )            
            file.save(tam_yol)            
            dosya_yolu = "uploads/" + filename

            # Görseli ImageAI TinyYOLOv3 ile analiz et
            output_filename = "sonuc_" + filename
            output_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                output_filename
            )

            detections = detector.detectObjectsFromImage(
                input_image=tam_yol,
                output_image_path=output_path,
                minimum_percentage_probability=30
            )

            # Model hiçbir nesne tespit etmediyse mesaj göster
            if not detections:
                eslesme_mesaji = "Eğitilen modelde eşleşme bulunamadı."

            # Tespit edilen nesneleri listeye ekle
            for detection in detections:
                etiket = detection["name"].replace(
                    "_",
                    " "
                ).capitalize()

                yuzde = round(
                    float(detection["percentage_probability"]),
                    2
                )

                tahminler.append({
                    "etiket": etiket,
                    "yuzde": yuzde
                })

            # Analizin tamamlandığını işaretleme
            analiz_yapildi = True


    # Sonuçları HTML sayfasına gönderme
    return render_template(
        "siniflandirma.html",
        dosya_yolu=dosya_yolu,
        tahminler=tahminler,
        analiz_yapildi=analiz_yapildi,
        eslesme_mesaji=eslesme_mesaji
    )


@app.route("/quiz")
def quiz_sayfasi():

    return render_template(
        "quiz.html",
        sorular=sinav_sorulari
    )



@app.route("/sinav_sonucu", methods=["POST"])
def sinav_sonucu():

    # Kullanıcı adını alma
    isim = request.form.get(
        "kullanici_adi",
        "Katılımcı"
    )

    # Kullanıcı adını session'a kaydetme
    session["aktif_isim"] = isim

    dogru_sayisi = 0
    yanlis_sayisi = 0
    kategori_stats = {}

    for soru in sinav_sorulari:
        kategori = soru["kategori"]
        if kategori not in kategori_stats:
            kategori_stats[kategori] = {
                "dogru": 0,
                "yanlis": 0
            }

        # Kullanıcının cevabını alma
        gelen_cevap = request.form.get(
            f"soru_{soru['id']}"
        )

        if gelen_cevap == soru["dogru_cevap"]:
            dogru_sayisi += 1
            kategori_stats[kategori]["dogru"] += 1

        else:
            yanlis_sayisi += 1
            kategori_stats[kategori]["yanlis"] += 1

    toplam_soru = len(sinav_sorulari)


    # Başarı yüzdesini hesaplama
    yuzde_puan = int(
        (dogru_sayisi / toplam_soru) * 100
    )

    # Kullanıcının skorunu veritabanına kaydetme
    yeni_kayit = KullaniciSkor(
        kullanici_adi=isim,
        puan=yuzde_puan
    )

    db.session.add(yeni_kayit)
    db.session.commit()


    # Veritabanındaki en yüksek puanı bulma
    genel_en_yuksek = (
        db.session
        .query(func.max(KullaniciSkor.puan))
        .scalar()
        or yuzde_puan
    )

    kategori_adlari = list(
        kategori_stats.keys()
    )

    kategori_dogru_sayilari = [
        kategori_stats[kategori]["dogru"]
        for kategori in kategori_adlari
    ]

    kategori_yanlis_sayilari = [
        kategori_stats[kategori]["yanlis"]
        for kategori in kategori_adlari
    ]


    return render_template(
        "sonuc.html",

        puan=yuzde_puan,
        dogru_sayisi=dogru_sayisi,
        yanlis_sayisi=yanlis_sayisi,
        genel_en_yuksek=genel_en_yuksek,
        kategori_adlari=kategori_adlari,
        kategori_dogru_sayilari=kategori_dogru_sayilari,
        kategori_yanlis_sayilari=kategori_yanlis_sayilari
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
