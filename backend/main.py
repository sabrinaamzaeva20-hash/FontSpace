import os
from typing import Literal
import httpx
import psycopg
from psycopg.rows import dict_row
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

app = FastAPI(title="FontSpace API", version="1.0.0")
DB = os.environ['DATABASE_URL']
FONT_SERVICE = os.getenv('FONT_SERVICE_URL', 'http://web-service:8001')

class Favorite(BaseModel):
    family: str = Field(min_length=1, max_length=120)
    category: Literal['serif', 'sans-serif', 'display', 'handwriting', 'monospace']
    project_name: str = Field(default='Личная коллекция', max_length=120)
    notes: str = Field(default='', max_length=250)

class FavoriteEdit(BaseModel):
    project_name: str = Field(min_length=1, max_length=120)
    notes: str = Field(default='', max_length=250)

@app.get('/api/health')
def health():
    with psycopg.connect(DB) as conn:
        conn.execute('SELECT 1')
    return {'ok': True}

@app.get('/api/fonts')
async def fonts(q: str = Query('', max_length=100), category: str = Query('all')):
    if category not in {'all', 'serif', 'sans-serif', 'display', 'handwriting', 'monospace'}:
        raise HTTPException(422, 'Неизвестная категория')
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.get(f'{FONT_SERVICE}/fonts', params={'q': q, 'category': category})
            response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(502, 'Сервис каталога временно недоступен') from e

@app.get('/api/favorites')
def favorites():
    with psycopg.connect(DB, row_factory=dict_row) as conn:
        items = conn.execute('SELECT * FROM favorites ORDER BY id DESC').fetchall()
    return [{'id': x['id'], 'family': x['family'], 'category': x['category'],
             'project_name': x['project_name'], 'notes': x['notes'],
             'created_at': x['created_at'].isoformat()} for x in items]

@app.post('/api/favorites', status_code=201)
def add_favorite(favorite: Favorite):
    with psycopg.connect(DB, row_factory=dict_row) as conn:
        result = conn.execute('''INSERT INTO favorites (family, category, project_name, notes)
           VALUES (%s,%s,%s,%s) ON CONFLICT (family) DO NOTHING RETURNING id, family''',
           (favorite.family, favorite.category, favorite.project_name or 'Личная коллекция', favorite.notes)).fetchone()
    if not result:
        raise HTTPException(409, 'Шрифт уже добавлен')
    return result

@app.patch('/api/favorites/{id}')
def update_favorite(id: int, item: FavoriteEdit):
    with psycopg.connect(DB, row_factory=dict_row) as conn:
        result = conn.execute('''UPDATE favorites SET project_name=%s,notes=%s WHERE id=%s
           RETURNING id, family, project_name, notes''', (item.project_name, item.notes, id)).fetchone()
    if not result:
        raise HTTPException(404, 'Запись не найдена')
    return result

@app.delete('/api/favorites/{id}', status_code=204)
def delete_favorite(id: int):
    with psycopg.connect(DB) as conn:
        result = conn.execute('DELETE FROM favorites WHERE id=%s RETURNING id', (id,)).fetchone()
    if not result:
        raise HTTPException(404, 'Запись не найдена')
