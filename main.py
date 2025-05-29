# Stohrer Sax Pad SVG Generator with Preview Panel Fixes Applied

import svgwrite
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

# Constants
FELT_OFFSET = 0.75
CARD_OFFSET = FELT_OFFSET + 2.0  # Tapered card
CENTER_HOLE_DIAMETER = 3.5
LAYER_COLORS = {'felt': 'black', 'card': 'blue', 'leather': 'red', 'center_hole': 'dimgray', 'engraving': 'orange'}

positions = {}
preview_window = None
preview_canvas = None
active_material = ''
canvas_items = {}

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
    for i, pad in enumerate(pads):
        size = pad['size']
        qty = pad['qty']
        for j in range(qty):
            pos = positions.get(material, {}).get((i, j), (10, 10))
            if material == 'felt':
                diameter = size - FELT_OFFSET
            elif material == 'card':
                diameter = size - CARD_OFFSET
            elif material == 'leather':
                diameter = size + 2 * (3.175 + leather_back_wrap(size))
                diameter = round(diameter * 2) / 2
            else:
                continue
            cx, cy = pos
            dwg.add(dwg.circle(center=(cx, cy), r=diameter / 2, stroke=LAYER_COLORS[material], fill='none'))
            if material != 'leather' and should_have_center_hole(size):
                dwg.add(dwg.circle(center=(cx, cy), r=CENTER_HOLE_DIAMETER / 2, stroke=LAYER_COLORS['center_hole'], fill='none'))
            radius = diameter / 2 - 1.0 if material == 'leather' else (diameter / 2 + CENTER_HOLE_DIAMETER / 2) / 2
            dwg.add(dwg.text(f"{size:.1f}".rstrip('0').rstrip('.'), insert=(cx, cy - radius), text_anchor="middle", alignment_baseline="middle", font_size="2mm", fill=LAYER_COLORS['engraving']))
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

def show_preview(pads, material, width_mm, height_mm):
    global preview_window, preview_canvas, positions, active_material, canvas_items
    if preview_window and preview_window.winfo_exists():
        preview_window.destroy()
        return
    preview_window = tk.Toplevel()
    preview_window.title("Preview Layout")
    preview_canvas = tk.Canvas(preview_window, width=width_mm, height=height_mm, bg='white')
    preview_canvas.pack()
    preview_window.geometry(f"{int(width_mm)}x{int(height_mm)}+1000+100")

    spacing = 1.0
    x, y = 10, 10
    row_height = 0
    active_material = material
    positions[material] = {}
    canvas_items = {}

    # Grid overlay
    inch_spacing = 25.4
    for i in range(int(width_mm // inch_spacing) + 1):
        pos = i * inch_spacing
        preview_canvas.create_line(pos, 0, pos, height_mm, fill='lightgray')
        preview_canvas.create_text(pos + 2, 10, anchor='nw', text=f"{i}", fill='gray')
    for j in range(int(height_mm // inch_spacing) + 1):
        pos = j * inch_spacing
        preview_canvas.create_line(0, pos, width_mm, pos, fill='lightgray')
        preview_canvas.create_text(2, pos + 2, anchor='nw', text=f"{j}", fill='gray')

    for i, pad in enumerate(pads):
        size = pad['size']
        qty = pad['qty']
        for j in range(qty):
            if material == 'felt':
                diameter = size - FELT_OFFSET
            elif material == 'card':
                diameter = size - CARD_OFFSET
            elif material == 'leather':
                diameter = size + 2 * (3.175 + leather_back_wrap(size))
                diameter = round(diameter * 2) / 2
            else:
                continue
            if x + diameter > width_mm:
                x, y = 10, y + row_height + spacing
                row_height = 0
            if y + diameter > height_mm:
                continue
            cx, cy = x + diameter / 2, y + diameter / 2
            tag = f"pad_{i}_{j}"
            circle = preview_canvas.create_oval(cx - diameter / 2, cy - diameter / 2, cx + diameter / 2, cy + diameter / 2, outline=LAYER_COLORS[material], tags=tag)
            label = preview_canvas.create_text(cx, cy, text=f"{size:.1f}".rstrip('0').rstrip('.'), fill=LAYER_COLORS['engraving'], tags=tag)
            positions[material][(i, j)] = (cx, cy)
            canvas_items[tag] = {'circle': circle, 'label': label}
            def make_drag(tag=tag, i=i, j=j):
                def start_drag(event):
                    preview_canvas.tag_bind(tag, "<B1-Motion>", drag(tag, i, j, event.x, event.y))
                return start_drag
            def drag(tag, i, j, x0, y0):
                def motion(event):
                    dx, dy = event.x - x0, event.y - y0
                    preview_canvas.move(tag, dx, dy)
                    pos = preview_canvas.coords(canvas_items[tag]['circle'])
                    cx = (pos[0] + pos[2]) / 2
                    cy = (pos[1] + pos[3]) / 2
                    positions[material][(i, j)] = (cx, cy)
                return motion
            preview_canvas.tag_bind(tag, "<ButtonPress-1>", make_drag(tag))
            x += diameter + spacing
            row_height = max(row_height, diameter)

def launch_gui():
    root = tk.Tk()
    root.title("Stohrer Sax Pad SVG Generator")
    root.configure(bg='#FFFDD0')

    tk.Label(root, text="Enter pad sizes (e.g. 42.0x3):", bg='#FFFDD0').pack(pady=5)
    pad_entry = tk.Text(root, height=10)
    pad_entry.pack(fill="x", padx=10)

    tk.Label(root, text="Select materials:", bg='#FFFDD0').pack(pady=5)
    material_vars = {'felt': tk.BooleanVar(), 'card': tk.BooleanVar(), 'leather': tk.BooleanVar()}
    for m in material_vars:
        tk.Checkbutton(root, text=m.capitalize(), variable=material_vars[m], bg='#FFFDD0').pack(anchor='w', padx=20)

    tk.Label(root, text="Sheet width (inches):", bg='#FFFDD0').pack()
    width_entry = tk.Entry(root)
    width_entry.insert(0, "13.5")
    width_entry.pack()

    tk.Label(root, text="Sheet height (inches):", bg='#FFFDD0').pack()
    height_entry = tk.Entry(root)
    height_entry.insert(0, "10")
    height_entry.pack()

    tk.Label(root, text="Output filename base (no extension):", bg='#FFFDD0').pack(pady=5)
    filename_entry = tk.Entry(root)
    filename_entry.insert(0, "my_pad_job")
    filename_entry.pack(fill="x", padx=10)

    def on_preview():
        try:
            width_mm = float(width_entry.get()) * 25.4
            height_mm = float(height_entry.get()) * 25.4
        except:
            messagebox.showerror("Error", "Invalid sheet dimensions.")
            return
        pads = parse_pad_list(pad_entry.get("1.0", tk.END))
        for material, var in material_vars.items():
            if var.get():
                show_preview(pads, material, width_mm, height_mm)
                break

    def on_generate():
        try:
            width_mm = float(width_entry.get()) * 25.4
            height_mm = float(height_entry.get()) * 25.4
        except:
            messagebox.showerror("Error", "Invalid sheet dimensions.")
            return
        pads = parse_pad_list(pad_entry.get("1.0", tk.END))
        base = filename_entry.get().strip()
        save_dir = filedialog.askdirectory(title="Select Folder to Save SVGs")
        if not save_dir: return
        for material, var in material_vars.items():
            if var.get():
                filepath = os.path.join(save_dir, f"{base}_{material}.svg")
                generate_svg(pads, material, width_mm, height_mm, filepath)
        messagebox.showinfo("Done", "SVGs generated successfully.")

    tk.Button(root, text="Preview Layout", command=on_preview).pack(pady=10)
    tk.Button(root, text="Generate SVGs", command=on_generate).pack(pady=10)
    root.mainloop()

if __name__ == '__main__':
    launch_gui()