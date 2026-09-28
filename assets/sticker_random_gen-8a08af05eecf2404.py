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


class App:
    def __init__(self, root):
        self.root = root
        root.title('INSIDE sticker variant generator')
        root.geometry('720x780')
        root.resizable(False, False)
        root.configure(bg='#1e1e2e')

        style = ttk.Style()
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass
        style.configure('Big.TNotebook', background='#1e1e2e',
                        borderwidth=0, tabmargins=[2, 8, 2, 0])
        style.configure('Big.TNotebook.Tab',
                        font=('Segoe UI', 11, 'bold'),
                        padding=[20, 10],
                        background='#3a3a4f',
                        foreground='#dddddd',
                        borderwidth=2)
        style.map('Big.TNotebook.Tab',
                  background=[('selected', '#5a9fd4')],
                  foreground=[('selected', 'white')],
                  expand=[('selected', [3, 5, 3, 0])])
        style.configure('Card.TLabelframe',
                        background='#2a2a3e', foreground='#dddddd',
                        bordercolor='#5a9fd4', borderwidth=1)
        style.configure('Card.TLabelframe.Label',
                        background='#2a2a3e', foreground='#5a9fd4',
                        font=('Segoe UI', 10, 'bold'))
        style.configure('TFrame', background='#1e1e2e')
        style.configure('TLabel', background='#1e1e2e', foreground='#dddddd')
        style.configure('Card.TLabel', background='#2a2a3e', foreground='#dddddd')

        tg, bg = zone_weights()
        n_known = len(KNOWN)
        n_unknown = 108 - n_known

        tk.Label(root, text='INSIDE Sticker Grid: Variant Generator',
                 font=('Segoe UI', 16, 'bold'),
                 bg='#1e1e2e', fg='#5a9fd4').pack(pady=(10, 2))
        tk.Label(root, font=('Segoe UI', 9), bg='#1e1e2e', fg='#aaaaaa',
                 text=('{} known stickers, {} unknown cells.    '
                       'Top zone: slash {:.0%} / dash {:.0%}    '
                       'Bottom: slash {:.0%} / dot {:.0%}'
                       ).format(n_known, n_unknown, tg, 1-tg, bg, 1-bg)
                 ).pack(pady=(0, 6))

        common = ttk.LabelFrame(root, text=' Common settings ',
                                style='Card.TLabelframe', padding=10)
        common.pack(fill='x', padx=18, pady=4)
        ttk.Label(common, text='Layout', style='Card.TLabel'
                  ).grid(row=0, column=0, sticky='w')
        self.layout_var = tk.StringVar(value='9x12')
        layout_combo = ttk.Combobox(common, textvariable=self.layout_var,
                                     state='readonly', width=8,
                                     values=list(LAYOUTS))
        layout_combo.grid(row=0, column=1, padx=6)
        layout_combo.bind('<<ComboboxSelected>>', lambda e: self._update_preview())
        ttk.Label(common, text='Cell size (PNG)', style='Card.TLabel'
                  ).grid(row=0, column=2, padx=(20, 0), sticky='w')
        self.cell_var = tk.StringVar(value='64')
        ttk.Spinbox(common, from_=16, to=256, increment=16,
                    textvariable=self.cell_var, width=6
                    ).grid(row=0, column=3, padx=6)
        ttk.Label(common, text='Output folder', style='Card.TLabel'
                  ).grid(row=1, column=0, sticky='w', pady=(10, 0))
        self.out_var = tk.StringVar(value=str(Path.cwd() / 'samples'))
        ttk.Entry(common, textvariable=self.out_var, width=44
                  ).grid(row=1, column=1, columnspan=2, padx=6,
                         pady=(10, 0), sticky='w')
        ttk.Button(common, text='Browse', command=self._browse
                   ).grid(row=1, column=3, padx=6, pady=(10, 0))

        self.nb = ttk.Notebook(root, style='Big.TNotebook')
        self.nb.pack(fill='x', padx=18, pady=(8, 0))
        self.nb.bind('<<NotebookTabChanged>>', lambda e: self._update_preview())
        self._build_tab_known()
        self._build_tab_mod54()
        self._build_tab_multi()
        self._build_tab_random()
        self._build_tab_compare()

        preview_frame = ttk.LabelFrame(root, text=' Live preview ',
                                       style='Card.TLabelframe', padding=12)
        preview_frame.pack(fill='both', expand=True, padx=18, pady=(8, 4))

        pv_left = tk.Frame(preview_frame, bg='#2a2a3e')
        pv_left.pack(side='left', fill='y')
        self.preview = tk.Canvas(pv_left, width=240, height=300,
                                  bg='#000000', highlightthickness=0)
        self.preview.pack()

        pv_right = tk.Frame(preview_frame, bg='#2a2a3e')
        pv_right.pack(side='left', fill='both', expand=True, padx=(20, 0))
        self.preview_stats = tk.StringVar(value='')
        tk.Label(pv_right, textvariable=self.preview_stats,
                 font=('Consolas', 11), bg='#2a2a3e', fg='#dddddd',
                 justify='left'
                 ).pack(anchor='w', pady=(6, 12))
        for color, name in [('G', 'slash (grey)'), ('R', 'dash (red)'),
                            ('Y', 'dot (yellow)'), ('K', 'unknown (black)')]:
            row = tk.Frame(pv_right, bg='#2a2a3e')
            row.pack(anchor='w', pady=2)
            tk.Canvas(row, width=22, height=22, bg=CMAP_HEX[color],
                      highlightthickness=0).pack(side='left', padx=(0, 8))
            tk.Label(row, text=name, font=('Segoe UI', 10),
                     bg='#2a2a3e', fg='#dddddd').pack(side='left')

        bottom = tk.Frame(root, bg='#1e1e2e')
        bottom.pack(fill='x', padx=18, pady=(4, 6))
        tk.Button(bottom, text='Open output folder', bg='#3a3a4f',
                  fg='white', activebackground='#4a4a5f',
                  font=('Segoe UI', 9), bd=0, padx=12, pady=4,
                  command=self._open_folder).pack(side='left')
        self.status_var = tk.StringVar(value='Ready.')
        tk.Label(bottom, textvariable=self.status_var,
                 font=('Segoe UI', 9), bg='#1e1e2e', fg='#aaaaaa'
                 ).pack(side='left', padx=12)

        self.progress = ttk.Progressbar(root, mode='determinate', length=680)
        self.progress.pack(padx=18, pady=(0, 4))

        tk.Label(root, font=('Segoe UI', 8), bg='#1e1e2e', fg='#666666',
                 text='Each grid is one hypothesis, not a final answer.'
                 ).pack(pady=(0, 4))

        self._update_preview()

    def _build_tab_known(self):
        f = ttk.Frame(self.nb, padding=14)
        self.nb.add(f, text='Known only')
        tk.Label(f, justify='left', font=('Segoe UI', 9),
                 bg='#1e1e2e', fg='#dddddd',
                 text=('Renders ONLY the 64 known stickers. Unknown cells stay '
                       'BLACK, no prediction.')
                 ).pack(anchor='w', pady=(0, 8))
        self._big_button(f, 'Save known-only grid', self._gen_known)

    def _build_tab_mod54(self):
        f = ttk.Frame(self.nb, padding=14)
        self.nb.add(f, text='mod54')
        tk.Label(f, justify='left', font=('Segoe UI', 9),
                 bg='#1e1e2e', fg='#dddddd',
                 text=('Single deterministic guess. Copy color from partner at '
                       'distance 54. Default to slash if unknown.')
                 ).pack(anchor='w', pady=(0, 8))
        self._big_button(f, 'Save mod54 prediction', self._gen_mod54)

    def _build_tab_multi(self):
        f = ttk.Frame(self.nb, padding=14)
        self.nb.add(f, text='Multi-period')
        tk.Label(f, justify='left', font=('Segoe UI', 9),
                 bg='#1e1e2e', fg='#dddddd',
                 text=('Votes across periods 54, 36, 27, 18, 12, 9, 6, 4. '
                       'Low-agreement cells stay black.')
                 ).pack(anchor='w', pady=(0, 6))
        row = tk.Frame(f, bg='#1e1e2e')
        row.pack(anchor='w', pady=4)
        ttk.Label(row, text='Min periods agree').pack(side='left')
        self.agree_var = tk.StringVar(value='2')
        sp = ttk.Spinbox(row, from_=1, to=8, textvariable=self.agree_var,
                         width=6, command=self._update_preview)
        sp.pack(side='left', padx=10)
        sp.bind('<KeyRelease>', lambda e: self._update_preview())
        self._big_button(f, 'Save multi-period prediction', self._gen_multi)

    def _build_tab_random(self):
        f = ttk.Frame(self.nb, padding=14)
        self.nb.add(f, text='Random-weighted')
        tk.Label(f, justify='left', font=('Segoe UI', 9),
                 bg='#1e1e2e', fg='#dddddd',
                 text=('Draw colors at random per zone weight. Same seed = same '
                       'grid. Use Reroll to see new seeds.')
                 ).pack(anchor='w', pady=(0, 6))
        row = tk.Frame(f, bg='#1e1e2e')
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
        tk.Button(row, text='Reroll', bg='#3a3a4f', fg='white',
                  bd=0, padx=10, pady=2, font=('Segoe UI', 9),
                  command=self._reroll).pack(side='left', padx=(10, 0))
        self._big_button(f, 'Save batch of samples', self._gen_random)

    def _build_tab_compare(self):
        f = ttk.Frame(self.nb, padding=14)
        self.nb.add(f, text='Compare all')
        tk.Label(f, justify='left', font=('Segoe UI', 9),
                 bg='#1e1e2e', fg='#dddddd',
                 text=('One-click bundle. Generates ALL modes plus 2 random '
                       'samples (6 PNGs total).')
                 ).pack(anchor='w', pady=(0, 8))
        self._big_button(f, 'Save full comparison bundle', self._gen_compare)

    def _big_button(self, parent, text, cmd):
        tk.Button(parent, text=text, bg='#5a9fd4', fg='white',
                  activebackground='#6aafd8',
                  font=('Segoe UI', 11, 'bold'),
                  bd=0, padx=20, pady=6,
                  width=32, command=cmd).pack(pady=4)

    def _current_grid(self):
        tab = self.nb.index('current')
        if tab == 0:
            return grid_known_only()
        if tab == 1:
            return predict_mod54()
        if tab == 2:
            try:
                return predict_multi(int(self.agree_var.get()))
            except (ValueError, AttributeError):
                return predict_multi(2)
        if tab == 3:
            try:
                return sample_random(int(self.seed_var.get()))
            except (ValueError, AttributeError):
                return sample_random(1)
        return predict_mod54()

    def _update_preview(self):
        cells = self._current_grid()
        layout = self.layout_var.get()
        if layout not in LAYOUTS:
            layout = '9x12'
        rows, cols = LAYOUTS[layout]
        cv = self.preview
        cv.delete('all')
        cw = int(cv['width'])
        ch = int(cv['height'])
        cell = min(cw // cols, ch // rows)
        gw, gh = cell * cols, cell * rows
        ox = (cw - gw) // 2
        oy = (ch - gh) // 2
        for k in range(108):
            if k >= rows * cols:
                break
            r, c = k // cols, k % cols
            x = ox + c * cell
            y = oy + r * cell
            color = CMAP_HEX[cells[k]]
            cv.create_rectangle(x, y, x + cell, y + cell,
                                fill=color, outline='')
        cnt = Counter(cells)
        self.preview_stats.set(
            'slash : {:>3d}\n'
            'dash  : {:>3d}\n'
            'dot   : {:>3d}\n'
            'unknown: {:>2d}'.format(
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
        if cp is None: return
        rows, cols, cs, out, lay = cp
        cells = grid_known_only()
        path = out / 'known_only_{}.png'.format(lay)
        render(cells, rows, cols, cs, path)
        unknown = sum(1 for c in cells if c == 'K')
        self.status_var.set('Saved {} ({} black cells)'.format(path.name, unknown))

    def _gen_mod54(self):
        cp = self._common()
        if cp is None: return
        rows, cols, cs, out, lay = cp
        cells = predict_mod54()
        path = out / 'mod54_{}.png'.format(lay)
        render(cells, rows, cols, cs, path)
        self.status_var.set('Saved ' + path.name)

    def _gen_multi(self):
        cp = self._common()
        if cp is None: return
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
        self.status_var.set('Saved {} ({} stay black)'.format(path.name, unknown))

    def _gen_random(self):
        cp = self._common()
        if cp is None: return
        rows, cols, cs, out, lay = cp
        try:
            count = int(self.count_var.get())
            seed_start = int(self.seed_var.get())
        except ValueError:
            messagebox.showerror('Bad input', 'Samples and seed must be integers.')
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
            'Done. {} random samples saved.'.format(count)))

    def _gen_compare(self):
        cp = self._common()
        if cp is None: return
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
            'Saved {} comparison files in {}/'.format(len(bundle), out.name))

    def _tick(self, done, total, name):
        self.progress['value'] = done
        self.status_var.set('[{}/{}] {}'.format(done, total, name))


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
