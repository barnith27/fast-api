from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from .database import get_db, engine
from .models import RecipeDB, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Кулинарная книга", version="1.0.0")


class RecipeCreate(BaseModel):
    name: str
    cooking_time: int
    ingredients: str
    description: str


class RecipeResponse(RecipeCreate):
    id: int
    views: int

    class Config:
        from_attributes = True


class RecipeList(BaseModel):
    id: int
    name: str
    cooking_time: int
    views: int

    class Config:
        from_attributes = True


@app.get("/recipes", response_model=List[RecipeList])
def get_all_recipes(db: Session = Depends(get_db)):
    try:
        recipes = db.query(RecipeDB).order_by(
            desc(RecipeDB.views),
            asc(RecipeDB.cooking_time)
        ).all()

        return [
            RecipeList(
                id=recipe.id,
                name=recipe.name,
                cooking_time=recipe.cooking_time,
                views=recipe.views
            ) for recipe in recipes
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/recipes/{recipe_id}", response_model=RecipeResponse)
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    try:
        recipe = db.query(RecipeDB).filter(RecipeDB.id == recipe_id).first()
        if not recipe:
            raise HTTPException(
                status_code=404,
                detail="Рецепт не найден"
            )

        recipe.views += 1
        db.commit()
        db.refresh(recipe)

        return RecipeResponse(
            id=recipe.id,
            name=recipe.name,
            cooking_time=recipe.cooking_time,
            ingredients=recipe.ingredients,
            description=recipe.description,
            views=recipe.views
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/recipes", response_model=RecipeResponse)
def create_recipe(recipe: RecipeCreate, db: Session = Depends(get_db)):
    try:
        db_recipe = RecipeDB(
            name=recipe.name,
            cooking_time=recipe.cooking_time,
            ingredients=recipe.ingredients,
            description=recipe.description
        )
        db.add(db_recipe)
        db.commit()
        db.refresh(db_recipe)

        return RecipeResponse(
            id=db_recipe.id,
            name=db_recipe.name,
            cooking_time=db_recipe.cooking_time,
            ingredients=db_recipe.ingredients,
            description=db_recipe.description,
            views=db_recipe.views
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/")
def read_root() -> dict:
    return {"message": "Добро пожаловать в Кулинарную книку!"}


@app.get("/health")
def health_check() -> dict:
    return {"status": "healthy"}