import os
from flask import Flask, request, jsonify
from supabase import create_client, Client
import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import requests
from io import BytesIO

# Load Supabase credentials from environment variables
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_API_KEY = os.getenv('SUPABASE_API_KEY')

# Initialize the Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_API_KEY)

# Load the CLIP model and processor
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# Initialize the Flask app
app = Flask(__name__)

def get_image_embedding(image_url):
    """
    Downloads an image from the given URL and returns its embedding vector.
    """
    try:
        response = requests.get(image_url)
        response.raise_for_status()  # Ensure we raise an error for bad responses
        image = Image.open(BytesIO(response.content)).convert("RGB")
    except Exception as e:
        print(f"Error downloading or processing image: {e}")
        return None

    # Process the image and get embeddings
    inputs = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        outputs = model.get_image_features(**inputs)

    # Normalize the embedding
    embedding = outputs[0].numpy().tolist()
    return embedding

def store_image_data(image_url, user_id):
    """
    Processes the image to get its embedding and stores the URL, embedding, and user_id in Supabase.
    
    Parameters:
        image_url (str): The URL of the image to be stored.
        user_id (str): The user ID associated with the image.
    """
    embedding = get_image_embedding(image_url)
    if embedding is None:
        return {"error": "Failed to get embedding for the image."}, 400

    # Prepare the data to insert
    data = {
        "user_id": user_id,
        "image_url": image_url,
        "embedding": embedding,
    }

    # Insert the data into the 'images' table in Supabase
    try:
        response = supabase.table("images").insert(data).execute()

        # Check if the response indicates success
        if response.data:
            return {"message": f"Successfully stored: {image_url} for user_id: {user_id}"}, 201
        else:
            return {"error": f"Failed to store {image_url}: {response.error}"}, 400
    except Exception as e:
        return {"error": f"An error occurred while inserting data: {e}"}, 500

@app.route('/insert-image', methods=['POST'])
def insert_image():
    """
    Endpoint to insert image data.
    Expects a JSON body with 'image_url' and 'user_id'.
    """
    data = request.json
