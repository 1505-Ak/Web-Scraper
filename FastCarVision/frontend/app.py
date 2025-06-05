import streamlit as st
import requests
import json
from PIL import Image
import io
import time
from typing import Dict, Any

# Page configuration
st.set_page_config(
    page_title="🚗 FastCarVision",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .feature-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    
    .result-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 4px solid #28a745;
    }
    
    .metric-card {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
    }
    
    .upload-section {
        border: 2px dashed #667eea;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

# Backend API configuration
API_BASE_URL = "http://localhost:8000"

def check_backend_health() -> bool:
    """Check if backend is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def upload_and_process_image(image_file) -> Dict[str, Any]:
    """Upload image to backend and get results"""
    try:
        files = {"file": ("image.jpg", image_file, "image/jpeg")}
        response = requests.post(
            f"{API_BASE_URL}/process-and-search", 
            files=files,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Backend error: {response.status_code}")
            return None
    
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")
        return None

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🚗 FastCarVision</h1>
        <p>Real-Time Car Recognition & Web Scraper</p>
        <p><em>Upload a car image and find matching listings instantly!</em></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🔍 How It Works")
        st.markdown("""
        1. **📸 Upload** a car image
        2. **🤖 AI Detection** identifies the vehicle
        3. **🌐 Smart Scraping** finds matching listings
        4. **⚡ Results** delivered in real-time
        """)
        
        st.markdown("### 🎯 Features")
        st.markdown("""
        - **YOLO & CLIP** powered detection
        - **Multiple sources** (AutoTrader, Cars.com)
        - **Real-time processing**
        - **Advanced filtering**
        """)
        
        # Backend status
        if check_backend_health():
            st.success("🟢 Backend Online")
        else:
            st.error("🔴 Backend Offline")
            st.info("Start the backend with: `uvicorn main:app --reload`")
    
    # Main content
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📤 Upload Car Image")
        
        uploaded_file = st.file_uploader(
            "Choose a car image...",
            type=['png', 'jpg', 'jpeg'],
            help="Upload a clear side-view image of a car for best results"
        )
        
        if uploaded_file is not None:
            # Display uploaded image
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_column_width=True)
            
            # Image info
            st.info(f"**Image Size:** {image.size[0]} x {image.size[1]} pixels")
            
            # Process button
            if st.button("🚀 Analyze & Search", type="primary", use_container_width=True):
                if not check_backend_health():
                    st.error("❌ Backend is not running. Please start the backend server.")
                    return
                
                with st.spinner("🔍 Analyzing image and searching for listings..."):
                    # Reset file pointer
                    uploaded_file.seek(0)
                    
                    # Process image
                    results = upload_and_process_image(uploaded_file)
                    
                    if results:
                        st.session_state['results'] = results
                        st.rerun()
    
    with col2:
        st.markdown("### 📊 Results")
        
        if 'results' in st.session_state:
            results = st.session_state['results']
            
            # Metrics
            col_metric1, col_metric2, col_metric3 = st.columns(3)
            
            with col_metric1:
                st.markdown("""
                <div class="metric-card">
                    <h3>{}</h3>
                    <p>Listings Found</p>
                </div>
                """.format(results.get('total_results', 0)), unsafe_allow_html=True)
            
            with col_metric2:
                st.markdown("""
                <div class="metric-card">
                    <h3>{:.2f}s</h3>
                    <p>Processing Time</p>
                </div>
                """.format(results.get('processing_time', 0)), unsafe_allow_html=True)
            
            with col_metric3:
                st.markdown("""
                <div class="metric-card">
                    <h3>{}</h3>
                    <p>Sources Used</p>
                </div>
                """.format(len(results.get('sources_used', []))), unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Search query
            st.markdown(f"**🔍 Search Query:** `{results.get('query', 'N/A')}`")
            
            # Listings
            listings = results.get('listings', [])
            if listings:
                st.markdown("### 🚗 Found Listings")
                
                for i, listing in enumerate(listings[:10]):  # Show first 10
                    with st.expander(f"🚙 {listing.get('title', 'Unknown Vehicle')}", expanded=i < 3):
                        listing_col1, listing_col2 = st.columns([2, 1])
                        
                        with listing_col1:
                            st.markdown(f"**Price:** {listing.get('price', 'N/A')}")
                            st.markdown(f"**Make:** {listing.get('make', 'N/A')}")
                            st.markdown(f"**Model:** {listing.get('model', 'N/A')}")
                            st.markdown(f"**Year:** {listing.get('year', 'N/A')}")
                            if listing.get('mileage'):
                                st.markdown(f"**Mileage:** {listing['mileage']}")
                            if listing.get('location'):
                                st.markdown(f"**Location:** {listing['location']}")
                        
                        with listing_col2:
                            st.markdown(f"**Source:** `{listing.get('source', 'N/A')}`")
                            if listing.get('listing_url'):
                                st.markdown(f"[🔗 View Listing]({listing['listing_url']})")
                            
                            # Display image if available
                            if listing.get('image_url'):
                                try:
                                    st.image(listing['image_url'], width=150)
                                except:
                                    st.info("📷 Image not available")
            else:
                st.warning("⚠️ No listings found. Try a different image or check your internet connection.")
        
        else:
            st.info("👆 Upload an image to see results here")
    
    # Footer
    st.markdown("---")
    
    # Demo section
    with st.expander("🎯 Try Demo Examples"):
        st.markdown("""
        ### Example Search Queries
        Try uploading images of these popular car types:
        
        - **🏎️ Sports Cars:** Ferrari, Lamborghini, Porsche
        - **🚗 Sedans:** Toyota Camry, Honda Accord, BMW 3 Series
        - **🚙 SUVs:** Ford Explorer, Jeep Wrangler, Range Rover
        - **🛻 Trucks:** Ford F-150, Chevrolet Silverado, RAM 1500
        """)
    
    # About section
    with st.expander("ℹ️ About FastCarVision"):
        st.markdown("""
        ### 🚀 Technology Stack
        
        **Backend:**
        - **FastAPI** for high-performance API
        - **YOLO v8** for car detection
        - **CLIP** for visual similarity
        - **BeautifulSoup & aiohttp** for web scraping
        
        **Frontend:**
        - **Streamlit** for modern web interface
        - **Real-time processing** with async operations
        
        **Data Sources:**
        - AutoTrader
        - Cars.com
        - eBay Motors (configurable)
        
        ### 🎯 Features
        - Real-time car detection and classification
        - Intelligent web scraping from multiple sources
        - CLIP-based visual similarity search
        - Async processing for maximum speed
        - Modern, responsive UI
        """)

if __name__ == "__main__":
    main() 