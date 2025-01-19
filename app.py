import os
import streamlit as st
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import networkx as nx
from pyvis.network import Network
import re

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
                            
                            st.download_button(
                                label="Zihin Haritasını İndir",
                                data=html,
                                file_name="mind_map.html",
                                mime="text/html"
                            )
        else:
            st.error("Geçersiz YouTube URL'si")

if __name__ == "__main__":
    main() 