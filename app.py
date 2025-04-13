from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import os
import google.generativeai as genai
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

# Initialize Flask app
app = Flask(__name__, 
    static_folder='static',    # Specify the static folder
    template_folder='templates' # Specify the template folder
)
CORS(app)

# Enable debug logging
app.logger.setLevel('DEBUG')

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///soiltech.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy()
db.init_app(app)

# Load environment variables
load_dotenv()

# Configure Gemini AI
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Pre-fetched soil data
SOIL_DATABASE = {
    "soil_types": {
        "sandy": {
            "characteristics": "Light, warm, dry, acidic, low in nutrients",
            "best_plants": ["Carrots", "Potatoes", "Radishes", "Lettuce"],
            "ph_range": "5.5-6.5",
            "improvements": ["Add organic matter", "Use mulch", "Add lime if too acidic"]
        },
        "clay": {
            "characteristics": "Heavy, cold, nutrient-rich, retains water",
            "best_plants": ["Roses", "Perennials", "Summer vegetables", "Fruit trees"],
            "ph_range": "6.0-7.0",
            "improvements": ["Add organic matter", "Avoid working when wet", "Add gypsum"]
        },
        "loamy": {
            "characteristics": "Perfect balance, fertile, well-draining",
            "best_plants": ["Most plants thrive", "Vegetables", "Fruits", "Herbs"],
            "ph_range": "6.0-7.0",
            "improvements": ["Maintain with compost", "Regular mulching", "Crop rotation"]
        }
    },
    "common_problems": {
        "poor_drainage": {
            "symptoms": ["Water pooling", "Root rot", "Yellowing leaves"],
            "solutions": ["Add organic matter", "Install drainage", "Raise beds"]
        },
        "nutrient_deficiency": {
            "symptoms": ["Yellow leaves", "Stunted growth", "Poor yields"],
            "solutions": ["Soil test", "Add appropriate fertilizer", "Compost"]
        }
    },
    "seasonal_tips": {
        "spring": ["Test soil pH", "Add compost", "Start planting"],
        "summer": ["Mulch soil", "Regular watering", "Monitor for issues"],
        "fall": ["Add organic matter", "Plant cover crops", "Prepare for winter"],
        "winter": ["Plan for spring", "Protect soil", "Study soil tests"]
    }
}

# Predefined questions categorized
SOIL_QUESTIONS = {
    "Basic Soil Info": [
        "What are the different types of soil?",
        "How can I check if my soil is fertile?",
        "What are the major nutrients in soil?",
    ],
    "Moisture & Drainage": [
        "How do I know if my soil has enough moisture?",
        "Which soil retains water better: clay or sandy?",
        "Tips for improving soil drainage?",
    ],
    "Planting Guide": [
        "Which soil type is best for growing vegetables?",
        "Can I plant fruit trees in clay soil?",
        "What crops grow best in loamy soil?",
    ],
    "Soil Nutrients": [
        "How can I increase nitrogen in my soil naturally?",
        "What does potassium do for soil health?",
        "Signs that my soil lacks phosphorus?",
    ],
    "pH & Temperature": [
        "How do I check soil pH at home?",
        "What is the ideal soil pH for tomatoes?",
        "How does soil temperature affect plant growth?",
    ],
    "Soil Health": [
        "How can I make my soil healthy again?",
        "What causes soil erosion and how to prevent it?",
        "What are organic ways to improve soil fertility?",
    ],
    "Environmental Impact": [
        "How does climate affect soil condition?",
        "What are the effects of deforestation on soil?",
        "How does soil support the ecosystem?",
    ]
}

# Enhanced context for better AI responses
SOIL_CONTEXT = {
    "types": ["Sandy", "Clay", "Loamy", "Silt", "Peat", "Chalk", "Saline"],
    "properties": ["texture", "structure", "pH", "fertility", "drainage"],
    "nutrients": ["Nitrogen", "Phosphorus", "Potassium", "Calcium", "Magnesium"],
    "indicators": ["color", "smell", "texture", "water retention", "plant growth"],
}

def get_enhanced_response(user_message):
    try:
        # Create a context-aware prompt
        prompt = f"""As a soil expert, please provide a detailed but concise answer to:
        "{user_message}"

        Consider these aspects in your response:
        - Soil types and their characteristics
        - Scientific accuracy and practical advice
        - Local environmental factors
        - Common problems and solutions
        - Best practices for soil management
        - Sustainable farming techniques
        
        Include specific examples and actionable steps when relevant.
        Keep the response informative but easy to understand.
        """

        response = model.generate_content(prompt)
        return {
            'response': response.text,
            'suggested_questions': get_related_questions(user_message)
        }
    except Exception as e:
        return {
            'response': f"I apologize, but I encountered an error: {str(e)}",
            'suggested_questions': get_default_questions()
        }

def get_related_questions(user_message):
    # Find relevant category based on user's question
    related = []
    message_lower = user_message.lower()
    
    if any(word in message_lower for word in ["moisture", "water", "drain"]):
        related = SOIL_QUESTIONS["Moisture & Drainage"]
    elif any(word in message_lower for word in ["plant", "grow", "crop"]):
        related = SOIL_QUESTIONS["Planting Guide"]
    elif any(word in message_lower for word in ["nutrient", "nitrogen", "phosphorus"]):
        related = SOIL_QUESTIONS["Soil Nutrients"]
    elif any(word in message_lower for word in ["ph", "temperature"]):
        related = SOIL_QUESTIONS["pH & Temperature"]
    else:
        # Return questions from a random category if no match
        import random
        category = random.choice(list(SOIL_QUESTIONS.keys()))
        related = SOIL_QUESTIONS[category]
    
    return related[:3]  # Return top 3 related questions

def get_default_questions():
    return [
        "What are the different types of soil?",
        "How can I check if my soil is fertile?",
        "Tips for improving soil drainage?"
    ]

# Routes
@app.route('/')
def home():
    return render_template('index.html', questions=SOIL_QUESTIONS)

@app.route('/test')
def test():
    return jsonify({'status': 'Server is working!'})

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    try:
        new_user = User(
            email=data['email'],
            password=data['password']
        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User created successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    
    if user and user.password == data['password']:
        return jsonify({'message': 'Login successful'})
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({
            'response': 'Please ask a question about soil.',
            'suggested_questions': get_default_questions()
        })
    
    if not GEMINI_API_KEY:
        return jsonify({
            'response': 'API key not configured. Please add your Gemini API key.',
            'suggested_questions': get_default_questions()
        })
    
    result = get_enhanced_response(user_message)
    return jsonify(result)

def init_db():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    print("Starting Flask server...")  # Debug print
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000) 