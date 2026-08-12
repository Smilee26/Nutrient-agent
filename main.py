import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="IBM Nutrition AI Agent API")

class QueryRequest(BaseModel):
    query: str

# Database of standard items per single unit/serving
NUTRITION_DB = {
    "roti": {"calories": 120, "protein": 3, "carbs": 20, "fats": 2},
    "chapati": {"calories": 120, "protein": 3, "carbs": 20, "fats": 2},
    "rice": {"calories": 200, "protein": 4, "carbs": 44, "fats": 1},
    "dalia": {"calories": 150, "protein": 5, "carbs": 28, "fats": 2},
    "dal": {"calories": 160, "protein": 9, "carbs": 22, "fats": 3},
    "daal": {"calories": 160, "protein": 9, "carbs": 22, "fats": 3},
    "egg": {"calories": 70, "protein": 6, "carbs": 1, "fats": 5},
    "paneer": {"calories": 250, "protein": 14, "carbs": 4, "fats": 18},
    "curd": {"calories": 100, "protein": 5, "carbs": 6, "fats": 4},
    "milk": {"calories": 150, "protein": 8, "carbs": 12, "fats": 8},
}

@app.get("/")
def read_root():
    return {"status": "online"}

@app.post("/query")
def process_query(request: QueryRequest):
    text = request.query.lower().strip()
    
    total_stats = {"calories": 0, "protein": 0, "carbs": 0, "fats": 0}
    found_any = False

    # Check for items and parse numbers (e.g., "2 roti", "1 rice")
    for item, values in NUTRITION_DB.items():
        if item in text:
            found_any = True
            # Look for numbers right before or around the food item name
            match = re.search(rf'(\d+)\s*(?:bowl|plate|cup|piece|pcs|g|gram)?\s*{item}', text)
            qty = int(match.group(1)) if match else 1
            
            total_stats["calories"] += values["calories"] * qty
            total_stats["protein"] += values["protein"] * qty
            total_stats["carbs"] += values["carbs"] * qty
            total_stats["fats"] += values["fats"] * qty

    # Fallback if unknown food item is entered
    if not found_any:
        total_stats = {"calories": 200, "protein": 8, "carbs": 25, "fats": 6}

    return {
        "status": "success",
        "query": request.query,
        "nutrition": total_stats,
        "message": f"Tracked nutrition: {total_stats['calories']} kcal, {total_stats['protein']}g protein, {total_stats['carbs']}g carbs, {total_stats['fats']}g fats."
    }