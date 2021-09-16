from PIL import Image, ImageDraw
 
img = Image.new('RGB', (100, 200), color = (255, 255, 255))
 
d = ImageDraw.Draw(img)
d.text((10,10), 'Hello World'+'\n'+'abc'+'\n'+'def', fill=(105,105,105))
 
img.save('pil_text.png')