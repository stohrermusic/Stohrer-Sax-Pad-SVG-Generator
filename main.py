
def generate_svg(pads, material, width_mm, height_mm, filename, hole_setting):
    dwg = svgwrite.Drawing(filename, size=(f"{width_mm}mm", f"{height_mm}mm"))
    spacing_mm = 1.0
    discs = []

    for pad in pads:
        pad_size = pad['size']
        qty = pad['qty']
        if material == 'felt':
            diameter = pad_size - 0.75
        elif material == 'card':
            diameter = pad_size - 2.75
        elif material == 'leather':
            def leather_back_wrap(pad_size):
                if pad_size <= 10:
                    return 1.3
                elif pad_size <= 15:
                    return 1.3 + (pad_size - 10) * (0.7 / 5.0)
                elif pad_size <= 40:
                    return 2.0 + (pad_size - 15) * (1.5 / 25.0)
                else:
                    return 3.5
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
        x = spacing_mm
        y = spacing_mm
        placed_successfully = False

        while y + dia + spacing_mm <= height_mm:
            while x + dia + spacing_mm <= width_mm:
                cx = x + r
                cy = y + r
                if not any((cx - px)**2 + (cy - py)**2 < (r + pr + spacing_mm)**2 for _, px, py, pr in placed):
                    placed.append((pad_size, cx, cy, r))
                    placed_successfully = True
                    break
                x += 1
            if placed_successfully:
                break
            x = spacing_mm
            y += 1

    for pad_size, cx, cy, r in placed:
        dwg.add(dwg.circle(center=(cx, cy), r=r, stroke=LAYER_COLORS[material], fill='none'))

        # Center hole logic
        hole_dia = 0
        if hole_setting == "3.5mm" and pad_size >= 16.5:
            hole_dia = 3.5
        elif hole_setting == "3.0mm" and pad_size >= 16.5:
            hole_dia = 3.0
        if hole_dia > 0:
            dwg.add(dwg.circle(center=(cx, cy), r=hole_dia / 2,
                               stroke=LAYER_COLORS['center_hole'], fill='none'))

        if material == 'leather':
            engraving_y = cy - (r - 1.0)
        else:
            engraving_y = cy - ((r + (hole_dia / 2 if hole_dia else CENTER_HOLE_DIAMETER / 2)) / 2)

        dwg.add(dwg.text(f"{pad_size:.1f}".rstrip('0').rstrip('.'),
                         insert=(cx, engraving_y),
                         text_anchor="middle", alignment_baseline="middle",
                         font_size="2mm", fill=LAYER_COLORS['engraving']))

    dwg.save()


# Stohrer Sax Pad SVG Generator - Full GUI and SVG Export Tool with Presets and Leather Center Holes

import svgwrite
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
import json

# Constants for material rules
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

PRESET_FILE = "pad_presets.json"

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

def save_preset(name, pad_text):
    try:
        presets = load_presets()
        presets[name] = pad_text
        with open("pad_presets.json", 'w') as f:
            json.dump(presets, f, indent=2)
        messagebox.showinfo("Preset Saved", f"Preset '{name}' saved successfully.")
    except Exception as e:
        messagebox.showerror("Error Saving Preset", str(e))

def delete_preset(name, combo, pad_entry):
    try:
        presets = load_presets()
        if name in presets:
            del presets[name]
            with open("pad_presets.json", 'w') as f:
                json.dump(presets, f, indent=2)
            combo['values'] = list(presets.keys())
            combo.set("Load Preset")
            pad_entry.delete("1.0", tk.END)
            messagebox.showinfo("Preset Deleted", f"Preset '{name}' deleted.")
    except Exception as e:
        messagebox.showerror("Error Deleting Preset", str(e))

def load_presets():
    if os.path.exists(PRESET_FILE):
        with open(PRESET_FILE, 'r') as f:
            return json.load(f)
    return {}

def launch_gui():
    root = tk.Tk()
    root.title("Stohrer Sax Pad SVG Generator")
    root.geometry("620x580")
    root.configure(bg="#FFFDD0")

    tk.Label(root, text="Enter pad sizes (e.g. 42.0x3):", bg="#FFFDD0").pack(pady=5)
    pad_entry = tk.Text(root, height=10)
    pad_entry.pack(fill="x", padx=10)

    tk.Label(root, text="Select materials:", bg="#FFFDD0").pack(pady=5)
    material_vars = {'felt': tk.BooleanVar(), 'card': tk.BooleanVar(), 'leather': tk.BooleanVar()}
    for m in material_vars:
        tk.Checkbutton(root, text=m.capitalize(), variable=material_vars[m], bg="#FFFDD0").pack(anchor='w', padx=20)

    
    tk.Label(root, text="Center hole:", bg="#FFFDD0").pack(pady=5)
    hole_var = tk.StringVar(value="3.5mm")
    hole_menu = tk.OptionMenu(root, hole_var, "No center holes", "3.5mm", "3.0mm")
    hole_menu.pack()

    tk.Label(root, text="Center hole size:", bg="#FFFDD0").pack()
    hole_var = tk.StringVar(value="3.5mm")
    tk.OptionMenu(root, hole_var, "No center holes", "3.5mm", "3.0mm").pack()
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
                generate_svg(pads, material, width_mm, height_mm, filename, hole_var.get())

        messagebox.showinfo("Done", "SVGs generated successfully.")

    def on_save_preset():
        name = simpledialog.askstring("Save Preset", "Enter a name for this preset:")
        if name:
            save_preset(name, pad_entry.get("1.0", tk.END))

    def on_load_preset(selected_name):
        presets = load_presets()
        if selected_name in presets:
            pad_entry.delete("1.0", tk.END)
            pad_entry.insert(tk.END, presets[selected_name])

    def on_delete_preset():
        selected = preset_var.get()
        if selected and selected != "Load Preset":
            delete_preset(selected, preset_menu, pad_entry)

    tk.Button(root, text="Generate SVGs", command=on_generate).pack(pady=15)

    preset_frame = tk.Frame(root, bg="#FFFDD0")
    preset_frame.pack(pady=10)
    tk.Button(preset_frame, text="Save Pad Sizes as Preset", command=on_save_preset).pack(side="left", padx=5)

    saved_presets = load_presets()
    preset_names = list(saved_presets.keys())
    preset_var = tk.StringVar()
    preset_menu = ttk.Combobox(preset_frame, textvariable=preset_var, values=preset_names, state="readonly", width=20)
    preset_menu.set("Load Preset")
    preset_menu.pack(side="left", padx=5)
    preset_menu.bind("<<ComboboxSelected>>", lambda e: on_load_preset(preset_var.get()))

    tk.Button(preset_frame, text="Delete Preset", command=on_delete_preset).pack(side="left", padx=5)

    root.mainloop()

if __name__ == '__main__':
    launch_gui()
