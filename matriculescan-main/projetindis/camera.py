import os
import cv2
import re
import time
import threading
import torch
from ultralytics import YOLO
import database

class CameraSystem:
    def __init__(self, arduino_controller=None):
        # ================== ⚙️ CONFIGURATION GPU ==================
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Démarrage du système ALPR sur : {self.device.upper()}")

        # ================== 🧠 CHARGEMENT DES MODÈLES YOLO ==================
        # Chemin relatif au dossier du script
        base_dir = os.path.dirname(os.path.abspath(__file__))

        print("Chargement YOLO 1 (Détection de la plaque)...")
        self.model_plaque = YOLO(os.path.join(base_dir, "best.pt"))
        self.model_plaque.to(self.device)

        print("Chargement YOLO 2 (Lecture des caractères)...")
        self.model_ocr = YOLO(os.path.join(base_dir, "best_ocr.pt"))
        self.model_ocr.to(self.device)
        print("IA prête !")

        # ================== 📖 DICTIONNAIRE DE TRADUCTION ==================
        # Liste des classes générée par l'entraînement (data.yaml)
        self.noms_yolo = [
            '0', '1', '10', '11', '12', '13', '14', '15', '16', '17',
            '18', '19', '2', '20', '3', '4', '5', '6', '7', '8', '9'
        ]
        # Traduction des numéros spéciaux en lettres arabes
        self.lettres_arabes = {
            '10': 'أ', '11': 'ب', '12': 'و', '13': 'د', '14': 'ه',
            '15': 'ج', '16': 'ز', '17': 'ط', '18': 'ي', '19': 'ك', '20': 'ل'
        }

        # ================== 📷 CONFIGURATION CAMÉRA (DroidCam) ==================
        url_camera = "http://100.72.66.91:4747/video"
        self.cap = cv2.VideoCapture(url_camera)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self.arduino = arduino_controller

        self.dernier_scan = 0
        self.delai_scan = 0.3  # Très rapide car tout est calculé en local
        self.statut_parking = "EN ATTENTE DE VEHICULE..."
        self.couleur_statut = (255, 255, 255)

        self.last_result = {
            "plate": "Aucune",
            "numbers": "",
            "letters": "",
            "status": "Inconnu",
            "confidence": 0
        }
        self.current_frame = None
        self.running = True
        self.lock = threading.Lock()

    def parse_plate(self, text):
        """Sépare les chiffres des lettres pour le dashboard."""
        numbers = "".join(re.findall(r'\d+', text))
        letters = "".join(re.findall(r'[\u0600-\u06FF]+', text))
        return numbers, letters

    def update(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                print("Erreur de connexion à la caméra.")
                time.sleep(1)
                continue

            try:
                # Redimensionner pour accélérer la détection YOLO
                small = cv2.resize(frame, (640, 480))

                # --- 1️⃣ DÉTECTION DE LA PLAQUE (YOLO modèle 1) ---
                device_arg = 0 if self.device == "cuda" else "cpu"
                results_plaque = self.model_plaque.predict(
                    small, conf=0.5, device=device_arg, verbose=False
                )

                for box in results_plaque[0].boxes:
                    if int(box.cls[0]) != 2:  # Ignorer ce qui n'est pas une plaque
                        continue

                    # Calcul des coordonnées et mise à l'échelle
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    sx = frame.shape[1] / 640
                    sy = frame.shape[0] / 480
                    x1, x2 = int(x1 * sx), int(x2 * sx)
                    y1, y2 = int(y1 * sy), int(y2 * sy)

                    # Ajout d'une marge (padding)
                    pad = 10
                    x1, y1 = max(0, x1 - pad), max(0, y1 - pad)
                    x2 = min(frame.shape[1], x2 + pad)
                    y2 = min(frame.shape[0], y2 + pad)

                    # Dessin du rectangle vert autour de la plaque
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                    # Anti-spam
                    if time.time() - self.dernier_scan < self.delai_scan:
                        continue

                    # Découpage de l'image de la plaque (Crop)
                    crop = frame[y1:y2, x1:x2]
                    if crop.size == 0:
                        continue

                    self.dernier_scan = time.time()

                    # --- 2️⃣ LECTURE DES CARACTÈRES (YOLO modèle 2) ---
                    # iou=0.4 empêche YOLO de compter deux fois le même chiffre
                    results_ocr = self.model_ocr.predict(
                        crop, conf=0.4, iou=0.4, device=device_arg, verbose=False
                    )

                    caracteres_detectes = []

                    for char_box in results_ocr[0].boxes:
                        centre_x = float(char_box.xyxy[0][0])
                        class_id = int(char_box.cls[0])

                        # Traduction intelligente via le dictionnaire arabe
                        nom_classe = self.noms_yolo[class_id]
                        caractere = self.lettres_arabes.get(nom_classe, nom_classe)

                        caracteres_detectes.append((centre_x, caractere))

                    # --- 3️⃣ RECONSTRUCTION DU TEXTE DE LA PLAQUE ---
                    if len(caracteres_detectes) > 0:
                        # Tri des caractères de gauche à droite
                        caracteres_detectes.sort(key=lambda item: item[0])
                        texte_plaque = "".join([item[1] for item in caracteres_detectes])

                        print(f"[SUCCÈS] Plaque lue : {texte_plaque}")

                        # Séparation chiffres / lettres arabes
                        numbers, letters = self.parse_plate(texte_plaque)

                        # Confiance moyenne des détections OCR
                        confs = [float(cb.conf[0]) for cb in results_ocr[0].boxes]
                        conf = int((sum(confs) / len(confs)) * 100) if confs else 0

                        # Vérification dans la base de données
                        is_vip = database.is_authorized(texte_plaque)
                        status = "Authorized" if is_vip else "Unauthorized"

                        # Signal Arduino : scan détecté
                        if self.arduino:
                            self.arduino.indicate_scan()

                        if is_vip:
                            self.statut_parking = "ACCES AUTORISE - BARRIERE OUVERTE"
                            self.couleur_statut = (0, 255, 0)
                            if self.arduino:
                                self.arduino.indicate_authorized()
                        else:
                            self.statut_parking = "ACCES REFUSE - PLAQUE INCONNUE"
                            self.couleur_statut = (0, 0, 255)

                        # Sauvegarde dans l'historique
                        database.save_scan(texte_plaque, numbers, letters, status, conf)

                        # Mise à jour du résultat pour le dashboard web
                        with self.lock:
                            self.last_result = {
                                "plate": texte_plaque,
                                "numbers": numbers,
                                "letters": letters,
                                "status": status,
                                "confidence": conf
                            }

            except Exception as e:
                pass  # Ignorer silencieusement les petites erreurs visuelles

            # --- AFFICHAGE DU STATUT SUR LE FRAME ---
            cv2.putText(frame, self.statut_parking, (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.couleur_statut, 2)

            with self.lock:
                self.current_frame = frame.copy()

    def get_frame(self):
        with self.lock:
            if self.current_frame is None:
                return None
            return self.current_frame.copy()

    def stop(self):
        self.running = False
        self.cap.release()

if __name__ == "__main__":
    # Test mode if run directly
    cam = CameraSystem()
    database.init_db()
    t = threading.Thread(target=cam.update)
    t.start()

    while True:
        frame = cam.get_frame()
        if frame is not None:
            cv2.imshow('SYSTEME ALPR - YASSINE', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cam.stop()
            break
    cv2.destroyAllWindows()