from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Databricks Tech Adapter",
    description="Microservice responsible to handle provisioning and access control requests for one or more data product components.",  # noqa: E501
    version="2.2.0",
)

# Add CORS middleware to allow Witboost UI to call Custom URL Picker endpoints
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific Witboost UI origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
