import sqlite3
import os
from datetime import datetime

DB_PATH = "plates.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialise la base de données avec les tables nécessaires."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Table des matricules autorisés (VIP)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS authorized (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricule TEXT UNIQUE NOT NULL
        )
    ''')
    
    # Table de l'historique des scans
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            matricule TEXT NOT NULL,
            numbers TEXT,
            letters TEXT,
            status TEXT NOT NULL,
            confidence INTEGER DEFAULT 0
        )
    ''')
    
    # Ajouter quelques matricules par défaut si la table est vide
    cursor.execute("SELECT COUNT(*) FROM authorized")
    if cursor.fetchone()[0] == 0:
        default_vips = ["12345أ6", "98765ب1", "11111د5", "13456"]
        for vip in default_vips:
            cursor.execute("INSERT OR IGNORE INTO authorized (matricule) VALUES (?)", (vip,))
            
    conn.commit()
    conn.close()

def is_authorized(matricule):
    """Vérifie si un matricule est dans la liste VIP."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM authorized WHERE matricule = ?", (matricule,))
    authorized = cursor.fetchone() is not None
    conn.close()
    return authorized

def save_scan(matricule, numbers, letters, status, confidence):
    """Enregistre un scan dans l'historique."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO history (matricule, numbers, letters, status, confidence) VALUES (?, ?, ?, ?, ?)",
        (matricule, numbers, letters, status, confidence)
    )
    conn.commit()
    conn.close()

def get_history(limit=20):
    """Récupère les derniers scans."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM history ORDER BY timestamp DESC LIMIT ?", (limit,))
    history = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return history

def get_stats():
    """Calcule les statistiques globales."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM authorized")
    allowed_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM history")
    total_scans = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM history WHERE status = 'Authorized'")
    authorized_scans = cursor.fetchone()[0]
    
    cursor.execute("SELECT AVG(confidence) FROM history")
    avg_confidence = cursor.fetchone()[0] or 0
    
    conn.close()
    return {
        "allowed_count": allowed_count,
        "total_scans": total_scans,
        "authorized_scans": authorized_scans,
        "avg_confidence": round(avg_confidence, 1)
    }

def get_authorized_list():
    """Récupère la liste des matricules autorisés."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT matricule FROM authorized")
    vips = [row['matricule'] for row in cursor.fetchall()]
    conn.close()
    return vips

def add_authorized(matricule):
    """Ajoute un matricule à la liste VIP."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO authorized (matricule) VALUES (?)", (matricule,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def remove_authorized(matricule):
    """Supprime un matricule de la liste VIP."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM authorized WHERE matricule = ?", (matricule,))
    conn.commit()
    conn.close()
    return True
