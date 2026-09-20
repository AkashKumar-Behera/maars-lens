import cv2, numpy as np, os

os.makedirs('audit_output/generated_labels', exist_ok=True)

def create_base_canvas(w=900, h=650, bg_color=(245, 245, 245)):
    return np.full((h, w, 3), bg_color, dtype=np.uint8)

def draw_header(img, title):
    cv2.putText(img, title, (40, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (20, 20, 20), 2)
    cv2.line(img, (40, 70), (860, 70), (100, 100, 100), 2)

# 1. 09_rotated_15deg.png
img1 = create_base_canvas()
draw_header(img1, 'PREMIUM CASHEW 500g')
cv2.putText(img1, 'MRP: Rs. 650.00 (Incl. of all taxes)', (50, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 2)
cv2.putText(img1, 'Net Qty: 500g', (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 2)
cv2.putText(img1, 'Mfg Date: 08/2026', (50, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 2)
cv2.putText(img1, 'Mfd by: NutriFoods Pvt Ltd, Sector 12, Pune 411001', (50, 320), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 2)
cv2.putText(img1, 'Consumer Care: care@nutrifoods.in Tel: 1800-222-333', (50, 380), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 2)
cv2.putText(img1, 'Country of Origin: India', (50, 440), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 2)
(h, w) = img1.shape[:2]
center = (w // 2, h // 2)
M = cv2.getRotationMatrix2D(center, 15, 1.0)
rot_img = cv2.warpAffine(img1, M, (w, h), borderValue=(245, 245, 245))
cv2.imwrite('audit_output/generated_labels/09_rotated_15deg.png', rot_img)

# 2. 10_glare_reflection.png
img2 = img1.copy()
# Add bright glare ellipse
overlay = img2.copy()
cv2.ellipse(overlay, (450, 280), (220, 100), 30, 0, 360, (255, 255, 255), -1)
glare_img = cv2.addWeighted(overlay, 0.75, img2, 0.25, 0)
cv2.imwrite('audit_output/generated_labels/10_glare_reflection.png', glare_img)

# 3. 11_low_light.png
dark_img = (img1 * 0.25).astype(np.uint8)
cv2.imwrite('audit_output/generated_labels/11_low_light.png', dark_img)

# 4. 12_non_permitted_units.png
img4 = create_base_canvas()
draw_header(img4, 'ORGANIC CORN FLAKES')
cv2.putText(img4, 'MRP: Rs. 220.00 (Incl. of all taxes)', (50, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 2)
cv2.putText(img4, 'Net Qty: 16 oz (450 gms)', (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 2)
cv2.putText(img4, 'Mfg Date: 05/2026', (50, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 2)
cv2.putText(img4, 'Mfd by: GreenFields Agro Ltd, Bengaluru 560001', (50, 320), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 2)
cv2.putText(img4, 'Consumer Care: help@greenfields.com Tel: 080-23456789', (50, 380), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 2)
cv2.putText(img4, 'Country of Origin: India', (50, 440), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 2)
cv2.imwrite('audit_output/generated_labels/12_non_permitted_units.png', img4)

# 5. 13_multi_mrp.png
img5 = create_base_canvas()
draw_header(img5, 'INSTANT NOODLES JUMBO')
cv2.putText(img5, 'MRP: Rs. 40.00 (Old)', (50, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 2)
cv2.putText(img5, 'SPECIAL PRICE MRP Rs. 55.00 (Incl. of taxes)', (50, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 180), 2)
cv2.putText(img5, 'Net Qty: 150g', (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 2)
cv2.putText(img5, 'Mfg Date: 07/2026', (50, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 2)
cv2.putText(img5, 'Mfd by: QuickFoods India Ltd, Baddi HP 173205', (50, 360), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 2)
cv2.putText(img5, 'Consumer Care: support@quickfoods.in Tel: 1800-111-222', (50, 420), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 2)
cv2.putText(img5, 'Country of Origin: India', (50, 480), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 2)
cv2.imwrite('audit_output/generated_labels/13_multi_mrp.png', img5)

print('Generated 5 test fixtures in audit_output/generated_labels/')
