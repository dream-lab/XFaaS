import base64
from python.src.utils.classes.commons.serwo_objects import SerWOObject


def overlay_text_on_base64_gif(base64_gif, text, font_size=20, duration=None):
    from PIL import Image, ImageDraw, ImageSequence
    import io

    gif_bytes = base64.b64decode(base64_gif)

    with open('/tmp/vid3.gif', 'wb') as gif_file:
        gif_file.write(gif_bytes)

    im = Image.open('/tmp/vid3.gif')
    frames = []
    for frame in ImageSequence.Iterator(im):
        # Draw the text on the frame
        d = ImageDraw.Draw(frame)
        d.text((10,100), "Sub : ")
        del d
        
        b = io.BytesIO()
        frame.save(b, format="GIF")
        frame = Image.open(b)
        
        frames.append(frame)
    gif_io = io.BytesIO()
    frames[0].save(
        gif_io,
        format='GIF',
        append_images=frames[1:],
        save_all=True,
        duration=100,  # Adjust the duration between frames as needed
        loop=0  # Loop indefinitely
    )
    encoded_gif = base64.b64encode(gif_io.getvalue()).decode('utf-8')

    return encoded_gif

def user_function(xfaas_object):
    l = xfaas_object.get_objects()
    b1 = l[0]
    g1 = b1["gif"]
    b2 = l[1]
    text = b2["sentiment"]

    r = overlay_text_on_base64_gif(g1, text)
    res = {"gif":r}
    s = SerWOObject(body=res)
    return s
