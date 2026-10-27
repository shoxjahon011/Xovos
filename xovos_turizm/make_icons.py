from PIL import Image, ImageDraw

for s in (192, 512):
    im = Image.new("RGB", (s, s), "#2e7d32")
    d = ImageDraw.Draw(im)
    d.ellipse([s*.25, s*.18, s*.75, s*.68], fill="white")
    d.polygon([(s*.35, s*.58), (s*.65, s*.58), (s*.5, s*.85)], fill="white")
    d.ellipse([s*.4, s*.33, s*.6, s*.53], fill="#2e7d32")
    im.save(f"places/static/places/icons/icon-{s}.png")