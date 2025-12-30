"""
Alacak-Verecek tablolarını ekle
"""

from database import Database

def migrate():
    db = Database()
    db.connect()
    
    print("Alacak-Verecek tabloları ekleniyor...")
    
    try:
        db.add_alacak_verecek_tables()
        print("✅ Tablolar başarıyla oluşturuldu!")
        print("   - alacaklar")
        print("   - alacak_tahsilatlari")
        print("   - verecekler")
        print("   - verecek_odemeleri")
    except Exception as e:
        print(f"❌ Hata: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
