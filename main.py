
# Stohrer Sax Pad SVG Generator - Full Version with Presets, V3 Rules, and Collision-Aware Nesting

import svgwrite
import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from math import sqrt

# Constants
FELT_OFFSET = 0.75
CARD_OFFSET = FELT_OFFSET + 2.0
CENTER_HOLE_DIAMETER = 3.5
SPACING_MM = 1.0
PRESET_FILE = "pad_presets.json"

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

def parse_pad_list(pad_input):
    pad_list = []
    for line in pad_input.strip().splitlines():
        try:
            size, qty = map(float, line.strip().split('x'))
            pad_list.append({'size': size, 'qty': int(qty)})
        except:
            continue
    return pad_list

def load_presets():
    if os.path.exists(PRESET_FILE):
        with open(PRESET_FILE, "r") as f:
            return json.load(f)
    return {}

def save_presets(presets):
    with open(PRESET_FILE, "w") as f:
        json.dump(presets, f, indent=2)

def generate_svg(pads, material, width_mm, height_mm, filename):
    dwg = svgwrite.Drawing(filename, size=(f"{width_mm}mm", f"{height_mm}mm"))
    discs = []

    for pad in pads:
        pad_size = pad['size']
        qty = pad['qty']
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
        for _ in range(qty):
            discs.append((pad_size, diameter))

    discs.sort(key=lambda x: -x[1])
    placed = []

    for pad_size, dia in discs:
        r = dia / 2
        x = SPACING_MM
        y = SPACING_MM
        placed_successfully = False

        while y + dia + SPACING_MM <= height_mm:
            while x + dia + SPACING_MM <= width_mm:
                cx = x + r
                cy = y + r
                if not any((cx - px)**2 + (cy - py)**2 < (r + pr + SPACING_MM)**2 for _, px, py, pr in placed):
                    placed.append((pad_size, cx, cy, r))
                    placed_successfully = True
                    break
                x += 1
            if placed_successfully:
                break
            x = SPACING_MM
            y += 1

    for pad_size, cx, cy, r in placed:
        dwg.add(dwg.circle(center=(cx, cy), r=r, stroke=LAYER_COLORS[material], fill='none'))

        if should_have_center_hole(pad_size):
            dwg.add(dwg.circle(center=(cx, cy), r=CENTER_HOLE_DIAMETER / 2,
                               stroke=LAYER_COLORS['center_hole'], fill='none'))

        if material == 'leather':
            engraving_y = cy - (r - 1.0)
        else:
            engraving_y = cy - ((CENTER_HOLE_DIAMETER / 2 + r) / 2)

        dwg.add(dwg.text(f"{pad_size:.1f}", insert=(cx, engraving_y),
                         text_anchor="middle", alignment_baseline="middle",
                         font_size="2mm", fill=LAYER_COLORS['engraving']))

    dwg.save()

def launch_gui():
    root = tk.Tk()
    root.title("Stohrer Sax Pad SVG Generator")
    root.configure(bg="#FFFDD0")
    root.geometry("600x560")

    tk.Label(root, text="Enter pad sizes (e.g. 42.0x3):", bg="#FFFDD0").pack(pady=5)
    pad_entry = tk.Text(root, height=10)
    pad_entry.pack(fill="x", padx=10)

    # Preset section
    preset_frame = tk.Frame(root, bg="#FFFDD0")
    preset_frame.pack(pady=5)
    tk.Label(preset_frame, text='Presets:', bg="#FFFDD0").grid(row=0, column=0)
    preset_var = tk.StringVar()
    preset_dropdown = tk.OptionMenu(preset_frame, preset_var, '')
    preset_dropdown.grid(row=0, column=1)

    def refresh_presets():
        presets = load_presets()
        menu = preset_dropdown['menu']
        menu.delete(0, 'end')
        for name in presets:
            menu.add_command(label=name, command=lambda v=name: preset_var.set(v))

    def apply_preset():
        name = preset_var.get()
        presets = load_presets()
        if name in presets:
            pad_entry.delete('1.0', tk.END)
            pad_entry.insert(tk.END, presets[name])

    def save_preset():
        name = preset_var.get()
        if name:
            presets = load_presets()
            presets[name] = pad_entry.get('1.0', tk.END).strip()
            save_presets(presets)
            refresh_presets()

    def delete_preset():
        name = preset_var.get()
        presets = load_presets()
        if name in presets:
            del presets[name]
            save_presets(presets)
            refresh_presets()
            preset_var.set('')

    tk.Button(preset_frame, text='Apply', command=apply_preset).grid(row=0, column=2)
    tk.Button(preset_frame, text='Save', command=save_preset).grid(row=0, column=3)
    tk.Button(preset_frame, text='Delete', command=delete_preset).grid(row=0, column=4)
    refresh_presets()

    tk.Label(root, text="Select materials:", bg="#FFFDD0").pack(pady=5)
    material_vars = {'felt': tk.BooleanVar(), 'card': tk.BooleanVar(), 'leather': tk.BooleanVar()}
    for m in material_vars:
        tk.Checkbutton(root, text=m.capitalize(), variable=material_vars[m], bg="#FFFDD0").pack(anchor='w', padx=20)

    tk.Label(root, text="Sheet width (inches):", bg="#FFFDD0").pack()
    width_entry = tk.Entry(root)
    width_entry.insert(0, "14.5")
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

    tk.Button(root, text="Generate SVGs", command=on_generate).pack(pady=20)
    root.mainloop()

if __name__ == '__main__':
    launch_gui()
