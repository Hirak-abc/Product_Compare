from flask import Flask, request, jsonify
import pandas as pd
import os
from flask_cors import CORS
import json

# Flask App
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Get the directory of the current script
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Category mapping to Excel files
CATEGORIES = {
    "headphones": os.path.join(CURRENT_DIR, "Cleaned_H.xlsx"),
    "phones": os.path.join(CURRENT_DIR, "Cleaned_P.xlsx"),
    "laptops": os.path.join(CURRENT_DIR, "Cleaned_L.xlsx"),
    "books": os.path.join(CURRENT_DIR, "Cleaned_B.xlsx")
}

def parse_price(price):
    try:
        return float(str(price).replace(",", "").strip())
    except:
        return float('inf')

def parse_rating(rating):
    try:
        return float(str(rating).strip())
    except:
        return 0.0

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Welcome to the Product API. Use /api/categories to get available categories."})

@app.route("/api/categories", methods=["GET"])
def get_categories():
    return jsonify(list(CATEGORIES.keys()))

@app.route("/api/products", methods=["GET"])
def get_products():
    category = request.args.get("category", "").lower()

    if category not in CATEGORIES:
        return jsonify({"error": "Invalid category selected."}), 400

    try:
        df = pd.read_excel(CATEGORIES[category])
    except Exception as e:
        return jsonify({"error": f"Failed to load data for {category}. Error: {str(e)}"}), 500

    products = df["Name"].dropna().tolist()
    return jsonify(products)

@app.route("/api/compare", methods=["GET"])
def compare_product():
    category = request.args.get("category", "").lower()
    product_name = request.args.get("product", "")
    include_buyhatke = request.args.get("include_buyhatke", "") == "yes"

    if category not in CATEGORIES:
        return jsonify({"error": "Invalid category selected."}), 400

    try:
        df = pd.read_excel(CATEGORIES[category])
    except Exception as e:
        return jsonify({"error": f"Failed to load data for {category}. Error: {str(e)}"}), 500

    if product_name not in df["Name"].values:
        return jsonify({"error": f"Product '{product_name}' not found."}), 404

    product = df[df["Name"] == product_name].iloc[0].to_dict()
    
    # Parse the relevant data
    amazon_price = parse_price(product.get("Price in Amazon"))
    flipkart_price = parse_price(product.get("Price in Flipkart"))
    amazon_rating = parse_rating(product.get("Rating in Amazon"))
    flipkart_rating = parse_rating(product.get("Rating in Flipkart"))
    amazon_url = product.get("URL in Amazon", "")
    flipkart_url = product.get("URL in Flipkart", "")

    better_price = (
        "Amazon" if amazon_price < flipkart_price else
        "Flipkart" if flipkart_price < amazon_price else
        "Both (Same Price)"
    )
    
    better_rating = (
        "Amazon" if amazon_rating > flipkart_rating else
        "Flipkart" if flipkart_rating > amazon_rating else
        "Both (Same Rating)"
    )

    buyhatke_search_url = ""
    if include_buyhatke:
        product_url = amazon_url or flipkart_url
        if product_url:
            encoded_url = product_url.replace("&", "%26")
            buyhatke_search_url = f"https://buyhatke.com/?q={encoded_url}"

    response_data = {
        "product_name": product_name,
        "amazon_price": float(amazon_price) if amazon_price != float('inf') else None,
        "flipkart_price": float(flipkart_price) if flipkart_price != float('inf') else None,
        "amazon_rating": float(amazon_rating),
        "flipkart_rating": float(flipkart_rating),
        "better_price": better_price,
        "better_rating": better_rating,
        "amazon_url": amazon_url,
        "flipkart_url": flipkart_url,
        "buyhatke_search_url": buyhatke_search_url if include_buyhatke else None
    }

    return jsonify(response_data)

if __name__ == "__main__":
    app.run(debug=True)
