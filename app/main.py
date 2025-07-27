from fastapi import FastAPI
from app.routes.all import routes
from fastapi.responses import RedirectResponse
from app.core.init_superadmin import create_super_admin
from fastapi.middleware.cors import CORSMiddleware




app = FastAPI(title="global divers app backend", description="global divers app backend server using ( fastapi, sqlalchemy, alembic, mysql )", version="1.0.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["*"] for all
    allow_credentials=True,
    allow_methods=["*"],  # Allows POST, GET, OPTIONS, etc.
    allow_headers=["*"],
)



@app.get("/", include_in_schema=False)
async  def root():
  return RedirectResponse(url="https://globaldivers.vercel.app/") # Add Frontend URL


@app.get("/document", include_in_schema=False)
async def redoc():
  return RedirectResponse(url="/docs")

@app.get("/documentation", include_in_schema=False)
async def docs():
  return RedirectResponse(url="/docs")



@app.get("/health", include_in_schema=False)
async def health():
  return {"status": "ok"}




for router in routes:
  app.include_router(router)


create_super_admin()


if __name__ == "__main__":
  import uvicorn
  uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)