# Stohrer Sax Pad SVG Generator - Full GUI and SVG Export Tool

import svgwrite
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Constants for material rules
FELT_OFFSET = 0.75
CARD_OFFSET = FELT_OFFSET + 2.0  # Tapered card
CENTER_HOLE_DIAMETER = 3.5

LAYER_COLORS = {
    'felt': 'black',
    'card': 'blue',
    'leather': 'red',
    'center_hole': 'dimgray',
    'engraving': 'orange'
}

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
    x, y = 10, 10
    spacing = 1.0
    row_height = 0

    for pad in pads:
        pad_size = pad['size']
        qty = pad['qty']

        for _ in range(qty):
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
                messagebox.showwarning("Layout Overflow", f"Not enough space to place all pads on the sheet.")
                return

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

            row_height = max(row_height, diameter)
            x += diameter + spacing

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

def launch_gui():
    root = tk.Tk()
    root.title("Stohrer Sax Pad SVG Generator")
    root.geometry("600x500")

    tk.Label(root, text="Enter pad sizes (e.g. 42.0x3):").pack(pady=5)
    pad_entry = tk.Text(root, height=10)
    pad_entry.pack(fill="x", padx=10)

    tk.Label(root, text="Select materials:").pack(pady=5)
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

    tk.Label(root, text="Output filename base (no extension):").pack(pady=5)
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

    tk.Button(root, text="Generate SVGs", command=on_generate).pack(pady=15)

    root.mainloop()

if __name__ == '__main__':
    launch_gui()
