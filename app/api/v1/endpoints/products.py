"""
Products API endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.product import Product, ProductCategory
from app.services.auth_service import AuthService
from app.schemas.product import ProductCreate, ProductResponse, ProductCategoryCreate, ProductCategoryResponse

router = APIRouter()


@router.post("/", response_model=ProductResponse)
async def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Yeni ürün oluştur"""
    # Kategori kontrolü
    category = db.query(ProductCategory).filter(ProductCategory.name == product_data.category).first()
    if not category:
        # Kategori yoksa oluştur
        category = ProductCategory(name=product_data.category)
        db.add(category)
        db.commit()
        db.refresh(category)
    
    # Ürün oluştur
    db_product = Product(
        name=product_data.name,
        description=product_data.description,
        category=product_data.category,
        cost_price=product_data.cost_price,
        target_profit_margin=product_data.target_profit_margin,
        owner_id=current_user.id
    )
    
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    return db_product


@router.get("/", response_model=List[ProductResponse])
async def get_products(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Kullanıcının ürünlerini getir"""
    products = db.query(Product).filter(Product.owner_id == current_user.id).offset(skip).limit(limit).all()
    return products


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Belirli bir ürünü getir"""
    product = db.query(Product).filter(Product.id == product_id, Product.owner_id == current_user.id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ürün bulunamadı"
        )
    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Ürün güncelle"""
    product = db.query(Product).filter(Product.id == product_id, Product.owner_id == current_user.id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ürün bulunamadı"
        )
    
    # Kategori kontrolü
    category = db.query(ProductCategory).filter(ProductCategory.name == product_data.category).first()
    if not category:
        # Kategori yoksa oluştur
        category = ProductCategory(name=product_data.category)
        db.add(category)
        db.commit()
        db.refresh(category)
    
    # Ürünü güncelle
    for key, value in product_data.dict().items():
        setattr(product, key, value)
    
    db.commit()
    db.refresh(product)
    
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Ürün sil"""
    product = db.query(Product).filter(Product.id == product_id, Product.owner_id == current_user.id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ürün bulunamadı"
        )
    
    db.delete(product)
    db.commit()
    
    return None


# Kategori endpoint'leri
@router.post("/categories/", response_model=ProductCategoryResponse)
async def create_category(
    category_data: ProductCategoryCreate,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Yeni kategori oluştur"""
    category = db.query(ProductCategory).filter(ProductCategory.name == category_data.name).first()
    if category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu kategori zaten var"
        )
    
    db_category = ProductCategory(
        name=category_data.name,
        description=category_data.description
    )
    
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    
    return db_category


@router.get("/categories/", response_model=List[ProductCategoryResponse])
async def get_categories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Tüm kategorileri getir"""
    categories = db.query(ProductCategory).offset(skip).limit(limit).all()
    return categories 