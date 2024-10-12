from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from pymongo import MongoClient

from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import os
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# FastAPI instance
app = FastAPI()

# Enable CORS for React (localhost:3000) or other front-end origins
origins = [
    "http://localhost:3000",  # React local server
    "http://127.0.0.1:3000",  # Another potential address for local React
    # Add other origins as needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Origins that can access the API
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# MongoDB client connection
MONGO_URI = os.getenv("URI")  # Load MongoDB URI from .env
client = MongoClient(MONGO_URI)

db = client.help_nepal_fund  # Database
donors_collection = db.donors  # Collection

# Pydantic model for Donor input
class Donor(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    amount: float
    thoughts: str
    date: str  # Use the ISO format from the client
    contributionsCount: int = 1
    publish_name: bool

# Pydantic model for Donor response (without email)
    date: str  # Use the ISO format from the client
class DonorResponse(BaseModel):
    first_name: str
    last_name: str
    amount: float
    thoughts: str
    date: str
    contributionsCount: int
    publish_name: bool

# API to add donor (excluding _id from the response)
@app.post("/add_donor")
async def add_donor(donor: Donor):
    # Check if donor with this email already exists
    if donors_collection.find_one({"email": donor.email}):
        raise HTTPException(status_code=400, detail="Donor with this email already exists.")
    
    # Insert donor into collection
    donor_dict = donor.dict()
    donors_collection.insert_one(donor_dict)
    
    # Remove _id from the response
    donor_dict.pop("_id", None)  # Remove the _id field if it exists
    
    return {"message": "Donor added successfully", "donor": donor_dict}


# API to list donors
@app.get("/list_donors", response_model=list[DonorResponse])
async def list_donors():
    donors = donors_collection.find({}, {"_id": 0, "email": 0})  # Exclude _id and email
    return list(donors)

