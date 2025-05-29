# Stohrer Sax Pad SVG Generator - Docked preview with grouped drag

# [snipped for brevity — only replacing the drag portion with grouped drag logic]

# Drag and drop with shared tag per disc group

    def start_drag(event):
        item = canvas.find_closest(event.x, event.y)[0]
        tags = canvas.gettags(item)
        canvas.drag_data = {"tag": tags[0], "x": event.x, "y": event.y}

    def do_drag(event):
        dx = event.x - canvas.drag_data["x"]
        dy = event.y - canvas.drag_data["y"]
        canvas.move(canvas.drag_data["tag"], dx, dy)
        canvas.drag_data["x"] = event.x
        canvas.drag_data["y"] = event.y


# All pad elements share the same tag:
# 
canvas.create_oval(..., tags=tag)
canvas.create_oval(..., tags=tag)  # center hole
canvas.create_text(..., tags=tag)  # engraving


# Full file includes existing logic, pad placement, canvas, etc.
