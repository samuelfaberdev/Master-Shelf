import os
import mlflow
from ultralytics import YOLO
from pathlib import Path
import cv2

def yolo_predict(image):
    username = Path.home().name

    print("⏳ Chargement du model Yolo ⏳")
    model = YOLO(f"models/epoch30.pt")
    print("✅ Model Yolo chargé ! ✅")

    print(f"🔎 Détection d'ingrédient pour l'image :\n{image}")
    # Baisser la confiance (conf) et augmenter le seuil d'intersection (iou)
    results = model.predict(
        source=image,
        conf=0.15,   # Affiche même les détections incertaines
        iou=0.45,    # Évite les boîtes qui se chevauchent trop
        save=True
    )

    ings = []

    class_names = model.names
    for result in results:
        boxes = result.boxes
        for box in boxes:
            # Récupérer l'ID de la classe (format float/tensor, converti en int)
            class_id = int(box.cls[0].item())

            # Obtenir le nom de la catégorie correspondante
            category_name = class_names[class_id]

            # Récupérer le score de confiance (optionnel)
            confidence = box.conf[0].item()

            print(f"💥 Objet détecté : {category_name} (Confiance : {confidence:.2f})")

            ings.append(category_name)
    # 3. Récupérer l'image avec les boîtes dessinées (format BGR pour OpenCV)
    annotated_frame = results[0].plot()

    # 4. Convertir BGR en RGB (Matplotlib utilise le format RGB)
    annotated_frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
    print(ings)
    return {
            "ingredients_list": ings,
            "imagebox" : annotated_frame_rgb
        }
