import os
from functools import lru_cache
import httpx
from fastapi import FastAPI, Query

app = FastAPI(title='FontSpace Font Catalog Service')
# Offline emulator is a documented option in the assignment. API mode requires an optional key.
DATA = [
 ('Inter','sans-serif',18), ('Roboto','sans-serif',12), ('Open Sans','sans-serif',10),
 ('Montserrat','sans-serif',18), ('Lato','sans-serif',10), ('Poppins','sans-serif',18),
 ('Nunito','sans-serif',14), ('Manrope','sans-serif',10), ('Jost','sans-serif',9),
 ('Raleway','sans-serif',14), ('DM Sans','sans-serif',8), ('Outfit','sans-serif',9),
 ('Playfair Display','serif',12), ('Merriweather','serif',8), ('Lora','serif',7),
 ('Libre Baskerville','serif',4), ('Cormorant Garamond','serif',10),
 ('EB Garamond','serif',12), ('Bodoni Moda','serif',12), ('DM Serif Display','serif',2),
 ('Oswald','sans-serif',7), ('Anton','sans-serif',1), ('Bebas Neue','display',1),
 ('Abril Fatface','display',1), ('Cinzel','serif',9), ('Righteous','display',1),
 ('Pacifico','handwriting',1), ('Caveat','handwriting',4), ('Dancing Script','handwriting',7),
 ('Great Vibes','handwriting',1), ('Sacramento','handwriting',1),
 ('Roboto Mono','monospace',10), ('Space Mono','monospace',2),
 ('JetBrains Mono','monospace',8), ('Inconsolata','monospace',9),
]
LOCAL = [{'family':family,'category':category,'variants':variants} for family,category,variants in DATA]
KEY = os.getenv('GOOGLE_FONTS_API_KEY', '').strip()

@app.get('/health')
def health():
    return {'ok':True,'mode':'google-fonts-api' if KEY else 'local-emulator'}

@app.get('/fonts')
async def fonts(q: str = Query('', max_length=100), category: str = 'all'):
    source = 'local-emulator'
    entries = LOCAL
    if KEY:
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                r = await client.get('https://www.googleapis.com/webfonts/v1/webfonts',
                    params={'key':KEY,'sort':'popularity'})
                r.raise_for_status()
            entries = [{'family':i['family'], 'category':i['category'],
                        'variants':len(i.get('variants', []))} for i in r.json().get('items', [])]
            source = 'google-fonts-api'
        except (httpx.HTTPError, KeyError, ValueError):
            source = 'local-emulator (API unavailable)'
    found = [x for x in entries if (category == 'all' or x['category'] == category)
             and q.casefold().strip() in x['family'].casefold()]
    return {'fonts':found[:60], 'total':len(found), 'source':source}
