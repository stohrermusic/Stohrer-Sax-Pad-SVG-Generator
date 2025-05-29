
# Stohrer Sax Pad SVG Generator - Docked Preview Panel, Toggle, and Cream Background
import svgwrite
import os
import tkinter as tk
from tkinter import filedialog, messagebox

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

positions = []

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

preview_window = None
canvas_items = {}

def toggle_preview(pads, material, width_mm, height_mm, parent):
    global preview_window, positions, canvas_items

    if preview_window and preview_window.winfo_exists():
        preview_window.destroy()
        preview_window = None
        return

    preview_window = tk.Toplevel(parent)
    preview_window.title("Preview Layout")
    preview_window.geometry(f"{int(width_mm)}x{int(height_mm)}+{parent.winfo_x() + parent.winfo_width() + 10}+{parent.winfo_y()}")
    canvas = tk.Canvas(preview_window, width=width_mm, height=height_mm, bg='white')
    canvas.pack()

    canvas_items = {}
    positions = []
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
            item = canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius,
                                      outline=LAYER_COLORS[material], tags=tag)
            canvas_items[tag] = {'id': item, 'x': x, 'y': y}
            row.append((x, y))
            row_height = max(row_height, diameter)
            x += diameter + spacing
        positions.append(row)

def launch_gui():
    root = tk.Tk()
    root.title("Stohrer Sax Pad SVG Generator")
    root.configure(bg="#FFFDD0")

    tk.Label(root, text="Enter pad sizes (e.g. 42.0x3):", bg="#FFFDD0").pack(pady=5)
    pad_entry = tk.Text(root, height=10)
    pad_entry.pack(fill="x", padx=10)

    tk.Label(root, text="Select materials:", bg="#FFFDD0").pack(pady=5)
    material_vars = {'felt': tk.BooleanVar(), 'card': tk.BooleanVar(), 'leather': tk.BooleanVar()}
    for m in material_vars:
        tk.Checkbutton(root, text=m.capitalize(), variable=material_vars[m], bg="#FFFDD0").pack(anchor='w', padx=20)

    tk.Label(root, text="Sheet width (inches):", bg="#FFFDD0").pack()
    width_entry = tk.Entry(root)
    width_entry.insert(0, "13.5")
    width_entry.pack()

    tk.Label(root, text="Sheet height (inches):", bg="#FFFDD0").pack()
    height_entry = tk.Entry(root)
    height_entry.insert(0, "10")
    height_entry.pack()

    tk.Label(root, text="Output filename base (no extension):", bg="#FFFDD0").pack(pady=5)
    filename_entry = tk.Entry(root)
    filename_entry.insert(0, "my_pad_job")
    filename_entry.pack(fill="x", padx=10)

    def on_generate():
        try:
            width_mm = float(width_entry.get()) * 25.4
            height_mm = float(height_entry.get()) * 25.4
        except:
            messagebox.showerror("Error", "Invalid sheet dimensions.")
            return

        pads = parse_pad_list(pad_entry.get("1.0", tk.END))
        if not pads:
            messagebox.showerror("Error", "No valid pad sizes entered.")
            return

        base = filename_entry.get().strip()
        save_dir = filedialog.askdirectory(title="Select Folder to Save SVGs")
        if not save_dir:
            return

        for material, var in material_vars.items():
            if var.get():
                filename = os.path.join(save_dir, f"{base}_{material}.svg")
                generate_svg(pads, material, width_mm, height_mm, filename)

        messagebox.showinfo("Done", "SVGs generated successfully.")

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
                toggle_preview(pads, material, width_mm, height_mm, root)

    tk.Button(root, text="Preview Layout", command=on_preview).pack(pady=10)
    tk.Button(root, text="Generate SVGs", command=on_generate).pack(pady=10)

    root.mainloop()

if __name__ == '__main__':
    launch_gui()
