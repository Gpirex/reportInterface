from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import report, report_services

import sentry_sdk

from utils.requests.middleware import CorrelationIdMiddleware
from utils.responses.middleware import SecurityHeadersMiddleware
from utils.system_settings import customization_setup, harpia_openapi

sentry_sdk.init(
    "https://998430b0e3a64216ba00cd9df01bdc88@sentry.safelabs.com.br/16",

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0
)

app = FastAPI(
    title="Harpia Reports",
    version="1.0.0"
)


origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SecurityHeadersMiddleware, csp=True)

app.add_middleware(CorrelationIdMiddleware)


@app.get("/")
def raiz():
    return {"Harpia": "Reports"}


app.include_router(report.router, prefix="/api")
# In production this is not sampled
app.include_router(report_services.router, prefix="/api")

app.openapi = harpia_openapi(app)
customization_setup(app)

# if __name__ == "__main__":
#     uvicorn.run("main:app", host="0.0.0.0", port=7000, reload=True)
