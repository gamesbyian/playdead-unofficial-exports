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
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    in_venv = (getattr(sys, 'base_prefix', sys.prefix) != sys.prefix)
    cmd = [sys.executable, '-m', 'pip', 'install', '--quiet', 'pillow']
    if not in_venv:
        cmd.append('--user')
    subprocess.check_call(cmd)
    from PIL import Image, ImageDraw, ImageFont

import tkinter as tk
from tkinter import ttk, filedialog, messagebox


KNOWN = {
      0: 'G',   2: 'G',   3: 'R',   4: 'R',   5: 'G',   7: 'G',
      9: 'G',  10: 'R',  12: 'R',  13: 'G',  14: 'R',  15: 'G',  17: 'G',
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
      0: ('G', 1.000),   1: ('R', 0.686),   2: ('G', 1.000),   3: ('R', 1.000),   4: ('R', 1.000),   5: ('G', 1.000),
      6: ('G', 0.831),   7: ('G', 1.000),   8: ('G', 0.524),   9: ('G', 1.000),  10: ('R', 1.000),  11: ('G', 0.849),
     12: ('R', 1.000),  13: ('G', 1.000),  14: ('R', 1.000),  15: ('G', 1.000),  16: ('R', 0.596),  17: ('G', 1.000),
     18: ('R', 1.000),  19: ('R', 1.000),  20: ('G', 1.000),  21: ('R', 1.000),  22: ('G', 0.685),  23: ('R', 1.000),
     24: ('R', 1.000),  25: ('G', 0.771),  26: ('R', 1.000),  27: ('G', 0.776),  28: ('G', 0.511),  29: ('G', 1.000),
     30: ('G', 1.000),  31: ('R', 1.000),  32: ('G', 1.000),  33: ('G', 0.749),  34: ('R', 0.520),  35: ('R', 0.608),
     36: ('G', 1.000),  37: ('R', 1.000),  38: ('G', 1.000),  39: ('G', 1.000),  40: ('G', 1.000),  41: ('G', 0.627),
     42: ('G', 1.000),  43: ('G', 1.000),  44: ('R', 1.000),  45: ('G', 0.625),  46: ('G', 1.000),  47: ('G', 1.000),
     48: ('G', 1.000),  49: ('G', 0.701),  50: ('R', 0.624),  51: ('R', 1.000),  52: ('G', 0.614),  53: ('R', 1.000),
     54: ('G', 0.668),  55: ('R', 0.675),  56: ('G', 1.000),  57: ('R', 1.000),  58: ('R', 0.637),  59: ('G', 1.000),
     60: ('G', 1.000),  61: ('G', 0.812),  62: ('R', 0.624),  63: ('G', 1.000),  64: ('R', 0.680),  65: ('G', 1.000),
     66: ('G', 1.000),  67: ('G', 0.629),  68: ('R', 0.519),  69: ('G', 1.000),  70: ('R', 1.000),  71: ('R', 1.000),
     72: ('R', 1.000),  73: ('R', 0.731),  74: ('R', 1.000),  75: ('R', 1.000),  76: ('G', 1.000),  77: ('R', 0.507),
     78: ('G', 1.000),  79: ('G', 1.000),  80: ('G', 1.000),  81: ('G', 1.000),  82: ('Y', 0.674),  83: ('Y', 0.565),
     84: ('G', 0.636),  85: ('Y', 1.000),  86: ('G', 1.000),  87: ('G', 0.702),  88: ('Y', 0.791),  89: ('Y', 1.000),
     90: ('Y', 1.000),  91: ('Y', 0.917),  92: ('Y', 1.000),  93: ('G', 0.646),  94: ('Y', 0.879),  95: ('Y', 1.000),
     96: ('G', 1.000),  97: ('Y', 1.000),  98: ('Y', 1.000),  99: ('G', 0.681), 100: ('G', 0.539), 101: ('G', 1.000),
    102: ('Y', 0.546), 103: ('Y', 0.854), 104: ('G', 0.536), 105: ('G', 0.862), 106: ('Y', 0.723), 107: ('Y', 0.815),
}

PRED_CROSS = {
      0: ('G', 1.000),   1: ('R', 0.706),   2: ('G', 1.000),   3: ('R', 1.000),   4: ('R', 1.000),   5: ('G', 1.000),
      6: ('G', 0.850),   7: ('G', 1.000),   8: ('G', 0.541),   9: ('G', 1.000),  10: ('R', 1.000),  11: ('G', 0.860),
     12: ('R', 1.000),  13: ('G', 1.000),  14: ('R', 1.000),  15: ('G', 1.000),  16: ('R', 0.613),  17: ('G', 1.000),
     18: ('R', 1.000),  19: ('R', 1.000),  20: ('G', 1.000),  21: ('R', 1.000),  22: ('G', 0.692),  23: ('R', 1.000),
     24: ('R', 1.000),  25: ('G', 0.790),  26: ('R', 1.000),  27: ('G', 0.835),  28: ('G', 0.513),  29: ('G', 1.000),
     30: ('G', 1.000),  31: ('R', 1.000),  32: ('G', 1.000),  33: ('G', 0.777),  34: ('R', 0.529),  35: ('R', 0.608),
     36: ('G', 1.000),  37: ('R', 1.000),  38: ('G', 1.000),  39: ('G', 1.000),  40: ('G', 1.000),  41: ('G', 0.703),
     42: ('G', 1.000),  43: ('G', 1.000),  44: ('R', 1.000),  45: ('G', 0.650),  46: ('G', 1.000),  47: ('G', 1.000),
     48: ('G', 1.000),  49: ('G', 0.706),  50: ('G', 0.503),  51: ('R', 1.000),  52: ('G', 0.611),  53: ('R', 1.000),
     54: ('G', 0.736),  55: ('R', 0.682),  56: ('G', 1.000),  57: ('R', 1.000),  58: ('R', 0.627),  59: ('G', 1.000),
     60: ('G', 1.000),  61: ('G', 0.839),  62: ('R', 0.558),  63: ('G', 1.000),  64: ('R', 0.682),  65: ('G', 1.000),
     66: ('G', 1.000),  67: ('G', 0.637),  68: ('G', 0.535),  69: ('G', 1.000),  70: ('R', 1.000),  71: ('R', 1.000),
     72: ('R', 1.000),  73: ('R', 0.748),  74: ('R', 1.000),  75: ('R', 1.000),  76: ('G', 1.000),  77: ('R', 0.504),
     78: ('G', 1.000),  79: ('G', 1.000),  80: ('G', 1.000),  81: ('G', 1.000),  82: ('G', 0.872),  83: ('G', 0.909),
     84: ('G', 0.939),  85: ('Y', 1.000),  86: ('G', 1.000),  87: ('G', 0.932),  88: ('G', 0.848),  89: ('Y', 1.000),
     90: ('Y', 1.000),  91: ('G', 0.704),  92: ('Y', 1.000),  93: ('G', 0.889),  94: ('G', 0.870),  95: ('Y', 1.000),
     96: ('G', 1.000),  97: ('Y', 1.000),  98: ('Y', 1.000),  99: ('G', 0.953), 100: ('G', 0.981), 101: ('G', 1.000),
    102: ('G', 0.963), 103: ('G', 0.836), 104: ('G', 0.902), 105: ('G', 0.974), 106: ('G', 0.900), 107: ('G', 0.745),
}

HARD_RESIDUES = [8, 28, 34, 68, 77, 100, 102, 104]
STICKERS_LOST = 40
STICKERS_UNKNOWN_OWNER = 25
STICKERS_FOUND_FALLBACK = 81
STICKER_DIR = Path('D:/INSIDE_ARG/ARG/inside-args/images/stickers')
HEATMAP_STOPS = [(0.00, (220, 30, 30)), (0.55, (230, 140, 0)),
                 (0.75, (180, 200, 0)), (1.00, (0, 180, 0))]
MAGENTA = (200, 60, 200)
DIM_PRED = (70, 80, 90)
DIM_KNOWN = (40, 40, 40)
KNOWN_HEAT_FILL = (210, 210, 210)

BG_BASE = '#0F1115'
BG_PANEL = '#1A1D24'
BG_CARD = '#232730'
BG_HOVER = '#2A2F3A'
BG_INPUT = '#1F232B'
ACCENT = '#4F8FF7'
ACCENT_HOVER = '#6BA3FB'
ACCENT_DIM = '#3A6FC7'
TEXT_PRIMARY = '#E8E8EC'
TEXT_SECONDARY = '#9598A1'
TEXT_DIM = '#6B6E78'
BORDER_SUBTLE = '#2A2F3A'
SUCCESS = '#4AC774'
WARN = '#F5A623'
DANGER = '#E74C3C'

BG_MAIN = BG_BASE
BG_SIDE = BG_PANEL
FG_MAIN = TEXT_PRIMARY
FG_DIM = TEXT_SECONDARY
BORDER_BLUE = ACCENT_DIM
ACCENT_BLUE = ACCENT
SIDE_INACTIVE_BG = BG_PANEL
SIDE_INACTIVE_FG = TEXT_SECONDARY

TAB_KEYS = [
    'known_only',
    'pattern_mod54',
    'multi_period',
    'random_sampler',
    'export_bundle',
    'prediction_zoned',
    'prediction_cross',
    'confidence_heatmap',
    'hard_residues',
]

TAB_META = {
    'known_only': {
        'card_title': 'Known cells',
        'card_subtitle': '65 confirmed stickers',
        'big_title': 'Known cells only',
        'description': 'Renders the 65 unique residues confirmed by community-collected stickers. 81 stickers have been physically collected; some share the same residue (production has 6 copies per residue), so they collapse to 65 unique cells. The remaining 43 residues stay BLACK.',
        'numbers_info': "Numbers: residue # on every known cell when 'Show numbers' is on. Predicted/unknown cells stay blank (black).",
        'legend_kind': 'symbol3_plus_unk',
    },
    'pattern_mod54': {
        'card_title': 'Pattern · mod 54',
        'card_subtitle': 'Deterministic baseline',
        'big_title': 'Pattern · mod 54 majority vote',
        'description': 'Single-feature baseline. For each unknown residue, take the symbol from partners at distance 54 and pick the majority. One period only - no row/column features, no confidence. Ceiling: 84.6% accuracy.',
        'numbers_info': "Numbers: 'Show numbers' overlays residue # on known cells. Predicted cells are not labelled.",
        'legend_kind': 'symbol3',
    },
    'multi_period': {
        'card_title': 'Multi-period vote',
        'card_subtitle': '8 periods, threshold',
        'big_title': 'Multi-period agreement vote',
        'description': 'Voting across 8 partner-periods (54, 36, 27, 18, 12, 9, 6, 4). A cell is filled only when at least N periods agree on the same class; otherwise it stays BLACK. No row/column features, no confidence.',
        'numbers_info': "Numbers: 'Show numbers' overlays residue # on known cells. Black cells = no period agreement; they stay unlabelled.",
        'legend_kind': 'symbol3_plus_lowagree',
    },
    'random_sampler': {
        'card_title': 'Random sampler',
        'card_subtitle': 'Seeded zone-weighted',
        'big_title': 'Random zone-weighted sample',
        'description': 'Fills each unknown cell randomly using empirical zone weights. Same seed always produces the same grid; the Reroll button bumps the seed by one.',
        'numbers_info': "Numbers: 'Show numbers' overlays residue # on known cells. Random fills are not labelled.",
        'legend_kind': 'symbol3',
    },
    'export_bundle': {
        'card_title': 'Export bundle',
        'card_subtitle': 'All modes, one click',
        'big_title': 'Export bundle · 6 PNGs',
        'description': 'One-click export of every static mode: known-only, mod54, multi-period (min agree 2 and 3), and two random samples (seeds 1 and 2). 6 PNGs saved to the output folder.',
        'numbers_info': 'Saved PNGs have no labels overlaid - they are raw 108-cell grids.',
        'legend_kind': 'symbol3',
    },
    'prediction_zoned': {
        'card_title': 'Prediction · zoned',
        'card_subtitle': 'Zone-aware, primary',
        'big_title': 'Prediction · zone-restricted (primary)',
        'description': "Production model. Partner-vote across 8 periods + row + column features, restricted to the unknown's own zone (TOP-only or BOTTOM-only partners). Outputs a per-cell confidence; cells fade toward white by (1 - confidence).",
        'numbers_info': "Numbers: 'Show numbers' overlays residue # on known cells. Predicted cells are coloured by (1 - confidence).",
        'legend_kind': 'symbol3_with_gradient',
    },
    'prediction_cross': {
        'card_title': 'Prediction · cross',
        'card_subtitle': 'Cross-zone, biased',
        'big_title': 'Prediction · cross-zone (audit only)',
        'description': 'Audit-only twin of the production model. Partners pulled from BOTH zones - BOTTOM cells suffer a Y-blackout bias (cross-zone partners vote R, then R gets masked, inflating G). Useful for diff against zoned; not for downstream.',
        'numbers_info': "Numbers: 'Show numbers' overlays residue # on known cells. Same blend rule as zoned.",
        'legend_kind': 'symbol3_with_gradient',
    },
    'confidence_heatmap': {
        'card_title': 'Confidence heatmap',
        'card_subtitle': 'Red to green by conf',
        'big_title': 'Zoned-prediction confidence heatmap',
        'description': 'Recolours every predicted cell red -> orange -> yellow -> green by its zoned confidence (the value used in the proof_stickers.md targeting). Known cells appear as light grey with a black border for contrast.',
        'numbers_info': "Numbers: residue # is always overlaid on every cell, regardless of the 'Show numbers' setting.",
        'legend_kind': 'heatmap_gradient',
    },
    'hard_residues': {
        'card_title': 'Hard residues',
        'card_subtitle': 'Below 0.55 confidence',
        'big_title': 'Hard residues · proof-sticker targets',
        'description': 'The N residues with zoned confidence below 0.55 - the proof-sticker targeting set. Each maps to 6 chain numbers in the 648-cell production sequence. Listed in reports/proof_stickers.md as community-confirmation targets.',
        'numbers_info': "Numbers: residue # is always overlaid on every hard (magenta) cell. 'Show numbers' adds residue # on dim grey known cells.",
        'legend_kind': 'hard_tri',
    },
}


LANGS = ('en', 'ru', 'de', 'it', 'da')
DEFAULT_LANG = 'en'

GLYPHS = {'G': '/', 'R': '—', 'Y': '•', 'K': ''}

_I18N_DATA: dict[str, tuple] = {
    'app_title': ('INSIDE Sticker Studio', 'INSIDE Sticker Studio', 'INSIDE Sticker Studio', 'INSIDE Sticker Studio', 'INSIDE Sticker Studio'),
    'app_subtitle': (
        "INSIDE Collector's Edition · 108-cell residue puzzle",
        'Коллекционное издание INSIDE · головоломка из 108 ячеек',
        "INSIDE Collector's Edition · Rätsel mit 108 Zellen",
        'Edizione da collezione INSIDE · puzzle da 108 celle',
        "INSIDE Collector's Edition · puslespil med 108 felter",
    ),
    'view_modes_header': ('VIEW MODES', 'РЕЖИМЫ', 'ANSICHTEN', 'MODI', 'VISNINGER'),
    'live_preview': ('Live preview', 'Превью', 'Live-Vorschau', 'Anteprima', 'Live preview'),
    'layout_label': ('Layout', 'Сетка', 'Layout', 'Layout', 'Layout'),
    'cell_size_label': ('Cell size (PNG output)', 'Размер ячейки (PNG)', 'Zellgröße (PNG)', 'Dimensione cella (PNG)', 'Cellestørrelse (PNG)'),
    'output_label': ('Output', 'Папка', 'Ausgabe', 'Output', 'Output'),
    'browse_button': ('Browse', 'Выбрать', 'Durchsuchen', 'Sfoglia', 'Gennemse'),
    'save_legend_button': ('Save with legend', 'Сохранить с легендой', 'Mit Legende speichern', 'Salva con legenda', 'Gem med forklaring'),
    'open_folder_button': ('Open folder', 'Открыть папку', 'Ordner öffnen', 'Apri cartella', 'Åbn mappe'),
    'show_numbers_checkbox': ('Show numbers (known)', 'Показать номера (известные)', 'Nummern anzeigen (bekannt)', 'Mostra numeri (noti)', 'Vis numre (kendte)'),
    'show_symbols_checkbox': ('Show symbols (/, —, •)', 'Показать символы (/, —, •)', 'Symbole anzeigen (/, —, •)', 'Mostra simboli (/, —, •)', 'Vis symboler (/, —, •)'),
    'ready_status': ('Ready.', 'Готово.', 'Bereit.', 'Pronto.', 'Klar.'),
    'pill_stickers_found': ('{n} stickers found', '{n} стикеров найдено', '{n} Sticker gefunden', '{n} sticker trovati', '{n} klistermaerker fundet'),
    'pill_lost': ('{n} lost', '{n} утеряно', '{n} verloren', '{n} persi', '{n} tabt'),
    'pill_owner_unknown': ('{n} owner-unknown', '{n} владелец неизвестен', '{n} Besitzer unbekannt', '{n} proprietario sconosciuto', '{n} ejer ukendt'),
    'pill_residues_known': ('{n} of 108 residues known', '{n} из 108 ячеек известно', '{n} von 108 Zellen bekannt', '{n} di 108 celle note', '{n} af 108 felter kendt'),
    'pill_top_slash': ('TOP slash {pct}%', 'ВЕРХ слеш {pct}%', 'OBEN Schrägstrich {pct}%', 'ALTO barra {pct}%', 'TOP skråstreg {pct}%'),
    'pill_bottom_slash': ('BOTTOM slash {pct}%', 'НИЗ слеш {pct}%', 'UNTEN Schrägstrich {pct}%', 'BASSO barra {pct}%', 'BUND skråstreg {pct}%'),
    'reroll_button': ('Reroll', 'Перебросить', 'Neu würfeln', 'Rilancia', 'Slå om'),
    'export_button': ('Export 6 PNGs', 'Экспорт 6 PNG', 'Export 6 PNGs', 'Esporta 6 PNG', 'Eksporter 6 PNG'),
    'seed_label': ('Seed', 'Seed', 'Seed', 'Seed', 'Seed'),
    'samples_label': ('Samples', 'Образцов', 'Proben', 'Campioni', 'Prøver'),
    'min_agree_label': ('Min periods to agree', 'Минимум согласных периодов', 'Min. übereinstimmende Perioden', 'Periodi minimi concordi', 'Min. enige perioder'),
    'status_saved': ('Saved {filename}', 'Сохранено: {filename}', 'Gespeichert: {filename}', 'Salvato: {filename}', 'Gemt: {filename}'),
    'status_generating': ('Generating...', 'Генерация...', 'Generierung...', 'Generazione...', 'Genererer...'),
    'status_done_count': ('Done. {n} samples saved.', 'Готово. Сохранено образцов: {n}.', 'Fertig. {n} Proben gespeichert.', 'Fatto. {n} campioni salvati.', 'Færdig. {n} prøver gemt.'),
    'status_progress': ('[{done}/{total}] {filename}', '[{done}/{total}] {filename}', '[{done}/{total}] {filename}', '[{done}/{total}] {filename}', '[{done}/{total}] {filename}'),
    'error_bad_input_int': (
        'Cell size must be an integer.',
        'Размер ячейки должен быть целым числом.',
        'Zellgröße muss eine Ganzzahl sein.',
        'La dimensione cella deve essere un intero.',
        'Cellestørrelse skal være et heltal.',
    ),
    'error_bad_input_int_title': ('Bad input', 'Неверный ввод', 'Ungültige Eingabe', 'Input non valido', 'Ugyldigt input'),
    'error_bad_layout': ('Pick a valid layout.', 'Выберите корректную сетку.', 'Wählen Sie ein gültiges Layout.', 'Selezionare un layout valido.', 'Vælg et gyldigt layout.'),
    'error_bad_layout_title': ('Bad layout', 'Неверная сетка', 'Ungültiges Layout', 'Layout non valido', 'Ugyldigt layout'),
    'error_folder_missing': ('Folder does not exist yet.', 'Папка ещё не существует.', 'Ordner existiert noch nicht.', 'La cartella non esiste ancora.', 'Mappen findes ikke endnu.'),
    'error_folder_missing_title': ('Not yet', 'Пока нет', 'Noch nicht', 'Non ancora', 'Ikke endnu'),
    'swatch_slash': ('/ slash', '/ слеш', '/ Schrägstrich', '/ barra', '/ skråstreg'),
    'swatch_dash': ('— dash', '— тире', '— Bindestrich', '— trattino', '— bindestreg'),
    'swatch_dot': ('• dot', '• точка', '• Punkt', '• punto', '• prik'),
    'swatch_unknown_black': ('unknown (black)', 'неизвестно (чёрное)', 'unbekannt (schwarz)', 'sconosciuto (nero)', 'ukendt (sort)'),
    'swatch_no_agreement': ('no agreement (black)', 'нет согласия (чёрное)', 'keine Übereinstimmung (schwarz)', 'nessun accordo (nero)', 'ingen enighed (sort)'),
    'swatch_conf': ('conf {value}', 'conf {value}', 'Konf. {value}', 'conf {value}', 'konf {value}'),
    'swatch_known_grey': ('known (grey)', 'известное (серое)', 'bekannt (grau)', 'noto (grigio)', 'kendt (grå)'),
    'swatch_hard_low': ('hard (< 0.55 conf)', 'сложное (< 0.55 conf)', 'schwer (< 0.55 Konf.)', 'difficile (< 0.55 conf)', 'svær (< 0.55 konf)'),
    'swatch_known': ('known', 'известное', 'bekannt', 'noto', 'kendt'),
    'swatch_predicted_ok': ('predicted (≥ 0.55)', 'предсказание (≥ 0.55)', 'vorhergesagt (≥ 0.55)', 'previsto (≥ 0.55)', 'forudsagt (≥ 0.55)'),
    'legend_note_blend': ('cells fade toward white by (1 − confidence)', 'ячейки выцветают к белому по (1 − confidence)', 'Zellen verblassen zu Weiß nach (1 − Konfidenz)', 'le celle sfumano verso il bianco per (1 − confidenza)', 'celler falmer mod hvidt efter (1 − konfidens)'),
    'stats_known': ('known', 'известно', 'bekannt', 'noti', 'kendte'),
    'stats_predicted': ('predicted', 'предсказано', 'vorhergesagt', 'previsti', 'forudsagte'),
    'stats_mean': ('mean', 'среднее', 'Mittel', 'media', 'middel'),
    'stats_hard_lt': ('hard<.55', 'сложных<.55', 'schwer<.55', 'difficili<.55', 'svære<.55'),
    'stats_slash': ('slash', 'слеш', 'Schrägstr.', 'barra', 'skråstreg'),
    'stats_dash': ('dash', 'тире', 'Bindestr.', 'trattino', 'bindestreg'),
    'stats_dot': ('dot', 'точка', 'Punkt', 'punto', 'prik'),
    'stats_unknown': ('unknown', 'неизв.', 'unbek.', 'sconosc.', 'ukendt'),
    'stats_chains': ('chains', 'цепочек', 'Ketten', 'catene', 'kæder'),
    'stats_hard': ('hard', 'сложных', 'schwer', 'difficili', 'svære'),
    'tail_prediction_numbers': ('cells fade by (1 − conf)', 'ячейки сглажены по (1 − conf)', 'Zellen verblassen nach (1 − Konf.)', 'celle sfumate per (1 − conf)', 'celler falmer efter (1 − konf)'),
    'tail_heatmap_numbers': ('residue # on every cell', 'номер на каждой ячейке', 'Nummer auf jeder Zelle', 'numero su ogni cella', 'nummer på hver celle'),
    'tail_hard_numbers': ('# on hard cells', 'номера на сложных ячейках', 'Nummern auf schweren Zellen', 'numeri sulle celle difficili', 'numre på svære celler'),
    'controls_status_known_only': ('65 cells rendered, 43 black', '65 ячеек отрисовано, 43 чёрных', '65 Zellen gerendert, 43 schwarz', '65 celle disegnate, 43 nere', '65 celler tegnet, 43 sorte'),
    'controls_status_pattern_mod54': ('Empirical ceiling: 84.6% accuracy', 'Эмпирический потолок: 84.6% точности', 'Empirisches Maximum: 84,6% Genauigkeit', 'Limite empirico: 84,6% di accuratezza', 'Empirisk loft: 84,6% nøjagtighed'),
    'controls_status_multi_period': ('   Default = 2. Cells below threshold stay BLACK.', '   По умолчанию = 2. Ячейки ниже порога остаются ЧЁРНЫМИ.', '   Standard = 2. Zellen unter der Schwelle bleiben SCHWARZ.', '   Default = 2. Le celle sotto la soglia restano NERE.', '   Standard = 2. Celler under tærsklen forbliver SORTE.'),
    'controls_status_export_bundle': ('   Saves known + mod54 + multi(2,3) + random(1,2) to output folder.', '   Сохраняет known + mod54 + multi(2,3) + random(1,2) в папку вывода.', '   Speichert known + mod54 + multi(2,3) + random(1,2) im Ausgabeordner.', '   Salva known + mod54 + multi(2,3) + random(1,2) nella cartella di output.', '   Gemmer known + mod54 + multi(2,3) + random(1,2) i outputmappen.'),
    'tab_known_only_card_title': ('Known cells', 'Известные ячейки', 'Bekannte Zellen', 'Celle note', 'Kendte felter'),
    'tab_known_only_card_subtitle': ('65 confirmed stickers', '65 подтверждённых стикеров', '65 bestätigte Sticker', '65 sticker confermati', '65 bekræftede klistermaerker'),
    'tab_known_only_big_title': ('Known cells only', 'Только известные ячейки', 'Nur bekannte Zellen', 'Solo celle note', 'Kun kendte felter'),
    'tab_known_only_description': (
        'Renders the 65 unique residues confirmed by community-collected stickers. 81 stickers have been physically collected; some share the same residue (production has 6 copies per residue), so they collapse to 65 unique cells. The remaining 43 residues stay BLACK.',
        'Отображает 65 уникальных ячеек, подтверждённых найденными в сообществе стикерами. Всего собран 81 стикер, но некоторые относятся к одной и той же ячейке (в производстве 6 копий каждой), поэтому остаётся 65 уникальных. 43 неразрешённые ячейки остаются ЧЁРНЫМИ.',
        'Rendert die 65 eindeutigen Zellen, die durch von der Community gesammelte Sticker bestätigt wurden. 81 Sticker wurden physisch gesammelt; einige teilen sich dieselbe Zelle (in der Produktion gibt es 6 Kopien pro Zelle), daher reduzieren sie sich auf 65 eindeutige Zellen. Die verbleibenden 43 Zellen bleiben SCHWARZ.',
        'Disegna le 65 celle uniche confermate dagli sticker raccolti dalla community. Sono stati raccolti fisicamente 81 sticker; alcuni condividono la stessa cella (in produzione ci sono 6 copie per cella), quindi si riducono a 65 celle uniche. Le restanti 43 celle restano NERE.',
        'Viser de 65 unikke felter, der er bekræftet af klistermaerker indsamlet af fællesskabet. Der er fysisk indsamlet 81 klistermaerker; nogle deler samme felt (produktionen har 6 kopier pr. felt), så de reduceres til 65 unikke felter. De resterende 43 felter forbliver SORTE.',
    ),
    'tab_known_only_numbers_info': (
        "Numbers: residue # on every known cell when 'Show numbers' is on. Predicted/unknown cells stay blank (black).",
        'Номера: номер ячейки накладывается на каждую известную ячейку, если включена опция «Показать номера». Предсказанные/неизвестные ячейки не подписываются (чёрные).',
        'Nummern: Zellnummer wird auf jeder bekannten Zelle eingeblendet, wenn «Nummern anzeigen» aktiv ist. Vorhergesagte/unbekannte Zellen bleiben leer (schwarz).',
        'Numeri: il numero della cella appare su ogni cella nota quando «Mostra numeri» è attivo. Le celle previste/sconosciute restano vuote (nere).',
        'Numre: feltnummeret vises på hvert kendt felt, når «Vis numre» er aktiveret. Forudsagte/ukendte felter forbliver tomme (sorte).',
    ),
    'tab_pattern_mod54_card_title': ('Pattern · mod 54', 'Шаблон · mod 54', 'Muster · mod 54', 'Pattern · mod 54', 'Mønster · mod 54'),
    'tab_pattern_mod54_card_subtitle': ('Deterministic baseline', 'Детерминированная база', 'Deterministische Basis', 'Base deterministica', 'Deterministisk basis'),
    'tab_pattern_mod54_big_title': (
        'Pattern · mod 54 majority vote',
        'Шаблон · голосование по mod 54',
        'Muster · Mehrheitsentscheid mod 54',
        'Pattern · voto di maggioranza mod 54',
        'Mønster · flertalsafstemning mod 54',
    ),
    'tab_pattern_mod54_description': (
        'Single-feature baseline. For each unknown residue, take the symbol from partners at distance 54 and pick the majority. One period only — no row/column features, no confidence. Ceiling: 84.6% accuracy.',
        'Базовая модель из одного признака. Для каждой неизвестной ячейки берётся символ партнёра на расстоянии 54 и выбирается мажоритарный. Один период, без признаков строки/столбца, без уверенности. Потолок: 84.6% точности.',
        'Einzelmerkmal-Basis. Für jede unbekannte Zelle nimm das Symbol der Partner im Abstand 54 und wähle die Mehrheit. Nur eine Periode — keine Zeilen-/Spaltenmerkmale, keine Konfidenz. Maximum: 84,6% Genauigkeit.',
        'Base a singolo tratto. Per ogni cella sconosciuta, prendi il simbolo dei partner a distanza 54 e scegli la maggioranza. Un solo periodo — nessuna caratteristica di riga/colonna, nessuna confidenza. Limite: 84,6% di accuratezza.',
        'En-feature basis. For hvert ukendt felt tages symbolet fra partnere i afstand 54 og flertallet vælges. Kun én periode — ingen række-/kolonne-features, ingen konfidens. Loft: 84,6% nøjagtighed.',
    ),
    'tab_pattern_mod54_numbers_info': (
        "Numbers: 'Show numbers' overlays residue # on known cells. Predicted cells are not labelled.",
        'Номера: опция «Показать номера» накладывает номер ячейки на известные. Предсказанные не подписываются.',
        'Nummern: «Nummern anzeigen» blendet die Zellnummer auf bekannten Zellen ein. Vorhergesagte Zellen werden nicht beschriftet.',
        'Numeri: «Mostra numeri» sovrappone il numero della cella su quelle note. Le celle previste non sono etichettate.',
        'Numre: «Vis numre» lægger feltnummeret oven på kendte felter. Forudsagte felter er ikke mærket.',
    ),
    'tab_multi_period_card_title': ('Multi-period vote', 'Многопериодное голосование', 'Mehrperioden-Abstimmung', 'Voto multi-periodo', 'Multi-periode afstemning'),
    'tab_multi_period_card_subtitle': ('8 periods, threshold', '8 периодов, порог', '8 Perioden, Schwelle', '8 periodi, soglia', '8 perioder, tærskel'),
    'tab_multi_period_big_title': ('Multi-period agreement vote', 'Голосование по 8 периодам', 'Mehrperioden-Konsensabstimmung', 'Voto di consenso multi-periodo', 'Multi-periode enighedsafstemning'),
    'tab_multi_period_description': (
        'Voting across 8 partner-periods (54, 36, 27, 18, 12, 9, 6, 4). A cell is filled only when at least N periods agree on the same class; otherwise it stays BLACK. No row/column features, no confidence.',
        'Голосование по 8 партнёрским периодам (54, 36, 27, 18, 12, 9, 6, 4). Ячейка заполняется только если как минимум N периодов согласны на один класс; иначе она остаётся ЧЁРНОЙ. Без признаков строки/столбца, без уверенности.',
        'Abstimmung über 8 Partner-Perioden (54, 36, 27, 18, 12, 9, 6, 4). Eine Zelle wird nur gefüllt, wenn mindestens N Perioden derselben Klasse zustimmen; andernfalls bleibt sie SCHWARZ. Keine Zeilen-/Spaltenmerkmale, keine Konfidenz.',
        'Votazione su 8 periodi di partner (54, 36, 27, 18, 12, 9, 6, 4). Una cella viene riempita solo se almeno N periodi concordano sulla stessa classe; altrimenti resta NERA. Nessuna caratteristica di riga/colonna, nessuna confidenza.',
        'Afstemning over 8 partner-perioder (54, 36, 27, 18, 12, 9, 6, 4). Et felt udfyldes kun, hvis mindst N perioder er enige om samme klasse; ellers forbliver det SORT. Ingen række-/kolonne-features, ingen konfidens.',
    ),
    'tab_multi_period_numbers_info': (
        "Numbers: 'Show numbers' overlays residue # on known cells. Black cells = no period agreement; they stay unlabelled.",
        'Номера: «Показать номера» накладывает номер ячейки на известные. Чёрные ячейки = периоды не сошлись; они не подписаны.',
        'Nummern: «Nummern anzeigen» blendet die Zellnummer auf bekannten Zellen ein. Schwarze Zellen = keine Perioden-Übereinstimmung; nicht beschriftet.',
        'Numeri: «Mostra numeri» sovrappone il numero della cella su quelle note. Celle nere = nessun accordo tra periodi; non etichettate.',
        'Numre: «Vis numre» lægger feltnummeret oven på kendte felter. Sorte felter = ingen periodeenighed; ikke mærket.',
    ),
    'tab_random_sampler_card_title': ('Random sampler', 'Случайная выборка', 'Zufallsstichprobe', 'Campione casuale', 'Tilfældig prøve'),
    'tab_random_sampler_card_subtitle': ('Seeded zone-weighted', 'С seed, по зонам', 'Seed, zonengewichtet', 'Seed, pesato per zona', 'Seed, zonevejet'),
    'tab_random_sampler_big_title': ('Random zone-weighted sample', 'Случайная выборка по зональным весам', 'Zufallsstichprobe nach Zonengewichten', 'Campione casuale pesato per zona', 'Tilfældig zonevejet prøve'),
    'tab_random_sampler_description': (
        'Fills each unknown cell randomly using empirical zone weights. Same seed always produces the same grid; the Reroll button bumps the seed by one.',
        'Заполняет каждую неизвестную ячейку случайным символом по эмпирическим зональным весам. Один и тот же seed всегда даёт одну сетку; кнопка «Перебросить» увеличивает seed на 1.',
        'Füllt jede unbekannte Zelle zufällig nach empirischen Zonengewichten. Derselbe Seed erzeugt immer dasselbe Gitter; «Neu würfeln» erhöht den Seed um 1.',
        'Riempie ogni cella sconosciuta in modo casuale usando pesi empirici per zona. Lo stesso seed produce sempre la stessa griglia; il pulsante «Rilancia» incrementa il seed di 1.',
        'Udfylder hvert ukendt felt tilfældigt med empiriske zonevaegte. Samme seed giver altid samme gitter; knappen «Slå om» hæver seed med 1.',
    ),
    'tab_random_sampler_numbers_info': (
        "Numbers: 'Show numbers' overlays residue # on known cells. Random fills are not labelled.",
        'Номера: «Показать номера» накладывает номер на известные. Случайные заполнения не подписаны.',
        'Nummern: «Nummern anzeigen» blendet die Nummer auf bekannten Zellen ein. Zufällige Füllungen werden nicht beschriftet.',
        'Numeri: «Mostra numeri» sovrappone il numero su quelle note. I riempimenti casuali non sono etichettati.',
        'Numre: «Vis numre» lægger nummeret oven på kendte. Tilfældige udfyldninger er ikke mærket.',
    ),
    'tab_export_bundle_card_title': ('Export bundle', 'Экспорт набора', 'Export-Paket', 'Bundle di esportazione', 'Eksport-pakke'),
    'tab_export_bundle_card_subtitle': ('All modes, one click', 'Все режимы за раз', 'Alle Modi, ein Klick', 'Tutti i modi, un clic', 'Alle modi, ét klik'),
    'tab_export_bundle_big_title': ('Export bundle · 6 PNGs', 'Экспорт набора · 6 PNG', 'Export-Paket · 6 PNGs', 'Bundle di esportazione · 6 PNG', 'Eksport-pakke · 6 PNG'),
    'tab_export_bundle_description': (
        'One-click export of every static mode: known-only, mod54, multi-period (min agree 2 and 3), and two random samples (seeds 1 and 2). 6 PNGs saved to the output folder.',
        'Однокликовый экспорт всех статичных режимов: только известные, mod54, многопериодные (min agree 2 и 3), и два случайных образца (seed 1 и 2). 6 PNG в папку вывода.',
        'Ein-Klick-Export jedes statischen Modus: known-only, mod54, multi-period (min agree 2 und 3) und zwei Zufallsstichproben (Seeds 1 und 2). 6 PNGs werden im Ausgabeordner gespeichert.',
        'Esportazione con un clic di ogni modalità statica: known-only, mod54, multi-period (min agree 2 e 3) e due campioni casuali (seed 1 e 2). 6 PNG salvati nella cartella di output.',
        'Eksport af hver statisk modus med ét klik: known-only, mod54, multi-period (min agree 2 og 3) og to tilfældige prøver (seed 1 og 2). 6 PNG gemmes i outputmappen.',
    ),
    'tab_export_bundle_numbers_info': (
        'Saved PNGs have no labels overlaid — they are raw 108-cell grids.',
        'Сохранённые PNG не содержат наложений — это голые сетки 108 ячеек.',
        'Gespeicherte PNGs haben keine Beschriftungen — reine 108-Zellen-Gitter.',
        'I PNG salvati non hanno etichette sovrapposte — sono griglie pure di 108 celle.',
        'Gemte PNG har ingen overlejringer — de er rene 108-felts gitre.',
    ),
    'tab_prediction_zoned_card_title': ('Prediction · zoned', 'Предсказание · зональное', 'Vorhersage · zonal', 'Previsione · zonale', 'Forudsigelse · zonal'),
    'tab_prediction_zoned_card_subtitle': ('Zone-aware, primary', 'Зональное, основное', 'Zonenbewusst, primär', 'Consapevole della zona, primaria', 'Zonebevidst, primær'),
    'tab_prediction_zoned_big_title': (
        'Prediction · zone-restricted (primary)',
        'Предсказание · ограничено зоной (основное)',
        'Vorhersage · zonenbeschränkt (primär)',
        'Previsione · ristretta alla zona (primaria)',
        'Forudsigelse · begrænset til zone (primær)',
    ),
    'tab_prediction_zoned_description': (
        "Production model. Partner-vote across 8 periods + row + column features, restricted to the unknown's own zone (TOP-only or BOTTOM-only partners). Outputs a per-cell confidence; cells fade toward white by (1 − confidence).",
        'Боевая модель. Голосование партнёров по 8 периодам + признаки строки + столбца, ограничено собственной зоной неизвестной ячейки (партнёры только из TOP или только из BOTTOM). На выходе — уверенность для каждой ячейки; ячейки выцветают к белому по (1 − confidence).',
        'Produktionsmodell. Partner-Abstimmung über 8 Perioden + Zeilen- + Spaltenmerkmale, beschränkt auf die eigene Zone der Unbekannten (nur TOP- oder nur BOTTOM-Partner). Gibt eine Pro-Zelle-Konfidenz aus; Zellen verblassen zu Weiß nach (1 − Konfidenz).',
        'Modello di produzione. Voto dei partner su 8 periodi + caratteristiche di riga + colonna, ristretto alla zona della cella sconosciuta (solo partner TOP o solo BOTTOM). Restituisce una confidenza per cella; le celle sfumano verso il bianco per (1 − confidenza).',
        'Produktionsmodel. Partner-afstemning over 8 perioder + række- + kolonne-features, begrænset til det ukendte felts egen zone (kun TOP- eller kun BOTTOM-partnere). Giver en konfidens pr. felt; celler falmer mod hvidt efter (1 − konfidens).',
    ),
    'tab_prediction_zoned_numbers_info': (
        "Numbers: 'Show numbers' overlays residue # on known cells. Predicted cells are coloured by (1 − confidence).",
        'Номера: «Показать номера» накладывает номер на известные. Предсказанные окрашены по (1 − confidence).',
        'Nummern: «Nummern anzeigen» blendet die Nummer auf bekannten Zellen ein. Vorhergesagte Zellen werden nach (1 − Konfidenz) eingefärbt.',
        'Numeri: «Mostra numeri» sovrappone il numero alle celle note. Le celle previste sono colorate per (1 − confidenza).',
        'Numre: «Vis numre» lægger nummeret oven på kendte. Forudsagte felter farves efter (1 − konfidens).',
    ),
    'tab_prediction_cross_card_title': ('Prediction · cross', 'Предсказание · кросс', 'Vorhersage · cross', 'Previsione · cross', 'Forudsigelse · cross'),
    'tab_prediction_cross_card_subtitle': ('Cross-zone, biased', 'Межзональное, со смещением', 'Zonenübergreifend, verzerrt', 'Tra zone, distorto', 'Cross-zone, forvrænget'),
    'tab_prediction_cross_big_title': (
        'Prediction · cross-zone (audit only)',
        'Предсказание · межзональное (только аудит)',
        'Vorhersage · zonenübergreifend (nur Audit)',
        'Previsione · tra zone (solo audit)',
        'Forudsigelse · cross-zone (kun audit)',
    ),
    'tab_prediction_cross_description': (
        'Audit-only twin of the production model. Partners pulled from BOTH zones — BOTTOM cells suffer a Y-blackout bias (cross-zone partners vote R, then R gets masked, inflating G). Useful for diff against zoned; not for downstream.',
        'Альтернативная модель — партнёры берутся из ОБЕИХ зон. Ячейки BOTTOM страдают от Y-blackout bias: межзональные партнёры могут проголосовать R, потом R маскируется, инфлирует G. Полезно для diff против зональной; не для боевого использования.',
        'Audit-Zwilling des Produktionsmodells. Partner aus BEIDEN Zonen — BOTTOM-Zellen leiden unter einem Y-Blackout-Bias (zonenübergreifende Partner wählen R, dann wird R maskiert, was G aufbläht). Nützlich für Diff gegen zoned; nicht für Downstream.',
        'Gemello di sola revisione del modello di produzione. Partner presi da ENTRAMBE le zone — le celle BOTTOM soffrono di un bias di Y-blackout (i partner cross-zone votano R, poi R viene mascherato, gonfiando G). Utile per il diff contro zoned; non per uso downstream.',
        'Audit-tvilling af produktionsmodellen. Partnere fra BEGGE zoner — BOTTOM-felter lider af en Y-blackout bias (cross-zone partnere stemmer R, derefter maskeres R, hvilket oppuster G). Núttig til diff mod zoned; ikke til downstream.',
    ),
    'tab_prediction_cross_numbers_info': (
        "Numbers: 'Show numbers' overlays residue # on known cells. Same blend rule as zoned.",
        'Номера: «Показать номера» накладывает номер на известные. Те же правила сглаживания, что и в зональной модели.',
        'Nummern: «Nummern anzeigen» blendet die Nummer auf bekannten Zellen ein. Dieselbe Verblassen-Regel wie zoned.',
        'Numeri: «Mostra numeri» sovrappone il numero alle celle note. Stessa regola di sfumatura di zoned.',
        'Numre: «Vis numre» lægger nummeret oven på kendte. Samme falmeregel som zoned.',
    ),
    'tab_confidence_heatmap_card_title': ('Confidence heatmap', 'Тепловая карта', 'Konfidenz-Heatmap', 'Heatmap di confidenza', 'Konfidens-heatmap'),
    'tab_confidence_heatmap_card_subtitle': ('Red → green by conf', 'Красный → зелёный по conf', 'Rot → Grün nach Konf.', 'Rosso → verde per conf.', 'Rød → grøn efter konf.'),
    'tab_confidence_heatmap_big_title': (
        'Zoned-prediction confidence heatmap',
        'Тепловая карта уверенности (зональная)',
        'Heatmap der zonalen Vorhersage-Konfidenz',
        'Heatmap di confidenza della previsione zonale',
        'Konfidens-heatmap af zonal forudsigelse',
    ),
    'tab_confidence_heatmap_description': (
        'Recolours every predicted cell red → orange → yellow → green by its zoned confidence (the value used in the proof_stickers.md targeting). Known cells appear as light grey with a black border for contrast.',
        'Перекрашивает каждую предсказанную ячейку красный → оранжевый → жёлтый → зелёный по уверенности зональной модели (это значение используется в proof_stickers.md для приоритизации). Известные ячейки — светло-серые с чёрной обводкой.',
        'Färbt jede vorhergesagte Zelle rot → orange → gelb → grün nach der zonalen Konfidenz um (dieser Wert wird im proof_stickers.md-Targeting verwendet). Bekannte Zellen erscheinen hellgrau mit schwarzem Rand zum Kontrast.',
        'Ricolora ogni cella prevista rosso → arancione → giallo → verde in base alla confidenza zonale (il valore usato nel targeting di proof_stickers.md). Le celle note appaiono grigio chiaro con bordo nero per contrasto.',
        'Farver hvert forudsagt felt rød → orange → gul → grøn efter zonal konfidens (den værdi der bruges i proof_stickers.md). Kendte felter er lysegrå med sort kant for kontrast.',
    ),
    'tab_confidence_heatmap_numbers_info': (
        "Numbers: residue # is always overlaid on every cell, regardless of the 'Show numbers' setting.",
        'Номера: номер ячейки накладывается ВСЕГДА, независимо от опции «Показать номера».',
        'Nummern: Zellnummer wird IMMER auf jeder Zelle eingeblendet, unabhängig von «Nummern anzeigen».',
        'Numeri: il numero della cella appare SEMPRE su ogni cella, indipendentemente da «Mostra numeri».',
        'Numre: feltnummeret vises ALTID på hvert felt, uanset «Vis numre».',
    ),
    'tab_hard_residues_card_title': ('Hard residues', 'Сложные ячейки', 'Schwere Zellen', 'Celle difficili', 'Svære felter'),
    'tab_hard_residues_card_subtitle': ('Below 0.55 confidence', 'Уверенность ниже 0.55', 'Konfidenz unter 0.55', 'Confidenza sotto 0.55', 'Konfidens under 0.55'),
    'tab_hard_residues_big_title': (
        'Hard residues · proof-sticker targets',
        'Сложные ячейки · цели для подтверждения',
        'Schwere Zellen · Proof-Sticker-Ziele',
        'Celle difficili · obiettivi proof-sticker',
        'Svære felter · proof-sticker mål',
    ),
    'tab_hard_residues_description': (
        'The N residues with zoned confidence below 0.55 — the proof-sticker targeting set. Each maps to 6 chain numbers in the 648-cell production sequence. Listed in reports/proof_stickers.md as community-confirmation targets.',
        'Резидуумы с зональной уверенностью ниже 0.55 — приоритетный набор для подтверждения сообществом. Каждая отображается в 6 цепочковых номерах в производственной последовательности из 648. Список в reports/proof_stickers.md.',
        'Die N Zellen mit zonaler Konfidenz unter 0,55 — das Proof-Sticker-Zielset. Jede entspricht 6 Kettennummern in der 648er-Produktionssequenz. Aufgelistet in reports/proof_stickers.md als Community-Bestätigungsziele.',
        'Le N celle con confidenza zonale sotto 0,55 — il set di proof-sticker. Ognuna corrisponde a 6 numeri di catena nella sequenza di produzione da 648. Elencati in reports/proof_stickers.md come obiettivi di conferma per la community.',
        'De N felter med zonal konfidens under 0,55 — proof-sticker målsættet. Hvert svarer til 6 kædenumre i 648-produktionssekvensen. Listet i reports/proof_stickers.md som bekræftelsesmål for fællesskabet.',
    ),
    'tab_hard_residues_numbers_info': (
        "Numbers: residue # is always overlaid on every hard (magenta) cell. 'Show numbers' adds residue # on dim grey known cells.",
        'Номера: номер ячейки ВСЕГДА накладывается на каждую сложную (мадженту) ячейку. «Показать номера» добавит номер на серые известные ячейки.',
        'Nummern: Zellnummer wird IMMER auf jeder schweren (Magenta-) Zelle eingeblendet. «Nummern anzeigen» fügt die Nummer auf dunkelgrauen bekannten Zellen hinzu.',
        'Numeri: il numero della cella appare SEMPRE su ogni cella difficile (magenta). «Mostra numeri» aggiunge il numero sulle celle note grigio scuro.',
        'Numre: feltnummeret vises ALTID på hvert svært (magenta) felt. «Vis numre» tilføjer numre på mørkegrå kendte felter.',
    ),
}

I18N: dict[str, dict[str, str]] = {
    lang: {k: vals[i] for k, vals in _I18N_DATA.items()}
    for i, lang in enumerate(LANGS)
}


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


def _contrast_text_color(hex_color):
    if not hex_color or not hex_color.startswith('#') or len(hex_color) < 7:
        return '#222222'
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    L = 0.299 * r + 0.587 * g + 0.114 * b
    return '#000000' if L > 140 else '#f0f0f0'


def count_stickers_found():
    try:
        if not STICKER_DIR.exists():
            return STICKERS_FOUND_FALLBACK
        seen = set()
        for f in STICKER_DIR.iterdir():
            if (f.is_file() and f.stem.isdigit()
                    and f.suffix.lower() in ('.jpg', '.jpeg', '.png')):
                seen.add(f.stem)
        for sub in ('slesh', 'dash', 'dot'):
            d = STICKER_DIR / 'resized' / sub
            if not d.exists():
                continue
            for f in d.iterdir():
                if (f.is_file() and f.stem.isdigit()
                        and f.suffix.lower() in ('.jpg', '.jpeg', '.png')):
                    seen.add(f.stem)
        return len(seen) if seen else STICKERS_FOUND_FALLBACK
    except Exception:
        return STICKERS_FOUND_FALLBACK


def chains_for(residue):
    if residue == 0:
        return [108 * (k + 1) for k in range(6)]
    return [residue + 108 * k for k in range(6)]


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


def _overlay_numbers(img, rows, cols, cell_px, labels, bg_lookup):
    if not labels or cell_px < 12:
        return
    draw = ImageDraw.Draw(img)
    size = max(9, int(round(cell_px * 0.34)))
    try:
        font = ImageFont.truetype('arial.ttf', size)
    except OSError:
        try:
            font = ImageFont.truetype('DejaVuSans.ttf', size)
        except OSError:
            font = ImageFont.load_default()
    for k, text in labels.items():
        if k >= rows * cols:
            continue
        r, c = k // cols, k % cols
        bg = bg_lookup(k)
        L = 0.299 * bg[0] + 0.587 * bg[1] + 0.114 * bg[2]
        fg = (0, 0, 0) if L > 140 else (255, 255, 255)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        cx = c * cell_px + cell_px // 2
        cy = r * cell_px + cell_px // 2
        draw.text((cx - tw // 2, cy - th // 2 - bbox[1]),
                  text, fill=fg, font=font)


def make_grid_image(cells, rows, cols, cell_px, labels=None):
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
    _overlay_numbers(img, rows, cols, cell_px, labels,
                     bg_lookup=lambda k: CMAP[cells[k]])
    return img


def make_grid_image_rgb(rgb_cells, rows, cols, cell_px, labels=None):
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
    _overlay_numbers(img, rows, cols, cell_px, labels,
                     bg_lookup=lambda k: rgb_cells[k])
    return img


def render(cells, rows, cols, cell_px, path):
    make_grid_image(cells, rows, cols, cell_px).save(path, dpi=(300, 300))


def render_rgb(rgb_cells, rows, cols, cell_px, path):
    make_grid_image_rgb(rgb_cells, rows, cols, cell_px).save(path, dpi=(300, 300))


def _load_fonts_sized(title_px, legend_px):
    title_font = legend_font = None
    for name in ('arial.ttf', 'Arial.ttf', 'segoeui.ttf', 'DejaVuSans.ttf'):
        try:
            title_font = ImageFont.truetype(name, title_px)
            legend_font = ImageFont.truetype(name, legend_px)
            break
        except OSError:
            continue
    if title_font is None:
        title_font = ImageFont.load_default()
        legend_font = ImageFont.load_default()
    return title_font, legend_font


def render_with_legend(grid_img, legend_items, title, subtitle, path, cell_px):
    gw, gh = grid_img.size
    title_px = max(16, int(round(cell_px * 0.55)))
    sub_px = max(11, int(round(cell_px * 0.32)))
    legend_px = max(11, int(round(cell_px * 0.36)))
    swatch = max(18, int(round(cell_px * 0.85)))
    pad = max(28, int(round(cell_px * 0.85)))
    title_to_grid_gap = max(18, int(round(cell_px * 0.5)))
    grid_to_legend_gap = max(20, int(round(cell_px * 0.6)))
    title_to_sub_gap = max(6, int(round(cell_px * 0.15)))
    item_gap = max(18, int(round(cell_px * 0.55)))
    label_gap = max(8, int(round(cell_px * 0.2)))
    border = max(1, int(round(cell_px * 0.05)))
    title_font, legend_font = _load_fonts_sized(title_px, legend_px)
    sub_font = legend_font if abs(sub_px - legend_px) < 2 else (
        _load_fonts_sized(sub_px, sub_px)[1])
    tmp_draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    tb = tmp_draw.textbbox((0, 0), title, font=title_font)
    title_h = tb[3] - tb[1]
    sub_h = 0
    if subtitle:
        sb = tmp_draw.textbbox((0, 0), subtitle, font=sub_font)
        sub_h = sb[3] - sb[1]
    total_title_h = title_h + (title_to_sub_gap + sub_h if subtitle else 0)
    items_w = []
    for color_hex, label in legend_items:
        bbox = tmp_draw.textbbox((0, 0), label, font=legend_font)
        items_w.append(swatch + label_gap + (bbox[2] - bbox[0]))
    legend_total_w = (sum(items_w) + item_gap * (len(legend_items) - 1)
                      if legend_items else 0)
    canvas_w = max(gw + 2 * pad, legend_total_w + 2 * pad)
    canvas_h = (pad + total_title_h + title_to_grid_gap + gh
                + grid_to_legend_gap + swatch + pad)
    img = Image.new('RGB', (canvas_w, canvas_h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    cur_y = pad
    tb = draw.textbbox((0, 0), title, font=title_font)
    tw = tb[2] - tb[0]
    draw.text(((canvas_w - tw) // 2, cur_y - tb[1]),
              title, fill=(20, 20, 30), font=title_font)
    cur_y += title_h
    if subtitle:
        cur_y += title_to_sub_gap
        sb = draw.textbbox((0, 0), subtitle, font=sub_font)
        sw = sb[2] - sb[0]
        draw.text(((canvas_w - sw) // 2, cur_y - sb[1]),
                  subtitle, fill=(90, 90, 110), font=sub_font)
        cur_y += sub_h
    cur_y += title_to_grid_gap
    gx = (canvas_w - gw) // 2
    gy = cur_y
    draw.rectangle([gx - border, gy - border,
                    gx + gw + border, gy + gh + border],
                   outline=(120, 120, 130), width=border)
    img.paste(grid_img, (gx, gy))
    cur_y = gy + gh + grid_to_legend_gap
    lx = (canvas_w - legend_total_w) // 2
    swatch_border = max(1, border // 2)
    for (color_hex, label), w in zip(legend_items, items_w):
        draw.rectangle([lx, cur_y, lx + swatch, cur_y + swatch],
                       fill=color_hex, outline=(40, 40, 50), width=swatch_border)
        bbox = draw.textbbox((0, 0), label, font=legend_font)
        th = bbox[3] - bbox[1]
        draw.text((lx + swatch + label_gap,
                   cur_y + (swatch - th) // 2 - bbox[1]),
                  label, fill=(20, 20, 30), font=legend_font)
        lx += w + item_gap
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
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.lang: str = DEFAULT_LANG
        self._tr_widgets: list = []
        self._lang_buttons: dict = {}
        self._title_label: tk.Label | None = None
        self._restore_binding = None
        self._drag_x = 0
        self._drag_y = 0
        self._resize_w0 = 0
        self._resize_h0 = 0
        self._resize_x0 = 0
        self._resize_y0 = 0

        root.title(self.tr('app_title'))
        root.overrideredirect(True)
        root.geometry('980x920+50+30')
        root.configure(bg=BG_BASE)

        self._init_styles()

        self.layout_var = tk.StringVar(value='9x12')
        self.cell_var = tk.StringVar(value='64')
        _script_dir = Path(__file__).resolve().parent
        self.out_var = tk.StringVar(value=str(_script_dir / 'samples'))
        self.seed_var = tk.StringVar(value='1')
        self.count_var = tk.StringVar(value='6')
        self.agree_var = tk.StringVar(value='2')
        self.show_numbers_var = tk.BooleanVar(value=False)
        self.show_glyphs_var = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar(value=self.tr('ready_status'))
        self.preview_stats = tk.StringVar(value='')
        self.pill_line1_var = tk.StringVar(value='')
        self.pill_line2_var = tk.StringVar(value='')

        self.active_tab = TAB_KEYS[0]
        self.sidebar_cards: dict = {}
        self._preview_after_id = None

        self._build_title_bar(root)
        self._build_header(root)
        self._build_settings_ribbon(root)
        self._build_bottom_bar(root)
        self._build_body(root)
        self._build_resize_grip(root)

        self._update_header_pill()
        self._select_tab(self.active_tab)

    def tr(self, key: str, **kwargs) -> str:
        lang = getattr(self, 'lang', DEFAULT_LANG)
        table = I18N.get(lang, I18N[DEFAULT_LANG])
        template = table.get(key) or I18N[DEFAULT_LANG].get(key, key)
        if kwargs:
            try:
                return template.format(**kwargs)
            except (KeyError, IndexError):
                return template
        return template

    def _add_tr(self, widget: tk.Widget, key: str, **kwargs) -> None:
        self._tr_widgets.append((widget, key, kwargs))
        widget.configure(text=self.tr(key, **kwargs))

    def _set_language(self, lang: str) -> None:
        if lang not in I18N or lang == self.lang:
            return
        self.lang = lang
        for widget, key, kwargs in self._tr_widgets:
            try:
                widget.configure(text=self.tr(key, **kwargs))
            except tk.TclError:
                pass
        try:
            self.root.title(self.tr('app_title'))
        except tk.TclError:
            pass
        if self._title_label is not None:
            self._title_label.configure(text=self.tr('app_title'))
        self.status_var.set(self.tr('ready_status'))
        self._rebuild_sidebar_labels()
        self._refresh_preview_label()
        self._update_header_pill()
        self._select_tab(self.active_tab)
        for code, btn in self._lang_buttons.items():
            active = (code == lang)
            btn.configure(bg=ACCENT if active else BG_PANEL,
                          fg='white' if active else TEXT_SECONDARY)

    def _build_title_bar(self, parent: tk.Misc) -> None:
        self.title_bar = tk.Frame(parent, bg=BG_PANEL, height=36)
        self.title_bar.pack(side='top', fill='x')
        self.title_bar.pack_propagate(False)

        logo_wrap = tk.Frame(self.title_bar, bg=BG_PANEL, cursor='fleur')
        logo_wrap.pack(side='left', padx=(10, 0))

        logo_sq = tk.Frame(logo_wrap, bg=ACCENT, width=22, height=22,
                           cursor='fleur')
        logo_sq.pack(side='left', pady=7)
        logo_sq.pack_propagate(False)

        self._title_label = tk.Label(logo_wrap, text=self.tr('app_title'),
                                     font=('Segoe UI', 10, 'bold'),
                                     bg=BG_PANEL, fg=TEXT_PRIMARY,
                                     cursor='fleur')
        self._title_label.pack(side='left', padx=(10, 0))

        ctrl_frame = tk.Frame(self.title_bar, bg=BG_PANEL)
        ctrl_frame.pack(side='right')

        close_btn = tk.Label(ctrl_frame, text='✕',
                             bg=BG_PANEL, fg=TEXT_PRIMARY,
                             font=('Segoe UI', 11),
                             width=4, height=2, cursor='hand2')
        close_btn.pack(side='right')
        close_btn.bind('<Enter>',
                       lambda e: close_btn.configure(bg='#c83838', fg='white'))
        close_btn.bind('<Leave>',
                       lambda e: close_btn.configure(bg=BG_PANEL,
                                                     fg=TEXT_PRIMARY))
        close_btn.bind('<Button-1>', lambda e: self.root.destroy())

        min_btn = tk.Label(ctrl_frame, text='–',
                           bg=BG_PANEL, fg=TEXT_PRIMARY,
                           font=('Segoe UI', 11),
                           width=4, height=2, cursor='hand2')
        min_btn.pack(side='right')
        min_btn.bind('<Enter>',
                     lambda e: min_btn.configure(bg=BG_HOVER))
        min_btn.bind('<Leave>',
                     lambda e: min_btn.configure(bg=BG_PANEL))
        min_btn.bind('<Button-1>', lambda e: self._minimize())

        lang_frame = tk.Frame(ctrl_frame, bg=BG_PANEL)
        lang_frame.pack(side='right', padx=(0, 14))
        for code in LANGS:
            btn = tk.Label(lang_frame, text=code.upper(),
                           bg=BG_PANEL,
                           fg=TEXT_SECONDARY,
                           font=('Segoe UI', 8, 'bold'),
                           width=4, height=2, cursor='hand2')
            btn.pack(side='left', padx=1)
            btn.bind('<Button-1>',
                     lambda e, c=code: self._set_language(c))

            def _enter(_e, b=btn, c=code):
                if c != self.lang:
                    b.configure(bg=BG_HOVER)

            def _leave(_e, b=btn, c=code):
                if c != self.lang:
                    b.configure(bg=BG_PANEL)

            btn.bind('<Enter>', _enter)
            btn.bind('<Leave>', _leave)
            self._lang_buttons[code] = btn
        active = self._lang_buttons[self.lang]
        active.configure(bg=ACCENT, fg='white')

        for w in (self.title_bar, logo_wrap, logo_sq, self._title_label):
            w.bind('<ButtonPress-1>', self._drag_start)
            w.bind('<B1-Motion>', self._drag_motion)

    def _drag_start(self, event) -> None:
        self._drag_x = event.x_root - self.root.winfo_x()
        self._drag_y = event.y_root - self.root.winfo_y()

    def _drag_motion(self, event) -> None:
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.root.geometry(f'+{x}+{y}')

    def _minimize(self) -> None:
        self.root.overrideredirect(False)
        try:
            self.root.iconify()
        except tk.TclError:
            self.root.overrideredirect(True)
            return
        self._restore_binding = self.root.bind('<Map>',
                                               self._on_restored, add='+')

    def _on_restored(self, event) -> None:
        if event.widget is self.root:
            self.root.overrideredirect(True)
            if self._restore_binding is not None:
                try:
                    self.root.unbind('<Map>', self._restore_binding)
                except tk.TclError:
                    pass
                self._restore_binding = None

    def _build_resize_grip(self, parent: tk.Misc) -> None:
        self.resize_grip = tk.Frame(parent, bg=BG_PANEL, width=16, height=16,
                                    cursor='size_nw_se')
        self.resize_grip.place(relx=1.0, rely=1.0, anchor='se')
        self.resize_grip.bind('<ButtonPress-1>', self._resize_start)
        self.resize_grip.bind('<B1-Motion>', self._resize_motion)

    def _resize_start(self, event) -> None:
        self._resize_w0 = self.root.winfo_width()
        self._resize_h0 = self.root.winfo_height()
        self._resize_x0 = event.x_root
        self._resize_y0 = event.y_root

    def _resize_motion(self, event) -> None:
        dx = event.x_root - self._resize_x0
        dy = event.y_root - self._resize_y0
        new_w = max(920, self._resize_w0 + dx)
        new_h = max(880, self._resize_h0 + dy)
        self.root.geometry(f'{new_w}x{new_h}')

    def _init_styles(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass
        style.configure('TFrame', background=BG_BASE)
        style.configure('TLabel', background=BG_BASE, foreground=TEXT_PRIMARY)
        for name in ('Ribbon.TCombobox', 'Ribbon.TSpinbox'):
            style.configure(name, fieldbackground=BG_INPUT, background=BG_INPUT,
                            foreground=TEXT_PRIMARY, bordercolor=BORDER_SUBTLE,
                            arrowcolor=TEXT_SECONDARY, lightcolor=BG_INPUT,
                            darkcolor=BG_INPUT, insertcolor=TEXT_PRIMARY)
        style.map('Ribbon.TCombobox',
                  fieldbackground=[('readonly', BG_INPUT)],
                  background=[('readonly', BG_INPUT)],
                  foreground=[('readonly', TEXT_PRIMARY)])
        style.configure('Ribbon.TEntry', fieldbackground=BG_INPUT,
                        foreground=TEXT_PRIMARY, bordercolor=BORDER_SUBTLE,
                        insertcolor=TEXT_PRIMARY, lightcolor=BG_INPUT,
                        darkcolor=BG_INPUT)
        style.configure('Accent.Horizontal.TProgressbar',
                        troughcolor=BG_PANEL, bordercolor=BG_PANEL,
                        background=ACCENT, lightcolor=ACCENT, darkcolor=ACCENT_DIM)

    def _build_header(self, parent: tk.Misc) -> None:
        header = tk.Frame(parent, bg=BG_BASE, height=78)
        header.pack(side='top', fill='x', padx=18, pady=(14, 0))
        header.pack_propagate(False)

        left = tk.Frame(header, bg=BG_BASE)
        left.pack(side='left', fill='y')
        self._hdr_title = tk.Label(left, text='',
                                   font=('Segoe UI', 16, 'bold'),
                                   bg=BG_BASE, fg=TEXT_PRIMARY, anchor='w')
        self._hdr_title.pack(anchor='w')
        self._add_tr(self._hdr_title, 'app_title')
        self._hdr_subtitle = tk.Label(left, text='',
                                      font=('Segoe UI', 9),
                                      bg=BG_BASE, fg=TEXT_SECONDARY, anchor='w')
        self._hdr_subtitle.pack(anchor='w', pady=(2, 0))
        self._add_tr(self._hdr_subtitle, 'app_subtitle')

        pill = tk.Frame(header, bg=BG_PANEL, padx=14, pady=8,
                        highlightthickness=1, highlightbackground=BORDER_SUBTLE)
        pill.pack(side='right', anchor='center')
        pill_inner = tk.Frame(pill, bg=BG_PANEL)
        pill_inner.pack()
        tk.Label(pill_inner, textvariable=self.pill_line1_var,
                 font=('Segoe UI', 9),
                 bg=BG_PANEL, fg=TEXT_PRIMARY, anchor='e', justify='right'
                 ).pack(anchor='e')
        tk.Label(pill_inner, textvariable=self.pill_line2_var,
                 font=('Segoe UI', 9),
                 bg=BG_PANEL, fg=TEXT_SECONDARY, anchor='e', justify='right'
                 ).pack(anchor='e', pady=(2, 0))

        for w in (header, left, pill, pill_inner):
            w.bind('<ButtonPress-1>', self._drag_start)
            w.bind('<B1-Motion>', self._drag_motion)

    def _update_header_pill(self) -> None:
        tg, bg_w = zone_weights()
        n_known = len(KNOWN)
        stickers_found = count_stickers_found()
        line1 = '   ·   '.join([
            self.tr('pill_stickers_found', n=stickers_found),
            self.tr('pill_lost', n=STICKERS_LOST),
            self.tr('pill_owner_unknown', n=STICKERS_UNKNOWN_OWNER),
        ])
        line2 = '   ·   '.join([
            self.tr('pill_residues_known', n=n_known),
            self.tr('pill_top_slash', pct=int(round(tg * 100))),
            self.tr('pill_bottom_slash', pct=int(round(bg_w * 100))),
        ])
        self.pill_line1_var.set(line1)
        self.pill_line2_var.set(line2)

    def _build_settings_ribbon(self, parent: tk.Misc) -> None:
        ribbon = tk.Frame(parent, bg=BG_BASE, height=62)
        ribbon.pack(side='top', fill='x', padx=18, pady=(10, 0))
        ribbon.pack_propagate(False)

        lbl = self._ribbon_label(ribbon, '')
        lbl.pack(side='left', padx=(0, 6))
        self._add_tr(lbl, 'layout_label')
        layout_combo = ttk.Combobox(ribbon, textvariable=self.layout_var,
                                    state='readonly', width=8,
                                    values=list(LAYOUTS),
                                    style='Ribbon.TCombobox')
        layout_combo.pack(side='left', padx=(0, 18))
        layout_combo.bind('<<ComboboxSelected>>',
                          lambda e: self._update_preview())

        lbl = self._ribbon_label(ribbon, '')
        lbl.pack(side='left', padx=(0, 6))
        self._add_tr(lbl, 'cell_size_label')
        ttk.Spinbox(ribbon, from_=16, to=256, increment=16,
                    textvariable=self.cell_var, width=6,
                    style='Ribbon.TSpinbox'
                    ).pack(side='left', padx=(0, 18))

        lbl = self._ribbon_label(ribbon, '')
        lbl.pack(side='left', padx=(0, 6))
        self._add_tr(lbl, 'output_label')
        ttk.Entry(ribbon, textvariable=self.out_var, style='Ribbon.TEntry'
                  ).pack(side='left', fill='x', expand=True, padx=(0, 8))

        browse_btn = self._secondary_button(ribbon, '', self._browse)
        browse_btn.pack(side='left')
        self._add_tr(browse_btn, 'browse_button')

    def _ribbon_label(self, parent: tk.Misc, text: str) -> tk.Label:
        return tk.Label(parent, text=text, font=('Segoe UI', 9),
                        bg=BG_BASE, fg=TEXT_SECONDARY)

    def _primary_button(self, parent: tk.Misc, text: str, cmd) -> tk.Button:
        return tk.Button(parent, text=text, command=cmd,
                         bg=ACCENT, fg='white', bd=0,
                         activebackground=ACCENT_HOVER, activeforeground='white',
                         font=('Segoe UI', 10, 'bold'),
                         padx=18, pady=6, cursor='hand2')

    def _secondary_button(self, parent: tk.Misc, text: str, cmd) -> tk.Button:
        return tk.Button(parent, text=text, command=cmd,
                         bg=BG_CARD, fg=TEXT_PRIMARY, bd=0,
                         activebackground=BG_HOVER, activeforeground=TEXT_PRIMARY,
                         font=('Segoe UI', 9),
                         padx=14, pady=6, cursor='hand2')

    def _build_bottom_bar(self, parent: tk.Misc) -> None:
        bottom = tk.Frame(parent, bg=BG_BASE, height=54)
        bottom.pack(side='bottom', fill='x', padx=18, pady=(8, 14))
        bottom.pack_propagate(False)

        save_btn = self._primary_button(bottom, '', self._save_with_legend)
        save_btn.pack(side='left')
        self._add_tr(save_btn, 'save_legend_button')

        folder_btn = self._secondary_button(bottom, '', self._open_folder)
        folder_btn.pack(side='left', padx=(10, 18))
        self._add_tr(folder_btn, 'open_folder_button')

        show_chk = tk.Checkbutton(bottom, text='',
                                  variable=self.show_numbers_var,
                                  bg=BG_BASE, fg=TEXT_PRIMARY,
                                  activebackground=BG_BASE,
                                  activeforeground=TEXT_PRIMARY,
                                  selectcolor=BG_CARD,
                                  font=('Segoe UI', 9), bd=0,
                                  highlightthickness=0,
                                  cursor='hand2', command=self._update_preview)
        show_chk.pack(side='left')
        self._add_tr(show_chk, 'show_numbers_checkbox')

        self.show_glyphs_check = tk.Checkbutton(
            bottom, variable=self.show_glyphs_var, bg=BG_BASE, fg=TEXT_PRIMARY,
            activebackground=BG_BASE, activeforeground=TEXT_PRIMARY,
            selectcolor=BG_CARD, font=('Segoe UI', 9), bd=0,
            highlightthickness=0, cursor='hand2', command=self._update_preview)
        self.show_glyphs_check.pack(side='left', padx=(0, 12))
        self._add_tr(self.show_glyphs_check, 'show_symbols_checkbox')

        self.progress = ttk.Progressbar(bottom, mode='determinate', length=220,
                                        style='Accent.Horizontal.TProgressbar')
        self.progress.pack(side='right')

        tk.Label(bottom, textvariable=self.status_var,
                 font=('Segoe UI', 9), bg=BG_BASE, fg=TEXT_SECONDARY
                 ).pack(side='right', padx=(0, 14))

    def _build_body(self, parent: tk.Misc) -> None:
        body = tk.Frame(parent, bg=BG_BASE)
        body.pack(side='top', fill='both', expand=True, padx=18, pady=(12, 0))

        sidebar = tk.Frame(body, bg=BG_BASE, width=220)
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)
        self._build_sidebar(sidebar)

        content = tk.Frame(body, bg=BG_BASE)
        content.pack(side='left', fill='both', expand=True, padx=(14, 0))

        self.info_card = tk.Frame(content, bg=BG_CARD)
        self.info_card.pack(side='top', fill='x')
        self._info_title = tk.Label(self.info_card, text='',
                                    font=('Segoe UI', 14, 'bold'),
                                    bg=BG_CARD, fg=ACCENT, anchor='w')
        self._info_title.pack(anchor='w', padx=16, pady=(14, 0))
        self._info_subtitle = tk.Label(self.info_card, text='',
                                       font=('Segoe UI', 9),
                                       bg=BG_CARD, fg=TEXT_SECONDARY, anchor='w')
        self._info_subtitle.pack(anchor='w', padx=16, pady=(2, 0))
        self._info_desc = tk.Label(self.info_card, text='',
                                   font=('Segoe UI', 9),
                                   bg=BG_CARD, fg=TEXT_PRIMARY, anchor='nw',
                                   justify='left', wraplength=640)
        self._info_desc.pack(anchor='w', padx=16, pady=(8, 4), fill='x')
        self._info_numbers = tk.Label(self.info_card, text='',
                                      font=('Segoe UI', 8, 'italic'),
                                      bg=BG_CARD, fg=TEXT_DIM, anchor='nw',
                                      justify='left', wraplength=640)
        self._info_numbers.pack(anchor='w', padx=16, pady=(0, 14), fill='x')
        self.info_card.bind('<Configure>', self._on_info_resize)

        self.controls_card = tk.Frame(content, bg=BG_CARD)
        self.controls_card.pack(side='top', fill='x', pady=(10, 0))

        preview_card = tk.LabelFrame(content, text='',
                                     bg=BG_CARD, fg=ACCENT, bd=0,
                                     font=('Segoe UI', 10, 'bold'),
                                     labelanchor='nw', padx=10, pady=8,
                                     highlightthickness=1,
                                     highlightbackground=BORDER_SUBTLE)
        preview_card.pack(side='top', fill='both', expand=True, pady=(10, 0))
        self._preview_card = preview_card
        self._refresh_preview_label()

        self.legend_strip = tk.Frame(preview_card, bg=BG_CARD)
        self.legend_strip.pack(side='bottom', fill='x', pady=(4, 0))

        stats_strip = tk.Frame(preview_card, bg=BG_CARD)
        stats_strip.pack(side='bottom', fill='x', pady=(6, 0))
        tk.Label(stats_strip, textvariable=self.preview_stats,
                 font=('Consolas', 9), bg=BG_CARD, fg=TEXT_SECONDARY,
                 anchor='w').pack(side='left')

        self.preview_canvas = tk.Canvas(preview_card, bg='#000000',
                                        highlightthickness=0,
                                        width=600, height=420)
        self.preview_canvas.pack(side='top', fill='both', expand=True)

        preview_card.bind('<Configure>', self._on_preview_resize)
        self.preview_canvas.bind('<Configure>', self._on_preview_resize)

    def _build_sidebar(self, parent: tk.Frame) -> None:
        hdr = tk.Label(parent, text='', font=('Segoe UI', 8, 'bold'),
                       bg=BG_BASE, fg=TEXT_DIM, anchor='w')
        hdr.pack(anchor='w', padx=4, pady=(2, 8))
        self._add_tr(hdr, 'view_modes_header')
        for key in TAB_KEYS:
            card = tk.Frame(parent, bg=BG_PANEL, height=56, cursor='hand2')
            card.pack(side='top', fill='x', pady=(0, 6))
            card.pack_propagate(False)
            strip = tk.Frame(card, bg=BG_PANEL, width=3)
            strip.pack(side='left', fill='y')
            inner = tk.Frame(card, bg=BG_PANEL)
            inner.pack(side='left', fill='both', expand=True, padx=(10, 6))
            title_lbl = tk.Label(inner, text='',
                                 font=('Segoe UI', 10, 'bold'),
                                 bg=BG_PANEL, fg=TEXT_PRIMARY, anchor='w',
                                 cursor='hand2')
            title_lbl.pack(anchor='w', pady=(8, 0), fill='x')
            sub_lbl = tk.Label(inner, text='',
                               font=('Segoe UI', 8),
                               bg=BG_PANEL, fg=TEXT_DIM, anchor='w',
                               cursor='hand2')
            sub_lbl.pack(anchor='w', pady=(1, 0), fill='x')
            self.sidebar_cards[key] = {
                'card': card, 'strip': strip, 'inner': inner,
                'title': title_lbl, 'sub': sub_lbl,
            }
            title_lbl.configure(text=self.tr(f'tab_{key}_card_title'))
            sub_lbl.configure(text=self.tr(f'tab_{key}_card_subtitle'))
            for w in (card, strip, inner, title_lbl, sub_lbl):
                w.bind('<Button-1>', lambda e, k=key: self._select_tab(k))
                w.bind('<Enter>', lambda e, k=key: self._hover_card(k, True))
                w.bind('<Leave>', lambda e, k=key: self._hover_card(k, False))

    def _rebuild_sidebar_labels(self) -> None:
        for key, c in self.sidebar_cards.items():
            c['title'].configure(text=self.tr(f'tab_{key}_card_title'))
            c['sub'].configure(text=self.tr(f'tab_{key}_card_subtitle'))

    def _refresh_preview_label(self) -> None:
        if hasattr(self, '_preview_card'):
            self._preview_card.configure(text=f' {self.tr("live_preview")} ')

    def _hover_card(self, key: str, entered: bool) -> None:
        if key == self.active_tab:
            return
        bg = BG_HOVER if entered else BG_PANEL
        c = self.sidebar_cards[key]
        c['card'].configure(bg=bg)
        c['inner'].configure(bg=bg)
        c['title'].configure(bg=bg)
        c['sub'].configure(bg=bg)
        c['strip'].configure(bg=bg)

    def _select_tab(self, key: str) -> None:
        if key not in TAB_META:
            return
        self.active_tab = key
        for k, c in self.sidebar_cards.items():
            active = (k == key)
            card_bg = BG_CARD if active else BG_PANEL
            c['card'].configure(bg=card_bg)
            c['inner'].configure(bg=card_bg)
            c['title'].configure(bg=card_bg,
                                 fg=TEXT_PRIMARY if active else TEXT_SECONDARY)
            c['sub'].configure(bg=card_bg,
                               fg=TEXT_SECONDARY if active else TEXT_DIM)
            c['strip'].configure(bg=ACCENT if active else card_bg)

        self._info_title.configure(text=self.tr(f'tab_{key}_big_title'))
        self._info_subtitle.configure(text=self.tr(f'tab_{key}_card_subtitle'))
        self._info_desc.configure(text=self.tr(f'tab_{key}_description'))
        self._info_numbers.configure(text=self.tr(f'tab_{key}_numbers_info'))

        self._build_controls_for_tab(key)
        self._rebuild_legend_strip(key)
        self._update_preview()

    def _build_controls_for_tab(self, key: str) -> None:
        for w in self.controls_card.winfo_children():
            w.destroy()
        inner = tk.Frame(self.controls_card, bg=BG_CARD)
        inner.pack(fill='both', expand=True, padx=14, pady=12)

        if key == 'known_only':
            self._controls_status(inner, self.tr('controls_status_known_only'))
            return
        if key == 'pattern_mod54':
            self._controls_status(inner,
                                  self.tr('controls_status_pattern_mod54'))
            return
        if key == 'multi_period':
            self._controls_label(inner, self.tr('min_agree_label')
                                 ).pack(side='left', padx=(0, 8))
            sp = ttk.Spinbox(inner, from_=1, to=8,
                             textvariable=self.agree_var, width=6,
                             style='Ribbon.TSpinbox',
                             command=self._update_preview)
            sp.pack(side='left')
            sp.bind('<KeyRelease>', lambda e: self._update_preview())
            self._controls_status(inner,
                                  self.tr('controls_status_multi_period'),
                                  side='left', padx=(16, 0))
            return
        if key == 'random_sampler':
            self._controls_label(inner, self.tr('seed_label')
                                 ).pack(side='left', padx=(0, 6))
            sp = ttk.Spinbox(inner, from_=0, to=999999,
                             textvariable=self.seed_var, width=10,
                             style='Ribbon.TSpinbox',
                             command=self._update_preview)
            sp.pack(side='left', padx=(0, 18))
            sp.bind('<KeyRelease>', lambda e: self._update_preview())
            self._controls_label(inner, self.tr('samples_label')
                                 ).pack(side='left', padx=(0, 6))
            ttk.Spinbox(inner, from_=1, to=999,
                        textvariable=self.count_var, width=6,
                        style='Ribbon.TSpinbox'
                        ).pack(side='left', padx=(0, 18))
            tk.Button(inner, text=self.tr('reroll_button'),
                      command=self._reroll,
                      bg=BG_HOVER, fg=TEXT_PRIMARY, bd=0,
                      activebackground=ACCENT_DIM, activeforeground='white',
                      font=('Segoe UI', 9), padx=14, pady=4, cursor='hand2'
                      ).pack(side='left')
            return
        if key == 'export_bundle':
            tk.Button(inner, text=self.tr('export_button'),
                      command=self._gen_compare,
                      bg=ACCENT, fg='white', bd=0,
                      activebackground=ACCENT_HOVER, activeforeground='white',
                      font=('Segoe UI', 10, 'bold'),
                      padx=22, pady=8, cursor='hand2'
                      ).pack(side='left')
            self._controls_status(inner,
                                  self.tr('controls_status_export_bundle'),
                                  side='left', padx=(16, 0))
            return
        if key in ('prediction_zoned', 'prediction_cross'):
            table = PRED_ZONED if key == 'prediction_zoned' else PRED_CROSS
            pred_only = [v for k, v in table.items() if k not in KNOWN]
            cnt = Counter(s for s, _ in pred_only)
            mean = sum(c for _, c in pred_only) / max(1, len(pred_only))
            hard = sum(1 for _, c in pred_only if c < 0.55)
            line = ('{}={}  G={}  R={}  Y={}  {}={:.2f}  {}={}').format(
                self.tr('stats_predicted'), len(pred_only),
                cnt.get('G', 0), cnt.get('R', 0), cnt.get('Y', 0),
                self.tr('stats_mean'), mean,
                self.tr('stats_hard_lt'), hard)
            tk.Label(inner, text=line, font=('Consolas', 9),
                     bg=BG_CARD, fg=TEXT_PRIMARY).pack(anchor='w')
            return
        if key == 'confidence_heatmap':
            for label, conf in [('0.00', 0.0), ('0.55', 0.55),
                                ('0.75', 0.75), ('1.00', 1.0)]:
                swatch = tk.Frame(inner, bg=hex_of(heatmap_rgb(conf)),
                                  width=22, height=22)
                swatch.pack(side='left', padx=(0, 4))
                swatch.pack_propagate(False)
                tk.Label(inner, text=label, font=('Consolas', 9),
                         bg=BG_CARD, fg=TEXT_PRIMARY
                         ).pack(side='left', padx=(0, 14))
            kn = tk.Frame(inner, bg=hex_of(KNOWN_HEAT_FILL),
                          width=22, height=22, highlightthickness=1,
                          highlightbackground='#000000')
            kn.pack(side='left', padx=(8, 4))
            kn.pack_propagate(False)
            tk.Label(inner, text=self.tr('swatch_known'), font=('Consolas', 9),
                     bg=BG_CARD, fg=TEXT_PRIMARY).pack(side='left')
            return
        if key == 'hard_residues':
            grid = tk.Frame(inner, bg=BG_CARD)
            grid.pack(anchor='nw', fill='x')
            for r in HARD_RESIDUES[:5]:
                sym, conf = PRED_ZONED[r]
                ch = chains_for(r)
                line = 'r={:>3d} {} {:.2f} ch={}, ...'.format(
                    r, sym, conf, ', '.join(str(x) for x in ch[:3]))
                tk.Label(grid, text=line, font=('Consolas', 8),
                         bg=BG_CARD, fg=TEXT_PRIMARY, anchor='w'
                         ).pack(anchor='w')

    def _controls_label(self, parent: tk.Misc, text: str) -> tk.Label:
        return tk.Label(parent, text=text, font=('Segoe UI', 9),
                        bg=BG_CARD, fg=TEXT_SECONDARY)

    def _controls_status(self, parent: tk.Misc, text: str,
                          side: str = 'top', padx=0) -> None:
        tk.Label(parent, text=text, font=('Segoe UI', 9),
                 bg=BG_CARD, fg=TEXT_SECONDARY, anchor='w', justify='left'
                 ).pack(side=side, anchor='w', padx=padx)

    def _on_preview_resize(self, _event) -> None:
        if self._preview_after_id is not None:
            try:
                self.root.after_cancel(self._preview_after_id)
            except Exception:
                pass
        self._preview_after_id = self.root.after(40, self._update_preview)

    def _on_info_resize(self, event) -> None:
        wrap = max(280, event.width - 40)
        self._info_desc.configure(wraplength=wrap)
        self._info_numbers.configure(wraplength=wrap)

    def _current_grid(self):
        key = self.active_tab
        if key == 'known_only':
            return grid_known_only()
        if key == 'pattern_mod54':
            return predict_mod54()
        if key == 'multi_period':
            try:
                return predict_multi(int(self.agree_var.get()))
            except (ValueError, AttributeError):
                return predict_multi(2)
        if key == 'random_sampler':
            try:
                return sample_random(int(self.seed_var.get()))
            except (ValueError, AttributeError):
                return sample_random(1)
        if key == 'export_bundle':
            return predict_mod54()
        if key in ('prediction_zoned', 'confidence_heatmap',
                   'hard_residues'):
            return [PRED_ZONED[i][0] for i in range(108)]
        if key == 'prediction_cross':
            return [PRED_CROSS[i][0] for i in range(108)]
        return predict_mod54()

    def _cell_visual(self, key: str, k: int, symbol: str):
        show_known = bool(self.show_numbers_var.get() and k in KNOWN)
        known_label = str(k) if show_known else ''
        if key == 'prediction_zoned':
            sym, conf = PRED_ZONED[k]
            return hex_of(blend_to_white(CMAP[sym], conf)), '', known_label
        if key == 'prediction_cross':
            sym, conf = PRED_CROSS[k]
            return hex_of(blend_to_white(CMAP[sym], conf)), '', known_label
        if key == 'confidence_heatmap':
            _, conf = PRED_ZONED[k]
            if k in KNOWN:
                return hex_of(KNOWN_HEAT_FILL), '#000000', str(k)
            return hex_of(heatmap_rgb(conf)), '', str(k)
        if key == 'hard_residues':
            if k in HARD_RESIDUES:
                return hex_of(MAGENTA), '', str(k)
            if k in KNOWN:
                return hex_of(DIM_KNOWN), '', known_label
            return hex_of(DIM_PRED), '', ''
        if key == 'multi_period':
            return CMAP_HEX[symbol], BORDER_SUBTLE, known_label
        return CMAP_HEX[symbol], '', known_label

    def _update_preview(self) -> None:
        self._preview_after_id = None
        if not hasattr(self, 'preview_canvas'):
            return
        cv = self.preview_canvas
        cv.delete('all')

        layout = self.layout_var.get()
        if layout not in LAYOUTS:
            layout = '9x12'
        rows, cols = LAYOUTS[layout]
        cells = self._current_grid()
        key = self.active_tab

        cw = int(cv.winfo_width())
        ch = int(cv.winfo_height())
        if cw <= 1:
            cw = int(cv['width'])
        if ch <= 1:
            ch = int(cv['height'])
        if cw < 30 or ch < 30:
            return

        cell = min((cw - 12) // cols, (ch - 12) // rows)
        if cell < 1:
            cell = 1
        gw, gh = cell * cols, cell * rows
        ox = (cw - gw) // 2
        oy = (ch - gh) // 2

        shows_numbers_only = key in ('confidence_heatmap', 'hard_residues')
        for k in range(108):
            if k >= rows * cols:
                break
            r, c = k // cols, k % cols
            x = ox + c * cell
            y = oy + r * cell
            symbol = cells[k]
            fill, outline, text = self._cell_visual(key, k, symbol)
            cv.create_rectangle(x, y, x + cell, y + cell,
                                fill=fill, outline=outline)
            glyph = GLYPHS.get(symbol, '')
            shows_glyph = (cell >= 18 and not shows_numbers_only and glyph
                           and self.show_glyphs_var.get())
            if text and cell >= 14:
                size = max(6, min(10, cell // 3))
                if shows_glyph:
                    cv.create_text(x + 3, y + 2, text=text, anchor='nw',
                                   font=('Consolas', size),
                                   fill=_contrast_text_color(fill))
                else:
                    cv.create_text(x + cell // 2, y + cell // 2, text=text,
                                   font=('Consolas', size),
                                   fill=_contrast_text_color(fill))
            if shows_glyph:
                glyph_size = min(cell // 2, 14)
                cv.create_text(x + cell // 2, y + cell // 2,
                               text=glyph,
                               font=('Consolas', glyph_size, 'bold'),
                               fill=_contrast_text_color(fill))
        self._update_stats(key, cells)

    def _update_stats(self, key: str, cells) -> None:
        if key in ('prediction_zoned', 'prediction_cross'):
            table = PRED_ZONED if key == 'prediction_zoned' else PRED_CROSS
            pred_only = [v for k, v in table.items() if k not in KNOWN]
            cnt = Counter(s for s, _ in pred_only)
            mean = sum(c for _, c in pred_only) / max(1, len(pred_only))
            hard = sum(1 for _, c in pred_only if c < 0.55)
            self.preview_stats.set(
                '{k_known}: {}   {k_pred}: {}   G:{} R:{} Y:{}   '
                '{k_mean}: {:.2f}   {k_hard}: {}'.format(
                    len(KNOWN), len(pred_only),
                    cnt.get('G', 0), cnt.get('R', 0), cnt.get('Y', 0),
                    mean, hard,
                    k_known=self.tr('stats_known'),
                    k_pred=self.tr('stats_predicted'),
                    k_mean=self.tr('stats_mean'),
                    k_hard=self.tr('stats_hard_lt')))
            return
        if key == 'confidence_heatmap':
            confs = [c for k, (_, c) in PRED_ZONED.items() if k not in KNOWN]
            edges = (0.55, 0.75, 1.0)
            b = [sum(1 for c in confs if (e_prev <= c < e_cur))
                 for e_prev, e_cur in zip((0.0,) + edges[:-1], edges)]
            self.preview_stats.set(
                '{k_known}: {}   <.55: {}   <.75: {}   <1.0: {}   '
                '{k_mean}: {:.2f}'.format(
                    len(KNOWN), b[0], b[1], b[2],
                    sum(confs) / max(1, len(confs)),
                    k_known=self.tr('stats_known'),
                    k_mean=self.tr('stats_mean')))
            return
        if key == 'hard_residues':
            self.preview_stats.set(
                '{k_hard}: {}   {k_ch}: {}   {k_known}: {}   {k_unk}: {}'
                .format(
                    len(HARD_RESIDUES), len(HARD_RESIDUES) * 6,
                    len(KNOWN), 108 - len(KNOWN),
                    k_hard=self.tr('stats_hard'),
                    k_ch=self.tr('stats_chains'),
                    k_known=self.tr('stats_known'),
                    k_unk=self.tr('stats_unknown')))
            return
        cnt = Counter(cells)
        self.preview_stats.set(
            '{k_sl}: {}   {k_da}: {}   {k_do}: {}   {k_un}: {}'.format(
                cnt.get('G', 0), cnt.get('R', 0),
                cnt.get('Y', 0), cnt.get('K', 0),
                k_sl=self.tr('stats_slash'),
                k_da=self.tr('stats_dash'),
                k_do=self.tr('stats_dot'),
                k_un=self.tr('stats_unknown')))

    def _legend_items_for(self, key: str):
        kind = TAB_META.get(key, {}).get('legend_kind', 'symbol3')
        base = [(CMAP_HEX['G'], self.tr('swatch_slash')),
                (CMAP_HEX['R'], self.tr('swatch_dash')),
                (CMAP_HEX['Y'], self.tr('swatch_dot'))]
        if kind == 'symbol3':
            return list(base)
        if kind == 'symbol3_plus_unk':
            return base + [(CMAP_HEX['K'], self.tr('swatch_unknown_black'))]
        if kind == 'symbol3_plus_lowagree':
            return base + [(CMAP_HEX['K'], self.tr('swatch_no_agreement'))]
        if kind == 'symbol3_with_gradient':
            grad = [
                (hex_of(blend_to_white(CMAP['G'], 1.00)),
                 self.tr('swatch_conf', value='1.00')),
                (hex_of(blend_to_white(CMAP['G'], 0.80)), '0.80'),
                (hex_of(blend_to_white(CMAP['G'], 0.60)), '0.60'),
                (hex_of(blend_to_white(CMAP['G'], 0.40)), '0.40'),
            ]
            return base + grad
        if kind == 'heatmap_gradient':
            return [
                (hex_of(heatmap_rgb(0.00)),
                 self.tr('swatch_conf', value='0.00')),
                (hex_of(heatmap_rgb(0.25)), '0.25'),
                (hex_of(heatmap_rgb(0.55)), '0.55'),
                (hex_of(heatmap_rgb(0.75)), '0.75'),
                (hex_of(heatmap_rgb(1.00)), '1.00'),
                (hex_of(KNOWN_HEAT_FILL), self.tr('swatch_known_grey')),
            ]
        if kind == 'hard_tri':
            return [
                (hex_of(MAGENTA), self.tr('swatch_hard_low')),
                (hex_of(DIM_KNOWN), self.tr('swatch_known')),
                (hex_of(DIM_PRED), self.tr('swatch_predicted_ok')),
            ]
        return list(base)

    def _legend_note_for(self, key: str):
        kind = TAB_META.get(key, {}).get('legend_kind', 'symbol3')
        if kind == 'symbol3_with_gradient':
            return self.tr('legend_note_blend')
        return ''

    def _rebuild_legend_strip(self, key: str) -> None:
        if not hasattr(self, 'legend_strip'):
            return
        for w in self.legend_strip.winfo_children():
            w.destroy()
        items = self._legend_items_for(key)
        note = self._legend_note_for(key)
        max_w = 560
        swatch_px = 12
        gap_px = 4
        item_pad = 14
        char_px = 7
        row = tk.Frame(self.legend_strip, bg=BG_CARD)
        row.pack(side='top', anchor='w', fill='x')
        used = 0
        for color_hex, label in items:
            est_w = swatch_px + gap_px + char_px * len(label) + item_pad
            if used > 0 and used + est_w > max_w:
                row = tk.Frame(self.legend_strip, bg=BG_CARD)
                row.pack(side='top', anchor='w', fill='x', pady=(2, 0))
                used = 0
            sw = tk.Frame(row, bg=color_hex,
                          width=swatch_px, height=swatch_px,
                          highlightthickness=1,
                          highlightbackground=BORDER_SUBTLE)
            sw.pack(side='left', padx=(0, gap_px), pady=1)
            sw.pack_propagate(False)
            tk.Label(row, text=label,
                     font=('Consolas', 9),
                     bg=BG_CARD, fg=TEXT_PRIMARY
                     ).pack(side='left', padx=(0, item_pad))
            used += est_w
        if note:
            note_row = tk.Frame(self.legend_strip, bg=BG_CARD)
            note_row.pack(side='top', anchor='w', fill='x', pady=(2, 0))
            tk.Label(note_row, text=note,
                     font=('Segoe UI', 8, 'italic'),
                     bg=BG_CARD, fg=TEXT_DIM
                     ).pack(side='left')

    def _labels_for_save(self, key: str, rows: int, cols: int):
        show_known = bool(self.show_numbers_var.get())
        cap = rows * cols
        if key == 'confidence_heatmap':
            return {k: str(k) for k in range(108) if k < cap}
        if key == 'hard_residues':
            base = {k: str(k) for k in HARD_RESIDUES if k < cap}
            if show_known:
                base.update({k: str(k) for k in KNOWN if k < cap})
            return base
        if show_known:
            return {k: str(k) for k in KNOWN if k < cap}
        return None

    def _grid_image_for_active(self, rows: int, cols: int, cell_px: int):
        key = self.active_tab
        labels = self._labels_for_save(key, rows, cols)
        rgb_factory = {
            'prediction_zoned': lambda: cells_pred_blended(PRED_ZONED),
            'prediction_cross': lambda: cells_pred_blended(PRED_CROSS),
            'confidence_heatmap': cells_heatmap,
            'hard_residues': cells_hard,
        }
        if key in rgb_factory:
            return make_grid_image_rgb(rgb_factory[key](),
                                       rows, cols, cell_px, labels=labels)
        return make_grid_image(self._current_grid(),
                               rows, cols, cell_px, labels=labels)

    def _title_for_active(self):
        key = self.active_tab
        big = self.tr(f'tab_{key}_big_title')
        sub = self.tr(f'tab_{key}_card_subtitle')
        if key == 'random_sampler':
            sub = f'{sub}  ·  seed = {self.seed_var.get()}'
        elif key == 'multi_period':
            sub = f'{sub}  ·  min agree = {self.agree_var.get()}'
        if key in ('prediction_zoned', 'prediction_cross'):
            sub = f"{sub}  ·  {self.tr('tail_prediction_numbers')}"
        elif key == 'confidence_heatmap':
            sub = f"{sub}  ·  {self.tr('tail_heatmap_numbers')}"
        elif key == 'hard_residues':
            sub = f"{sub}  ·  {self.tr('tail_hard_numbers')}"
        return big, sub

    def _save_with_legend(self) -> None:
        cp = self._common()
        if cp is None:
            return
        rows, cols, cs, out_dir, lay = cp
        key = self.active_tab
        if key == 'export_bundle':
            self._gen_compare()
            return
        grid_img = self._grid_image_for_active(rows, cols, cs)
        title, subtitle = self._title_for_active()
        items = self._legend_items_for(key)
        path = out_dir / f'with_legend_{key}_{lay}_cs{cs}.png'
        render_with_legend(grid_img, items, title, subtitle, path, cs)
        self.status_var.set(self.tr('status_saved', filename=path.name))

    def _reroll(self) -> None:
        try:
            cur = int(self.seed_var.get())
        except ValueError:
            cur = 0
        self.seed_var.set(str(cur + 1))
        self._update_preview()

    def _browse(self) -> None:
        d = filedialog.askdirectory(initialdir=self.out_var.get())
        if d:
            self.out_var.set(d)

    def _open_folder(self) -> None:
        p = Path(self.out_var.get())
        if p.exists():
            try:
                os.startfile(str(p))
            except Exception:
                pass
        else:
            messagebox.showinfo(self.tr('error_folder_missing_title'),
                                self.tr('error_folder_missing'))

    def _common(self):
        try:
            cell_size = int(self.cell_var.get())
        except ValueError:
            messagebox.showerror(self.tr('error_bad_input_int_title'),
                                 self.tr('error_bad_input_int'))
            return None
        layout = self.layout_var.get()
        if layout not in LAYOUTS:
            messagebox.showerror(self.tr('error_bad_layout_title'),
                                 self.tr('error_bad_layout'))
            return None
        out_dir = Path(self.out_var.get())
        out_dir.mkdir(parents=True, exist_ok=True)
        rows, cols = LAYOUTS[layout]
        return rows, cols, cell_size, out_dir, layout

    def _gen_known(self) -> None:
        cp = self._common()
        if cp is None:
            return
        rows, cols, cs, out, lay = cp
        cells = grid_known_only()
        path = out / f'known_only_{lay}.png'
        render(cells, rows, cols, cs, path)
        self.status_var.set(self.tr('status_saved', filename=path.name))

    def _gen_mod54(self) -> None:
        cp = self._common()
        if cp is None:
            return
        rows, cols, cs, out, lay = cp
        cells = predict_mod54()
        path = out / f'mod54_{lay}.png'
        render(cells, rows, cols, cs, path)
        self.status_var.set(self.tr('status_saved', filename=path.name))

    def _gen_multi(self) -> None:
        cp = self._common()
        if cp is None:
            return
        rows, cols, cs, out, lay = cp
        try:
            min_a = int(self.agree_var.get())
        except ValueError:
            messagebox.showerror(self.tr('error_bad_input_int_title'),
                                 self.tr('error_bad_input_int'))
            return
        cells = predict_multi(min_a)
        path = out / f'multi_min{min_a}_{lay}.png'
        render(cells, rows, cols, cs, path)
        self.status_var.set(self.tr('status_saved', filename=path.name))

    def _gen_random(self) -> None:
        cp = self._common()
        if cp is None:
            return
        rows, cols, cs, out, lay = cp
        try:
            count = int(self.count_var.get())
            seed_start = int(self.seed_var.get())
        except ValueError:
            messagebox.showerror(self.tr('error_bad_input_int_title'),
                                 self.tr('error_bad_input_int'))
            return
        self.progress['maximum'] = count
        self.progress['value'] = 0
        self.status_var.set(self.tr('status_generating'))
        threading.Thread(
            target=self._random_worker,
            args=(count, rows, cols, cs, seed_start, out, lay),
            daemon=True,
        ).start()

    def _random_worker(self, count, rows, cols, cs, seed_start, out, lay):
        for i in range(count):
            seed = seed_start + i
            cells = sample_random(seed)
            path = out / f'random_{lay}_seed{seed:03d}.png'
            render(cells, rows, cols, cs, path)
            self.root.after(0, self._tick, i + 1, count, path.name)
        self.root.after(0, lambda: self.status_var.set(
            self.tr('status_done_count', n=count)))

    def _gen_compare(self) -> None:
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
            path = out / f'compare_{name}_{lay}.png'
            render(cells, rows, cols, cs, path)
        self.status_var.set(self.tr('status_done_count', n=len(bundle)))

    def _save_rgb_grid(self, rgb_cells, basename: str) -> None:
        cp = self._common()
        if cp is None:
            return
        rows, cols, cs, out, lay = cp
        path = out / f'{basename}_{lay}.png'
        render_rgb(rgb_cells, rows, cols, cs, path)
        self.status_var.set(self.tr('status_saved', filename=path.name))

    def _gen_pred_zoned(self) -> None:
        self._save_rgb_grid(cells_pred_blended(PRED_ZONED), 'predicted_zoned')

    def _gen_pred_cross(self) -> None:
        self._save_rgb_grid(cells_pred_blended(PRED_CROSS), 'predicted_cross')

    def _gen_heatmap(self) -> None:
        self._save_rgb_grid(cells_heatmap(), 'confidence_heatmap')

    def _gen_hard(self) -> None:
        self._save_rgb_grid(cells_hard(), 'hard_cells')

    def _tick(self, done: int, total: int, name: str) -> None:
        self.progress['value'] = done
        self.status_var.set(self.tr('status_progress', done=done,
                                    total=total, filename=name))


def main() -> None:
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
