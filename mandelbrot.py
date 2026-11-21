from PIL import Image
import colorsys

def mandelbrot(h, w, max_iter):
    y, x = np.ogrid[-1.4:1.4:h*1j, -2:0.8:w*1j]
    c = x + y*1j
    z = c
    divtime = max_iter + np.zeros(z.shape, dtype=int)

    for i in range(max_iter):
        z = z**2 + c
        diverge = z*np.conj(z) > 2**2
        div_now = diverge & (divtime == max_iter)
        divtime[div_now] = i
        z[diverge] = 2

    return divtime

def create_fractal(width, height, max_iter=100):
    import numpy as np

    fractal = mandelbrot(height, width, max_iter)
    
    img = Image.new('RGB', (width, height), (0, 0, 0))
    pixels = img.load()
    
    for x in range(width):
        for y in range(height):
            iterations = fractal[y, x]
            if iterations == max_iter:
                pixels[x, y] = (0, 0, 0)
            else:
                hue = iterations / max_iter
                saturation = 1.0
                value = 1.0 if iterations < max_iter else 0.0
                rgb = tuple(int(255 * i) for i in colorsys.hsv_to_rgb(hue, saturation, value))
                pixels[x, y] = rgb
    
    return img

if __name__ == "__main__":
    width, height = 800, 600
    image = create_fractal(width, height)
    image.save('mandelbrot.png')
    print("Mandelbrot fractal has been generated and saved as 'mandelbrot.png'")