from fastapi import FastAPI

from app.routers import auth, contracts, counterparties


app = FastAPI(title="Money MVP")

app.include_router(auth.router)
app.include_router(counterparties.router)
app.include_router(contracts.router)

