from fastapi import FastAPI, HTTPException, Depends
from fastapi_csrf_protect import CsrfProtect
from pydantic import BaseModel, EmailStr
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from datetime import datetime
import uvicorn

# Load environment variables
load_dotenv()

# FastAPI instance
app = FastAPI()

# MongoDB connection
MONGO_URI = os.getenv("URI")
client = MongoClient(MONGO_URI)
db = client.help_nepal_fund
donors_collection = db.donors

# Add CORS middleware
origins = os.getenv("ALLOWED_ORIGINS")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CSRF Configuration
class CsrfSettings(BaseModel):
    secret_key: str = os.getenv("CSRF_SECRET_KEY")

@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings()

# Models
class Donor(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    amount: float
    thoughts: str
    date: str
    contributionsCount: int = 1
    publish_name: bool

class DonorResponse(BaseModel):
    first_name: str
    last_name: str
    amount: float
    thoughts: str
    date: str
    contributionsCount: int
    publish_name: bool

from fastapi import Cookie

@app.get("/csrf_token")
async def get_csrf_token(csrf_protect: CsrfProtect = Depends()):
    csrf_token = csrf_protect.generate_csrf()
    return {"csrfToken": csrf_token}


# Add donor endpoint
@app.post("/add_donor")
async def add_donor(donor: Donor, csrf_protect: CsrfProtect = Depends()):
    try:
        # CSRF Validation
        csrf_protect.validate_csrf(csrf_protect)
    except Exception as e:
        raise HTTPException(status_code=403, detail=f"CSRF validation failed: {str(e)}")

    # Donor processing logic here
    existing_donor = donors_collection.find_one({"email": donor.email})
    if existing_donor:
        updated_donor = {
            "first_name": existing_donor["first_name"],
            "last_name": existing_donor["last_name"],
            "amount": existing_donor["amount"] + donor.amount,
            "thoughts": donor.thoughts,
            "date": donor.date,
            "publish_name": donor.publish_name,
            "contributionsCount": existing_donor["contributionsCount"] + 1
        }
        donors_collection.update_one({"email": donor.email}, {"$set": updated_donor})
        return {"message": "Donor information updated successfully", "donor": updated_donor}
    else:
        donor_dict = donor.dict()
        donors_collection.insert_one(donor_dict)
        donor_dict.pop("_id", None)
        return {"message": "Donor added successfully", "donor": donor_dict}

# List donors endpoint
@app.get("/list_donors", response_model=list[DonorResponse])
async def list_donors():
    donors = donors_collection.find({}, {"_id": 0, "email": 0})
    return list(donors)

# Run the FastAPI app
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
