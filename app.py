import os
import streamlit as st
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import networkx as nx
from pyvis.network import Network
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time # if a simple sleep is needed for waiting

# Çevre değişkenlerini yükle
load_dotenv()

# Gemini API anahtarını ayarla
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

def get_video_id(url):
    """YouTube URL'sinden video ID'sini çıkarır."""
    video_id = None
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            break
    return video_id

def get_transcript(video_id):
    """Video altyazılarını çeker."""
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['tr', 'en'])
        return ' '.join([t['text'] for t in transcript_list])
    except Exception as e:
        st.error(f"Altyazı çekilirken hata oluştu: {str(e)}")
        return None

def analyze_content(text):
    """Metni analiz eder ve zihin haritası için yapı oluşturur."""
    model = genai.GenerativeModel('gemini-pro')
    prompt = """
    Aşağıdaki metni analiz et ve zihin haritası için hiyerarşik bir yapı oluştur.
    Format şu şekilde olmalı:
    {
        "merkez": "Ana Konu",
        "dallar": [
            {
                "başlık": "Ana Başlık 1",
                "alt_başlıklar": ["Alt Başlık 1", "Alt Başlık 2"]
            },
            {
                "başlık": "Ana Başlık 2",
                "alt_başlıklar": ["Alt Başlık 1", "Alt Başlık 2"]
            }
        ]
    }
    
    Metin:
    """
    
    response = model.generate_content(prompt + text)
    try:
        return eval(response.text)
    except:
        st.error("İçerik analizi sırasında hata oluştu.")
        return None

def create_mind_map(data):
    """Zihin haritası oluşturur."""
    # Ağ ayarları
    net = Network(height="750px", width="100%", bgcolor="#ffffff", font_color="#333333")
    net.set_options("""
    const options = {
        "nodes": {
            "font": {
                "size": 14,
                "face": "Arial",
                "color": "#333333",
                "bold": false
            },
            "borderWidth": 1,
            "borderWidthSelected": 1,
            "chosen": false,
            "shape": "box",
            "shadow": false,
            "widthConstraint": {
                "minimum": 100,
                "maximum": 250
            },
            "margin": {
                "top": 5,
                "bottom": 5,
                "left": 10,
                "right": 10
            },
            "heightConstraint": {
                "minimum": 30
            }
        },
        "edges": {
            "color": {
                "inherit": "from"
            },
            "smooth": {
                "enabled": true,
                "type": "straightCross",
                "roundness": 0
            },
            "width": 1,
            "selectionWidth": 1,
            "hoverWidth": 1,
            "arrows": {
                "to": {
                    "enabled": false
                }
            }
        },
        "physics": {
            "enabled": false
        },
        "layout": {
            "hierarchical": {
                "enabled": true,
                "direction": "LR",
                "sortMethod": "directed",
                "levelSeparation": 300,
                "nodeSpacing": 50,
                "treeSpacing": 200,
                "blockShifting": true,
                "edgeMinimization": true,
                "parentCentralization": false
            }
        },
        "interaction": {
            "dragNodes": false,
            "dragView": true,
            "zoomView": true,
            "hover": true
        }
    }
    """)
    
    # Renk paleti
    colors = {
        "center": "#333333",  # Merkez başlık rengi
        "main_branches": {
            0: "#0066cc",  # Mavi
            1: "#ff6633",  # Turuncu
            2: "#339933",  # Yeşil
            3: "#9933cc"   # Mor
        }
    }
    
    # Merkez düğümü ekle
    net.add_node(0, 
                 label=data['merkez'],
                 color={"background": "#ffffff", "border": colors["center"]},
                 size=30,
                 shape="box",
                 font={"size": 16, "color": colors["center"], "bold": True},
                 level=0)
    
    node_id = 1
    for i, dal in enumerate(data['dallar']):
        branch_color = colors["main_branches"][i % len(colors["main_branches"])]
        
        # Ana başlık düğümü
        net.add_node(node_id,
                    label=dal['başlık'].upper(),
                    color={"background": "#ffffff", "border": branch_color},
                    size=25,
                    shape="box",
                    font={"size": 14, "color": branch_color, "bold": True},
                    level=1)
        
        # Merkez ile ana başlık arasındaki bağlantı
        net.add_edge(0, node_id, 
                    color={"color": branch_color},
                    width=1)
        
        parent_id = node_id
        node_id += 1
        
        # Alt başlıklar
        for alt_baslik in dal['alt_başlıklar']:
            net.add_node(node_id,
                        label=alt_baslik,
                        color={"background": "#ffffff", "border": branch_color},
                        size=20,
                        shape="box",
                        font={"size": 12, "color": "#333333"},
                        level=2)
            
            # Ana başlık ile alt başlık arasındaki bağlantı
            net.add_edge(parent_id, node_id,
                        color={"color": branch_color},
                        width=1)
            node_id += 1
    
    return net

def export_mind_map_as_png(html_file_path, png_file_path="mind_map.png"):
    # Set up Chrome options for headless browsing
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox") # Often needed in restricted environments
    chrome_options.add_argument("--disable-dev-shm-usage") # Also common in restricted environments
    chrome_options.add_argument("--window-size=1200,800") # Set a reasonable window size

    # Optional: Specify ChromeDriver path if not in PATH
    # service = Service(executable_path='/path/to/chromedriver')
    # driver = webdriver.Chrome(service=service, options=chrome_options)
    # If ChromeDriver is in PATH, the service argument is not strictly needed
    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Load the local HTML file
        # Ensure html_file_path is an absolute path or correctly relative
        driver.get("file://" + os.path.abspath(html_file_path))

        # Wait for the page and pyvis graph to load
        # A simple time.sleep might be okay for a start, but a more robust
        # solution would be to use WebDriverWait for a specific element.
        # For pyvis, the graph is often rendered in a div with id 'mynetwork' or a canvas within it.
        # Let's try a short sleep first, can be refined if needed.
        time.sleep(5) # Adjust as necessary

        # Take a screenshot of the entire page or a specific element
        # For simplicity, let's start with the whole body.
        # If pyvis renders in a predictable container (e.g., <div id="mynetwork">...</div>),
        # you could target that element:
        # element = driver.find_element(By.ID, "mynetwork")
        # element.screenshot(png_file_path)
        # For now, let's screenshot the body
        driver.save_screenshot(png_file_path)
        
        return png_file_path
    except Exception as e:
        st.error(f"Error exporting to PNG: {str(e)}") # Make sure st is available or log differently
        print(f"Error exporting to PNG: {str(e)}") # Also print to console for worker logs
        return None
    finally:
        if 'driver' in locals():
            driver.quit()

def main():
    st.title("YouTube Video Zihin Haritası Oluşturucu")
    st.write("YouTube videosundan otomatik olarak zihin haritası oluşturun.")
    
    url = st.text_input("YouTube Video URL'si:")
    
    if url:
        video_id = get_video_id(url)
        if video_id:
            st.video(f"https://www.youtube.com/watch?v={video_id}")
            
            if st.button("Zihin Haritası Oluştur"):
                with st.spinner("Video altyazıları çekiliyor..."):
                    transcript = get_transcript(video_id)
                
                if transcript:
                    with st.spinner("İçerik analiz ediliyor..."):
                        mind_map_data = analyze_content(transcript)
                    
                    if mind_map_data:
                        with st.spinner("Zihin haritası oluşturuluyor..."):
                            net = create_mind_map(mind_map_data)
                            net.save_graph("mind_map.html")
                            
                            with open("mind_map.html", "r", encoding="utf-8") as f:
                                html = f.read()
                            st.components.v1.html(html, height=800)
                            
                            # HTML indirme butonu
                            st.download_button(
                                label="Zihin Haritasını (HTML) İndir",
                                data=html,
                                file_name="mind_map.html",
                                mime="text/html"
                            )

                            # PNG olarak dışa aktar ve indirme butonu ekle
                            png_file_path = "mind_map.png"
                            with st.spinner("PNG olarak dışa aktarılıyor..."):
                                exported_png_path = export_mind_map_as_png("mind_map.html", png_file_path)
                            
                            if exported_png_path:
                                with open(exported_png_path, "rb") as f:
                                    png_data = f.read()
                                st.download_button(
                                    label="Zihin Haritasını (PNG) İndir",
                                    data=png_data,
                                    file_name="mind_map.png",
                                    mime="image/png"
                                )
                            else:
                                st.warning("PNG dışa aktarma başarısız oldu.")
        else:
            st.error("Geçersiz YouTube URL'si")

if __name__ == "__main__":
    main() 