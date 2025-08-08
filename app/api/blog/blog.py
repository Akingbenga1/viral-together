import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.api.auth import get_current_user
from app.core.dependencies import require_role
from app.db.session import get_db
from app.db.models import Blog
from app.schemas.blog import BlogCreate, BlogRead, BlogUpdate


# Authenticated router (super_admin only for write)
router = APIRouter(dependencies=[Depends(get_current_user)])

# Public router
public_router = APIRouter()


def _serialize_images(images_json: str | None) -> List[str] | None:
    if not images_json:
        return None
    try:
        data = json.loads(images_json)
        return data if isinstance(data, list) else None
    except Exception:
        return None


@router.post("/create", response_model=BlogRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role("super_admin"))])
async def create_blog(payload: BlogCreate, db: AsyncSession = Depends(get_db)):
    new_blog = Blog(
        slug=payload.slug,
        author_id=payload.author_id,
        topic=payload.topic,
        description=payload.description,
        body=payload.body,
        images_json=json.dumps(payload.images) if payload.images else None,
        cover_image_url=payload.cover_image_url,
    )
    db.add(new_blog)
    await db.commit()
    await db.refresh(new_blog)

    return BlogRead(
        id=new_blog.id,
        slug=new_blog.slug,
        author_id=new_blog.author_id,
        topic=new_blog.topic,
        description=new_blog.description,
        body=new_blog.body,
        images=_serialize_images(new_blog.images_json),
        cover_image_url=new_blog.cover_image_url,
        created_at=new_blog.created_at,
        updated_at=new_blog.updated_at,
    )


@router.put("/update/{blog_id}", response_model=BlogRead, dependencies=[Depends(require_role("super_admin"))])
async def update_blog(blog_id: int, payload: BlogUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Blog).where(Blog.id == blog_id))
    blog = result.scalars().first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")

    if payload.topic is not None:
        blog.topic = payload.topic
    if payload.description is not None:
        blog.description = payload.description
    if payload.body is not None:
        blog.body = payload.body
    if payload.images is not None:
        blog.images_json = json.dumps(payload.images)
    if payload.cover_image_url is not None:
        blog.cover_image_url = payload.cover_image_url

    await db.commit()
    await db.refresh(blog)

    return BlogRead(
        id=blog.id,
        slug=blog.slug,
        author_id=blog.author_id,
        topic=blog.topic,
        description=blog.description,
        body=blog.body,
        images=_serialize_images(blog.images_json),
        cover_image_url=blog.cover_image_url,
        created_at=blog.created_at,
        updated_at=blog.updated_at,
    )


@public_router.get("/blogs", response_model=List[BlogRead])
async def list_blogs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Blog))
    blogs = result.scalars().all()
    return [
        BlogRead(
            id=b.id,
            slug=b.slug,
            author_id=b.author_id,
            topic=b.topic,
            description=b.description,
            body=b.body,
            images=_serialize_images(b.images_json),
            cover_image_url=b.cover_image_url,
            created_at=b.created_at,
            updated_at=b.updated_at,
        )
        for b in blogs
    ]


@public_router.get("/blogs/{slug}", response_model=BlogRead)
async def get_blog_by_slug(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Blog).where(Blog.slug == slug))
    blog = result.scalars().first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    return BlogRead(
        id=blog.id,
        slug=blog.slug,
        author_id=blog.author_id,
        topic=blog.topic,
        description=blog.description,
        body=blog.body,
        images=_serialize_images(blog.images_json),
        cover_image_url=blog.cover_image_url,
        created_at=blog.created_at,
        updated_at=blog.updated_at,
    )


@router.post("/upload-image", dependencies=[Depends(require_role("super_admin"))])
async def upload_image(file: UploadFile = File(...)):
    # For simplicity, just return a fake URL path; integrate actual storage later
    return {"url": f"/static/uploads/{file.filename}"}


