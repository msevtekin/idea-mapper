# YouTube Video Zihin Haritası Oluşturucu

Bu uygulama, YouTube videolarından otomatik olarak zihin haritası oluşturmanızı sağlar. Video altyazılarını kullanarak içeriği analiz eder ve interaktif bir zihin haritası oluşturur.

## Özellikler

- YouTube video URL'sinden otomatik altyazı çekme
- Gemini AI ile içerik analizi
- İnteraktif zihin haritası görselleştirme
- Haritayı HTML olarak kaydetme ve indirme
- Türkçe ve İngilizce altyazı desteği

## Kurulum

1. Gerekli Python paketlerini yükleyin:
```bash
pip install -r requirements.txt
```

2. `.env` dosyası oluşturun ve Google API anahtarınızı ekleyin:
```
GOOGLE_API_KEY=your_api_key_here
```

## Kullanım

1. Uygulamayı başlatın:
```bash
streamlit run app.py
```

2. Web tarayıcınızda açılan uygulamaya YouTube video URL'sini yapıştırın
3. "Zihin Haritası Oluştur" butonuna tıklayın
4. Oluşturulan zihin haritasını görüntüleyin ve indirin

## Gereksinimler

- Python 3.8+
- Google API anahtarı (Gemini AI için)
- İnternet bağlantısı 