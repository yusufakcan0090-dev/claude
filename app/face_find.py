"""Yüz bulucu işçi: klasördeki karelerde yüzleri bulur, JSON yazar.

  python face_find.py <kare_klasörü> <yunet.onnx>
Çıktı (stdout, tek satır JSON): [[{"x":..,"y":..,"w":..,"h":..,"s":..}, ...], ...]  (her kare için, 0-1 arası)
"""
import json
import os
import sys

import cv2
import numpy as np


def main():
    folder, model = sys.argv[1], sys.argv[2]
    files = sorted(f for f in os.listdir(folder) if f.lower().endswith((".jpg", ".png")))
    det = None
    out = []
    for f in files:
        img = cv2.imdecode(np.fromfile(os.path.join(folder, f), np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            out.append([])
            continue
        h, w = img.shape[:2]
        if det is None:
            det = cv2.FaceDetectorYN.create(model, "", (w, h), 0.6, 0.3, 50)
        det.setInputSize((w, h))
        _, faces = det.detect(img)
        fr = []
        for fc in (faces if faces is not None else []):
            x, y, fw, fh, s = float(fc[0]), float(fc[1]), float(fc[2]), float(fc[3]), float(fc[-1])
            if fw * fh < 0.0004 * w * h:  # çok küçük (kalabalık / yanlış) yüzleri at
                continue
            fr.append({"x": x / w, "y": y / h, "w": fw / w, "h": fh / h, "s": s})
        out.append(fr)
    print(json.dumps(out))


if __name__ == "__main__":
    main()
