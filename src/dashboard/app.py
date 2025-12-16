"""
Streamlit Dashboard for Real Estate Payment Management

Interactive web interface for receipt processing and visualization.
"""

import streamlit as st
import sys
from pathlib import Path
import json
import tempfile
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.pipeline.full_pipeline import ReceiptPipeline
from src.chatbot import RealEstateChatbot


# Page config
st.set_page_config(
    page_title="Emlak Ödeme Yönetimi",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'pipeline' not in st.session_state:
    st.session_state.pipeline = None
    st.session_state.chatbot = None
    st.session_state.result = None
    st.session_state.processing = False
    st.session_state.chat_messages = []
    st.session_state.chat_enabled = False


@st.cache_resource
def load_pipeline():
    """Load pipeline (cached)."""
    with st.spinner("🚀 NLP modelleri yükleniyor..."):
        pipeline = ReceiptPipeline(enable_matching=True, mock_db_path='tests/mock-data.json')
        chatbot = RealEstateChatbot(mock_db_path='tests/mock-data.json')
    return pipeline, chatbot


def create_score_gauge(score: float, title: str):
    """Create a gauge chart for score visualization."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score * 100,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 16}},
        delta={'reference': 70, 'increasing': {'color': "green"}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 70], 'color': "yellow"},
                {'range': [70, 100], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 70
            }
        }
    ))
    
    fig.update_layout(height=250, margin=dict(l=10, r=10, t=50, b=10))
    return fig


def create_scores_bar_chart(scores: dict):
    """Create bar chart for matching scores."""
    data = {
        'Kriter': ['IBAN', 'Tutar', 'İsim', 'Adres', 'Gönderen'],
        'Skor': [
            scores.get('iban', 0) * 100,
            scores.get('amount', 0) * 100,
            scores.get('name', 0) * 100,
            scores.get('address', 0) * 100,
            scores.get('sender', 0) * 100
        ]
    }
    
    fig = px.bar(
        data,
        x='Kriter',
        y='Skor',
        title='Eşleşme Skorları',
        color='Skor',
        color_continuous_scale=['red', 'yellow', 'green'],
        range_color=[0, 100]
    )
    
    fig.update_layout(
        height=400,
        yaxis_title="Skor (%)",
        xaxis_title="",
        showlegend=False
    )
    
    return fig


def display_results(result: dict):
    """Display processing results."""
    st.markdown("---")
    st.markdown("## 📊 İşlem Sonuçları")
    
    # Status indicator
    status = result.get('status', 'unknown')
    if status == 'success':
        st.success("✅ Dekont başarıyla işlendi!")
    else:
        st.error(f"❌ Hata: {status}")
        return
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Özet", "🎯 Intent & NER", "🔗 Eşleşme", "📄 Ham Veri"])
    
    with tab1:
        display_summary(result)
    
    with tab2:
        display_nlp_results(result)
    
    with tab3:
        display_matching_results(result)
    
    with tab4:
        display_raw_data(result)


def display_summary(result: dict):
    """Display summary information."""
    ocr_data = result.get('ocr_data', {})
    matching = result.get('matching', {})
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 👤 Gönderen")
        st.info(f"**{ocr_data.get('sender', 'Bilinmiyor')}**")
        st.caption(f"IBAN: `{ocr_data.get('sender_iban', 'N/A')}`")
    
    with col2:
        st.markdown("### 👤 Alıcı")
        st.info(f"**{ocr_data.get('recipient', 'Bilinmiyor')}**")
        st.caption(f"IBAN: `{ocr_data.get('receiver_iban', 'N/A')}`")
    
    with col3:
        st.markdown("### 💰 Tutar")
        st.success(f"**{ocr_data.get('amount', '0')} {ocr_data.get('amount_currency', 'TRY')}**")
        st.caption(f"Tarih: {ocr_data.get('date', 'N/A')}")
    
    # Description
    st.markdown("### 📝 Açıklama")
    st.write(ocr_data.get('description', 'Yok'))
    
    # Matching status
    if matching:
        st.markdown("---")
        match_status = matching.get('status', 'unknown')
        confidence = matching.get('confidence', 0)
        
        if match_status == 'matched':
            st.markdown(f"""
            <div class="success-box">
                <h3>✅ Eşleşme Bulundu!</h3>
                <p><strong>Güven Skoru:</strong> {confidence:.1f}%</p>
                <p><strong>Mülk Sahibi ID:</strong> {matching.get('owner_id')}</p>
                <p><strong>Mülk ID:</strong> {matching.get('property_id')}</p>
            </div>
            """, unsafe_allow_html=True)
        elif match_status == 'manual_review':
            st.markdown(f"""
            <div class="warning-box">
                <h3>⚠️ Manuel İnceleme Gerekli</h3>
                <p><strong>Güven Skoru:</strong> {confidence:.1f}%</p>
                <p>Eşleşme belirsiz, manuel kontrol önerilir.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="error-box">
                <h3>❌ Eşleşme Bulunamadı</h3>
                <p>Veritabanında eşleşen kayıt yok.</p>
            </div>
            """, unsafe_allow_html=True)


def display_nlp_results(result: dict):
    """Display NLP results."""
    intent = result.get('intent', {})
    ner = result.get('ner', {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎯 Intent Classification")
        primary_intent = intent.get('primary', 'unknown')
        confidence = intent.get('confidence', 0)
        
        st.metric(
            label="Ana Intent",
            value=primary_intent.replace('_', ' ').title(),
            delta=f"{confidence*100:.1f}% güven"
        )
        
        # All intents
        if 'all_intents' in intent:
            st.markdown("**Tüm Intent Skorları:**")
            for intent_item in intent['all_intents'][:3]:
                intent_name = intent_item['intent'].replace('_', ' ').title()
                intent_conf = intent_item['confidence'] * 100
                st.progress(intent_conf / 100, text=f"{intent_name}: {intent_conf:.1f}%")
    
    with col2:
        st.markdown("### 🏷️ Named Entity Recognition")
        entities = ner.get('entities', {})
        
        if entities:
            for entity_type, entity_value in entities.items():
                if entity_value and entity_value not in [[], ['']]:
                    # Clean value
                    if isinstance(entity_value, list):
                        entity_value = ', '.join(str(v) for v in entity_value if v)
                    
                    st.text(f"• {entity_type}: {entity_value}")
        else:
            st.info("Entity bulunamadı")


def display_matching_results(result: dict):
    """Display matching results with visualizations."""
    matching = result.get('matching', {})
    
    if not matching:
        st.info("Eşleşme bilgisi yok")
        return
    
    confidence = matching.get('confidence', 0)
    scores = matching.get('scores', {})
    
    # Confidence gauge
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.plotly_chart(
            create_score_gauge(confidence / 100, "Toplam Güven Skoru"),
            use_container_width=True
        )
    
    with col2:
        st.plotly_chart(
            create_scores_bar_chart(scores),
            use_container_width=True
        )
    
    # Score details
    st.markdown("### 📊 Skor Detayları")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("IBAN", f"{scores.get('iban', 0)*100:.0f}%")
    with col2:
        st.metric("Tutar", f"{scores.get('amount', 0)*100:.0f}%")
    with col3:
        st.metric("İsim", f"{scores.get('name', 0)*100:.0f}%")
    with col4:
        st.metric("Adres", f"{scores.get('address', 0)*100:.0f}%")
    with col5:
        st.metric("Gönderen", f"{scores.get('sender', 0)*100:.0f}%")
    
    # Messages
    if matching.get('messages'):
        st.markdown("### 💬 Mesajlar")
        for msg in matching['messages']:
            st.info(msg)


def display_raw_data(result: dict):
    """Display raw JSON data."""
    st.markdown("### 📄 Ham JSON Verisi")
    st.json(result)


def display_chatbot():
    """Display interactive chatbot."""
    st.markdown("---")
    st.markdown("## 🤖 AI Asistan")
    
    # Welcome message if no messages
    if not st.session_state.chat_messages:
        st.session_state.chat_messages = [{
            "role": "assistant",
            "content": st.session_state.chatbot.get_welcome_message()
        }]
    
    # Display chat messages
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Mesajınızı yazın... (örn: 'yardım', 'kiracı bilgisi')"):
        # Add user message
        st.session_state.chat_messages.append({
            "role": "user",
            "content": prompt
        })
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get bot response
        with st.chat_message("assistant"):
            with st.spinner("💭 Düşünüyorum..."):
                try:
                    # Check for special commands
                    if prompt.lower() in ['yardım', 'help', 'komutlar']:
                        response = st.session_state.chatbot.get_help_message()
                    else:
                        response = st.session_state.chatbot.handle_message(prompt)
                    
                    st.markdown(response)
                    
                    # Add to messages
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": response
                    })
                
                except Exception as e:
                    error_msg = f"❌ Hata: {str(e)}"
                    st.error(error_msg)
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })
    
    # Clear chat button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🗑️ Sohbeti Temizle", use_container_width=True):
            st.session_state.chat_messages = []
            st.rerun()


def receipt_processing_page(bank_hint):
    """Receipt processing page."""
    st.markdown("## 📤 Dekont Yükleme")
    
    uploaded_file = st.file_uploader(
        "PDF dekont dosyası seçin",
        type=['pdf'],
        help="Banka dekont PDF'inizi buraya yükleyin"
    )
    
    if uploaded_file:
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        # Process button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 İşle", type="primary", use_container_width=True):
                # Check if pipeline is loaded
                if st.session_state.pipeline is None:
                    with st.spinner("🚀 Modeller yükleniyor..."):
                        st.session_state.pipeline, st.session_state.chatbot = load_pipeline()
                    st.success("✅ Modeller yüklendi!")
                
                # Process
                with st.spinner("⏳ Dekont işleniyor..."):
                    try:
                        result = st.session_state.pipeline.process_from_file(
                            tmp_path,
                            bank=bank_hint
                        )
                        st.session_state.result = result
                        st.rerun()
                    
                    except Exception as e:
                        st.error(f"❌ Hata: {str(e)}")
                        st.exception(e)
    
    # Display results if available
    if st.session_state.result:
        display_results(st.session_state.result)
        
        # Download button
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            result_json = json.dumps(st.session_state.result, indent=2, ensure_ascii=False)
            st.download_button(
                label="📥 JSON İndir",
                data=result_json,
                file_name=f"receipt_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )


def chatbot_page():
    """Chatbot page - standalone like ChatGPT."""
    st.markdown("## 🤖 AI Asistan")
    
    # Check if chatbot is loaded
    if st.session_state.chatbot is None:
        st.warning("⚠️ AI Asistan henüz yüklenmedi!")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🚀 AI Asistan'ı Başlat", type="primary", use_container_width=True):
                with st.spinner("🤖 AI Asistan yükleniyor..."):
                    st.session_state.pipeline, st.session_state.chatbot = load_pipeline()
                st.success("✅ AI Asistan hazır!")
                st.rerun()
        
        st.info("""
        ### 💡 AI Asistan Özellikleri:
        
        - 💬 **Genel Sohbet**: Merhaba, nasılsın gibi genel sorular
        - 🏠 **Kiracı Sorguları**: "Furkan Turan kimdir?" 
        - 💰 **Ödeme Bilgileri**: Kiracı ödeme durumları
        - 📋 **Komut Listesi**: "yardım" yazarak tüm komutları gör
        - 📄 **PDF Yükleme**: Dekont PDF'i yükleyerek analiz
        
        **Örnek Sorular:**
        - "Merhaba"
        - "Yardım"
        - "Furkan Turan'ın ödeme durumu nedir?"
        - "Kiracı bilgisi"
        """)
        return
    
    # Create two columns: chat on left, PDF upload on right
    col_chat, col_pdf = st.columns([2, 1])
    
    with col_pdf:
        st.markdown("### 📤 Dekont Yükle")
        
        uploaded_file = st.file_uploader(
            "PDF dekont",
            type=['pdf'],
            help="Dekont PDF'ini yükle ve AI ile konuş",
            key="chatbot_pdf_uploader"
        )
        
        if uploaded_file:
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            # Process button
            if st.button("🔄 Dekontu İşle", type="primary", use_container_width=True):
                with st.spinner("⏳ Dekont işleniyor..."):
                    try:
                        # Process with chatbot
                        result = st.session_state.chatbot.process_receipt(tmp_path)
                        
                        # Extract key info from result
                        if isinstance(result, dict) and 'pipeline_result' in result:
                            pipeline = result['pipeline_result']
                            summary = pipeline.get('summary', '')
                            matching = pipeline.get('matching', {})
                            ocr_data = pipeline.get('ocr_data', {})
                            
                            # Format beautiful response
                            formatted_response = f"""
📄 **Dekont Analizi Tamamlandı!**

{summary}

---

🎯 **Eşleşme Sonucu:**
   • Durum: {'✅ Eşleşti' if matching.get('status') == 'matched' else '⚠️ Manuel İnceleme' if matching.get('status') == 'manual_review' else '❌ Eşleşmedi'}
   • Güven Skoru: **{matching.get('confidence', 0):.1f}%**
   • Mülk Sahibi ID: {matching.get('owner_id', 'Yok')}
   • Kiracı ID: {matching.get('customer_id', 'Yok')}
   • Mülk ID: {matching.get('property_id', 'Yok')}

📊 **Eşleşme Skorları:**
   • IBAN: {matching.get('scores', {}).get('iban', 0)*100:.0f}%
   • Tutar: {matching.get('scores', {}).get('amount', 0)*100:.0f}%
   • İsim: {matching.get('scores', {}).get('name', 0)*100:.0f}%
   • Adres: {matching.get('scores', {}).get('address', 0)*100:.0f}%
   • Gönderen: {matching.get('scores', {}).get('sender', 0)*100:.0f}%

💬 **Mesajlar:**
{chr(10).join(f"   • {msg}" for msg in matching.get('messages', ['Bilgi yok']))}

---

💡 **Daha fazla bilgi için:**
   • "Detayları göster" yaz
   • "Furkan Turan kimdir?" gibi sorular sor
   • "geçmiş ödemelerini göster" diye sor
"""
                        else:
                            # Fallback to raw response
                            formatted_response = result if isinstance(result, str) else str(result)
                        
                        # Add to chat messages
                        st.session_state.chat_messages.append({
                            "role": "user",
                            "content": f"📄 Dekont yüklendi: {uploaded_file.name}"
                        })
                        
                        st.session_state.chat_messages.append({
                            "role": "assistant",
                            "content": formatted_response
                        })
                        
                        st.success("✅ Dekont işlendi!")
                        st.rerun()
                    
                    except Exception as e:
                        error_msg = f"❌ Hata: {str(e)}"
                        st.error(error_msg)
                        st.session_state.chat_messages.append({
                            "role": "assistant",
                            "content": error_msg
                        })
            
            # Show upload info
            st.info(f"""
            **Yüklenen:**
            - 📄 {uploaded_file.name}
            - 📏 {uploaded_file.size / 1024:.1f} KB
            
            "🔄 Dekontu İşle" butonuna tıkla
            """)
        else:
            st.info("""
            💡 **Nasıl Kullanılır?**
            
            1. PDF dekont yükle
            2. "Dekontu İşle" tıkla
            3. Sonuç chat'te görünür
            4. AI ile konuşmaya devam et
            """)
    
    with col_chat:
        # Chatbot is loaded - display chat interface
        display_chatbot()


def main():
    """Main dashboard function."""
    
    # Header
    st.markdown('<div class="main-header">🏢 Emlak Ödeme Yönetim Sistemi</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Ayarlar")
        
        # Models status
        if st.session_state.pipeline is not None:
            st.success("✅ Modeller yüklü")
            st.success("🤖 AI Asistan aktif")
        else:
            st.warning("⚠️ Modeller yüklenmedi")
            st.info("💡 İlk kullanımda otomatik yüklenecek")
        
        # Manual load button
        if st.session_state.pipeline is None:
            if st.button("🚀 Modelleri Şimdi Yükle", type="primary", use_container_width=True):
                with st.spinner("⏳ Yükleniyor... (~10 saniye)"):
                    st.session_state.pipeline, st.session_state.chatbot = load_pipeline()
                st.success("✅ Tamamlandı!")
                st.rerun()
        
        st.markdown("---")
        
        # Bank selection
        st.markdown("### 🏦 Dekont Ayarları")
        bank_options = ["Otomatik", "halkbank", "kuveytturk", "yapikredi", "ziraatbank"]
        selected_bank = st.selectbox("Banka Seçimi", bank_options)
        bank_hint = None if selected_bank == "Otomatik" else selected_bank
        
        # Enable matching
        enable_matching = st.checkbox("🔗 Eşleşme Analizi", value=True)
        
        st.markdown("---")
        
        # Info
        st.markdown("### ℹ️ Bilgi")
        st.info("""
        **"Modelleri Yükle" Butonu:**
        - NLP modellerini hafızaya yükler
        - BERT modelini başlatır (~10 sn)
        - İlk kullanımda gerekli
        - Sonra hızlı çalışır
        
        **Sayfalar:**
        - 📤 Dekont: PDF işleme
        - 🤖 AI: ChatGPT gibi sohbet
        """)
        
        st.markdown("---")
        st.caption(f"v2.0.0 | {datetime.now().strftime('%Y')}")
    
    # Main tabs
    tab1, tab2 = st.tabs(["📤 Dekont İşleme", "🤖 AI Asistan"])
    
    with tab1:
        receipt_processing_page(bank_hint)
    
    with tab2:
        chatbot_page()


if __name__ == "__main__":
    main()
