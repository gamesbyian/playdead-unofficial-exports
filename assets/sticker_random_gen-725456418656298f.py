from __future__ import annotations

import os
import random
import subprocess
import sys
import threading
from collections import Counter
from pathlib import Path

if sys.version_info < (3, 8) or sys.version_info >= (3, 17):
    sys.exit('Python 3.8 to 3.16 required.')

try:
    from PIL import Image
except ImportError:
    in_venv = (getattr(sys, 'base_prefix', sys.prefix) != sys.prefix)
    cmd = [sys.executable, '-m', 'pip', 'install', '--quiet', 'pillow']
    if not in_venv:
        cmd.append('--user')
    subprocess.check_call(cmd)
    from PIL import Image

import tkinter as tk
from tkinter import ttk, filedialog, messagebox


KNOWN = {
      0: 'G',   2: 'G',   3: 'R',   4: 'R',   5: 'G',   7: 'G',
      9: 'G',  10: 'R',  12: 'R',  14: 'R',  15: 'G',  17: 'G',
     18: 'R',  19: 'R',  20: 'G',  21: 'R',  23: 'R',  24: 'R',
     26: 'R',  29: 'G',  30: 'G',  31: 'R',  32: 'G',  36: 'G',
     37: 'R',  38: 'G',  39: 'G',  40: 'G',  42: 'G',  43: 'G',
     44: 'R',  46: 'G',  47: 'G',  48: 'G',  51: 'R',  53: 'R',
     56: 'G',  57: 'R',  59: 'G',  60: 'G',  63: 'G',  65: 'G',
     66: 'G',  69: 'G',  70: 'R',  71: 'R',  72: 'R',  74: 'R',
     75: 'R',  76: 'G',  78: 'G',  79: 'G',  80: 'G',  81: 'G',
     85: 'Y',  86: 'G',  89: 'Y',  90: 'Y',  92: 'Y',  95: 'Y',
     96: 'G',  97: 'Y',  98: 'Y', 101: 'G',
}
LAYOUTS = {'9x12': (12, 9), '12x9': (9, 12), '6x18': (18, 6),
           '18x6': (6, 18), '4x27': (27, 4), '27x4': (4, 27)}
CMAP = {'G': (160, 160, 160), 'R': (220, 30, 30),
        'Y': (240, 220, 30), 'K': (0, 0, 0)}
CMAP_HEX = {k: '#{:02x}{:02x}{:02x}'.format(*v) for k, v in CMAP.items()}
PERIODS = [54, 36, 27, 18, 12, 9, 6, 4]

PRED_ZONED = {
      0: ('G', 1.000),   1: ('R', 0.755),   2: ('G', 1.000),   3: ('R', 1.000),   4: ('R', 1.000),   5: ('G', 1.000),
      6: ('G', 0.831),   7: ('G', 1.000),   8: ('G', 0.524),   9: ('G', 1.000),  10: ('R', 1.000),  11: ('G', 0.844),
     12: ('R', 1.000),  13: ('R', 0.534),  14: ('R', 1.000),  15: ('G', 1.000),  16: ('R', 0.602),  17: ('G', 1.000),
     18: ('R', 1.000),  19: ('R', 1.000),  20: ('G', 1.000),  21: ('R', 1.000),  22: ('G', 0.667),  23: ('R', 1.000),
     24: ('R', 1.000),  25: ('G', 0.716),  26: ('R', 1.000),  27: ('G', 0.775),  28: ('G', 0.509),  29: ('G', 1.000),
     30: ('G', 1.000),  31: ('R', 1.000),  32: ('G', 1.000),  33: ('G', 0.746),  34: ('R', 0.522),  35: ('R', 0.609),
     36: ('G', 1.000),  37: ('R', 1.000),  38: ('G', 1.000),  39: ('G', 1.000),  40: ('G', 1.000),  41: ('G', 0.624),
     42: ('G', 1.000),  43: ('G', 1.000),  44: ('R', 1.000),  45: ('G', 0.622),  46: ('G', 1.000),  47: ('G', 1.000),
     48: ('G', 1.000),  49: ('R', 0.525),  50: ('R', 0.624),  51: ('R', 1.000),  52: ('G', 0.612),  53: ('R', 1.000),
     54: ('G', 0.668),  55: ('R', 0.684),  56: ('G', 1.000),  57: ('R', 1.000),  58: ('R', 0.655),  59: ('G', 1.000),
     60: ('G', 1.000),  61: ('G', 0.758),  62: ('R', 0.624),  63: ('G', 1.000),  64: ('R', 0.682),  65: ('G', 1.000),
     66: ('G', 1.000),  67: ('R', 0.547),  68: ('R', 0.519),  69: ('G', 1.000),  70: ('R', 1.000),  71: ('R', 1.000),
     72: ('R', 1.000),  73: ('R', 0.778),  74: ('R', 1.000),  75: ('R', 1.000),  76: ('G', 1.000),  77: ('R', 0.509),
     78: ('G', 1.000),  79: ('G', 1.000),  80: ('G', 1.000),  81: ('G', 1.000),  82: ('Y', 0.674),  83: ('Y', 0.565),
     84: ('G', 0.636),  85: ('Y', 1.000),  86: ('G', 1.000),  87: ('G', 0.702),  88: ('Y', 0.791),  89: ('Y', 1.000),
     90: ('Y', 1.000),  91: ('Y', 0.917),  92: ('Y', 1.000),  93: ('G', 0.646),  94: ('Y', 0.879),  95: ('Y', 1.000),
     96: ('G', 1.000),  97: ('Y', 1.000),  98: ('Y', 1.000),  99: ('G', 0.681), 100: ('G', 0.539), 101: ('G', 1.000),
    102: ('Y', 0.546), 103: ('Y', 0.854), 104: ('G', 0.536), 105: ('G', 0.862), 106: ('Y', 0.723), 107: ('Y', 0.815),
}

PRED_CROSS = {
      0: ('G', 1.000),   1: ('R', 0.744),   2: ('G', 1.000),   3: ('R', 1.000),   4: ('R', 1.000),   5: ('G', 1.000),
      6: ('G', 0.850),   7: ('G', 1.000),   8: ('G', 0.541),   9: ('G', 1.000),  10: ('R', 1.000),  11: ('G', 0.855),
     12: ('R', 1.000),  13: ('G', 0.560),  14: ('R', 1.000),  15: ('G', 1.000),  16: ('R', 0.620),  17: ('G', 1.000),
     18: ('R', 1.000),  19: ('R', 1.000),  20: ('G', 1.000),  21: ('R', 1.000),  22: ('G', 0.678),  23: ('R', 1.000),
     24: ('R', 1.000),  25: ('G', 0.770),  26: ('R', 1.000),  27: ('G', 0.835),  28: ('G', 0.511),  29: ('G', 1.000),
     30: ('G', 1.000),  31: ('R', 1.000),  32: ('G', 1.000),  33: ('G', 0.775),  34: ('R', 0.530),  35: ('R', 0.609),
     36: ('G', 1.000),  37: ('R', 1.000),  38: ('G', 1.000),  39: ('G', 1.000),  40: ('G', 1.000),  41: ('G', 0.701),
     42: ('G', 1.000),  43: ('G', 1.000),  44: ('R', 1.000),  45: ('G', 0.648),  46: ('G', 1.000),  47: ('G', 1.000),
     48: ('G', 1.000),  49: ('G', 0.571),  50: ('G', 0.503),  51: ('R', 1.000),  52: ('G', 0.609),  53: ('R', 1.000),
     54: ('G', 0.736),  55: ('R', 0.690),  56: ('G', 1.000),  57: ('R', 1.000),  58: ('R', 0.644),  59: ('G', 1.000),
     60: ('G', 1.000),  61: ('G', 0.820),  62: ('R', 0.558),  63: ('G', 1.000),  64: ('R', 0.683),  65: ('G', 1.000),
     66: ('G', 1.000),  67: ('R', 0.518),  68: ('G', 0.535),  69: ('G', 1.000),  70: ('R', 1.000),  71: ('R', 1.000),
     72: ('R', 1.000),  73: ('R', 0.774),  74: ('R', 1.000),  75: ('R', 1.000),  76: ('G', 1.000),  77: ('R', 0.506),
     78: ('G', 1.000),  79: ('G', 1.000),  80: ('G', 1.000),  81: ('G', 1.000),  82: ('G', 0.871),  83: ('G', 0.909),
     84: ('G', 0.939),  85: ('Y', 1.000),  86: ('G', 1.000),  87: ('G', 0.932),  88: ('G', 0.847),  89: ('Y', 1.000),
     90: ('Y', 1.000),  91: ('G', 0.690),  92: ('Y', 1.000),  93: ('G', 0.888),  94: ('G', 0.860),  95: ('Y', 1.000),
     96: ('G', 1.000),  97: ('Y', 1.000),  98: ('Y', 1.000),  99: ('G', 0.953), 100: ('G', 0.980), 101: ('G', 1.000),
    102: ('G', 0.963), 103: ('G', 0.775), 104: ('G', 0.902), 105: ('G', 0.973), 106: ('G', 0.899), 107: ('G', 0.745),
}

HARD_RESIDUES = [8, 13, 28, 34, 49, 67, 68, 77, 100, 102, 104]
HEATMAP_STOPS = [(0.00, (220, 30, 30)), (0.55, (230, 140, 0)),
                 (0.75, (180, 200, 0)), (1.00, (0, 180, 0))]
MAGENTA = (200, 60, 200)
DIM_PRED = (70, 80, 90)
DIM_KNOWN = (40, 40, 40)
KNOWN_HEAT_FILL = (210, 210, 210)

BG_MAIN = '#1a1a24'
BG_SIDE = '#22222e'
BG_CARD = '#2a2a3a'
FG_MAIN = '#d8d8e0'
FG_DIM = '#9090a0'
BORDER_BLUE = '#3a5a8a'
ACCENT_BLUE = '#5a9fd4'
SIDE_INACTIVE_BG = '#2a2a3a'
SIDE_INACTIVE_FG = '#c0c0c8'

TAB_KEYS = ['Known', 'mod54', 'Multi-P', 'Random', 'Bundle',
            'Pred Z', 'Pred X', 'ConfHeat', 'Hard']


def blend_to_white(rgb, conf):
    w = max(0.0, min(1.0, 1.0 - conf))
    r, g, b = rgb
    return (int(r + (255 - r) * w),
            int(g + (255 - g) * w),
            int(b + (255 - b) * w))


def heatmap_rgb(conf):
    if conf <= HEATMAP_STOPS[0][0]:
        return HEATMAP_STOPS[0][1]
    if conf >= HEATMAP_STOPS[-1][0]:
        return HEATMAP_STOPS[-1][1]
    for i in range(len(HEATMAP_STOPS) - 1):
        x0, c0 = HEATMAP_STOPS[i]
        x1, c1 = HEATMAP_STOPS[i + 1]
        if x0 <= conf <= x1:
            t = (conf - x0) / (x1 - x0)
            return (int(c0[0] + (c1[0] - c0[0]) * t),
                    int(c0[1] + (c1[1] - c0[1]) * t),
                    int(c0[2] + (c1[2] - c0[2]) * t))
    return HEATMAP_STOPS[-1][1]


def hex_of(rgb):
    return '#{:02x}{:02x}{:02x}'.format(*rgb)


def chains_for(residue):
    return [residue + 1 + 108 * k for k in range(6)]


def is_top(p):
    return p < 81


def zone_weights():
    tg = sum(1 for p, s in KNOWN.items() if is_top(p) and s == 'G')
    tr = sum(1 for p, s in KNOWN.items() if is_top(p) and s == 'R')
    bg = sum(1 for p, s in KNOWN.items() if not is_top(p) and s == 'G')
    by = sum(1 for p, s in KNOWN.items() if not is_top(p) and s == 'Y')
    return tg / (tg + tr), bg / (bg + by)


def grid_known_only():
    return [KNOWN.get(i, 'K') for i in range(108)]


def predict_mod54():
    pred = dict(KNOWN)
    bucket = {}
    for r, s in KNOWN.items():
        bucket.setdefault(r % 54, Counter())[s] += 1
    for r in range(108):
        if r in KNOWN:
            continue
        b = r % 54
        if b in bucket and bucket[b]:
            top = bucket[b].most_common(1)[0][0]
            if is_top(r) and top == 'Y':
                others = {s: c for s, c in bucket[b].items() if s != 'Y'}
                top = max(others, key=others.get) if others else 'G'
            elif (not is_top(r)) and top == 'R':
                others = {s: c for s, c in bucket[b].items() if s != 'R'}
                top = max(others, key=others.get) if others else 'G'
            pred[r] = top
        else:
            pred[r] = 'G'
    return [pred[i] for i in range(108)]


def predict_multi(min_agree):
    pred = dict(KNOWN)
    for pos in range(108):
        if pos in KNOWN:
            continue
        votes = Counter()
        for N in PERIODS:
            partners = [p for p in range(108) if p != pos and p % N == pos % N]
            colors = [KNOWN[p] for p in partners if p in KNOWN]
            valid = [c for c in colors
                     if not (is_top(pos) and c == 'Y')
                     and not (not is_top(pos) and c == 'R')]
            if not valid:
                continue
            ccount = Counter(valid)
            if len(ccount) == 1:
                votes[next(iter(ccount))] += 1
            else:
                votes[ccount.most_common(1)[0][0]] += 0.5
        if votes:
            color, score = votes.most_common(1)[0]
            if score >= min_agree:
                pred[pos] = color
    return [pred.get(i, 'K') for i in range(108)]


def sample_random(seed):
    rng = random.Random(seed)
    tg, bg = zone_weights()
    out = []
    for i in range(108):
        if i in KNOWN:
            out.append(KNOWN[i])
        elif is_top(i):
            out.append('G' if rng.random() < tg else 'R')
        else:
            out.append('G' if rng.random() < bg else 'Y')
    return out


def render(cells, rows, cols, cell_px, path):
    img = Image.new('RGB', (cols * cell_px, rows * cell_px), (0, 0, 0))
    px = img.load()
    for k in range(108):
        if k >= rows * cols:
            break
        r, c = k // cols, k % cols
        color = CMAP[cells[k]]
        for dy in range(cell_px):
            for dx in range(cell_px):
                px[c * cell_px + dx, r * cell_px + dy] = color
    img.save(path, dpi=(300, 300))


def render_rgb(rgb_cells, rows, cols, cell_px, path):
    img = Image.new('RGB', (cols * cell_px, rows * cell_px), (0, 0, 0))
    px = img.load()
    for k in range(108):
        if k >= rows * cols:
            break
        r, c = k // cols, k % cols
        color = rgb_cells[k]
        for dy in range(cell_px):
            for dx in range(cell_px):
                px[c * cell_px + dx, r * cell_px + dy] = color
    img.save(path, dpi=(300, 300))


def cells_pred_blended(table):
    out = []
    for k in range(108):
        sym, conf = table[k]
        out.append(blend_to_white(CMAP[sym], conf))
    return out


def cells_heatmap():
    out = []
    for k in range(108):
        if k in KNOWN:
            out.append(KNOWN_HEAT_FILL)
            continue
        _, conf = PRED_ZONED[k]
        out.append(heatmap_rgb(conf))
    return out


def cells_hard():
    out = []
    for k in range(108):
        if k in HARD_RESIDUES:
            out.append(MAGENTA)
        elif k in KNOWN:
            out.append(DIM_KNOWN)
        else:
            out.append(DIM_PRED)
    return out


class App:
    def __init__(self, root):
        self.root = root
        root.title('INSIDE sticker variant generator')
        root.geometry('720x900')
        root.resizable(False, False)
        root.configure(bg=BG_MAIN)

        style = ttk.Style()
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass
        style.configure('Card.TLabelframe',
                        background=BG_CARD, foreground=FG_MAIN,
                        bordercolor=BORDER_BLUE, borderwidth=1)
        style.configure('Card.TLabelframe.Label',
                        background=BG_CARD, foreground=ACCENT_BLUE,
                        font=('Segoe UI', 10, 'bold'))
        style.configure('TFrame', background=BG_MAIN)
        style.configure('TLabel', background=BG_MAIN, foreground=FG_MAIN)
        style.configure('Card.TLabel', background=BG_CARD, foreground=FG_MAIN)
        style.configure('TCombobox', fieldbackground=BG_CARD,
                        foreground=FG_MAIN, background=BG_CARD)
        style.configure('TSpinbox', fieldbackground=BG_CARD,
                        foreground=FG_MAIN, background=BG_CARD)
        style.configure('TEntry', fieldbackground=BG_CARD,
                        foreground=FG_MAIN)

        tg, bg = zone_weights()
        n_known = len(KNOWN)
        n_unknown = 108 - n_known

        tk.Label(root, text='INSIDE Sticker Grid: Variant Generator',
                 font=('Segoe UI', 13, 'bold'),
                 bg=BG_MAIN, fg=ACCENT_BLUE
                 ).place(x=12, y=6, width=696, height=24)
        tk.Label(root, font=('Segoe UI', 8), bg=BG_MAIN, fg=FG_DIM,
                 text=('{} known, {} unknown.  '
                       'Top: slash {:.0%} / dash {:.0%}    '
                       'Bottom: slash {:.0%} / dot {:.0%}'
                       ).format(n_known, n_unknown, tg, 1-tg, bg, 1-bg)
                 ).place(x=12, y=32, width=696, height=18)

        common = ttk.LabelFrame(root, text=' Common settings ',
                                style='Card.TLabelframe', padding=6)
        common.place(x=12, y=55, width=696, height=85)
        ttk.Label(common, text='Layout', style='Card.TLabel'
                  ).grid(row=0, column=0, sticky='w', padx=(2, 4), pady=(2, 0))
        self.layout_var = tk.StringVar(value='9x12')
        layout_combo = ttk.Combobox(common, textvariable=self.layout_var,
                                    state='readonly', width=8,
                                    values=list(LAYOUTS))
        layout_combo.grid(row=0, column=1, padx=(0, 14), sticky='w', pady=(2, 0))
        layout_combo.bind('<<ComboboxSelected>>',
                          lambda e: self._update_preview())
        ttk.Label(common, text='Cell size (PNG output)',
                  style='Card.TLabel'
                  ).grid(row=0, column=2, padx=(0, 4), sticky='w', pady=(2, 0))
        self.cell_var = tk.StringVar(value='64')
        ttk.Spinbox(common, from_=16, to=256, increment=16,
                    textvariable=self.cell_var, width=6
                    ).grid(row=0, column=3, sticky='w', pady=(2, 0))
        ttk.Label(common, text='Output folder', style='Card.TLabel'
                  ).grid(row=1, column=0, sticky='w', pady=(6, 0), padx=(2, 4))
        self.out_var = tk.StringVar(value=str(Path.cwd() / 'samples'))
        ttk.Entry(common, textvariable=self.out_var, width=58
                  ).grid(row=1, column=1, columnspan=2, padx=(0, 4),
                         pady=(6, 0), sticky='w')
        ttk.Button(common, text='Browse', command=self._browse
                   ).grid(row=1, column=3, padx=(0, 0), pady=(6, 0), sticky='w')

        main = tk.Frame(root, bg=BG_MAIN)
        main.place(x=12, y=145, width=696, height=720)

        sidebar = tk.Frame(main, bg=BG_SIDE, width=100, height=720)
        sidebar.place(x=0, y=0, width=100, height=720)
        sidebar.pack_propagate(False)

        self.sidebar_buttons = {}
        for key in TAB_KEYS:
            b = tk.Label(sidebar, text=key,
                         bg=SIDE_INACTIVE_BG, fg=SIDE_INACTIVE_FG,
                         font=('Segoe UI', 10, 'bold'),
                         bd=0, padx=4, pady=8, cursor='hand2',
                         anchor='center')
            b.pack(fill='x', padx=4, pady=2)
            b.bind('<Button-1>', lambda e, k=key: self._select_tab(k))
            self.sidebar_buttons[key] = b

        content = tk.Frame(main, bg=BG_MAIN)
        content.place(x=104, y=0, width=592, height=720)

        controls_host = tk.Frame(content, bg=BG_MAIN)
        controls_host.place(x=0, y=0, width=592, height=180)
        controls_host.grid_rowconfigure(0, weight=1)
        controls_host.grid_columnconfigure(0, weight=1)

        self.tab_frames = {}
        for key in TAB_KEYS:
            f = tk.Frame(controls_host, bg=BG_MAIN)
            f.grid(row=0, column=0, sticky='nsew')
            self.tab_frames[key] = f

        self._build_tab_known(self.tab_frames['Known'])
        self._build_tab_mod54(self.tab_frames['mod54'])
        self._build_tab_multi(self.tab_frames['Multi-P'])
        self._build_tab_random(self.tab_frames['Random'])
        self._build_tab_compare(self.tab_frames['Bundle'])
        self._build_tab_pred_zoned(self.tab_frames['Pred Z'])
        self._build_tab_pred_cross(self.tab_frames['Pred X'])
        self._build_tab_heatmap(self.tab_frames['ConfHeat'])
        self._build_tab_hard(self.tab_frames['Hard'])

        preview_frame = ttk.LabelFrame(content, text=' Live preview ',
                                       style='Card.TLabelframe', padding=4)
        preview_frame.place(x=0, y=185, width=592, height=535)

        pv_top = tk.Frame(preview_frame, bg=BG_CARD)
        pv_top.pack(fill='x')
        self.preview_canvas = tk.Canvas(pv_top, width=580, height=470,
                                        bg='#000000', highlightthickness=0)
        self.preview_canvas.pack()
        self.preview = self.preview_canvas

        pv_strip = tk.Frame(preview_frame, bg=BG_CARD)
        pv_strip.pack(fill='x', pady=(4, 0))
        self.preview_stats = tk.StringVar(value='')
        tk.Label(pv_strip, textvariable=self.preview_stats,
                 font=('Segoe UI', 8), bg=BG_CARD,
                 fg='#c8c8d0', justify='left'
                 ).pack(side='left', padx=(2, 10))
        for color, name in [('G', 'slash'), ('R', 'dash'),
                            ('Y', 'dot'), ('K', 'unk')]:
            tk.Canvas(pv_strip, width=12, height=12, bg=CMAP_HEX[color],
                      highlightthickness=0).pack(side='left', padx=(0, 3))
            tk.Label(pv_strip, text=name, font=('Segoe UI', 8),
                     bg=BG_CARD, fg='#c8c8d0'
                     ).pack(side='left', padx=(0, 8))

        bottom = tk.Frame(root, bg=BG_MAIN)
        bottom.place(x=12, y=868, width=696, height=28)
        tk.Button(bottom, text='Open output folder', bg='#3a3a4a',
                  fg='white', activebackground='#4a4a5a',
                  font=('Segoe UI', 8), bd=0, padx=10, pady=3,
                  command=self._open_folder).pack(side='left')
        self.status_var = tk.StringVar(value='Ready.')
        tk.Label(bottom, textvariable=self.status_var,
                 font=('Segoe UI', 8), bg=BG_MAIN, fg=FG_DIM
                 ).pack(side='left', padx=10)
        self.progress = ttk.Progressbar(bottom, mode='determinate', length=180)
        self.progress.pack(side='right', padx=4)

        self.active_tab = 'Known'
        self._select_tab('Known')

    def _select_tab(self, key):
        self.active_tab = key
        for k, b in self.sidebar_buttons.items():
            if k == key:
                b.configure(bg=ACCENT_BLUE, fg='white',
                            font=('Segoe UI', 10, 'bold'))
            else:
                b.configure(bg=SIDE_INACTIVE_BG, fg=SIDE_INACTIVE_FG,
                            font=('Segoe UI', 10, 'bold'))
        self.tab_frames[key].tkraise()
        self._update_preview()

    def _build_tab_known(self, f):
        tk.Label(f, justify='left', font=('Segoe UI', 9),
                 bg=BG_MAIN, fg=FG_MAIN, wraplength=580,
                 text=('Renders ONLY the 64 known stickers. Unknown cells stay '
                       'BLACK, no prediction.')
                 ).pack(anchor='w', pady=(0, 8))
        self._big_button(f, 'Save known-only grid', self._gen_known)

    def _build_tab_mod54(self, f):
        tk.Label(f, justify='left', font=('Segoe UI', 9),
                 bg=BG_MAIN, fg=FG_MAIN, wraplength=580,
                 text=('Single deterministic guess. Copy color from partner at '
                       'distance 54. Default to slash if unknown.')
                 ).pack(anchor='w', pady=(0, 8))
        self._big_button(f, 'Save mod54 prediction', self._gen_mod54)

    def _build_tab_multi(self, f):
        tk.Label(f, justify='left', font=('Segoe UI', 9),
                 bg=BG_MAIN, fg=FG_MAIN, wraplength=580,
                 text=('Votes across periods 54, 36, 27, 18, 12, 9, 6, 4. '
                       'Low-agreement cells stay black.')
                 ).pack(anchor='w', pady=(0, 6))
        row = tk.Frame(f, bg=BG_MAIN)
        row.pack(anchor='w', pady=4)
        ttk.Label(row, text='Min periods agree').pack(side='left')
        self.agree_var = tk.StringVar(value='2')
        sp = ttk.Spinbox(row, from_=1, to=8, textvariable=self.agree_var,
                         width=6, command=self._update_preview)
        sp.pack(side='left', padx=10)
        sp.bind('<KeyRelease>', lambda e: self._update_preview())
        self._big_button(f, 'Save multi-period prediction', self._gen_multi)

    def _build_tab_random(self, f):
        tk.Label(f, justify='left', font=('Segoe UI', 9),
                 bg=BG_MAIN, fg=FG_MAIN, wraplength=580,
                 text=('Draw colors at random per zone weight. Same seed = same '
                       'grid. Use Reroll to see new seeds.')
                 ).pack(anchor='w', pady=(0, 6))
        row = tk.Frame(f, bg=BG_MAIN)
        row.pack(anchor='w', pady=4)
        ttk.Label(row, text='Samples').pack(side='left')
        self.count_var = tk.StringVar(value='6')
        ttk.Spinbox(row, from_=1, to=999, textvariable=self.count_var,
                    width=6).pack(side='left', padx=10)
        ttk.Label(row, text='Seed').pack(side='left', padx=(16, 0))
        self.seed_var = tk.StringVar(value='1')
        sp = ttk.Spinbox(row, from_=0, to=999999, textvariable=self.seed_var,
                         width=8, command=self._update_preview)
        sp.pack(side='left', padx=10)
        sp.bind('<KeyRelease>', lambda e: self._update_preview())
        tk.Button(row, text='Reroll', bg='#3a3a4a', fg='white',
                  bd=0, padx=10, pady=2, font=('Segoe UI', 9),
                  command=self._reroll).pack(side='left', padx=(10, 0))
        self._big_button(f, 'Save batch of samples', self._gen_random)

    def _build_tab_compare(self, f):
        tk.Label(f, justify='left', font=('Segoe UI', 9),
                 bg=BG_MAIN, fg=FG_MAIN, wraplength=580,
                 text=('One-click bundle. Generates ALL modes plus 2 random '
                       'samples (6 PNGs total).')
                 ).pack(anchor='w', pady=(0, 8))
        self._big_button(f, 'Save full comparison bundle', self._gen_compare)

    def _build_tab_pred_zoned(self, f):
        pred_only = [v for k, v in PRED_ZONED.items() if k not in KNOWN]
        cnt = Counter(s for s, _ in pred_only)
        mean = sum(c for _, c in pred_only) / max(1, len(pred_only))
        hard = sum(1 for _, c in pred_only if c < 0.55)
        tk.Label(f, justify='left', font=('Segoe UI', 9),
                 bg=BG_MAIN, fg=FG_MAIN, wraplength=580,
                 text=('Zone-restricted prediction. Predicted cells are blended '
                       'toward white by (1 - confidence).')
                 ).pack(anchor='w', pady=(0, 4))
        tk.Label(f, justify='left', font=('Consolas', 9),
                 bg=BG_MAIN, fg=FG_DIM,
                 text=('known=64  predicted=44  '
                       'G={}  R={}  Y={}  mean={:.3f}  hard<.55={}'
                       ).format(cnt.get('G', 0), cnt.get('R', 0),
                                cnt.get('Y', 0), mean, hard)
                 ).pack(anchor='w', pady=(0, 8))
        self._big_button(f, 'Save predicted-zoned grid', self._gen_pred_zoned)

    def _build_tab_pred_cross(self, f):
        pred_only = [v for k, v in PRED_CROSS.items() if k not in KNOWN]
        cnt = Counter(s for s, _ in pred_only)
        mean = sum(c for _, c in pred_only) / max(1, len(pred_only))
        hard = sum(1 for _, c in pred_only if c < 0.55)
        tk.Label(f, justify='left', font=('Segoe UI', 9),
                 bg=BG_MAIN, fg=FG_MAIN, wraplength=580,
                 text=('Cross-zone prediction. Notice the BOTTOM Y-blackout bias: '
                       'partners are taken across both zones so Y votes get '
                       'masked, inflating G.')
                 ).pack(anchor='w', pady=(0, 4))
        tk.Label(f, justify='left', font=('Consolas', 9),
                 bg=BG_MAIN, fg=FG_DIM,
                 text=('known=64  predicted=44  '
                       'G={}  R={}  Y={}  mean={:.3f}  hard<.55={}'
                       ).format(cnt.get('G', 0), cnt.get('R', 0),
                                cnt.get('Y', 0), mean, hard)
                 ).pack(anchor='w', pady=(0, 8))
        self._big_button(f, 'Save predicted-cross grid', self._gen_pred_cross)

    def _build_tab_heatmap(self, f):
        tk.Label(f, justify='left', font=('Segoe UI', 9),
                 bg=BG_MAIN, fg=FG_MAIN, wraplength=580,
                 text=('Recolour each cell by its zoned confidence. Known cells '
                       'are light grey with a black border; the residue number '
                       'is overlaid on every cell.')
                 ).pack(anchor='w', pady=(0, 6))
        legend = tk.Frame(f, bg=BG_MAIN)
        legend.pack(anchor='w', pady=(0, 8))
        for label, conf in [('0.00', 0.0), ('0.55', 0.55),
                            ('0.75', 0.75), ('1.00', 1.0)]:
            sw = tk.Frame(legend, bg=BG_MAIN)
            sw.pack(side='left', padx=(0, 10))
            tk.Canvas(sw, width=20, height=12, bg=hex_of(heatmap_rgb(conf)),
                      highlightthickness=0).pack(side='left', padx=(0, 3))
            tk.Label(sw, text=label, font=('Consolas', 8),
                     bg=BG_MAIN, fg=FG_MAIN).pack(side='left')
        kn = tk.Frame(legend, bg=BG_MAIN)
        kn.pack(side='left', padx=(0, 6))
        tk.Canvas(kn, width=20, height=12, bg=hex_of(KNOWN_HEAT_FILL),
                  highlightthickness=1, highlightbackground='#000000'
                  ).pack(side='left', padx=(0, 3))
        tk.Label(kn, text='known', font=('Consolas', 8),
                 bg=BG_MAIN, fg=FG_MAIN).pack(side='left')
        self._big_button(f, 'Save confidence heatmap', self._gen_heatmap)

    def _build_tab_hard(self, f):
        tk.Label(f, justify='left', font=('Segoe UI', 9),
                 bg=BG_MAIN, fg=FG_MAIN, wraplength=580,
                 text=('The {} residues whose zoned confidence is below 0.55. '
                       'Each maps to 6 chain numbers in the 648-chain '
                       'production sequence.').format(len(HARD_RESIDUES))
                 ).pack(anchor='w', pady=(0, 4))
        rows = []
        for r in HARD_RESIDUES[:5]:
            sym, conf = PRED_ZONED[r]
            ch = chains_for(r)
            rows.append('r={:>3d} {} {:.2f} ch={}'.format(
                r, sym, conf, ','.join(str(x) for x in ch[:3]) + '...'))
        tk.Label(f, justify='left', font=('Consolas', 8),
                 bg=BG_MAIN, fg=FG_MAIN,
                 text='\n'.join(rows)
                 ).pack(anchor='w', pady=(0, 4))
        self._big_button(f, 'Save hard-cells highlight', self._gen_hard)

    def _big_button(self, parent, text, cmd):
        tk.Button(parent, text=text, bg=ACCENT_BLUE, fg='white',
                  activebackground='#6aafd8',
                  font=('Segoe UI', 10, 'bold'),
                  bd=0, padx=14, pady=4,
                  width=30, command=cmd).pack(pady=2, anchor='w')

    def _current_grid(self):
        key = self.active_tab
        if key == 'Known':
            return grid_known_only()
        if key == 'mod54':
            return predict_mod54()
        if key == 'Multi-P':
            try:
                return predict_multi(int(self.agree_var.get()))
            except (ValueError, AttributeError):
                return predict_multi(2)
        if key == 'Random':
            try:
                return sample_random(int(self.seed_var.get()))
            except (ValueError, AttributeError):
                return sample_random(1)
        if key == 'Bundle':
            return predict_mod54()
        if key == 'Pred Z':
            return [PRED_ZONED[i][0] for i in range(108)]
        if key == 'Pred X':
            return [PRED_CROSS[i][0] for i in range(108)]
        if key == 'ConfHeat':
            return [PRED_ZONED[i][0] for i in range(108)]
        if key == 'Hard':
            return [PRED_ZONED[i][0] for i in range(108)]
        return predict_mod54()

    def _update_preview(self):
        cells = self._current_grid()
        key = self.active_tab
        layout = self.layout_var.get()
        if layout not in LAYOUTS:
            layout = '9x12'
        rows, cols = LAYOUTS[layout]
        cv = self.preview_canvas
        cv.delete('all')
        cw = int(cv['width'])
        ch = int(cv['height'])
        cell = min((cw - 8) // cols, (ch - 8) // rows)
        if cell < 1:
            cell = 1
        gw, gh = cell * cols, cell * rows
        ox = (cw - gw) // 2
        oy = (ch - gh) // 2
        for k in range(108):
            if k >= rows * cols:
                break
            r, c = k // cols, k % cols
            x = ox + c * cell
            y = oy + r * cell
            fill, outline, text = self._cell_visual(key, k, cells[k])
            cv.create_rectangle(x, y, x + cell, y + cell,
                                fill=fill, outline=outline)
            if text and cell >= 14:
                tx = x + cell // 2
                ty = y + cell // 2
                size = max(6, min(9, cell // 3))
                cv.create_text(tx, ty, text=text,
                               font=('Consolas', size),
                               fill='#000000' if key == 'ConfHeat'
                               else '#222222')
        self._update_stats_panel(key, cells)

    def _cell_visual(self, key, k, symbol):
        if key == 'Pred Z':
            sym, conf = PRED_ZONED[k]
            base = CMAP[sym]
            return hex_of(blend_to_white(base, conf)), '', ''
        if key == 'Pred X':
            sym, conf = PRED_CROSS[k]
            base = CMAP[sym]
            return hex_of(blend_to_white(base, conf)), '', ''
        if key == 'ConfHeat':
            sym, conf = PRED_ZONED[k]
            if k in KNOWN:
                return hex_of(KNOWN_HEAT_FILL), '#000000', str(k)
            return hex_of(heatmap_rgb(conf)), '', str(k)
        if key == 'Hard':
            if k in HARD_RESIDUES:
                return hex_of(MAGENTA), '', str(k)
            if k in KNOWN:
                return hex_of(DIM_KNOWN), '', ''
            return hex_of(DIM_PRED), '', ''
        return CMAP_HEX[symbol], '', ''

    def _update_stats_panel(self, key, cells):
        if key in ('Pred Z', 'Pred X'):
            table = PRED_ZONED if key == 'Pred Z' else PRED_CROSS
            pred_only = [v for k, v in table.items() if k not in KNOWN]
            cnt = Counter(s for s, _ in pred_only)
            mean = sum(c for _, c in pred_only) / max(1, len(pred_only))
            hard = sum(1 for _, c in pred_only if c < 0.55)
            self.preview_stats.set(
                'kn:{}  pr:{}  G:{} R:{} Y:{}  mean:{:.2f}  hard:{}'.format(
                    len(KNOWN), len(pred_only),
                    cnt.get('G', 0), cnt.get('R', 0), cnt.get('Y', 0),
                    mean, hard))
            return
        if key == 'ConfHeat':
            pred_only = [v for k, v in PRED_ZONED.items() if k not in KNOWN]
            confs = [c for _, c in pred_only]
            bins = [0, 0, 0, 0]
            for c in confs:
                if c < 0.55:
                    bins[0] += 1
                elif c < 0.75:
                    bins[1] += 1
                elif c < 1.0:
                    bins[2] += 1
                else:
                    bins[3] += 1
            self.preview_stats.set(
                'kn:{}  <.55:{}  <.75:{}  <1.0:{}  mean:{:.2f}'.format(
                    len(KNOWN), bins[0], bins[1], bins[2],
                    sum(confs) / max(1, len(confs))))
            return
        if key == 'Hard':
            self.preview_stats.set(
                'hard:{}  pred:{}  kn:{}  chains:{}'.format(
                    len(HARD_RESIDUES),
                    108 - len(KNOWN), len(KNOWN),
                    len(HARD_RESIDUES) * 6))
            return
        cnt = Counter(cells)
        self.preview_stats.set(
            'slash:{}  dash:{}  dot:{}  unk:{}'.format(
                cnt.get('G', 0), cnt.get('R', 0),
                cnt.get('Y', 0), cnt.get('K', 0)))

    def _reroll(self):
        try:
            cur = int(self.seed_var.get())
        except ValueError:
            cur = 0
        self.seed_var.set(str(cur + 1))
        self._update_preview()

    def _browse(self):
        d = filedialog.askdirectory(initialdir=self.out_var.get())
        if d:
            self.out_var.set(d)

    def _open_folder(self):
        p = Path(self.out_var.get())
        if p.exists():
            try:
                os.startfile(str(p))
            except Exception:
                pass
        else:
            messagebox.showinfo('Not yet', 'Folder does not exist yet.')

    def _common(self):
        try:
            cell_size = int(self.cell_var.get())
        except ValueError:
            messagebox.showerror('Bad input', 'Cell size must be an integer.')
            return None
        layout = self.layout_var.get()
        if layout not in LAYOUTS:
            messagebox.showerror('Bad layout', 'Pick a valid layout.')
            return None
        out_dir = Path(self.out_var.get())
        out_dir.mkdir(parents=True, exist_ok=True)
        rows, cols = LAYOUTS[layout]
        return rows, cols, cell_size, out_dir, layout

    def _gen_known(self):
        cp = self._common()
        if cp is None:
            return
        rows, cols, cs, out, lay = cp
        cells = grid_known_only()
        path = out / 'known_only_{}.png'.format(lay)
        render(cells, rows, cols, cs, path)
        unknown = sum(1 for c in cells if c == 'K')
        self.status_var.set('Saved {} ({} black)'.format(path.name, unknown))

    def _gen_mod54(self):
        cp = self._common()
        if cp is None:
            return
        rows, cols, cs, out, lay = cp
        cells = predict_mod54()
        path = out / 'mod54_{}.png'.format(lay)
        render(cells, rows, cols, cs, path)
        self.status_var.set('Saved ' + path.name)

    def _gen_multi(self):
        cp = self._common()
        if cp is None:
            return
        rows, cols, cs, out, lay = cp
        try:
            min_a = int(self.agree_var.get())
        except ValueError:
            messagebox.showerror('Bad input', 'Min agree must be an integer.')
            return
        cells = predict_multi(min_a)
        path = out / 'multi_min{}_{}.png'.format(min_a, lay)
        render(cells, rows, cols, cs, path)
        unknown = sum(1 for c in cells if c == 'K')
        self.status_var.set('Saved {} ({} stay black)'.format(
            path.name, unknown))

    def _gen_random(self):
        cp = self._common()
        if cp is None:
            return
        rows, cols, cs, out, lay = cp
        try:
            count = int(self.count_var.get())
            seed_start = int(self.seed_var.get())
        except ValueError:
            messagebox.showerror('Bad input',
                                 'Samples and seed must be integers.')
            return
        self.progress['maximum'] = count
        self.progress['value'] = 0
        self.status_var.set('Generating...')
        threading.Thread(target=self._random_worker,
                         args=(count, rows, cols, cs, seed_start, out, lay),
                         daemon=True).start()

    def _random_worker(self, count, rows, cols, cs, seed_start, out, lay):
        for i in range(count):
            seed = seed_start + i
            cells = sample_random(seed)
            path = out / 'random_{}_seed{:03d}.png'.format(lay, seed)
            render(cells, rows, cols, cs, path)
            self.root.after(0, self._tick, i + 1, count, path.name)
        self.root.after(0, lambda: self.status_var.set(
            'Done. {} samples saved.'.format(count)))

    def _gen_compare(self):
        cp = self._common()
        if cp is None:
            return
        rows, cols, cs, out, lay = cp
        bundle = [
            ('known_only', grid_known_only()),
            ('mod54', predict_mod54()),
            ('multi_min2', predict_multi(2)),
            ('multi_min3', predict_multi(3)),
            ('random_seed1', sample_random(1)),
            ('random_seed2', sample_random(2)),
        ]
        for name, cells in bundle:
            path = out / 'compare_{}_{}.png'.format(name, lay)
            render(cells, rows, cols, cs, path)
        self.status_var.set(
            'Saved {} files in {}/'.format(len(bundle), out.name))

    def _gen_pred_zoned(self):
        cp = self._common()
        if cp is None:
            return
        rows, cols, cs, out, lay = cp
        rgb = cells_pred_blended(PRED_ZONED)
        path = out / 'predicted_zoned_{}.png'.format(lay)
        render_rgb(rgb, rows, cols, cs, path)
        self.status_var.set('Saved ' + path.name)

    def _gen_pred_cross(self):
        cp = self._common()
        if cp is None:
            return
        rows, cols, cs, out, lay = cp
        rgb = cells_pred_blended(PRED_CROSS)
        path = out / 'predicted_cross_{}.png'.format(lay)
        render_rgb(rgb, rows, cols, cs, path)
        self.status_var.set('Saved ' + path.name)

    def _gen_heatmap(self):
        cp = self._common()
        if cp is None:
            return
        rows, cols, cs, out, lay = cp
        rgb = cells_heatmap()
        path = out / 'confidence_heatmap_{}.png'.format(lay)
        render_rgb(rgb, rows, cols, cs, path)
        self.status_var.set('Saved ' + path.name)

    def _gen_hard(self):
        cp = self._common()
        if cp is None:
            return
        rows, cols, cs, out, lay = cp
        rgb = cells_hard()
        path = out / 'hard_cells_{}.png'.format(lay)
        render_rgb(rgb, rows, cols, cs, path)
        self.status_var.set('Saved ' + path.name)

    def _tick(self, done, total, name):
        self.progress['value'] = done
        self.status_var.set('[{}/{}] {}'.format(done, total, name))


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
