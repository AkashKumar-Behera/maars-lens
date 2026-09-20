"""
Preprocessing Evaluation Script for MAARS Lens
==============================================
Compares OCR recognition accuracy and latency on the 8 label fixtures across:
1. Raw (original image)
2. CLAHE (Contrast-Limited Adaptive Histogram Equalization)
3. Full Preprocessing (Grayscale + Gaussian Blur + CLAHE + Bilateral Filter)
"""

import os
import cv2
import json
import time
import numpy as np

from app.services.ocr.extractor import PaddleOCRExtractor, extract_facts
from app.services.ocr.preprocessor import preprocess_image


def run_clahe_only(image: np.ndarray) -> np.ndarray:
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def main():
    fixtures_dir = os.path.join(os.path.dirname(__file__), "..", "tests", "fixtures", "labels")
    meta_path = os.path.join(fixtures_dir, "expected_results.json")
    with open(meta_path, "r", encoding="utf-8") as f:
        fixtures_meta = json.load(f)

    extractor = PaddleOCRExtractor()

    methods = ["raw", "clahe", "full"]
    results = {m: {"total_expected": 0, "detected": 0, "latencies": [], "confidences": []} for m in methods}

    image_files = [k for k in sorted(fixtures_meta.keys()) if k.endswith(".png")]

    print("Benchmarking Preprocessing Methods across 8 Fixtures...")
    for img_name in image_files:
        meta = fixtures_meta[img_name]
        expected_fields = meta.get("mandatory_fields_present", [])
        if not expected_fields:
            continue

        img_path = os.path.join(fixtures_dir, img_name)
        orig_img = cv2.imread(img_path)
        if orig_img is None:
            continue

        with open(img_path, "rb") as f:
            raw_bytes = f.read()

        for m in methods:
            t0 = time.time()
            if m == "raw":
                test_img = orig_img
            elif m == "clahe":
                test_img = run_clahe_only(orig_img)
            elif m == "full":
                test_img = preprocess_image(raw_bytes)

            facts, raw_text, avg_conf, per_field = extract_facts(test_img, extractor=extractor)
            elapsed = time.time() - t0

            results[m]["latencies"].append(elapsed)
            results[m]["confidences"].append(avg_conf)

            for ef in expected_fields:
                results[m]["total_expected"] += 1
                if facts.get(ef) is not None:
                    results[m]["detected"] += 1

    print("\n--- PREPROCESSING BENCHMARK RESULTS ---")
    print(f"{'Method':<10} | {'Expected':<8} | {'Detected':<8} | {'Recall %':<10} | {'Avg Conf %':<10} | {'Mean Latency':<12}")
    print("-" * 72)
    best_method = "raw"
    best_score = 0.0

    for m in methods:
        total = results[m]["total_expected"]
        det = results[m]["detected"]
        recall = (det / total * 100.0) if total > 0 else 0.0
        avg_conf = (np.mean(results[m]["confidences"]) * 100.0) if results[m]["confidences"] else 0.0
        mean_lat = np.mean(results[m]["latencies"]) if results[m]["latencies"] else 0.0

        print(f"{m:<10} | {total:<8} | {det:<8} | {recall:>8.2f}% | {avg_conf:>9.2f}% | {mean_lat:>9.3f}s")
        if recall > best_score:
            best_score = recall
            best_method = m

    print("-" * 72)
    print(f"Optimal Pipeline Pick: '{best_method}' (Recall: {best_score:.2f}%)\n")


if __name__ == "__main__":
    main()
