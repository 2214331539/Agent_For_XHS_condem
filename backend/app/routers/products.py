from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models import Post, Product
from app.schemas import ProductCreate, ProductRead, ProductUpdate

router = APIRouter(tags=["products"])


@router.post("/posts/{post_id}/products", response_model=ProductRead)
def create_product(post_id: str, payload: ProductCreate, db: Session = Depends(get_db)) -> Product:
    if not db.get(Post, post_id):
        raise HTTPException(status_code=404, detail="Post not found")
    product = Product(post_id=post_id, **payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/posts/{post_id}/products", response_model=list[ProductRead])
def list_products(post_id: str, db: Session = Depends(get_db)) -> list[Product]:
    stmt = select(Product).options(selectinload(Product.images)).where(Product.post_id == post_id).order_by(Product.sort_order)
    return list(db.scalars(stmt).all())


@router.get("/products/{product_id}", response_model=ProductRead)
def get_product(product_id: str, db: Session = Depends(get_db)) -> Product:
    product = db.scalars(select(Product).options(selectinload(Product.images)).where(Product.id == product_id)).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.patch("/products/{product_id}", response_model=ProductRead)
def update_product(product_id: str, payload: ProductUpdate, db: Session = Depends(get_db)) -> Product:
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, key, value)
    db.commit()
    return get_product(product_id, db)


@router.delete("/products/{product_id}")
def delete_product(product_id: str, db: Session = Depends(get_db)) -> dict[str, bool]:
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"ok": True}

