from fastapi import FastAPI
from wed_expert_genspark_integration import GensparktWEDAgent, ProductClassification

app = FastAPI()
genspark_agent = GensparktWEDAgent()

@app.get("/")
def root():
    return {"message": "VED Expert is alive"}
@app.post("/api/genspark/classify")
async def classify_with_genspark(
    name: str,
    material: str,
    function: str,
    origin_country: str,
    value: float
):
    try:
        product = ProductClassification(
            name=name, material=material, function=function,
            processing_level="готовое изделие",
            origin_country=origin_country, value=value
        )
        
        result = genspark_agent.determine_tn_ved(product)
        cost_calc = genspark_agent.calculate_total_cost(result, value)
        
        return {
            "success": True,
            "tn_ved_code": result.code,
            "description": result.description,
            "confidence": f"{result.confidence*100:.1f}%",
            "total_cost": cost_calc['total_cost'],
            "duty_amount": cost_calc['duty_amount'],
            "vat_amount": cost_calc['vat_amount']
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
