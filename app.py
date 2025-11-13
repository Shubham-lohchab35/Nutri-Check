from flask import Flask, request, jsonify
import requests
from flask_cors import CORS  # <-- Handles cross-origin requests

app = Flask(__name__)
CORS(app)  # <-- Enable CORS

# Basic health scoring
def health_score(nf):
    score = 100
    reasons = []
    if nf['calories'] > 700:
        score -= 40
        reasons.append('High calories')
    if nf['sugars'] > 30:
        score -= 30
        reasons.append('High sugar')
    if nf['saturated_fat'] > 10:
        score -= 20
        reasons.append('High saturated fat')
    if nf['sodium'] > 1000:
        score -= 15
        reasons.append('High sodium')
    
    label = "Healthy" if score >= 85 else "Moderate" if score >= 60 else "Unhealthy"
    return {"score": score, "label": label, "reasons": reasons}

# Personalized advice based on user profile
def personalized_advice(nf, profile):
    advice = []
    cond = profile.get('conditions', '').lower()
    goal = profile.get('goal', '').lower()
    
    if 'diabetes' in cond and nf['sugars'] > 15:
        advice.append("Avoid: High sugar for diabetes")
    if 'hypertension' in cond and nf['sodium'] > 500:
        advice.append("Avoid: High sodium for hypertension")
    if goal == 'weight loss' and nf['calories'] > 400:
        advice.append("Too many calories for weight loss")
    return advice

@app.route("/check_food", methods=["POST"])
def check_food():
    data = request.json
    food_name = data.get("food")
    profile = data.get("profile", {})

    if not food_name:
        return jsonify({"error": "No food provided"}), 400

    # Query OpenFoodFacts API
    url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={food_name.replace(' ', '%20')}&search_simple=1&action=process&json=1&page_size=1"
    try:
        r = requests.get(url, timeout=5).json()
    except Exception as e:
        return jsonify({"error": "Failed to fetch from OpenFoodFacts", "details": str(e)}), 500

    if not r.get('products'):
        return jsonify({"error": "Food not found"}), 404

    product = r['products'][0]
    nutr = product.get('nutriments', {})
    nf = {
        "calories": nutr.get('energy-kcal_100g', 0),
        "sugars": nutr.get('sugars_100g', 0),
        "saturated_fat": nutr.get('saturated-fat_100g', 0),
        "sodium": nutr.get('sodium_100g', 0),
        "protein": nutr.get('proteins_100g', 0)
    }

    score = health_score(nf)
    advice = personalized_advice(nf, profile)

    return jsonify({
        "product_name": product.get("product_name", "Unknown"),
        "nutriments": nf,
        "health_score": score,
        "personalized_advice": advice
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
