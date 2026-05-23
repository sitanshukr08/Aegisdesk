import io
import warnings

from PIL import Image

warnings.filterwarnings("ignore", category=FutureWarning)
import google.generativeai as genai

from app.config.settings import settings
from src.aegisdesk.observability.logger import get_logger

logger = get_logger("aegisdesk.vision")

# Configure Gemini with the API key from settings
genai.configure(api_key=settings.gemini_api_key)

def analyze_screenshot(image_bytes: bytes, user_query: str = "") -> str:
    """Uses Google Gemini to extract error text and context from a screenshot."""
    try:
        logger.debug("Analyzing uploaded screenshot...")
        # Convert raw bytes into a PIL Image object
        image = Image.open(io.BytesIO(image_bytes))
        
        prompt = "Analyze this IT support screenshot. Extract any exact error codes, stop codes, system messages, or application names visible. Be concise and describe what the screen shows."
        if user_query:
            prompt += f"\nThe user also added this context: '{user_query}'"

        # 1. Get ALL valid generation models available to your API key
        available_models = [
            m.name for m in genai.list_models() 
            if 'generateContent' in m.supported_generation_methods
        ]
        
        # 2. Safely pick the best standard Vision model
        working_model = None
        preferred_models = [
            'models/gemini-1.5-flash', 
            'models/gemini-1.5-pro', 
            'models/gemini-1.0-pro-vision', 
            'models/gemini-pro-vision'
        ]
        
        for pref in preferred_models:
            if pref in available_models:
                working_model = pref
                break
                
        # If standard models aren't found, safely pick the first available one that isn't robotics
        if not working_model:
            for m in available_models:
                if 'robotics' not in m and 'preview' not in m:
                    working_model = m
                    break
        
        # Absolute fallback
        if not working_model and available_models:
            working_model = available_models[-1]

        logger.info(f"Vision service connected. Using model: {working_model}")

        # 3. Initialize the model and generate
        model = genai.GenerativeModel(working_model)
        response = model.generate_content([prompt, image])
        
        return response.text
        
    except Exception as e:
        logger.error(f"Gemini Vision Failed: {e}", exc_info=True)
        return user_query # Fallback to just the text if vision fails