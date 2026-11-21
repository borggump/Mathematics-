import turtle

def dragon_curve(t, order, size, direction):
    if order == 0:
        t.forward(size)
    else:
        dragon_curve(t, order-1, size, 1)
        t.right(90 * direction)
        dragon_curve(t, order-1, size, -1)
def draw_dragon_fractal(order, size=7):
    window = turtle.Screen()
    window.setup(800, 600)
    window.title("Dragon Fractal")
    window.bgcolor("black")

    t = turtle.Turtle()
    t.speed(0)  # Fastest speed
    t.hideturtle()
    t.color("cyan")
    t.penup()
    t.goto(-100, 0)
    t.pendown()

    dragon_curve(t, order, size, 1)

    window.mainloop()

# Call the function to draw the dragon fractal
# You can adjust the order (complexity) here
draw_dragon_fractal(order=42)