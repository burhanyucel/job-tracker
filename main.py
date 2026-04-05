from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from google import genai
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from database import SessionLocal, veritabani_olustur, Is, Kullanici
from auth import sifreyi_hashle, sifreyi_dogrula, token_olustur, tokeni_coz
from datetime import datetime
from typing import Optional
import os

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")



veritabani_olustur()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="giris", auto_error=False)

class KullaniciKayit(BaseModel):
    email: str
    sifre: str

class IsEkle(BaseModel):
    sirket: str
    pozisyon: str
    durum: str = "Basvuruldu"
    aciklama: str = ""
    notlar: str = ""

class IsGuncelle(BaseModel):
    sirket: Optional[str] = None
    pozisyon: Optional[str] = None
    durum: Optional[str] = None
    notlar: Optional[str] = None

def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def aktif_kullanici(token: str = Depends(oauth2_scheme), db: Session = Depends(db_session)):
    if not token:
        raise HTTPException(status_code=401, detail="Giris yapmaniz gerekiyor")
    email = tokeni_coz(token)
    if not email:
        raise HTTPException(status_code=401, detail="Gecersiz token")
    kullanici = db.query(Kullanici).filter(Kullanici.email == email).first()
    if not kullanici:
        raise HTTPException(status_code=401, detail="Kullanici bulunamadi")
    return kullanici

@app.get("/")
def ana_sayfa():
    return FileResponse("static/index.html")

@app.post("/kayit")
def kayit(veri: KullaniciKayit, db: Session = Depends(db_session)):
    mevcut = db.query(Kullanici).filter(Kullanici.email == veri.email).first()
    if mevcut:
        raise HTTPException(status_code=400, detail="Bu email zaten kayitli")
    kullanici = Kullanici(
        email=veri.email,
        sifre_hash=sifreyi_hashle(veri.sifre)
    )
    db.add(kullanici)
    db.commit()
    return {"mesaj": "Kayit basarili"}

@app.post("/giris")
def giris(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(db_session)):
    kullanici = db.query(Kullanici).filter(Kullanici.email == form.username).first()
    if not kullanici or not sifreyi_dogrula(form.password, kullanici.sifre_hash):
        raise HTTPException(status_code=401, detail="Email veya sifre yanlis")
    token = token_olustur({"sub": kullanici.email})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/isler")
def isleri_getir(kullanici: Kullanici = Depends(aktif_kullanici), db: Session = Depends(db_session)):
    isler = db.query(Is).filter(Is.kullanici_id == kullanici.id).order_by(Is.basvuru_tarihi.desc()).all()
    return isler

@app.post("/isler")
def is_ekle(veri: IsEkle, kullanici: Kullanici = Depends(aktif_kullanici), db: Session = Depends(db_session)):
    yeni_is = Is(
        kullanici_id=kullanici.id,
        sirket=veri.sirket,
        pozisyon=veri.pozisyon,
        durum=veri.durum,
        aciklama=veri.aciklama,
        notlar=veri.notlar
    )
    db.add(yeni_is)
    db.commit()
    db.refresh(yeni_is)

    if veri.aciklama:
        mesaj = f"""
        Su is ilanini analiz et:
        Pozisyon: {veri.pozisyon}
        Sirket: {veri.sirket}
        Aciklama: {veri.aciklama}

        Kurallar:
        - Cevabi Turkce ver
        - Kisa ve net yaz
        - Sadece asagidaki 3 basligi kullan

        Basliklar:
        1. Gerekli beceriler
        2. Eksik olabilecek beceriler
        3. Basvuru onerileri
        """
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=mesaj
            )
            yeni_is.ai_analiz = response.text
            db.commit()
        except:
            pass

    return yeni_is

@app.put("/isler/{is_id}")
def is_guncelle(is_id: int, veri: IsGuncelle, kullanici: Kullanici = Depends(aktif_kullanici), db: Session = Depends(db_session)):
    is_kaydi = db.query(Is).filter(Is.id == is_id, Is.kullanici_id == kullanici.id).first()
    if not is_kaydi:
        raise HTTPException(status_code=404, detail="Is bulunamadi")
    
    if veri.sirket: is_kaydi.sirket = veri.sirket
    if veri.pozisyon: is_kaydi.pozisyon = veri.pozisyon
    if veri.durum: is_kaydi.durum = veri.durum
    if veri.notlar: is_kaydi.notlar = veri.notlar
    
    is_kaydi.guncelleme_