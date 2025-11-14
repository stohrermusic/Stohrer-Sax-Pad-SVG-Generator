import svgwrite
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
import json
import time
import random
import math

# --- Lightburn Color Palette ---
LIGHTBURN_COLORS = [
    ("00 - Black", "#000000"), ("01 - Blue", "#0000FF"), ("02 - Red", "#FF0000"),
    ("03 - Green", "#00E000"), ("04 - Yellow", "#D0D000"), ("05 - Orange", "#FF8000"),
    ("06 - Cyan", "#00E0E0"), ("07 - Magenta", "#FF00FF"), ("08 - Light Gray", "#B4B4B4"),
    ("09 - Dark Blue", "#0000A0"), ("10 - Dark Red", "#A00000"), ("11 - Dark Green", "#00A000"),
    ("12 - Dark Yellow", "#A0A000"), ("13 - Brown", "#C08000"), ("14 - Light Blue", "#00A0FF"),
    ("15 - Dark Magenta", "#A000A0"), ("16 - Gray", "#808080"), ("17 - Periwinkle", "#7D87B9"),
    ("18 - Rose", "#BB7784"), ("19 - Cornflower", "#4A6FE3"), ("20 - Cerise", "#D33F6A"),
    ("21 - Light Green", "#8CD78C"), ("22 - Tan", "#F0B98D"), ("23 - Pink", "#F6C4E1"),
    ("24 - Lavender", "#FA9ED4"), ("25 - Purple", "#500A78"), ("26 - Ochre", "#B45A00"),
    ("27 - Teal", "#004754"), ("28 - Mint", "#86FA88"), ("29 - Pale Yellow", "#FFDB66")
]

# --- Default Key Height Fields ---
# All possible keys in their desired display order
ALL_KEY_HEIGHT_FIELDS = [
    "B", "F", "Palm F", "Palm E", "Palm Eb", "Palm D", 
    "G", "D", "Low C", "Low B", "Low Bb"
]

# --- Default Configuration ---
DEFAULT_SETTINGS = {
    "units": "in",
    "felt_offset": 0.75,
    "card_to_felt_offset": 2.0,
    "leather_wrap_multiplier": 1.00,
    "sheet_width": "13.5",
    "sheet_height": "10",
    "hole_option": "3.5mm",
    "custom_hole_size": "4.0",
    "min_hole_size": 16.5,
    "felt_thickness": 3.175,
    "felt_thickness_unit": "mm",
    "engraving_on": True,
    "show_engraving_warning": True,
    "last_output_dir": "",
    "resonance_clicks": 0, # Easter Egg Counter
    "compatibility_mode": False, # For Inkscape/etc.
    
    "key_layout": {
        "show_serial": False,
        "large_notes": False,
        "show_B": True, # Default on
        "show_F": True, # Default on
        "show_Palm F": False,
        "show_Palm E": False,
        "show_Palm Eb": False,
        "show_Palm D": False,
        "show_G": False,
        "show_D": False,
        "show_Low C": True, # Keep this on by default from old "required"
        "show_Low B": False,
        "show_Low Bb": False
    },

    "engraving_font_size": {
        "felt": 2.0,
        "card": 2.0,
        "leather": 2.0,
        "exact_size": 2.0
    },
    "engraving_location": {
        "felt": {"mode": "centered", "value": 0.0},
        "card": {"mode": "centered", "value": 0.0},
        "leather": {"mode": "from_outside", "value": 1.0},
        "exact_size": {"mode": "centered", "value": 0.0}
    },
    "layer_colors": {
        'felt_outline': '#000000',
        'felt_center_hole': '#0000A0',
        'felt_engraving': '#A00000',
        'card_outline': '#0000FF',
        'card_center_hole': '#00A0FF',
        'card_engraving': '#A000A0',
        'leather_outline': '#FF0000',
        'leather_center_hole': '#00E000',
        'leather_engraving': '#FF8000',
        'exact_size_outline': '#D0D000',
        'exact_size_center_hole': '#A0A000',
        'exact_size_engraving': '#BB7784'
    }
}

PAD_PRESET_FILE = "pad_presets.json"
KEY_PRESET_FILE = "key_height_library.json" # New file for key heights
SETTINGS_FILE = "app_settings.json"

# --- Easter Egg Constants ---
RESONANCE_MESSAGES = [
    "Resonance added!", "Pad resonance increased!", "More resonance now!",
    "Timbral focus enhanced!", "Harmonic alignment optimized!", "Acoustic reflection matrix calibrated!",
    "Core vibrations synchronized!", "Nodal points stabilized!", "Overtone series enriched!",
    "Sonic clarity has been improved!", "Relacquer devaluation reversed!", "Heavy mass screws ain't SHIT!",
    "Now you don't even have to fit the neck!", "Let's call this the ULTRAhaul!", "Now safe to use hot glue!",
    "Look at me! I am the resonator now!"
]
COOL_BLUE = "#E0F7FA"
COOL_GREEN = "#E8F5E9"

class ConfirmationDialog(tk.Toplevel):
    def __init__(self, parent, title, message):
        super().__init__(parent)
        self.title(title)
        self.geometry("450x150")
        self.configure(bg="#F0EAD6")
        self.transient(parent)
        self.grab_set()

        self.result = False
        self.dont_show_again = tk.BooleanVar()

        tk.Label(self, text=message, wraplength=430, bg="#F0EAD6", justify="left").pack(padx=10, pady=10)
        
        checkbox_frame = tk.Frame(self, bg="#F0EAD6")
        checkbox_frame.pack(pady=5)
        tk.Checkbutton(checkbox_frame, text="Don't show this message again", variable=self.dont_show_again, bg="#F0EAD6").pack()
        
        button_frame = tk.Frame(self, bg="#F0EAD6")
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Yes, Proceed", command=self.on_yes).pack(side="left", padx=10)
        tk.Button(button_frame, text="No, Cancel", command=self.on_no).pack(side="left", padx=10)

        self.protocol("WM_DELETE_WINDOW", self.on_no)
        self.wait_window(self)

    def on_yes(self):
        self.result = True
        self.destroy()

    def on_no(self):
        self.result = False
        self.destroy()

class PadSVGGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Stohrer Sax Pad SVG Generator")
        self.root.geometry("620x640")
        self.default_bg = "#FFFDD0"
        self.root.configure(bg=self.default_bg)

        self.settings = self.load_settings()
        self.pad_presets = self.load_presets(PAD_PRESET_FILE, preset_type_name="Pad Preset")
        self.key_presets = self.load_presets(KEY_PRESET_FILE, preset_type_name="Key Height")
        
        self.create_menus()
        self.create_widgets() # This will now create the tabbed interface
        
        self.apply_resonance_theme() # Apply theme on startup
        
        self.root.config(menu=self.pad_menu) # Set initial menu
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)

    def on_exit(self):
        # Save settings from pad generator tab
        self.settings["sheet_width"] = self.width_entry.get()
        self.settings["sheet_height"] = self.height_entry.get()
        self.settings["hole_option"] = self.hole_var.get()
        if self.hole_var.get() == "Custom":
            self.settings["custom_hole_size"] = self.custom_hole_entry.get()
        self.save_settings()
        self.root.destroy()

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    loaded_settings = json.load(f)
                    settings = DEFAULT_SETTINGS.copy()
                    
                    # Ensure new nested dicts are created
                    if "key_layout" not in loaded_settings:
                        loaded_settings["key_layout"] = settings["key_layout"].copy()

                    for key, default_value in DEFAULT_SETTINGS.items():
                        if key in loaded_settings:
                            if isinstance(default_value, dict):
                                settings[key] = default_value.copy()
                                settings[key].update(loaded_settings[key])
                            else:
                                settings[key] = loaded_settings[key]
                    
                    dart_keys = [k for k in settings if k.startswith("dart_")]
                    for k in dart_keys:
                        if k in settings:
                            del settings[k]
                        
                    return settings
            except (json.JSONDecodeError, TypeError):
                return DEFAULT_SETTINGS.copy()
        return DEFAULT_SETTINGS.copy()


    def save_settings(self):
        try:
            dart_keys = [k for k in self.settings if k.startswith("dart_")]
            for k in dart_keys:
                 if k in self.settings:
                    del self.settings[k]
            
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error Saving Settings", f"Could not save settings:\n{e}")
            
    def apply_resonance_theme(self):
        clicks = self.settings.get("resonance_clicks", 0)
        color = self.default_bg
        if 10 <= clicks < 50:
            color = COOL_BLUE
        elif 50 <= clicks < 100:
            color = COOL_GREEN

        self.set_background_color(self.root, color)
        if clicks < 100:
            self.root.attributes('-alpha', 1.0)


    def set_background_color(self, parent, color):
        parent.configure(bg=color)
        
        # Configure ttk styles
        style = ttk.Style()
        style.configure('App.TFrame', background=color)
        style.map('TNotebook.Tab', background=[('selected', color), ('!selected', color)], foreground=[('selected', 'black')])
        style.configure('TNotebook', background=color)

        for widget in parent.winfo_children():
            widget_class = widget.winfo_class()
            
            if widget_class in ('Frame', 'Label', 'Radiobutton', 'Checkbutton', 'LabelFrame'):
                try:
                    widget.configure(bg=color)
                except tk.TclError:
                    pass
            elif widget_class in ('TFrame', 'TLabel', 'TRadiobutton', 'TCheckbutton', 'TLabelframe', 'TNotebook'):
                try:
                    style_name = f"{widget_class}.{color.upper()}"
                    style.configure(style_name, background=color)
                    widget.configure(style=style_name)
                except tk.TclError:
                    pass

            if isinstance(widget, (tk.Frame, tk.LabelFrame, ttk.Frame, ttk.LabelFrame)):
                self.set_background_color(widget, color)


    def create_menus(self):
        # --- Pad Generator Menu ---
        self.pad_menu = tk.Menu(self.root)
        
        pad_file_menu = tk.Menu(self.pad_menu, tearoff=0)
        self.pad_menu.add_cascade(label="File", menu=pad_file_menu)
        pad_file_menu.add_command(label="Import Pad Presets...", command=self.on_import_pad_presets)
        pad_file_menu.add_command(label="Export Pad Presets...", command=self.on_export_pad_presets)
        pad_file_menu.add_separator()
        pad_file_menu.add_command(label="Exit", command=self.on_exit)

        pad_options_menu = tk.Menu(self.pad_menu, tearoff=0)
        self.pad_menu.add_cascade(label="Options", menu=pad_options_menu)
        pad_options_menu.add_command(label="Sizing Rules...", command=self.open_options_window)
        pad_options_menu.add_command(label="Layer Colors...", command=self.open_color_window)

        # --- Key Height Library Menu ---
        self.key_menu = tk.Menu(self.root)
        
        key_file_menu = tk.Menu(self.key_menu, tearoff=0)
        self.key_menu.add_cascade(label="File", menu=key_file_menu)
        key_file_menu.add_command(label="Import Key Sets...", command=self.on_import_key_sets)
        key_file_menu.add_command(label="Export Key Sets...", command=self.on_export_key_sets)
        key_file_menu.add_separator()
        key_file_menu.add_command(label="Exit", command=self.on_exit)
        
        key_options_menu = tk.Menu(self.key_menu, tearoff=0)
        self.key_menu.add_cascade(label="Options", menu=key_options_menu)
        key_options_menu.add_command(label="Layout Options...", command=self.open_key_layout_window)

    def on_tab_changed(self, event):
        """Called when the notebook tab is changed."""
        current_tab = self.notebook.index(self.notebook.select())
        if current_tab == 0:
            self.root.config(menu=self.pad_menu)
        elif current_tab == 1:
            self.root.config(menu=self.key_menu)

    def create_widgets(self):
        self.notebook = ttk.Notebook(self.root)
        
        # --- Create Tab 1: Pad SVG Generator ---
        self.pad_tab = ttk.Frame(self.notebook, style='App.TFrame')
        self.notebook.add(self.pad_tab, text='Pad SVG Generator')
        self.create_pad_generator_tab(self.pad_tab)

        # --- Create Tab 2: Key Height Library ---
        self.key_tab = ttk.Frame(self.notebook, style='App.TFrame')
        self.notebook.add(self.key_tab, text='Key Height Library')
        self.create_key_library_tab(self.key_tab)
        
        self.notebook.pack(expand=True, fill="both", padx=5, pady=5)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
        # Apply theme colors to the new notebook tabs
        style = ttk.Style()
        style.configure('App.TFrame', background=self.root.cget('bg'))
        style.map('TNotebook.Tab', background=[('selected', self.default_bg), ('!selected', self.default_bg)], foreground=[('selected', 'black')])
        style.configure('TNotebook', background=self.root.cget('bg'))
        
        self.apply_resonance_theme() # Re-apply to make sure tabs get colored

    def create_pad_generator_tab(self, parent):
        tk.Label(parent, text="Enter pad sizes (e.g. 42.0x3):", bg=self.root.cget('bg')).pack(pady=5)
        self.pad_entry = tk.Text(parent, height=10)
        self.pad_entry.pack(fill="x", padx=10)

        preset_frame = tk.Frame(parent, bg=self.root.cget('bg'))
        preset_frame.pack(pady=10)
        
        tk.Button(preset_frame, text="Save as Preset", command=self.on_save_pad_preset).pack(side="left", padx=5)
        
        # --- Library Dropdown for Pads ---
        tk.Label(preset_frame, text="Library:", bg=self.root.cget('bg')).pack(side="left", padx=(10, 2))
        self.pad_library_var = tk.StringVar()
        self.pad_library_dropdown = ttk.Combobox(preset_frame, textvariable=self.pad_library_var, state="readonly", width=15)
        self.pad_library_dropdown.pack(side="left")
        self.pad_library_dropdown.bind("<<ComboboxSelected>>", self.on_pad_library_selected)
        
        preset_names = [] # Will be populated by on_pad_library_selected
        self.pad_preset_var = tk.StringVar()
        self.pad_preset_menu = ttk.Combobox(preset_frame, textvariable=self.pad_preset_var, values=preset_names, state="readonly", width=40) # Made wider
        self.pad_preset_menu.set("Load Pad Preset")
        self.pad_preset_menu.pack(side="left", padx=5)
        self.pad_preset_menu.bind("<<ComboboxSelected>>", lambda e: self.on_load_pad_preset(self.pad_preset_var.get()))
        
        tk.Button(preset_frame, text="Delete Preset", command=self.on_delete_pad_preset).pack(side="left", padx=5)

        self.update_pad_library_dropdown() # Initial population

        tk.Label(parent, text="Select materials:", bg=self.root.cget('bg')).pack(pady=5)
        self.material_vars = {
            'felt': tk.BooleanVar(value=True), 
            'card': tk.BooleanVar(value=True), 
            'leather': tk.BooleanVar(value=True),
            'exact_size': tk.BooleanVar(value=False)
        }
        for m in self.material_vars:
            tk.Checkbutton(parent, text=m.replace('_', ' ').capitalize(), variable=self.material_vars[m], bg=self.root.cget('bg')).pack(anchor='w', padx=20)

        options_frame = tk.Frame(parent, bg=self.root.cget('bg'))
        options_frame.pack(pady=10, fill='x', padx=10)

        hole_frame = tk.LabelFrame(options_frame, text="Center Hole", bg=self.root.cget('bg'), padx=5, pady=5)
        hole_frame.pack(fill="x")
        self.hole_var = tk.StringVar(value=self.settings["hole_option"])
        
        tk.Radiobutton(hole_frame, text="None", variable=self.hole_var, value="No center holes", bg=self.root.cget('bg'), command=self.toggle_custom_hole_entry).pack(side="left")
        tk.Radiobutton(hole_frame, text="3.0mm", variable=self.hole_var, value="3.0mm", bg=self.root.cget('bg'), command=self.toggle_custom_hole_entry).pack(side="left")
        tk.Radiobutton(hole_frame, text="3.5mm", variable=self.hole_var, value="3.5mm", bg=self.root.cget('bg'), command=self.toggle_custom_hole_entry).pack(side="left")
        tk.Radiobutton(hole_frame, text="Custom:", variable=self.hole_var, value="Custom", bg=self.root.cget('bg'), command=self.toggle_custom_hole_entry).pack(side="left")
        
        self.custom_hole_entry = tk.Entry(hole_frame, width=6)
        self.custom_hole_entry.insert(0, self.settings.get("custom_hole_size", "4.0"))
        self.custom_hole_entry.pack(side="left", padx=2)
        tk.Label(hole_frame, text="mm", bg=self.root.cget('bg')).pack(side="left")
        self.toggle_custom_hole_entry()

        sheet_frame = tk.LabelFrame(options_frame, text="Sheet Size", bg=self.root.cget('bg'), padx=5, pady=5)
        sheet_frame.pack(fill="x", pady=(10,0))

        self.unit_label = tk.Label(sheet_frame, text=f"Width ({self.settings['units']}):", bg=self.root.cget('bg'))
        self.unit_label.grid(row=0, column=0, sticky='w', padx=5)
        self.width_entry = tk.Entry(sheet_frame)
        self.width_entry.insert(0, self.settings["sheet_width"])
        self.width_entry.grid(row=0, column=1, sticky='w')

        self.height_label = tk.Label(sheet_frame, text=f"Height ({self.settings['units']}):", bg=self.root.cget('bg'))
        self.height_label.grid(row=1, column=0, sticky='w', padx=5)
        self.height_entry = tk.Entry(sheet_frame)
        self.height_entry.insert(0, self.settings["sheet_height"])
        self.height_entry.grid(row=1, column=1, sticky='w')

        tk.Label(parent, text="Output filename base (no extension):", bg=self.root.cget('bg')).pack(pady=5)
        self.filename_entry = tk.Entry(parent)
        self.filename_entry.insert(0, "my_pad_job")
        self.filename_entry.pack(padx=10) 

        tk.Button(parent, text="Generate SVGs", command=self.on_generate, font=('Helvetica', 10, 'bold')).pack(pady=15)
        
    def create_key_library_tab(self, parent):
        self.key_field_vars = {} # To store all StringVars
        self.key_info_widgets = {} # To store Label/Entry widgets
        self.key_height_widgets = {} # To store Label/Entry widgets
        
        # --- Preset Management Frame ---
        preset_frame = tk.Frame(parent, bg=self.root.cget('bg'))
        preset_frame.pack(pady=10)
        
        tk.Button(preset_frame, text="Save as Set", command=self.on_save_key_preset).pack(side="left", padx=5)
        
        # --- Library Dropdown ---
        tk.Label(preset_frame, text="Library:", bg=self.root.cget('bg')).pack(side="left", padx=(10, 2))
        self.key_library_var = tk.StringVar()
        self.key_library_dropdown = ttk.Combobox(preset_frame, textvariable=self.key_library_var, state="readonly", width=15)
        self.key_library_dropdown.pack(side="left")
        self.key_library_dropdown.bind("<<ComboboxSelected>>", self.on_key_library_selected)
        
        self.key_preset_var = tk.StringVar()
        self.key_preset_menu = ttk.Combobox(preset_frame, textvariable=self.key_preset_var, state="readonly", width=40) # Made wider
        self.key_preset_menu.set("Load Key Set")
        self.key_preset_menu.pack(side="left", padx=5)
        self.key_preset_menu.bind("<<ComboboxSelected>>", lambda e: self.on_load_key_preset(self.key_preset_var.get()))
        
        tk.Button(preset_frame, text="Delete Set", command=self.on_delete_key_preset).pack(side="left", padx=5)
        
        self.update_key_library_dropdown() # Initial population

        # --- Main Data Entry Frame ---
        data_frame = tk.Frame(parent, bg=self.root.cget('bg'), padx=10)
        data_frame.pack(fill="both", expand=True)

        # --- Horn Info Section ---
        self.horn_info_frame = tk.LabelFrame(data_frame, text="Horn Info", bg=self.root.cget('bg'), padx=5, pady=5)
        self.horn_info_frame.pack(fill="x", pady=5)
        self.horn_info_frame.columnconfigure(1, weight=1)
        
        # --- Key Heights Section ---
        self.key_height_frame = tk.LabelFrame(data_frame, text="Key Heights", bg=self.root.cget('bg'), padx=5, pady=5)
        self.key_height_frame.pack(fill="x", pady=5)
        self.key_height_frame.columnconfigure(1, weight=1)
        self.key_height_frame.columnconfigure(3, weight=1)
        
        # --- Create ALL widgets (but don't show them all yet) ---
        self.create_key_info_widgets()
        self.create_key_height_widgets()
        
        # --- Apply initial layout settings ---
        self.rebuild_key_tab()


    def create_key_info_widgets(self):
        frame = self.horn_info_frame
        self.key_info_widgets = {} # Clear/init widget dict
        
        # --- Default ON fields ---
        default_fields = ["Make", "Model", "Size"]
        for i, field in enumerate(default_fields):
            label = tk.Label(frame, text=f"{field}:", bg=self.root.cget('bg'))
            var = tk.StringVar()
            entry = tk.Entry(frame, textvariable=var)
            self.key_field_vars[field.lower()] = var
            self.key_info_widgets[field.lower()] = (label, entry)

        # --- Optional "Serial" field ---
        label = tk.Label(frame, text="Serial:", bg=self.root.cget('bg'))
        var = tk.StringVar()
        entry = tk.Entry(frame, textvariable=var)
        self.key_field_vars["serial"] = var
        self.key_info_widgets["serial"] = (label, entry)

        # --- Default ON "Notes" field ---
        label = tk.Label(frame, text="Notes:", bg=self.root.cget('bg'))
        entry = tk.Text(frame, height=3)
        self.key_field_vars['notes'] = entry
        self.key_info_widgets['notes'] = (label, entry)

    def create_key_height_widgets(self):
        frame = self.key_height_frame
        self.key_height_vars = {} # Clear/init dicts
        self.key_height_widgets = {}
        
        # --- Unit Conversion (always on) ---
        self.key_unit_var = tk.StringVar(value="mm")
        self.previous_key_unit = "mm"
        unit_frame = tk.Frame(frame, bg=self.root.cget('bg'))
        tk.Label(unit_frame, text="Units:", bg=self.root.cget('bg')).pack(side="left")
        tk.Radiobutton(unit_frame, text="mm", variable=self.key_unit_var, value="mm", bg=self.root.cget('bg'), command=self.on_unit_convert).pack(side="left")
        tk.Radiobutton(unit_frame, text="inches", variable=self.key_unit_var, value="in", bg=self.root.cget('bg'), command=self.on_unit_convert).pack(side="left")
        self.key_height_widgets['units'] = unit_frame # Store the whole frame

        # --- Create ALL key height fields ---
        for key in ALL_KEY_HEIGHT_FIELDS:
            label = tk.Label(frame, text=f"{key}:", bg=self.root.cget('bg'))
            var = tk.StringVar()
            entry = tk.Entry(frame, textvariable=var, width=10)
            self.key_height_vars[key] = var
            self.key_height_widgets[key] = (label, entry)

    def rebuild_key_tab(self):
        """ Hides or shows widgets based on settings """
        layout_settings = self.settings.get("key_layout", DEFAULT_SETTINGS["key_layout"])

        # --- Horn Info Section ---
        # Clear frame
        for widget in self.horn_info_frame.winfo_children():
            widget.grid_remove()

        row = 0
        for field in ["make", "model", "size"]:
            label, entry = self.key_info_widgets[field]
            label.grid(row=row, column=0, sticky='w', padx=5, pady=2)
            entry.grid(row=row, column=1, sticky='ew', padx=5)
            row += 1
        
        if layout_settings.get("show_serial", False):
            label, entry = self.key_info_widgets["serial"]
            label.grid(row=row, column=0, sticky='w', padx=5, pady=2)
            entry.grid(row=row, column=1, sticky='ew', padx=5)
            row += 1
            
        notes_label, notes_entry = self.key_info_widgets["notes"]
        notes_height = 6 if layout_settings.get("large_notes", False) else 3
        notes_entry.config(height=notes_height)
        notes_label.grid(row=row, column=0, sticky='nw', padx=5, pady=2)
        notes_entry.grid(row=row, column=1, sticky='ew', padx=5)

        # --- Key Heights Section ---
        # Clear frame
        for widget in self.key_height_frame.winfo_children():
            widget.grid_remove()
            
        row = 0
        self.key_height_widgets['units'].grid(row=row, column=0, columnspan=2, sticky='w', pady=5)
        row += 1
        
        # Place visible keys in two columns
        col = 0
        for key in ALL_KEY_HEIGHT_FIELDS:
            show_key = f"show_{key.replace(' ', '_')}"
            if layout_settings.get(show_key, True): # Default to True if key missing
                label, entry = self.key_height_widgets[key]
                label.grid(row=row, column=col*2, sticky='w', padx=5, pady=2)
                entry.grid(row=row, column=col*2 + 1, sticky='w', padx=5)
                
                col += 1
                if col > 1: # Max 2 columns
                    col = 0
                    row += 1

    def on_unit_convert(self):
        new_unit = self.key_unit_var.get()
        old_unit = self.previous_key_unit

        if new_unit == old_unit:
            return

        for var in self.key_height_vars.values():
            try:
                val = float(var.get())
                if new_unit == "in" and old_unit == "mm":
                    new_val = val / 25.4
                    var.set(f"{new_val:.4f}") # More precision for inches
                elif new_unit == "mm" and old_unit == "in":
                    new_val = val * 25.4
                    var.set(f"{new_val:.2f}")
            except (ValueError, TypeError):
                continue # Skip empty or invalid fields
        
        self.previous_key_unit = new_unit

    def on_save_key_preset(self):
        name = simpledialog.askstring("Save Key Height Set", "Enter a name for this set:")
        if not name:
            return
            
        active_library = self.key_library_var.get()
        if not active_library or active_library == "All Libraries":
            messagebox.showwarning("Save Error", "Please select a specific library to save to.")
            return

        make = self.key_field_vars['make'].get()
        model = self.key_field_vars['model'].get()
        size = self.key_field_vars['size'].get()
        
        if not all([make, model, size]):
            messagebox.showwarning("Missing Info", "Please fill in at least Make, Model, and Size before saving.")
            return
            
        data = {
            "make": make,
            "model": model,
            "size": size,
            "serial": self.key_field_vars['serial'].get(),
            "notes": self.key_notes_entry.get("1.0", tk.END).strip(),
            "units": self.key_unit_var.get(),
            # Save ALL keys, not just visible ones
            "heights": {key: var.get() for key, var in self.key_height_vars.items()}
        }
        
        if name in self.key_presets[active_library]:
            if not messagebox.askyesno("Overwrite", f"A set named '{name}' already exists in this library. Overwrite it?"):
                return
        
        self.key_presets[active_library][name] = data
        if self.save_presets(self.key_presets, KEY_PRESET_FILE):
            self.on_key_library_selected() # Refresh preset list
            messagebox.showinfo("Preset Saved", f"Preset '{name}' saved successfully to '{active_library}'.")

    def on_load_key_preset(self, selected_name):
        if not selected_name or selected_name == "Load Key Set":
            return
            
        lib_name = self.key_library_var.get()
        data = None
        
        if lib_name == "All Libraries":
            try:
                lib_name, preset_name = selected_name.split("] ", 1)
                lib_name = lib_name[1:]
                if lib_name in self.key_presets and preset_name in self.key_presets[lib_name]:
                    data = self.key_presets[lib_name][preset_name]
            except ValueError:
                return
        else:
            if lib_name in self.key_presets and selected_name in self.key_presets[lib_name]:
                data = self.key_presets[lib_name][selected_name]

        if data:
            self.key_field_vars['make'].set(data.get("make", ""))
            self.key_field_vars['model'].set(data.get("model", ""))
            self.key_field_vars['size'].set(data.get("size", ""))
            
            # Load serial only if its var exists (it always should)
            if 'serial' in self.key_field_vars:
                self.key_field_vars['serial'].set(data.get("serial", ""))
            
            self.key_notes_entry.delete("1.0", tk.END)
            self.key_notes_entry.insert(tk.END, data.get("notes", ""))
            
            unit = data.get("units", "mm")
            self.key_unit_var.set(unit)
            self.previous_key_unit = unit
            
            # Load all keys, even if hidden
            for key, var in self.key_height_vars.items():
                var.set(data.get("heights", {}).get(key, ""))
            
    def on_delete_key_preset(self):
        selected_lib = self.key_library_var.get()
        selected_preset = self.key_preset_var.get()

        if not selected_preset or selected_preset == "Load Key Set":
            messagebox.showwarning("Delete Error", "Please load a set to delete.")
            return

        if selected_lib == "All Libraries":
            try:
                selected_lib, selected_preset = selected_preset.split("] ", 1)
                selected_lib = selected_lib[1:]
            except ValueError:
                messagebox.showerror("Delete Error", "Cannot delete from 'All Libraries' view. Please select the specific library first.")
                return

        if messagebox.askyesno("Delete Key Height Set", f"Are you sure you want to delete the set '{selected_preset}' from the '{selected_lib}' library?"):
            del self.key_presets[selected_lib][selected_preset]
            if self.save_presets(self.key_presets, KEY_PRESET_FILE):
                self.on_key_library_selected() # Refresh preset list
                # Clear the form
                for var in self.key_field_vars.values():
                    if isinstance(var, tk.StringVar):
                        var.set("")
                self.key_notes_entry.delete("1.0", tk.END)
                for var in self.key_height_vars.values():
                    var.set("")
                messagebox.showinfo("Preset Deleted", f"Preset '{selected_preset}' deleted.")

    def on_pad_library_selected(self, event=None):
        lib_name = self.pad_library_var.get()
        preset_list = []
        if lib_name == "All Libraries":
            for library, presets in sorted(self.pad_presets.items()):
                for name in sorted(presets.keys()):
                    preset_list.append(f"[{library}] {name}")
        else:
            preset_list = sorted(self.pad_presets.get(lib_name, {}).keys())
        
        self.pad_preset_menu['values'] = preset_list
        self.pad_preset_menu.set("Load Pad Preset")

    def update_pad_library_dropdown(self):
        lib_names = ["All Libraries"] + sorted(self.pad_presets.keys())
        self.pad_library_dropdown['values'] = lib_names
        self.pad_library_var.set("All Libraries")
        self.on_pad_library_selected()
        
    def on_key_library_selected(self, event=None):
        lib_name = self.key_library_var.get()
        preset_list = []
        if lib_name == "All Libraries":
            for library, presets in sorted(self.key_presets.items()):
                for name in sorted(presets.keys()):
                    preset_list.append(f"[{library}] {name}")
        else:
            preset_list = sorted(self.key_presets.get(lib_name, {}).keys())
        
        self.key_preset_menu['values'] = preset_list
        self.key_preset_menu.set("Load Key Set")

    def update_key_library_dropdown(self):
        lib_names = ["All Libraries"] + sorted(self.key_presets.keys())
        self.key_library_dropdown['values'] = lib_names
        self.key_library_var.set("All Libraries")
        self.on_key_library_selected()

    # --- Pad Preset Import/Export (from File Menu) ---
    def on_import_pad_presets(self):
        filepath = filedialog.askopenfilename(
            title="Import Pad Presets",
            filetypes=(("JSON files", "*.json"), ("All files", "*.*")),
            initialdir=self.settings.get("last_output_dir", "")
        )
        if not filepath:
            return
        try:
            with open(filepath, 'r') as f:
                imported_presets = json.load(f)
            if not isinstance(imported_presets, dict):
                raise TypeError("File is not a valid preset dictionary.")

            target_lib = ImportTargetWindow(self.root, list(self.pad_presets.keys())).get_target_library()
            if not target_lib:
                return # User cancelled

            if target_lib not in self.pad_presets:
                self.pad_presets[target_lib] = {}

            ImportPresetsWindow(self.root, self.pad_presets[target_lib], imported_presets, PAD_PRESET_FILE, self.pad_preset_menu, self, "Pad Preset", save_data=self.pad_presets)
        except Exception as e:
            messagebox.showerror("Import Error", f"Could not import pad presets:\n{e}")

    def on_export_pad_presets(self):
        ExportPresetsWindow(self.root, self.pad_presets, "Pad Presets", "pad_preset_export.json", False)

    # --- Key Height Import/Export (from File Menu) ---
    def on_import_key_sets(self):
        filepath = filedialog.askopenfilename(
            title="Import Key Height Sets",
            filetypes=(("JSON files", "*.json"), ("All files", "*.*")),
            initialdir=self.settings.get("last_output_dir", "")
        )
        if not filepath:
            return
        try:
            with open(filepath, 'r') as f:
                imported_presets = json.load(f)
            if not isinstance(imported_presets, dict):
                raise TypeError("File is not a valid key height set file.")
            
            target_lib = ImportTargetWindow(self.root, list(self.key_presets.keys())).get_target_library()
            if not target_lib:
                return # User cancelled

            if target_lib not in self.key_presets:
                self.key_presets[target_lib] = {}

            ImportPresetsWindow(self.root, self.key_presets[target_lib], imported_presets, KEY_PRESET_FILE, self.key_preset_menu, self, "Key Height Set", save_data=self.key_presets)

        except Exception as e:
            messagebox.showerror("Import Error", f"Could not import key sets:\n{e}")

    def on_export_key_sets(self):
        ExportPresetsWindow(self.root, self.key_presets, "Key Height Sets", "key_height_export.json", True)
        
    # ... (rest of the methods are for the pad generator) ...

    def toggle_custom_hole_entry(self):
        if self.hole_var.get() == "Custom":
            self.custom_hole_entry.config(state='normal')
        else:
            self.custom_hole_entry.config(state='disabled')

    def open_options_window(self):
        OptionsWindow(self.root, self, self.settings, self.update_ui_from_settings, self.save_settings)
        
    def open_key_layout_window(self):
        KeyLayoutWindow(self.root, self.settings, self.rebuild_key_tab, self.save_settings)

    def open_color_window(self):
        LayerColorWindow(self.root, self.settings, self.save_settings)
        
    def open_resonance_window(self):
        ResonanceWindow(self.root, self.settings, self.save_settings, self.apply_resonance_theme)

    def update_ui_from_settings(self):
        self.unit_label.config(text=f"Width ({self.settings['units']}):")
        self.height_label.config(text=f"Height ({self.settings['units']}):")

    def get_hole_dia(self):
        hole_option = self.hole_var.get()
        if hole_option == "3.5mm": return 3.5
        if hole_option == "3.0mm": return 3.0
        if hole_option == "Custom":
            try:
                return float(self.custom_hole_entry.get())
            except (ValueError, TypeError):
                messagebox.showerror("Invalid Input", "Custom hole size must be a valid number.")
                return None
        return 0

    def on_generate(self):
        try:
            hole_dia = self.get_hole_dia()
            if hole_dia is None: return

            pads = self.parse_pad_list(self.pad_entry.get("1.0", tk.END))
            if not pads:
                messagebox.showerror("Error", "No valid pad sizes entered.")
                return

            if self.settings.get("engraving_on", True):
                oversized_engravings = check_for_oversized_engravings(pads, self.material_vars, self.settings)
                if oversized_engravings and self.settings.get("show_engraving_warning", True):
                    message = "Warning: The current font size is too large for some pads and the engraving will be skipped:\n\n"
                    for mat, sizes in oversized_engravings.items():
                        message += f"- {mat.replace('_', ' ').capitalize()}: {', '.join(map(str, sorted(sizes)))}\n"
                    message += "\nDo you want to proceed?"

                    dialog = ConfirmationDialog(self.root, "Engraving Size Warning", message)
                    if not dialog.result:
                        return
                    if dialog.dont_show_again.get():
                        self.settings["show_engraving_warning"] = False

            width_val = float(self.width_entry.get())
            height_val = float(self.height_entry.get())
            
            if self.settings['units'] == 'in':
                width_mm, height_mm = width_val * 25.4, height_val * 25.4
            elif self.settings['units'] == 'cm':
                width_mm, height_mm = width_val * 10, height_val * 10
            elif self.settings['units'] == 'mm':
                width_mm, height_mm = width_val, height_val
            else:
                messagebox.showerror("Error", f"Unknown unit '{self.settings['units']}' in settings.")
                return


            base = self.filename_entry.get().strip()
            if not base:
                messagebox.showerror("Error", "Please enter a base filename.")
                return
            
            for material, var in self.material_vars.items():
                if var.get() and not can_all_pads_fit(pads, material, width_mm, height_mm, self.settings):
                    messagebox.showerror("Nesting Error", f"Could not fit all '{material.replace('_',' ')}' pieces on the specified sheet size.")
                    return

            save_dir = filedialog.askdirectory(title="Select Folder to Save SVGs", initialdir=self.settings.get("last_output_dir", ""))
            if not save_dir:
                return
            
            self.settings["last_output_dir"] = save_dir 

            files_generated = False
            for material, var in self.material_vars.items():
                if var.get():
                    filename = os.path.join(save_dir, f"{base}_{material}.svg")
                    generate_svg(pads, material, width_mm, height_mm, filename, hole_dia, self.settings)
                    files_generated = True
            
            if files_generated:
                self.save_settings() 
                messagebox.showinfo("Done", "SVGs generated successfully.")
            else:
                messagebox.showwarning("No Materials Selected", "Please select at least one material.")

        except Exception as e:
            print(f"An error occurred during SVG generation: {e}")
            messagebox.showerror("An Error Occurred", f"Something went wrong during generation:\n\n{e}")

    def parse_pad_list(self, pad_input):
        pad_list = []
        for line in pad_input.strip().splitlines():
            try:
                size, qty = map(float, line.strip().lower().split('x'))
                pad_list.append({'size': size, 'qty': int(qty)})
            except ValueError:
                continue
        return pad_list

    def load_presets(self, file_path, preset_type_name="Preset", is_flat=False): # is_flat is for pad presets
        data = {}
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                if not isinstance(data, dict):
                    data = {}
            except (json.JSONDecodeError, TypeError):
                data = {}
        
        # Check for migration
        if data and not any(isinstance(v, dict) for v in data.values()):
            # This is an OLD flat file. Migrate it.
            print(f"Migrating old {preset_type_name} file...")
            new_data = {"My Presets": data}
            if self.save_presets(new_data, file_path): # Save the migrated data
                messagebox.showinfo("Library Updated", f"Your existing {preset_type_name} sets have been moved into a new library called 'My Presets'.")
                return new_data
            else:
                return {"My Presets": {}} # Failed to migrate, return default
        
        return data if data else {"My Presets": {}}


    def save_presets(self, presets, file_path):
        try:
            with open(file_path, 'w') as f:
                json.dump(presets, f, indent=2)
            return True
        except Exception as e:
            messagebox.showerror("Error Saving Preset", str(e))
            return False

    def refresh_preset_menu(self, menu_widget, presets, preset_type_name="Preset"):
        menu_widget['values'] = list(presets.keys())
        menu_widget.set(f"Load {preset_type_name}")

    def on_save_preset(self, presets, file_path, entry_widget, menu_widget, preset_type_name, library_var):
        active_library = library_var.get()
        if not active_library or active_library == "All Libraries":
            messagebox.showwarning("Save Error", "Please select a specific library to save to.")
            return

        name = simpledialog.askstring(f"Save {preset_type_name} Preset", "Enter a name for this preset:")
        if name:
            text_data = entry_widget.get("1.0", tk.END)
            if not text_data.strip():
                messagebox.showwarning(f"Save {preset_type_name} Preset", "Cannot save an empty list.")
                return
            
            if active_library not in presets:
                presets[active_library] = {}

            if name in presets[active_library]:
                if not messagebox.askyesno("Overwrite", f"A set named '{name}' already exists in this library. Overwrite it?"):
                    return
            
            presets[active_library][name] = text_data
            if self.save_presets(presets, file_path):
                if preset_type_name == "Pad":
                    self.on_pad_library_selected()
                else:
                    self.on_key_library_selected()
                messagebox.showinfo("Preset Saved", f"Preset '{name}' saved successfully.")

    def on_load_preset(self, selected_name, presets, entry_widget, library_var, load_label):
        if not selected_name or selected_name == load_label:
            return
            
        lib_name = library_var.get()
        data = None
        
        if lib_name == "All Libraries":
            try:
                lib_name, preset_name = selected_name.split("] ", 1)
                lib_name = lib_name[1:] # Remove starting '['
                if lib_name in presets and preset_name in presets[lib_name]:
                    data = presets[lib_name][preset_name]
            except ValueError:
                return # Malformed name
        else:
            # We are in a specific library
            if lib_name in presets and selected_name in presets[lib_name]:
                data = presets[lib_name][selected_name]

        if data:
            entry_widget.delete("1.0", tk.END)
            entry_widget.insert(tk.END, data)

    def on_delete_preset(self, presets, file_path, preset_var, menu_widget, entry_widget, preset_type_name, library_var, library_refresh_func):
        selected_lib = library_var.get()
        selected_preset = preset_var.get()

        if not selected_preset or selected_preset.startswith("Load"):
            messagebox.showwarning("Delete Error", "Please load a set to delete.")
            return

        if selected_lib == "All Libraries":
            try:
                selected_lib, selected_preset = selected_preset.split("] ", 1)
                selected_lib = selected_lib[1:]
            except ValueError:
                messagebox.showerror("Delete Error", "Cannot delete from 'All Libraries' view. Please select the specific library first.")
                return
        
        if messagebox.askyesno(f"Delete {preset_type_name} Preset", f"Are you sure you want to delete the preset '{selected_preset}' from the '{selected_lib}' library?"):
            if selected_lib in presets and selected_preset in presets[selected_lib]:
                del presets[selected_lib][selected_preset]
                if self.save_presets(presets, file_path):
                    library_refresh_func() # Refresh preset list
                    if isinstance(entry_widget, tk.Text):
                        entry_widget.delete("1.0", tk.END)
                    messagebox.showinfo("Preset Deleted", f"Preset '{selected_preset}' deleted.")
            else:
                messagebox.showerror("Delete Error", "Could not find the preset to delete.")
    
    # --- Wrappers for new preset system ---
    def on_save_pad_preset(self):
        self.on_save_preset(self.pad_presets, PAD_PRESET_FILE, self.pad_entry, self.pad_preset_menu, "Pad", self.pad_library_var)
        
    def on_delete_pad_preset(self):
        self.on_delete_preset(self.pad_presets, PAD_PRESET_FILE, self.pad_preset_var, self.pad_preset_menu, self.pad_entry, "Pad", self.pad_library_var, self.on_pad_library_selected)
    
    def on_load_pad_preset(self, selected_name):
        self.on_load_preset(selected_name, self.pad_presets, self.pad_entry, self.pad_library_var, "Load Pad Preset")
        
# ... (rest of the classes) ...

class OptionsWindow:
    def __init__(self, parent, app, settings, update_callback, save_callback):
        self.app = app
        self.settings = settings
        self.update_callback = update_callback
        self.save_callback = save_callback
        
        self.top = tk.Toplevel(parent)
        self.top.title("Sizing Rules")
        self.top.geometry("500x700") 
        self.top.configure(bg="#F0EAD6")
        self.top.transient(parent)
        self.top.grab_set()

        # --- Main Layout Frames ---
        bottom_button_frame = tk.Frame(self.top, bg="#F0EAD6")
        bottom_button_frame.pack(side="bottom", fill="x", pady=10, padx=10)
        
        tk.Button(bottom_button_frame, text="Save", command=self.save_options).pack(side="left", padx=5)
        tk.Button(bottom_button_frame, text="Cancel", command=self.top.destroy).pack(side="left", padx=5)
        
        tk.Button(bottom_button_frame, text="Advanced", command=self.app.open_resonance_window).pack(side="right", padx=5)
        tk.Button(bottom_button_frame, text="Revert to Defaults", command=self.revert_to_defaults).pack(side="right", padx=5)
        
        main_canvas_frame = tk.Frame(self.top)
        main_canvas_frame.pack(side="top", fill="both", expand=True)

        self.canvas = tk.Canvas(main_canvas_frame, bg="#F0EAD6", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(main_canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#F0EAD6", padx=10, pady=10)

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        self.top.bind('<MouseWheel>', self._on_mousewheel)

        # --- Sizing variables ---
        self.unit_var = tk.StringVar(value=self.settings["units"])
        self.felt_offset_var = tk.DoubleVar(value=self.settings["felt_offset"])
        self.card_offset_var = tk.DoubleVar(value=self.settings["card_to_felt_offset"])
        self.leather_mult_var = tk.DoubleVar(value=self.settings["leather_wrap_multiplier"])
        self.min_hole_size_var = tk.DoubleVar(value=self.settings["min_hole_size"])
        self.felt_thickness_var = tk.DoubleVar(value=self.settings["felt_thickness"])
        self.felt_thickness_unit_var = tk.StringVar(value=self.settings["felt_thickness_unit"])
        
        # --- Engraving variables ---
        self.engraving_on_var = tk.BooleanVar(value=self.settings["engraving_on"])
        self.compatibility_mode_var = tk.BooleanVar(value=self.settings.get("compatibility_mode", False))
        self.engraving_font_size_vars = {}
        self.engraving_loc_vars = {}
        
        self.create_option_widgets()
    
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def create_option_widgets(self):
        main_frame = self.scrollable_frame
        
        unit_frame = tk.LabelFrame(main_frame, text="Sheet Units", bg="#F0EAD6", padx=5, pady=5)
        unit_frame.pack(fill="x", pady=5)
        tk.Radiobutton(unit_frame, text="Inches (in)", variable=self.unit_var, value="in", bg="#F0EAD6").pack(side="left", padx=5)
        tk.Radiobutton(unit_frame, text="Centimeters (cm)", variable=self.unit_var, value="cm", bg="#F0EAD6").pack(side="left", padx=5)
        tk.Radiobutton(unit_frame, text="Millimeters (mm)", variable=self.unit_var, value="mm", bg="#F0EAD6").pack(side="left", padx=5)

        rules_frame = tk.LabelFrame(main_frame, text="Sizing Rules (Advanced)", bg="#F0EAD6", padx=5, pady=5)
        rules_frame.pack(fill="x", pady=5)
        rules_frame.columnconfigure(1, weight=1)

        tk.Label(rules_frame, text="Felt Diameter Reduction (mm):", bg="#F0EAD6").grid(row=0, column=0, sticky='w', pady=2)
        tk.Entry(rules_frame, textvariable=self.felt_offset_var, width=10).grid(row=0, column=1, sticky='w', pady=2)

        tk.Label(rules_frame, text="Card Additional Reduction (mm):", bg="#F0EAD6").grid(row=1, column=0, sticky='w', pady=2)
        tk.Entry(rules_frame, textvariable=self.card_offset_var, width=10).grid(row=1, column=1, sticky='w', pady=2)

        tk.Label(rules_frame, text="Leather Wrap Multiplier (1.00=default):", bg="#F0EAD6").grid(row=2, column=0, sticky='w', pady=2)
        tk.Entry(rules_frame, textvariable=self.leather_mult_var, width=10).grid(row=2, column=1, sticky='w', pady=2)

        tk.Label(rules_frame, text="Min. Pad Size for Hole (mm):", bg="#F0EAD6").grid(row=3, column=0, sticky='w', pady=2)
        tk.Entry(rules_frame, textvariable=self.min_hole_size_var, width=10).grid(row=3, column=1, sticky='w', pady=2)
        
        felt_thickness_frame = tk.Frame(rules_frame, bg="#F0EAD6")
        felt_thickness_frame.grid(row=4, column=0, columnspan=2, sticky='w', pady=2)
        tk.Label(felt_thickness_frame, text="Felt Thickness:", bg="#F0EAD6").pack(side="left")
        tk.Entry(felt_thickness_frame, textvariable=self.felt_thickness_var, width=10).pack(side="left", padx=5)
        tk.Radiobutton(felt_thickness_frame, text="in", variable=self.felt_thickness_unit_var, value="in", bg="#F0EAD6").pack(side="left")
        tk.Radiobutton(felt_thickness_frame, text="mm", variable=self.felt_thickness_unit_var, value="mm", bg="#F0EAD6").pack(side="left")

        engraving_frame = tk.LabelFrame(main_frame, text="Engraving Settings", bg="#F0EAD6", padx=5, pady=5)
        engraving_frame.pack(fill="x", pady=5)
        
        tk.Checkbutton(engraving_frame, text="Show Size Label (Engraving)", variable=self.engraving_on_var, bg="#F0EAD6").pack(anchor='w')

        font_size_frame = tk.LabelFrame(engraving_frame, text="Font Sizes (mm)", bg="#F0EAD6", padx=5, pady=5)
        font_size_frame.pack(fill='x', pady=5)
        
        materials = ['felt', 'card', 'leather', 'exact_size']
        for i, material in enumerate(materials):
            tk.Label(font_size_frame, text=f"{material.replace('_', ' ').capitalize()}:", bg="#F0EAD6").grid(row=i, column=0, sticky='w', padx=5, pady=2)
            font_size_var = tk.DoubleVar(value=self.settings["engraving_font_size"].get(material, 2.0))
            self.engraving_font_size_vars[material] = font_size_var
            tk.Entry(font_size_frame, textvariable=font_size_var, width=8).grid(row=i, column=1, sticky='w', padx=5, pady=2)


        engraving_loc_frame = tk.LabelFrame(main_frame, text="Engraving Placement", bg="#F0EAD6", padx=5, pady=5)
        engraving_loc_frame.pack(fill="x", pady=5)
        
        for material in materials:
            frame = tk.Frame(engraving_loc_frame, bg="#F0EAD6")
            frame.pack(fill='x', pady=2)
            tk.Label(frame, text=material.replace('_', ' ').capitalize() + ":", bg="#F0EAD6", width=10, anchor='w').pack(side="left")

            mode_var = tk.StringVar(value=self.settings["engraving_location"][material]['mode'])
            val_var = tk.DoubleVar(value=self.settings["engraving_location"][material]['value'])
            self.engraving_loc_vars[material] = {'mode': mode_var, 'value': val_var}

            tk.Radiobutton(frame, text="from outside", variable=mode_var, value="from_outside", bg="#F0EAD6").pack(side="left")
            tk.Radiobutton(frame, text="from inside", variable=mode_var, value="from_inside", bg="#F0EAD6").pack(side="left")
            tk.Radiobutton(frame, text="centered", variable=mode_var, value="centered", bg="#F0EAD6").pack(side="left")
            
            tk.Entry(frame, textvariable=val_var, width=6).pack(side="left", padx=5)
            tk.Label(frame, text="mm", bg="#F0EAD6").pack(side="left")
            
        export_frame = tk.LabelFrame(main_frame, text="Export Settings", bg="#F0EAD6", padx=5, pady=5)
        export_frame.pack(fill="x", pady=5)
        tk.Checkbutton(export_frame, text="Enable Inkscape/Compatibility Mode (unitless SVG)", variable=self.compatibility_mode_var, bg="#F0EAD6").pack(anchor='w')


    def save_options(self):
        # Sizing
        self.settings["units"] = self.unit_var.get()
        self.settings["felt_offset"] = self.felt_offset_var.get()
        self.settings["card_to_felt_offset"] = self.card_offset_var.get()
        self.settings["leather_wrap_multiplier"] = self.leather_mult_var.get()
        self.settings["min_hole_size"] = self.min_hole_size_var.get()
        self.settings["felt_thickness"] = self.felt_thickness_var.get()
        self.settings["felt_thickness_unit"] = self.felt_thickness_unit_var.get()
        
        # Engraving
        self.settings["engraving_on"] = self.engraving_on_var.get()
        for material, var in self.engraving_font_size_vars.items():
            self.settings["engraving_font_size"][material] = var.get()

        for material, vars in self.engraving_loc_vars.items():
            self.settings["engraving_location"][material]['mode'] = vars['mode'].get()
            self.settings["engraving_location"][material]['value'] = vars['value'].get()
            
        # Export
        self.settings["compatibility_mode"] = self.compatibility_mode_var.get()
        
        self.save_callback()
        self.update_callback()
        self.top.destroy()

    def revert_to_defaults(self):
        if messagebox.askyesno("Revert to Defaults", "Are you sure you want to revert all settings to their original defaults?"):
            # Sizing
            self.unit_var.set(DEFAULT_SETTINGS["units"])
            self.felt_offset_var.set(DEFAULT_SETTINGS["felt_offset"])
            self.card_offset_var.set(DEFAULT_SETTINGS["card_to_felt_offset"])
            self.leather_mult_var.set(DEFAULT_SETTINGS["leather_wrap_multiplier"])
            self.min_hole_size_var.set(DEFAULT_SETTINGS["min_hole_size"])
            self.felt_thickness_var.set(DEFAULT_SETTINGS["felt_thickness"])
            self.felt_thickness_unit_var.set(DEFAULT_SETTINGS["felt_thickness_unit"])
            
            # Engraving
            self.engraving_on_var.set(DEFAULT_SETTINGS["engraving_on"])
            for material, var in self.engraving_font_size_vars.items():
                 var.set(DEFAULT_SETTINGS["engraving_font_size"][material])
            
            for material, vars in self.engraving_loc_vars.items():
                 vars['mode'].set(DEFAULT_SETTINGS["engraving_location"][material]['mode'])
                 vars['value'].set(DEFAULT_SETTINGS["engraving_location"][material]['value'])
                 
            # Export
            self.compatibility_mode_var.set(DEFAULT_SETTINGS.get("compatibility_mode", False))


class LayerColorWindow:
    def __init__(self, parent, settings, save_callback):
        self.settings = settings
        self.save_callback = save_callback
        
        self.top = tk.Toplevel(parent)
        self.top.title("Layer Color Mapping")
        self.top.geometry("450x420")
        self.top.configure(bg="#F0EAD6")
        self.top.transient(parent)
        self.top.grab_set()

        self.color_map = {name: hex_val for name, hex_val in LIGHTBURN_COLORS}
        color_names = list(self.color_map.keys())
        self.hex_to_name_map = {hex_val: name for name, hex_val in LIGHTBURN_COLORS}

        self.color_vars = {}

        main_frame = tk.Frame(self.top, bg="#F0EAD6", padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)
        main_frame.columnconfigure(1, weight=1)

        layer_map_keys = [
            'felt_outline', 'felt_center_hole', 'felt_engraving',
            'card_outline', 'card_center_hole', 'card_engraving',
            'leather_outline', 'leather_center_hole', 'leather_engraving',
            'exact_size_outline', 'exact_size_center_hole', 'exact_size_engraving'
        ]
        
        for i, key in enumerate(layer_map_keys):
            label_text = key.replace('_', ' ').capitalize() + ":"
            tk.Label(main_frame, text=label_text, bg="#F0EAD6").grid(row=i, column=0, sticky='w', pady=3)
            
            var = tk.StringVar()
            current_hex = self.settings["layer_colors"].get(key, "#000000")
            current_name = self.hex_to_name_map.get(current_hex, color_names[0])
            var.set(current_name)
            
            combo = ttk.Combobox(main_frame, textvariable=var, values=color_names, state="readonly")
            combo.grid(row=i, column=1, sticky='ew', padx=5)
            self.color_vars[key] = var

        button_frame = tk.Frame(self.top, bg="#F0EAD6")
        button_frame.grid(row=len(layer_map_keys), column=0, columnspan=2, pady=20)
        tk.Button(button_frame, text="Save", command=self.save_colors).pack(side="left", padx=10)
        tk.Button(button_frame, text="Cancel", command=self.top.destroy).pack(side="left", padx=10)

    def save_colors(self):
        for key, var in self.color_vars.items():
            selected_name = var.get()
            self.settings["layer_colors"][key] = self.color_map[selected_name]
        
        self.save_callback()
        self.top.destroy()
        
class ResonanceWindow(tk.Toplevel):
    def __init__(self, parent, settings, save_callback, theme_callback):
        super().__init__(parent)
        self.settings = settings
        self.save_callback = save_callback
        self.theme_callback = theme_callback
        self.parent = parent
        
        self.title("Resonance Chamber")
        self.geometry("400x200")
        self.configure(bg="#F0EAD6")
        self.transient(parent)
        self.grab_set()

        main_frame = tk.Frame(self, bg="#F0EAD6")
        main_frame.pack(expand=True)

        res_button = tk.Button(main_frame, text="Add Resonance", command=self.start_resonance, font=("Helvetica", 14, "bold"))
        res_button.pack(pady=20, padx=40, ipadx=10, ipady=10)

    def start_resonance(self):
        self.withdraw()
        ResonanceProgressDialog(self.parent, self.settings, self.save_callback, self.theme_callback)
        self.destroy()

class ResonanceProgressDialog(tk.Toplevel):
    def __init__(self, parent, settings, save_callback, theme_callback):
        super().__init__(parent)
        self.settings = settings
        self.save_callback = save_callback
        self.theme_callback = theme_callback
        self.parent_app = parent
        
        self.title("Optimizing...")
        self.geometry("300x100")
        self.configure(bg="#F0EAD6")
        self.transient(parent)
        self.grab_set()
        
        tk.Label(self, text="Applying resonance...", bg="#F0EAD6").pack(pady=10)
        self.progress = ttk.Progressbar(self, orient="horizontal", length=250, mode="determinate")
        self.progress.pack(pady=5)
        
        self.update_progress(0)

    def update_progress(self, val):
        self.progress['value'] = val
        if val < 100:
            self.after(70, self.update_progress, val + 1)
        else:
            self.after(200, self.finish_resonance)
            
    def finish_resonance(self):
        clicks = self.settings.get("resonance_clicks", 0) + 1
        self.settings["resonance_clicks"] = clicks
        
        if clicks >= 100:
            messagebox.showinfo("Power Overwhelming", "You have become too powerful.")
            self.destroy() # Close this window
            # Start the "uninstall" process
            UninstallResonanceDialog(self.parent_app, self.settings, self.save_callback, self.theme_callback)
        else:
            self.save_callback()
            messagebox.showinfo("Success", random.choice(RESONANCE_MESSAGES))
            self.theme_callback()
            self.destroy()

class UninstallResonanceDialog(tk.Toplevel):
    def __init__(self, parent, settings, save_callback, theme_callback):
        super().__init__(parent)
        self.settings = settings
        self.save_callback = save_callback
        self.theme_callback = theme_callback
        
        self.title("Resetting...")
        self.geometry("300x100")
        self.configure(bg="#F0EAD6")
        self.transient(parent)
        self.grab_set() # This makes the main window unusable

        tk.Label(self, text="Uninstalling resonance...", bg="#F0EAD6").pack(pady=10)
        self.progress = ttk.Progressbar(self, orient="horizontal", length=250, mode="determinate")
        self.progress.pack(pady=5)
        self.update_progress(0)

    def update_progress(self, val):
        self.progress['value'] = val
        if val < 100:
            # 2 seconds total duration
            self.after(20, self.update_progress, val + 1)
        else:
            self.after(200, self.finish_uninstall)

    def finish_uninstall(self):
        self.settings["resonance_clicks"] = 0
        self.save_callback()
        self.theme_callback()
        self.destroy()

class ExportPresetsWindow(tk.Toplevel):
    def __init__(self, parent, presets, title, default_filename, ask_provenance=False):
        super().__init__(parent)
        self.presets = presets # For Pads, this is flat. For Keys, this is nested.
        self.title(title)
        self.default_filename = default_filename
        self.ask_provenance = ask_provenance
        self.geometry("400x500")
        self.configure(bg="#F0EAD6")
        self.transient(parent)
        self.grab_set()

        self.vars = {}

        tk.Label(self, text="Select sets to export:", bg="#F0EAD6", font=("Helvetica", 12)).pack(pady=10)

        button_frame = tk.Frame(self, bg="#F0EAD6")
        button_frame.pack(pady=5)
        tk.Button(button_frame, text="Select All", command=self.select_all).pack(side="left", padx=5)
        tk.Button(button_frame, text="Select None", command=self.select_none).pack(side="left", padx=5)

        list_frame = tk.Frame(self, bg="#F0EAD6")
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.canvas = tk.Canvas(list_frame, bg="#F0EAD6", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#F0EAD6")

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        if not presets:
             tk.Label(self.scrollable_frame, text="No local sets found.", bg="#F0EAD6").pack(pady=10)
        else:
            # Check if this is a nested dictionary (Key Libraries)
            if any(isinstance(v, dict) for v in presets.values()):
                for lib_name in sorted(self.presets.keys()):
                    tk.Label(self.scrollable_frame, text=f"[{lib_name}]", bg="#F0EAD6", font=("Helvetica", 10, "bold")).pack(anchor='w', pady=(5,0))
                    for preset_name in sorted(self.presets[lib_name].keys()):
                        var = tk.BooleanVar()
                        full_name = f"{lib_name}::{preset_name}" # Internal delimiter
                        cb = tk.Checkbutton(self.scrollable_frame, text=f"  {preset_name}", variable=var, bg="#F0EAD6")
                        cb.pack(anchor='w')
                        self.vars[full_name] = var
            else: # Flat dictionary (Pad Presets) - This is for legacy support, should be nested now
                for name in sorted(self.presets.keys()):
                    var = tk.BooleanVar()
                    cb = tk.Checkbutton(self.scrollable_frame, text=name, variable=var, bg="#F0EAD6")
                    cb.pack(anchor='w')
                    self.vars[name] = var

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.bind('<MouseWheel>', self._on_mousewheel)

        export_button = tk.Button(self, text="Export Selected", command=self.export_selected, font=("Helvetica", 10, "bold"))
        export_button.pack(pady=10)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def select_all(self):
        for var in self.vars.values():
            var.set(True)

    def select_none(self):
        for var in self.vars.values():
            var.set(False)

    def export_selected(self):
        to_export = {}
        selected_count = 0
        last_selected_data = None
        
        is_nested = any("::" in k for k in self.vars.keys())

        for name, var in self.vars.items():
            if var.get():
                if is_nested:
                    lib_name, preset_name = name.split("::", 1)
                    preset_data = self.presets[lib_name][preset_name]
                    to_export[f"[{lib_name}] {preset_name}"] = preset_data
                    selected_count += 1
                    last_selected_data = preset_data
                else:
                    to_export[name] = self.presets[name]
                    selected_count += 1

        
        if not to_export:
            messagebox.showwarning("No Selection", "Please select at least one set to export.")
            return

        initialfile = self.default_filename
        
        if self.ask_provenance:
            user_name = simpledialog.askstring("Provenance", "Enter your name (for filename):")
            if not user_name:
                user_name = "Export" # Default if cancelled
            user_name = user_name.replace(" ", "_")
            
            if selected_count == 1 and last_selected_data:
                try:
                    make = last_selected_data.get("make", "UnknownMake").replace(" ", "_")
                    model = last_selected_data.get("model", "UnknownModel").replace(" ", "_")
                    size = last_selected_data.get("size", "UnknownSize").replace(" ", "_")
                    initialfile = f"{make}_{model}_{size}_{user_name}.json"
                except Exception:
                    initialfile = f"key_height_export_{user_name}.json"
            else:
                initialfile = f"key_height_export_{user_name}.json"

        filepath = filedialog.asksaveasfilename(
            title=f"Save {self.title} As...",
            defaultextension=".json",
            filetypes=(("JSON files", "*.json"), ("All files", "*.*")),
            initialfile=initialfile
        )
        
        if not filepath:
            return

        try:
            with open(filepath, 'w') as f:
                json.dump(to_export, f, indent=2)
            messagebox.showinfo("Export Successful", f"Successfully exported {len(to_export)} sets.")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Export Error", f"Could not export presets:\n{e}")

class ImportPresetsWindow(tk.Toplevel):
    def __init__(self, parent, local_presets_lib, imported_presets, file_path, menu_widget, app_instance, preset_type_name="Preset", save_data=None):
        super().__init__(parent)
        self.parent_app = app_instance
        self.local_presets_lib = local_presets_lib # This is the specific library dict for key heights, or all presets for pads
        self.imported_presets = imported_presets # This is the dict of presets from the file
        self.file_path = file_path
        self.menu_widget = menu_widget
        self.preset_type_name = preset_type_name
        # This is the *entire* preset object (e.g., self.key_presets, which is a dict of dicts) for saving
        self.save_data = save_data if save_data is not None else local_presets_lib
        
        self.title(f"Import {preset_type_name}s")
        self.geometry("450x500")
        self.configure(bg="#F0EAD6")
        self.transient(parent)
        self.grab_set()

        self.vars = {}

        tk.Label(self, text=f"Select {preset_type_name}s to import:", bg="#F0EAD6", font=("Helvetica", 12)).pack(pady=10)

        button_frame = tk.Frame(self, bg="#F0EAD6")
        button_frame.pack(pady=5)
        tk.Button(button_frame, text="Select All", command=self.select_all).pack(side="left", padx=5)
        tk.Button(button_frame, text="Select None", command=self.select_none).pack(side="left", padx=5)

        list_frame = tk.Frame(self, bg="#F0EAD6")
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.canvas = tk.Canvas(list_frame, bg="#F0EAD6", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#F0EAD6")

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        if not imported_presets:
             tk.Label(self.scrollable_frame, text="No presets found in file.", bg="#F0EAD6").pack(pady=10)
        else:
            for name in sorted(self.imported_presets.keys()):
                var = tk.BooleanVar(value=True) # Default to selected
                cb = tk.Checkbutton(self.scrollable_frame, text=name, variable=var, bg="#F0EAD6")
                cb.pack(anchor='w')
                self.vars[name] = var

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.bind('<MouseWheel>', self._on_mousewheel)

        import_button = tk.Button(self, text="Import Selected", command=self.import_selected, font=("Helvetica", 10, "bold"))
        import_button.pack(pady=10)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def select_all(self):
        for var in self.vars.values():
            var.set(True)

    def select_none(self):
        for var in self.vars.values():
            var.set(False)

    def import_selected(self):
        added_count = 0
        renamed_count = 0
        
        for name, var in self.vars.items():
            if var.get():
                preset_data = self.imported_presets[name]
                new_name = name
                
                # Handle bracketed library names from key set exports
                if new_name.startswith("[") and "] " in new_name:
                    try:
                        new_name = new_name.split("] ", 1)[1]
                    except Exception:
                        pass # Keep original name if split fails
                
                while new_name in self.local_presets:
                    new_name += "*"
                
                if new_name != name:
                    renamed_count += 1
                
                self.local_presets[new_name] = preset_data
                added_count += 1
        
        if added_count > 0:
            if self.parent_app.save_presets(self.save_data, self.file_path):
                # Special refresh for key height library
                if self.preset_type_name == "Key Height Set":
                    self.parent_app.update_key_library_dropdown()
                else:
                    self.parent_app.update_pad_library_dropdown()
                
                messagebox.showinfo("Import Successful", 
                                  f"Import complete.\n\n"
                                  f"Added: {added_count} presets\n"
                                  f"Renamed due to conflicts: {renamed_count} presets")
            else:
                messagebox.showerror("Import Error", "Could not save new presets to file.")
        else:
            messagebox.showinfo("Import Complete", "No new presets were imported.")
            
        self.destroy()

class ImportTargetWindow(tk.Toplevel):
    def __init__(self, parent, existing_libraries):
        super().__init__(parent)
        self.parent = parent
        self.existing_libraries = existing_libraries
        self.target_library = None

        self.title("Select Import Library")
        self.geometry("350x150")
        self.configure(bg="#F0EAD6")
        self.transient(parent)
        self.grab_set()

        self.mode = tk.StringVar(value="existing")
        
        tk.Label(self, text="Where do you want to add these sets?", bg="#F0EAD6").pack(pady=10)

        existing_frame = tk.Frame(self, bg="#F0EAD6")
        existing_frame.pack(fill='x', padx=10)
        tk.Radiobutton(existing_frame, text="Add to existing library:", variable=self.mode, value="existing", bg="#F0EAD6", command=self.toggle_widgets).pack(side="left")
        self.library_dropdown = ttk.Combobox(existing_frame, values=self.existing_libraries, state="readonly", width=15)
        self.library_dropdown.pack(side="left", padx=5)
        if self.existing_libraries:
            self.library_dropdown.set(self.existing_libraries[0])

        new_frame = tk.Frame(self, bg="#F0EAD6")
        new_frame.pack(fill='x', padx=10, pady=5)
        tk.Radiobutton(new_frame, text="Create new library:", variable=self.mode, value="new", bg="#F0EAD6", command=self.toggle_widgets).pack(side="left")
        self.new_lib_entry = tk.Entry(new_frame, width=18)
        self.new_lib_entry.pack(side="left", padx=5)
        
        button_frame = tk.Frame(self, bg="#F0EAD6")
        button_frame.pack(pady=15)
        tk.Button(button_frame, text="Import", command=self.on_import).pack(side="left", padx=10)
        tk.Button(button_frame, text="Cancel", command=self.on_cancel).pack(side="left", padx=10)
        
        self.toggle_widgets()
        self.wait_window(self)

    def toggle_widgets(self):
        if self.mode.get() == "existing":
            self.library_dropdown.config(state="readonly")
            self.new_lib_entry.config(state="disabled")
        else: # "new"
            self.library_dropdown.config(state="disabled")
            self.new_lib_entry.config(state="normal")
            
    def on_import(self):
        if self.mode.get() == "existing":
            self.target_library = self.library_dropdown.get()
            if not self.target_library:
                messagebox.showwarning("No Library", "Please select a library.", parent=self)
                return
        else: # "new"
            self.target_library = self.new_lib_entry.get().strip()
            if not self.target_library:
                messagebox.showwarning("No Name", "Please enter a name for the new library.", parent=self)
                return
        
        self.destroy()
        
    def on_cancel(self):
        self.target_library = None
        self.destroy()

    def get_target_library(self):
        return self.target_library

# --- Core SVG Generation Logic ---
def get_disc_diameter(pad_size, material, settings):
    if material == 'felt': return pad_size - settings["felt_offset"]
    if material == 'card': return pad_size - (settings["felt_offset"] + settings["card_to_felt_offset"])
    if material == 'leather':
        wrap = leather_back_wrap(pad_size, settings["leather_wrap_multiplier"])
        felt_thickness_mm = get_felt_thickness_mm(settings)
        diameter = pad_size + 2 * (felt_thickness_mm + wrap)
        return round(diameter * 2) / 2
    if material == 'exact_size': return pad_size
    return 0

def check_for_oversized_engravings(pads, material_vars, settings):
    oversized = {}
    for material, var in material_vars.items():
        if not var.get(): continue
        
        font_size = settings["engraving_font_size"].get(material, 2.0)
        oversized_sizes = set()

        for pad in pads:
            pad_size = pad['size']
            diameter = get_disc_diameter(pad_size, material, settings)
            radius = diameter / 2
            if font_size >= radius * 0.8:
                oversized_sizes.add(pad_size)
        
        if oversized_sizes:
            oversized[material] = oversized_sizes
    return oversized


def leather_back_wrap(pad_size, multiplier):
    base_wrap = 0
    if pad_size >= 45:
        base_wrap = 3.2
    elif pad_size >= 12:
        base_wrap = 1.2 + (pad_size - 12) * (2.0 / 33.0)
    elif pad_size >= 6:
        base_wrap = 1.0 + (pad_size - 6) * (0.2 / 6.0)
    else:
        base_wrap = 1.0
    return base_wrap * multiplier

def should_have_center_hole(pad_size, hole_dia, settings):
    min_size = settings.get("min_hole_size", 16.5)
    return hole_dia > 0 and pad_size >= min_size

def get_felt_thickness_mm(settings):
    thickness = settings.get("felt_thickness", 3.175)
    if settings.get("felt_thickness_unit") == "in":
        return thickness * 25.4
    return thickness

def can_all_pads_fit(pads, material, width_mm, height_mm, settings):
    spacing_mm = 1.0
    discs = []
    
    for pad in pads:
        pad_size, qty = pad['size'], pad['qty']
        diameter = get_disc_diameter(pad_size, material, settings)
        for _ in range(qty): discs.append((pad_size, diameter))

    discs.sort(key=lambda x: -x[1])
    placed = []
    for _, dia in discs:
        r = dia / 2
        placed_successfully = False
        y = spacing_mm
        while y + dia + spacing_mm <= height_mm and not placed_successfully:
            x = spacing_mm
            while x + dia + spacing_mm <= width_mm:
                cx, cy = x + r, y + r
                is_collision = any((cx - px)**2 + (cy - py)**2 < (r + pr + spacing_mm)**2 for _, px, py, pr in placed)
                if not is_collision:
                    placed.append((None, cx, cy, r))
                    placed_successfully = True
                    break
                x += 1
            y += 1
    
    return len(placed) == len(discs)

def generate_svg(pads, material, width_mm, height_mm, filename, hole_dia_preset, settings):
    spacing_mm = 1.0
    discs = []

    for pad in pads:
        pad_size, qty = pad['size'], pad['qty']
        diameter = get_disc_diameter(pad_size, material, settings)
        for _ in range(qty): discs.append((pad_size, diameter))

    discs.sort(key=lambda x: -x[1])
    placed = []
    for pad_size, dia in discs:
        r = dia / 2
        placed_successfully = False
        y = spacing_mm
        while y + dia + spacing_mm <= height_mm and not placed_successfully:
            x = spacing_mm
            while x + dia + spacing_mm <= width_mm:
                cx, cy = x + r, y + r
                is_collision = any((cx - px)**2 + (cy - py)**2 < (r + pr + spacing_mm)**2 for _, px, py, pr in placed)
                if not is_collision:
                    placed.append((pad_size, cx, cy, r))
                    placed_successfully = True
                    break
                x += 1
            y += 1

    compatibility_mode = settings.get("compatibility_mode", False)
    
    if compatibility_mode:
        dwg = svgwrite.Drawing(filename, size=(f"{width_mm}mm", f"{height_mm}mm"), viewBox=f"0 0 {width_mm} {height_mm}")
        stroke_w = 0.1
    else:
        dwg = svgwrite.Drawing(filename, size=(f"{width_mm}mm", f"{height_mm}mm"), profile='tiny')
        stroke_w = '0.1mm'

    layer_colors = settings.get("layer_colors", DEFAULT_SETTINGS["layer_colors"])

    for pad_size, cx, cy, r in placed:
        
        # --- Check if darts are active for this pad ---
        # ALL DARTING LOGIC REMOVED
        darts_active = False

        # --- Draw Circle (Outline) ---
        if compatibility_mode:
            dwg.add(dwg.circle(center=(cx, cy), r=r, stroke=layer_colors[f'{material}_outline'], fill='none', stroke_width=stroke_w))
        else:
            dwg.add(dwg.circle(center=(f"{cx}mm", f"{cy}mm"), r=f"{r}mm", stroke=layer_colors[f'{material}_outline'], fill='none', stroke_width=stroke_w))

        hole_dia = 0
        if should_have_center_hole(pad_size, hole_dia_preset, settings):
            hole_dia = hole_dia_preset

        # --- Draw Center Hole ---
        if hole_dia > 0:
            if compatibility_mode:
                dwg.add(dwg.circle(center=(cx, cy), r=hole_dia / 2, stroke=layer_colors[f'{material}_center_hole'], fill='none', stroke_width=stroke_w))
            else:
                dwg.add(dwg.circle(center=(f"{cx}mm", f"{cy}mm"), r=f"{hole_dia / 2}mm", stroke=layer_colors[f'{material}_center_hole'], fill='none', stroke_width=stroke_w))

        font_size = settings.get("engraving_font_size", {}).get(material, 2.0)
        
        # --- Draw Engraving Text ---
        if settings.get("engraving_on", True) and (font_size < r * 0.8): # Dart check removed
            engraving_settings = settings["engraving_location"][material]
            mode = engraving_settings['mode']
            value = engraving_settings['value']
            
            engraving_y = 0
            if mode == 'from_outside':
                engraving_y = cy - (r - value)
            elif mode == 'from_inside':
                hole_r = hole_dia / 2 if hole_dia > 0 else 0
                engraving_y = cy - (hole_r + value)
            else: # centered
                hole_r = hole_dia / 2 if hole_dia > 0 else 1.75
                offset_from_center = (r + hole_r) / 2
                engraving_y = cy - offset_from_center

            vertical_adjust = font_size * 0.35
            text_content = f"{pad_size:.1f}".rstrip('0').rstrip('.')
            
            if compatibility_mode:
                dwg.add(dwg.text(text_content,
                                 insert=(cx, engraving_y + vertical_adjust),
                                 text_anchor="middle",
                                 font_size=font_size,
                                 fill=layer_colors[f'{material}_engraving']))
            else:
                dwg.add(dwg.text(text_content,
                                 insert=(f"{cx}mm", f"{engraving_y + vertical_adjust}mm"),
                                 text_anchor="middle",
                                 font_size=f"{font_size}mm",
                                 fill=layer_colors[f'{material}_engraving']))
        
        # --- Draw Darts (if applicable) ---
        # ALL DARTING LOGIC REMOVED

    dwg.save()

if __name__ == '__main__':
    root = tk.Tk()
    app = PadSVGGeneratorApp(root)
    root.mainloop()
