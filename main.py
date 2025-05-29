
# Stohrer Sax Pad SVG Generator - Updated with Dockable Preview, Drag-and-Drop, Accurate Grid, and Layout Persistence

import svgwrite
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

FELT_OFFSET = 0.75
CARD_OFFSET = FELT_OFFSET + 2.0
CENTER_HOLE_DIAMETER = 3.5

LAYER_COLORS = {
    'felt': 'black',
    'card': 'blue',
    'leather': 'red',
    'center_hole': 'dimgray',
    'engraving': 'orange'
}

positions_by_material = {}

def leather_back_wrap(pad_size):
    if pad_size <= 10:
        return 1.3
    elif pad_size <= 15:
        return 1.3 + (pad_size - 10) * (0.7 / 5.0)
    elif pad_size <= 40:
        return 2.0 + (pad_size - 15) * (1.5 / 25.0)
    else:
        return 3.5

def should_have_center_hole(pad_size):
    return pad_size >= 16.5

def generate_svg(pads, material, width_mm, height_mm, filename):
    dwg = svgwrite.Drawing(filename, size=(f"{width_mm}mm", f"{height_mm}mm"))
    positions = positions_by_material.get(material, [])
    for i, pad in enumerate(pads):
        pad_size = pad['size']
        qty = pad['qty']
        for j in range(qty):
            if material == 'felt':
                diameter = pad_size - FELT_OFFSET
            elif material == 'card':
                diameter = pad_size - CARD_OFFSET
            elif material == 'leather':
                back_wrap = leather_back_wrap(pad_size)
                diameter = pad_size + 2 * (3.175 + back_wrap)
                diameter = round(diameter * 2) / 2
            else:
                continue
            x, y = positions[i][j] if i < len(positions) and j < len(positions[i]) else (10, 10)
            cx = x + diameter / 2
            cy = y + diameter / 2
            dwg.add(dwg.circle(center=(cx, cy), r=diameter/2, stroke=LAYER_COLORS[material], fill='none'))
            if material != 'leather' and should_have_center_hole(pad_size):
                dwg.add(dwg.circle(center=(cx, cy), r=CENTER_HOLE_DIAMETER / 2, stroke=LAYER_COLORS['center_hole'], fill='none'))
            if material in ['felt', 'card']:
                radius = (diameter / 2 + CENTER_HOLE_DIAMETER / 2) / 2
                dwg.add(dwg.text(f"{pad_size:.1f}".rstrip('0').rstrip('.'),
                                 insert=(cx, cy - radius),
                                 text_anchor="middle", alignment_baseline="middle",
                                 font_size="2mm", fill=LAYER_COLORS['engraving']))
            elif material == 'leather':
                radius = diameter / 2 - 1.0
                dwg.add(dwg.text(f"{pad_size:.1f}".rstrip('0').rstrip('.'),
                                 insert=(cx, cy - radius),
                                 text_anchor="middle", alignment_baseline="middle",
                                 font_size="2mm", fill=LAYER_COLORS['engraving']))
    dwg.save()

def parse_pad_list(pad_input):
    pad_list = []
    for line in pad_input.strip().splitlines():
        try:
            size, qty = map(float, line.strip().split('x'))
            pad_list.append({'size': size, 'qty': int(qty)})
        except:
            continue
    return pad_list

def create_grid(canvas, width_px, height_px, scale):
    spacing = 25.4 * scale  # every inch
    for i in range(int(width_px // spacing)):
        x = i * spacing
        canvas.create_line(x, 0, x, height_px, fill='lightgray')
        canvas.create_text(x + 2, 10, anchor='nw', text=f"{i}"", fill='gray')
    for i in range(int(height_px // spacing)):
        y = i * spacing
        canvas.create_line(0, y, width_px, y, fill='lightgray')
        canvas.create_text(2, y + 2, anchor='nw', text=f"{i}"", fill='gray')

def preview_layout(pads, material, width_mm, height_mm, root):
    width_px = width_mm * 2
    height_px = height_mm * 2
    scale = 2

    if hasattr(root, 'preview_frame'):
        root.preview_frame.destroy()

    preview_frame = tk.Frame(root)
    preview_frame.pack(side='right', fill='both', expand=False)
    root.preview_frame = preview_frame

    label = tk.Label(preview_frame, text=f"{material.upper()} Layout")
    label.pack()

    canvas = tk.Canvas(preview_frame, width=width_px, height=height_px, bg='white')
    canvas.pack()

    create_grid(canvas, width_px, height_px, scale)

    positions = []
    tag_map = {}

    x, y = 10, 10
    spacing = 1.0
    row_height = 0

    for i, pad in enumerate(pads):
        pad_size = pad['size']
        qty = pad['qty']
        row = []

        for j in range(qty):
            if material == 'felt':
                diameter = pad_size - FELT_OFFSET
            elif material == 'card':
                diameter = pad_size - CARD_OFFSET
            elif material == 'leather':
                back_wrap = leather_back_wrap(pad_size)
                diameter = pad_size + 2 * (3.175 + back_wrap)
                diameter = round(diameter * 2) / 2
            else:
                continue

            if x + diameter > width_mm:
                x = 10
                y += row_height + spacing
                row_height = 0
            if y + diameter > height_mm:
                break

            cx = x + diameter / 2
            cy = y + diameter / 2
            radius = diameter / 2

            tag = f"disc_{i}_{j}"
            outer = canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, outline=LAYER_COLORS[material], tags=tag)
            if material != 'leather' and should_have_center_hole(pad_size):
                canvas.create_oval(cx - CENTER_HOLE_DIAMETER / 2, cy - CENTER_HOLE_DIAMETER / 2,
                                   cx + CENTER_HOLE_DIAMETER / 2, cy + CENTER_HOLE_DIAMETER / 2,
                                   outline=LAYER_COLORS['center_hole'], tags=tag)
            row.append((x, y))
            tag_map[tag] = (i, j)
            x += diameter + spacing
            row_height = max(row_height, diameter)

        positions.append(row)

    drag_data = {"x": 0, "y": 0, "tag": None}

    def on_start_drag(event):
        drag_data["tag"] = canvas.gettags("current")[0]
        drag_data["x"] = event.x
        drag_data["y"] = event.y

    def on_drag(event):
        dx = (event.x - drag_data["x"])
        dy = (event.y - drag_data["y"])
        drag_data["x"] = event.x
        drag_data["y"] = event.y
        tag = drag_data["tag"]
        canvas.move(tag, dx, dy)
        i, j = tag_map[tag]
        positions[i][j] = (positions[i][j][0] + dx / scale, positions[i][j][1] + dy / scale)

    canvas.tag_bind("all", "<ButtonPress-1>", on_start_drag)
    canvas.tag_bind("all", "<B1-Motion>", on_drag)

    positions_by_material[material] = positions

def launch_gui():
    root = tk.Tk()
    root.title("Stohrer Sax Pad SVG Generator")
    root.geometry("900x600")

    tk.Label(root, text="Enter pad sizes (e.g. 42.0x3):").pack()
    pad_entry = tk.Text(root, height=10)
    pad_entry.pack(fill="x", padx=10)

    tk.Label(root, text="Select materials:").pack()
    material_vars = {'felt': tk.BooleanVar(), 'card': tk.BooleanVar(), 'leather': tk.BooleanVar()}
    for m in material_vars:
        tk.Checkbutton(root, text=m.capitalize(), variable=material_vars[m]).pack(anchor='w', padx=20)

    tk.Label(root, text="Sheet width (inches):").pack()
    width_entry = tk.Entry(root)
    width_entry.insert(0, "13.5")
    width_entry.pack()

    tk.Label(root, text="Sheet height (inches):").pack()
    height_entry = tk.Entry(root)
    height_entry.insert(0, "10")
    height_entry.pack()

    tk.Label(root, text="Output filename base:").pack()
    filename_entry = tk.Entry(root)
    filename_entry.insert(0, "my_pad_job")
    filename_entry.pack(fill="x", padx=10)

    def on_generate():
        try:
            width_mm = float(width_entry.get()) * 25.4
            height_mm = float(height_entry.get()) * 25.4
        except:
            messagebox.showerror("Error", "Invalid dimensions.")
            return
        pads = parse_pad_list(pad_entry.get("1.0", tk.END))
        if not pads:
            messagebox.showerror("Error", "No pad sizes entered.")
            return
        base = filename_entry.get().strip()
        save_dir = filedialog.askdirectory(title="Save SVGs to...")
        if not save_dir:
            return
        for material, var in material_vars.items():
            if var.get():
                filename = os.path.join(save_dir, f"{base}_{material}.svg")
                generate_svg(pads, material, width_mm, height_mm, filename)
        messagebox.showinfo("Success", "SVGs generated.")

    def on_preview():
        try:
            width_mm = float(width_entry.get()) * 25.4
            height_mm = float(height_entry.get()) * 25.4
        except:
            messagebox.showerror("Error", "Invalid dimensions.")
            return
        pads = parse_pad_list(pad_entry.get("1.0", tk.END))
        for material, var in material_vars.items():
            if var.get():
                preview_layout(pads, material, width_mm, height_mm, root)

    tk.Button(root, text="Preview Layout", command=on_preview).pack(pady=10)
    tk.Button(root, text="Generate SVGs", command=on_generate).pack(pady=10)

    root.mainloop()

if __name__ == '__main__':
    launch_gui()
