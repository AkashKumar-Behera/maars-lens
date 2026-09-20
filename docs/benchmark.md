# MAARS Lens — Synthetic Label OCR Performance Benchmark
> **IMPORTANT DISCLOSURE**: This benchmark measures performance across **8 self-generated synthetic label fixtures** with computer-generated text. It is **NOT a real-world packaging photography accuracy benchmark**. Real-world performance on wrinkled, curved, reflective, or poorly lit packages will vary.

## Benchmark Environment
- **OCR Engine**: PaddleOCR 2.9.1 (Dual English + Hindi passes, process-singleton cached)
- **Framework**: PaddlePaddle 2.6.2 (CPU build, oneDNN / MKLDNN disabled for stability on Windows)
- **Hardware Platform**: Windows x86_64, Python 3.11.9
- **Model Warmup / Initialization Time**: 12.23 seconds
- **Dataset**: 8 Self-Generated Synthetic Packaging Label Test Fixtures

---

## Synthetic Benchmark Results Table

| Fixture Image | Scenario | Dimensions | Latency (s) | OCR Confidence | Synthetic Fields Match | Synthetic Match Rate |
|:---|:---|:---|:---|:---|:---|:---|
| `01_compliant_bilingual.png` | compliant_bilingual | 700x420 | 2.98s | 95% | 6/6 | 100.0% |
| `02_missing_mrp.png` | missing_mrp | 700x360 | 2.47s | 96% | 5/5 | 100.0% |
| `03_tiny_font.png` | tiny_font | 400x200 | 2.07s | 87% | 5/6 | 83.3% |
| `04_missing_address.png` | missing_address | 700x360 | 1.59s | 96% | 5/5 | 100.0% |
| `05_imported_no_origin.png` | imported_no_origin | 700x340 | 2.30s | 94% | 5/5 | 100.0% |
| `06_blurry_label.png` | blurry_label | 700x360 | 0.11s | 0% | 0/0 | 100.0% |
| `07_hindi_english_mix.png` | hindi_english_mix | 700x450 | 2.82s | 95% | 6/6 | 100.0% |
| `08_multi_panel.png` | multi_panel | 800x380 | 2.61s | 94% | 6/6 | 100.0% |

---

## Synthetic Test Observations
- **Average Extraction Latency**: `2.12s` per synthetic label (dual bilingual passes on CPU)
- **Synthetic Fixture Match Rate**: High match on clean flat digital graphics; real-world photos have not been systematically field-tested.
- **Quality Rejection Handling**: Fixture `06_blurry_label.png` (Gaussian blur) correctly flagged with low confidence and blurred visual quality.
- **Hindi / Devanagari Extraction**: Dual bilingual merging successfully parses Hindi numerals (e.g. Devanagari digits `०-९ -> 0-9`) and bilingual MRP/Net Quantity declarations on flat backgrounds.
