"""
╔══════════════════════════════════════════════════════╗
║   የንግድ ስራ ረዳት — Business Assistant App  v3.0       ║
║   Android-safe, zero-crash build                    ║
╚══════════════════════════════════════════════════════╝

FIXES vs v2:
  FIX-1  DB path   → self.user_data_dir  (guaranteed writable on Android)
  FIX-2  Font      → resource_find()     (__file__ removed — crashes Android)
  FIX-3  Canvas    → Color.rgba mutated in-place (no repeated attach_bg layers)
  FIX-4  Entry     → BusinessApp().run() (kelalApp typo removed)
  FIX-5  spec      → requirements clean  (no python3 / sqlite3)
"""

# ── stdlib ────────────────────────────────────────────────────────────────────
import os
import sys
import sqlite3
from datetime import datetime

# ── Kivy env BEFORE any kivy import ──────────────────────────────────────────
os.environ["KIVY_NO_ENV_CONFIG"] = "1"

from kivy.config import Config
Config.set("graphics", "width",    "420")
Config.set("graphics", "height",   "800")
Config.set("graphics", "resizable","0")
Config.set("input",    "mouse",    "mouse,multitouch_on_demand")

from kivy.app               import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout     import BoxLayout
from kivy.uix.scrollview    import ScrollView
from kivy.uix.label         import Label
from kivy.uix.button        import Button
from kivy.uix.textinput     import TextInput
from kivy.uix.spinner       import Spinner
from kivy.uix.popup         import Popup
from kivy.uix.widget        import Widget
from kivy.graphics          import Color, Rectangle, RoundedRectangle
from kivy.core.window       import Window
from kivy.core.text         import LabelBase
from kivy.resources         import resource_find   # FIX-2
from kivy.metrics           import dp
from kivy.utils             import get_color_from_hex

# ── Colour palette ────────────────────────────────────────────────────────────
BG     = get_color_from_hex("#0D0F14")
CARD   = get_color_from_hex("#161A24")
CARD2  = get_color_from_hex("#1C2130")
ACCENT = get_color_from_hex("#1FBF8A")
GOLD   = get_color_from_hex("#F5A623")
RED    = get_color_from_hex("#E5534B")
TEXT   = get_color_from_hex("#E8EAF0")
MUTED  = get_color_from_hex("#8A8FA8")
BORDER = get_color_from_hex("#252A3A")
NAV_BG = get_color_from_hex("#111318")

Window.clearcolor = BG

# ── FIX-2: Font — resource_find works on Android; __file__ does NOT ──────────
FONT    = "Roboto"
_nyala  = resource_find("Nyala.ttf")
if _nyala:
    try:
        LabelBase.register(name="Nyala", fn_regular=_nyala)
        FONT = "Nyala"
    except Exception:
        pass

# ══════════════════════════════════════════════════════════════════════════════
#  DATABASE
#  FIX-1: DB_PATH is set inside App.build() using self.user_data_dir
#         which is the only guaranteed-writable location on Android.
# ══════════════════════════════════════════════════════════════════════════════

DB_PATH = None

def _db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def setup_db(path: str):
    global DB_PATH
    DB_PATH = path
    with _db() as c:
        c.executescript("""
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS items (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT    NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS shipments (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            total_cost REAL    NOT NULL,
            note       TEXT    DEFAULT '',
            created_at TEXT    NOT NULL
        );
        CREATE TABLE IF NOT EXISTS shipment_lines (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            shipment_id INTEGER NOT NULL,
            item_name   TEXT    NOT NULL,
            qty         REAL    NOT NULL,
            unit_buy    REAL    NOT NULL,
            landed_unit REAL    NOT NULL,
            FOREIGN KEY(shipment_id) REFERENCES shipments(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS profit_plans (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name       TEXT    NOT NULL,
            landed_cost     REAL    NOT NULL,
            qty             REAL    NOT NULL,
            profit_per_unit REAL    NOT NULL,
            days_to_sell    INTEGER NOT NULL,
            sale_price      REAL    NOT NULL,
            total_profit    REAL    NOT NULL,
            daily_sales     REAL    NOT NULL,
            daily_profit    REAL    NOT NULL,
            created_at      TEXT    NOT NULL
        );
        CREATE TABLE IF NOT EXISTS budget_plans (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id        INTEGER NOT NULL,
            total_profit   REAL NOT NULL,
            daily_profit   REAL NOT NULL,
            monthly_profit REAL NOT NULL,
            exp_day  REAL NOT NULL, fix_day  REAL NOT NULL,
            emg_day  REAL NOT NULL, per_day  REAL NOT NULL,
            exp_mon  REAL NOT NULL, fix_mon  REAL NOT NULL,
            emg_mon  REAL NOT NULL, per_mon  REAL NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(plan_id) REFERENCES profit_plans(id) ON DELETE CASCADE
        );
        """)

def all_item_names():
    with _db() as c:
        rows = c.execute("SELECT name FROM items ORDER BY name").fetchall()
    return [r["name"] for r in rows]

# ══════════════════════════════════════════════════════════════════════════════
#  UI PRIMITIVES
# ══════════════════════════════════════════════════════════════════════════════

def _z(n): return dp(n)

def attach_bg(widget, color, radius=dp(12)):
    """Attach ONE background layer. Returns (Color, RoundedRectangle)."""
    with widget.canvas.before:
        clr  = Color(*color)
        rect = RoundedRectangle(pos=widget.pos, size=widget.size,
                                radius=[radius])
    def _upd(inst, _):
        rect.pos  = inst.pos
        rect.size = inst.size
    widget.bind(pos=_upd, size=_upd)
    return clr, rect

def lbl(text, size=14, color=TEXT, bold=False, align="left", h=30):
    w = Label(text=text, font_name=FONT, font_size=size,
              color=color, bold=bold, halign=align, valign="middle",
              size_hint_y=None, height=_z(h))
    w.bind(size=lambda i, v: setattr(i, "text_size", (v[0], None)))
    return w

def tinput(hint="", filt=None, h=46):
    t = TextInput(
        hint_text=hint, font_name=FONT, font_size=15,
        multiline=False, input_filter=filt,
        size_hint_y=None, height=_z(h),
        background_color=get_color_from_hex("#1E2336"),
        foreground_color=TEXT,
        hint_text_color=(*MUTED[:3], 0.8),
        cursor_color=ACCENT,
        padding=[_z(12), _z(11)], write_tab=False,
    )
    with t.canvas.before:
        Color(*BORDER)
        r = RoundedRectangle(pos=t.pos, size=t.size, radius=[_z(8)])
    t.bind(pos =lambda i, v: setattr(r, "pos",  v),
           size=lambda i, v: setattr(r, "size", v))
    return t

def btn(text, bg=ACCENT, fg=None, h=50, size=15, bold=True, radius=dp(10)):
    fg = fg or get_color_from_hex("#0A0C10")
    b  = Button(text=text, font_name=FONT, font_size=size, bold=bold,
                color=fg, background_normal="", background_color=(0,0,0,0),
                size_hint_y=None, height=_z(h))
    with b.canvas.before:
        clr = Color(*bg)
        r   = RoundedRectangle(pos=b.pos, size=b.size, radius=[radius])
    b.bind(pos =lambda i, v: setattr(r, "pos",  v),
           size=lambda i, v: setattr(r, "size", v))
    b.bind(on_press  =lambda *_: setattr(clr, "rgba", (*bg[:3], 0.72)),
           on_release=lambda *_: setattr(clr, "rgba", bg))
    return b

def _btn_color(button):
    """Return the first Color instruction in button.canvas.before."""
    for instr in button.canvas.before.children:
        if isinstance(instr, Color):
            return instr
    return None

def spnr(values=None, text="-- ምረጥ --", h=46):
    return Spinner(text=text, values=values or [],
                   font_name=FONT, font_size=14, color=TEXT,
                   background_normal="",
                   background_color=get_color_from_hex("#1E2336"),
                   size_hint_y=None, height=_z(h))

def card(pad=16, sp=10, color=CARD, radius=14):
    bx = BoxLayout(orientation="vertical",
                   padding=_z(pad), spacing=_z(sp), size_hint_y=None)
    bx.bind(minimum_height=bx.setter("height"))
    attach_bg(bx, color, _z(radius))
    return bx

def stitle(text):
    return lbl(text, size=17, color=ACCENT, bold=True, h=36)

def divider():
    w = Widget(size_hint_y=None, height=_z(1))
    with w.canvas:
        Color(*BORDER)
        r = Rectangle(pos=w.pos, size=w.size)
    w.bind(pos =lambda i, v: setattr(r, "pos",  v),
           size=lambda i, v: setattr(r, "size", v))
    return w

def space(h=8):
    return Widget(size_hint_y=None, height=_z(h))

def popup(title, msg, color=ACCENT):
    content = BoxLayout(orientation="vertical", padding=_z(16), spacing=_z(12))
    content.add_widget(space(4))
    content.add_widget(lbl(msg, size=14, color=TEXT, align="center", h=70))
    ok  = btn("  ዝጋ  ", bg=color, h=44)
    pop = Popup(title=title, title_font=FONT, title_color=color, title_size=16,
                content=content, size_hint=(0.85, None), height=_z(190),
                background_color=CARD2, separator_color=color)
    ok.bind(on_release=pop.dismiss)
    content.add_widget(ok)
    pop.open()

def scrollpage(pad=16, sp=14):
    sv   = ScrollView(do_scroll_x=False, bar_width=3,
                      bar_color=(*ACCENT[:3], 0.5),
                      bar_inactive_color=(*MUTED[:3], 0.2))
    body = BoxLayout(orientation="vertical", padding=_z(pad), spacing=_z(sp),
                     size_hint_y=None)
    body.bind(minimum_height=body.setter("height"))
    sv.add_widget(body)
    return sv, body

def page_header(title_text, icon=""):
    h = BoxLayout(size_hint_y=None, height=_z(62),
                  padding=[_z(18), 0, _z(18), 0])
    attach_bg(h, NAV_BG, 0)
    with h.canvas.after:
        Color(*BORDER)
        ln = Rectangle(pos=(h.x, h.y), size=(h.width, _z(1)))
    h.bind(pos =lambda i, v: setattr(ln, "pos",  (v[0], v[1])),
           size=lambda i, v: setattr(ln, "size", (v[0], _z(1))))
    h.add_widget(lbl(f"{icon}  {title_text}", size=19,
                     color=ACCENT, bold=True, h=62))
    return h

# ══════════════════════════════════════════════════════════════════════════════
#  NAV BAR
# ══════════════════════════════════════════════════════════════════════════════

_NAV = [("🏠","home"),("📦","shipment"),("📈","profit"),("🕐","history")]

class NavBar(BoxLayout):
    def __init__(self, sm, **kw):
        super().__init__(size_hint_y=None, height=_z(64),
                         orientation="horizontal", **kw)
        self.sm = sm
        attach_bg(self, NAV_BG, 0)
        with self.canvas.after:
            Color(*BORDER)
            self._ln = Rectangle(pos=self.pos, size=(self.width, _z(1)))
        self.bind(pos =lambda i,v: setattr(self._ln,"pos", (v[0],v[1]+_z(63))),
                  size=lambda i,v: setattr(self._ln,"size",(v[0],_z(1))))
        self._btns = {}
        for icon, name in _NAV:
            b = Button(text=icon, font_size=26,
                       background_normal="", background_color=(0,0,0,0),
                       color=MUTED)
            b.bind(on_release=lambda inst, n=name: self.go(n))
            self._btns[name] = b
            self.add_widget(b)

    def go(self, name):
        self.sm.current = name

    def mark(self, name):
        for k, b in self._btns.items():
            b.color = ACCENT if k == name else MUTED
            b.bold  = (k == name)

# ══════════════════════════════════════════════════════════════════════════════
#  SCREEN 1 — HOME
# ══════════════════════════════════════════════════════════════════════════════

class HomeScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        attach_bg(self, BG, 0)
        root = BoxLayout(orientation="vertical", spacing=0)
        root.add_widget(page_header("የእቃ ዝርዝር መዝገብ", "📋"))
        sv, body = scrollpage()

        c = card()
        c.add_widget(stitle("✚  አዲስ እቃ ምዝገባ"))
        c.add_widget(lbl("የእቃ ስም:", size=13, color=MUTED))
        self.inp = tinput("ለምሳሌ: ሩዝ, ዘይት, ሽንኩርት …")
        c.add_widget(self.inp)
        b = btn("✚  ምዝገባ", bg=ACCENT)
        b.bind(on_release=self._register)
        c.add_widget(b)
        body.add_widget(c)

        c2 = card()
        c2.add_widget(stitle("📋  የተመዘገቡ እቃዎች"))
        self.list_box = BoxLayout(orientation="vertical",
                                  spacing=_z(6), size_hint_y=None)
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        c2.add_widget(self.list_box)
        body.add_widget(c2)

        root.add_widget(sv)
        self.add_widget(root)

    def on_enter(self): self._refresh()

    def _register(self, *_):
        name = self.inp.text.strip()
        if not name:
            popup("⚠️", "የእቃ ስም ያስገቡ!", RED); return
        try:
            with _db() as conn:
                conn.execute("INSERT INTO items(name) VALUES(?)", (name,))
            self.inp.text = ""
            self._refresh()
            popup("✅ ተሳካ", f'"{name}" ተመዘገበ!')
        except sqlite3.IntegrityError:
            popup("ማስጠንቀቂያ", f'"{name}" አስቀድሞ አለ!', GOLD)
        except Exception as e:
            popup("ስህተት", str(e), RED)

    def _delete(self, name):
        try:
            with _db() as conn:
                conn.execute("DELETE FROM items WHERE name=?", (name,))
            self._refresh()
        except Exception as e:
            popup("ስህተት", str(e), RED)

    def _refresh(self):
        self.list_box.clear_widgets()
        try:   names = all_item_names()
        except Exception: names = []
        if not names:
            self.list_box.add_widget(
                lbl("ምንም እቃ አልተመዘገበም።", size=13, color=MUTED,
                    align="center")); return
        for name in names:
            row = BoxLayout(size_hint_y=None, height=_z(42), spacing=_z(8))
            row.add_widget(lbl(f"• {name}", size=14, h=42))
            d = btn("🗑", bg=RED, fg=TEXT, h=36, size=13,
                    bold=False, radius=_z(7))
            d.size_hint_x = None; d.width = _z(42)
            d.bind(on_release=lambda inst, n=name: self._delete(n))
            row.add_widget(d)
            self.list_box.add_widget(row)

# ══════════════════════════════════════════════════════════════════════════════
#  SCREEN 2 — SHIPMENT
# ══════════════════════════════════════════════════════════════════════════════

class ShipmentScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._lines = []
        attach_bg(self, BG, 0)
        root = BoxLayout(orientation="vertical", spacing=0)
        root.add_widget(page_header("የጭነት ወጪ ማከፋፈያ", "📦"))
        sv, body = scrollpage()

        c1 = card()
        c1.add_widget(stitle("💵  አጠቃላይ የጭነት ወጪ"))
        c1.add_widget(lbl("ጠቅላላ ወጪ (ብር):", size=13, color=MUTED))
        self.total_inp = tinput("ለምሳሌ: 100000", filt="float")
        c1.add_widget(self.total_inp)
        c1.add_widget(lbl("አጭር መግለጫ:", size=13, color=MUTED))
        self.note_inp = tinput("ለምሳሌ: ጭነት ቁጥር 3")
        c1.add_widget(self.note_inp)
        body.add_widget(c1)

        c2 = card()
        c2.add_widget(stitle("➕  እቃ ጨምር"))
        c2.add_widget(lbl("እቃ ምረጥ:", size=13, color=MUTED))
        self.item_sp = spnr()
        c2.add_widget(self.item_sp)
        c2.add_widget(lbl("ብዛት  /  ዋጋ/ነጠላ (ብር):", size=13, color=MUTED))
        row = BoxLayout(size_hint_y=None, height=_z(46), spacing=_z(8))
        self.qty_inp = tinput("ብዛት",    filt="float")
        self.buy_inp = tinput("ዋጋ/ነጠላ", filt="float")
        row.add_widget(self.qty_inp); row.add_widget(self.buy_inp)
        c2.add_widget(row)
        b_add = btn("➕  ለዝርዝር ጨምር", bg=GOLD, fg=get_color_from_hex("#0A0C10"))
        b_add.bind(on_release=self._add_line)
        c2.add_widget(b_add)
        body.add_widget(c2)

        c3 = card()
        c3.add_widget(stitle("🧾  ዝርዝር"))
        self.lines_box = BoxLayout(orientation="vertical",
                                   spacing=_z(6), size_hint_y=None)
        self.lines_box.bind(minimum_height=self.lines_box.setter("height"))
        c3.add_widget(self.lines_box)
        body.add_widget(c3)

        b_calc = btn("📊  ወጪ አከፋፍልና አስቀምጥ", bg=ACCENT, h=52, size=16)
        b_calc.bind(on_release=self._calculate)
        body.add_widget(b_calc)

        self.res_card = card(color=CARD2)
        self.res_card.add_widget(stitle("✅  ውጤት"))
        self.res_lbl = lbl("", size=13, h=20)
        self.res_card.add_widget(self.res_lbl)
        self.res_card.opacity = 0
        body.add_widget(self.res_card)

        b_reset = btn("🔄  ዳግም ጀምር", bg=BORDER, fg=TEXT, h=42,
                      size=14, bold=False)
        b_reset.bind(on_release=self._reset)
        body.add_widget(b_reset)

        root.add_widget(sv)
        self.add_widget(root)

    def on_enter(self):
        names = all_item_names()
        self.item_sp.values = names
        self.item_sp.text   = names[0] if names else "-- እቃ የለም --"

    def _add_line(self, *_):
        name = self.item_sp.text
        if not name or name.startswith("--"):
            popup("⚠️", "እቃ ምረጥ!", RED); return
        try:
            qty = float(self.qty_inp.text or "0")
            buy = float(self.buy_inp.text or "0")
        except ValueError:
            popup("⚠️", "ቁጥሮቹን ትክክል ያስገቡ!", RED); return
        if qty <= 0 or buy <= 0:
            popup("⚠️", "ብዛትና ዋጋ ከዜሮ በላይ ይሁን!", RED); return
        self._lines.append({"name": name, "qty": qty, "buy": buy})
        self.qty_inp.text = ""; self.buy_inp.text = ""
        self._refresh_lines()

    def _remove_line(self, idx):
        if 0 <= idx < len(self._lines):
            self._lines.pop(idx); self._refresh_lines()

    def _refresh_lines(self):
        self.lines_box.clear_widgets()
        if not self._lines:
            self.lines_box.add_widget(
                lbl("ምንም አልጨመሩም።", size=13, color=MUTED, align="center")); return
        for i, ln in enumerate(self._lines):
            row = BoxLayout(size_hint_y=None, height=_z(38), spacing=_z(6))
            row.add_widget(lbl(
                f"• {ln['name']}  ×{ln['qty']:.0f}  @{ln['buy']:.2f} ብር",
                size=13, h=38))
            d = btn("✕", bg=RED, fg=TEXT, h=32, size=12,
                    bold=False, radius=_z(6))
            d.size_hint_x = None; d.width = _z(36)
            d.bind(on_release=lambda inst, idx=i: self._remove_line(idx))
            row.add_widget(d)
            self.lines_box.add_widget(row)

    def _calculate(self, *_):
        if not self._lines:
            popup("⚠️", "ቢያንስ አንድ እቃ ጨምሩ!", RED); return
        try:   total = float(self.total_inp.text or "0")
        except ValueError:
            popup("⚠️", "ጠቅላላ ወጪ ቁጥር ያስገቡ!", RED); return
        if total <= 0:
            popup("⚠️", "ጠቅላላ ወጪ ከዜሮ በላይ ይሁን!", RED); return

        cpt = total / len(self._lines)
        results = []
        txt = [f"💵 ጠቅላላ: {total:,.2f} ብር → {cpt:,.2f} ብር/ዓይነት\n"]
        for ln in self._lines:
            landed = ln["buy"] + cpt / ln["qty"]
            results.append({**ln, "landed": landed})
            txt.append(f"• {ln['name']}  ×{ln['qty']:.0f}"
                       f"  ገዛ={ln['buy']:.2f} → መነሻ={landed:.2f} ብር/ነጠላ")

        self.res_lbl.text   = "\n".join(txt)
        self.res_lbl.height = _z(28 * (len(txt) + 1))
        self.res_card.opacity = 1

        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            with _db() as conn:
                cur = conn.execute(
                    "INSERT INTO shipments(total_cost,note,created_at)"
                    " VALUES(?,?,?)",
                    (total, self.note_inp.text.strip(), now))
                sid = cur.lastrowid
                conn.executemany(
                    "INSERT INTO shipment_lines"
                    "(shipment_id,item_name,qty,unit_buy,landed_unit)"
                    " VALUES(?,?,?,?,?)",
                    [(sid, r["name"], r["qty"], r["buy"], r["landed"])
                     for r in results])
        except Exception as e:
            popup("DB ስህተት", str(e), RED)

    def _reset(self, *_):
        self._lines.clear()
        self.total_inp.text = ""; self.note_inp.text = ""
        self.res_lbl.text   = ""; self.res_card.opacity = 0
        self._refresh_lines()

# ══════════════════════════════════════════════════════════════════════════════
#  SCREEN 3 + 4 — PROFIT & BUDGET
# ══════════════════════════════════════════════════════════════════════════════

class ProfitScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._plan_id = None; self._tp = 0.0; self._dp = 0.0
        attach_bg(self, BG, 0)
        root = BoxLayout(orientation="vertical", spacing=0)
        root.add_widget(page_header("ትርፍ እና በጀት ትንበያ", "📈"))
        sv, body = scrollpage()

        c1 = card()
        c1.add_widget(stitle("📈  ደረጃ 3 — የትርፍ ትንበያ"))
        c1.add_widget(lbl("እቃ ምረጥ:", size=13, color=MUTED))
        self.item_sp  = spnr()
        c1.add_widget(self.item_sp)
        for lbl_txt, attr, hint, filt in [
            ("የእቃ መነሻ ዋጋ (ብር/ነጠላ):", "lnd_inp", "250",   "float"),
            ("ጠቅላላ ብዛት:",            "qty_inp", "200",   "float"),
            ("ትርፍ/ነጠላ (ብር):",        "ppu_inp", "50",    "float"),
            ("ጊዜ ለመሸጥ (ቀናት):",       "days_inp","30",    "int"),
        ]:
            c1.add_widget(lbl(lbl_txt, size=13, color=MUTED))
            inp = tinput(f"ለምሳሌ: {hint}", filt=filt)
            setattr(self, attr, inp)
            c1.add_widget(inp)
        bp = btn("📊  ትርፍ አሰላ", bg=ACCENT)
        bp.bind(on_release=self._calc_profit)
        c1.add_widget(bp)
        body.add_widget(c1)

        self.p_card = card(color=CARD2)
        self.p_card.add_widget(stitle("✅  የትርፍ ውጤት"))
        self.p_lbl = lbl("", size=14, h=20)
        self.p_card.add_widget(self.p_lbl)
        self.p_card.opacity = 0
        body.add_widget(self.p_card)
        body.add_widget(divider())

        c2 = card()
        c2.add_widget(stitle("💰  ደረጃ 4 — የበጀት ክፍፍል"))
        c2.add_widget(lbl("(አስቀድሞ ትርፍ ያሰሉ)", size=12, color=MUTED))
        bb = btn("💰  በጀት አሰላ", bg=GOLD, fg=get_color_from_hex("#0A0C10"))
        bb.bind(on_release=self._calc_budget)
        c2.add_widget(bb)
        body.add_widget(c2)

        self.b_card = card(color=CARD2)
        self.b_card.add_widget(stitle("📊  የበጀት ስርጭት"))
        self.b_lbl = lbl("", size=14, h=20)
        self.b_card.add_widget(self.b_lbl)
        self.b_card.opacity = 0
        body.add_widget(self.b_card)

        root.add_widget(sv)
        self.add_widget(root)

    def on_enter(self):
        names = all_item_names()
        self.item_sp.values = names
        self.item_sp.text   = names[0] if names else "-- እቃ የለም --"

    def _calc_profit(self, *_):
        try:
            landed = float(self.lnd_inp.text  or "0")
            qty    = float(self.qty_inp.text  or "0")
            ppu    = float(self.ppu_inp.text  or "0")
            days   = int(self.days_inp.text   or "0")
        except ValueError:
            popup("⚠️", "ቁጥሮቹን ትክክል ያስገቡ!", RED); return
        if landed <= 0: popup("⚠️", "መነሻ ዋጋ ያስገቡ!", RED); return
        if qty    <= 0: popup("⚠️", "ብዛት ከዜሮ በላይ!", RED); return
        if days   <= 0: popup("⚠️", "ቀናት ከዜሮ በላይ!", RED); return

        sale = landed + ppu
        tp   = qty * ppu
        ds   = qty / days
        dp_  = tp / days

        self._tp = tp; self._dp = dp_
        self.p_lbl.text = (
            f"💲 የሽያጭ ዋጋ/ነጠላ:  {sale:,.2f} ብር\n"
            f"💰 አጠቃላይ ትርፍ:   {tp:,.2f} ብር\n"
            f"📦 በቀን ሽያጭ:      {ds:.2f} ነጠላ\n"
            f"📈 በቀን ትርፍ:      {dp_:,.2f} ብር"
        )
        self.p_lbl.height   = _z(32 * 4 + 8)
        self.p_card.opacity = 1
        try:
            name = self.item_sp.text
            now  = datetime.now().strftime("%Y-%m-%d %H:%M")
            with _db() as conn:
                cur = conn.execute(
                    "INSERT INTO profit_plans"
                    "(item_name,landed_cost,qty,profit_per_unit,days_to_sell,"
                    " sale_price,total_profit,daily_sales,daily_profit,created_at)"
                    " VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (name, landed, qty, ppu, days, sale, tp, ds, dp_, now))
                self._plan_id = cur.lastrowid
        except Exception as e:
            popup("DB ስህተት", str(e), RED)

    def _calc_budget(self, *_):
        if self._tp <= 0:
            popup("ማስጠንቀቂያ", "አስቀድሞ ትርፍ ያሰሉ!", GOLD); return
        tp = self._tp; dp_ = self._dp; mon = dp_ * 30
        pcts = [("70% ማስፋፊያ",0.70),("20% ቋሚ ወጪ",0.20),
                ("5%  ድንገተኛ", 0.05),("5%  ለግል",   0.05)]
        txt = [f"💰 አጠቃላይ ትርፍ:  {tp:,.2f} ብር\n"]
        vals = []
        for label, pct in pcts:
            d = dp_ * pct; m = mon * pct; vals.append((d, m))
            txt.append(f"{label}:\n    ቀን={d:,.2f}  ወር={m:,.2f} ብር")
        self.b_lbl.text   = "\n".join(txt)
        self.b_lbl.height = _z(32 * (len(txt) + 2))
        self.b_card.opacity = 1
        if self._plan_id:
            try:
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                with _db() as conn:
                    conn.execute(
                        "INSERT INTO budget_plans"
                        "(plan_id,total_profit,daily_profit,monthly_profit,"
                        " exp_day,fix_day,emg_day,per_day,"
                        " exp_mon,fix_mon,emg_mon,per_mon,created_at)"
                        " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (self._plan_id, tp, dp_, mon,
                         vals[0][0],vals[1][0],vals[2][0],vals[3][0],
                         vals[0][1],vals[1][1],vals[2][1],vals[3][1], now))
            except Exception as e:
                popup("DB ስህተት", str(e), RED)

# ══════════════════════════════════════════════════════════════════════════════
#  SCREEN 5 — HISTORY
#  FIX-3: Tab colours mutated in-place via Color instruction refs.
#          NO repeated attach_bg() calls → zero canvas layer accumulation.
# ══════════════════════════════════════════════════════════════════════════════

class HistoryScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._tab = "ship"
        attach_bg(self, BG, 0)
        root = BoxLayout(orientation="vertical", spacing=0)
        root.add_widget(page_header("ታሪክ ማህደር", "🕐"))

        tabs = BoxLayout(size_hint_y=None, height=_z(52),
                         spacing=_z(8), padding=[_z(12), _z(7)])
        self.t_ship   = btn("📦 ጭነቶች",     bg=ACCENT, h=38, size=13)
        self.t_profit = btn("📈 ትርፍ ሪፖርት", bg=BORDER, fg=TEXT,
                            h=38, size=13, bold=False)

        # FIX-3: capture Color refs ONCE here — reuse forever
        self._c_ship   = _btn_color(self.t_ship)
        self._c_profit = _btn_color(self.t_profit)

        self.t_ship.bind(  on_release=lambda *_: self._switch("ship"))
        self.t_profit.bind(on_release=lambda *_: self._switch("profit"))
        tabs.add_widget(self.t_ship)
        tabs.add_widget(self.t_profit)
        root.add_widget(tabs)

        self.sv, self.body = scrollpage()
        root.add_widget(self.sv)
        self.add_widget(root)

    def on_enter(self):
        self._switch(self._tab)

    def _switch(self, tab):
        self._tab = tab
        # FIX-3: mutate rgba in-place — no new layer added to canvas
        if tab == "ship":
            if self._c_ship:   self._c_ship.rgba   = ACCENT
            if self._c_profit: self._c_profit.rgba = BORDER
            self.t_ship.color   = get_color_from_hex("#0A0C10")
            self.t_profit.color = TEXT
        else:
            if self._c_ship:   self._c_ship.rgba   = BORDER
            if self._c_profit: self._c_profit.rgba = ACCENT
            self.t_ship.color   = TEXT
            self.t_profit.color = get_color_from_hex("#0A0C10")
        self.body.clear_widgets()
        if tab == "ship": self._load_shipments()
        else:             self._load_profits()

    def _load_shipments(self):
        try:
            with _db() as conn:
                ships = conn.execute(
                    "SELECT * FROM shipments ORDER BY id DESC LIMIT 30"
                ).fetchall()
                lines_map = {
                    s["id"]: conn.execute(
                        "SELECT * FROM shipment_lines WHERE shipment_id=?",
                        (s["id"],)).fetchall()
                    for s in ships}
        except Exception as e:
            self.body.add_widget(lbl(f"ስህተት: {e}", color=RED)); return
        if not ships:
            self.body.add_widget(
                lbl("ምንም ጭነት አልተቀመጠም።", size=14, color=MUTED,
                    align="center")); return
        for s in ships:
            c = card()
            c.add_widget(lbl(f"📦 ጭነት #{s['id']}   {s['created_at']}",
                             size=14, color=ACCENT, bold=True, h=28))
            if s["note"]:
                c.add_widget(lbl(s["note"], size=12, color=MUTED, h=22))
            c.add_widget(lbl(f"ጠቅላላ ወጪ: {s['total_cost']:,.2f} ብር",
                             size=13, h=24))
            c.add_widget(divider())
            for ln in lines_map.get(s["id"], []):
                c.add_widget(lbl(
                    f"  • {ln['item_name']}  ×{ln['qty']:.0f}"
                    f"  ገዛ={ln['unit_buy']:.2f}"
                    f"  → {ln['landed_unit']:.2f} ብር",
                    size=12, color=MUTED, h=22))
            self.body.add_widget(c)

    def _load_profits(self):
        try:
            with _db() as conn:
                plans = conn.execute(
                    "SELECT p.*, b.exp_mon, b.fix_mon, b.emg_mon, b.per_mon "
                    "FROM profit_plans p "
                    "LEFT JOIN budget_plans b ON b.plan_id = p.id "
                    "ORDER BY p.id DESC LIMIT 30"
                ).fetchall()
        except Exception as e:
            self.body.add_widget(lbl(f"ስህተት: {e}", color=RED)); return
        if not plans:
            self.body.add_widget(
                lbl("ምንም ሪፖርት አልተቀመጠም።", size=14, color=MUTED,
                    align="center")); return
        for p in plans:
            c = card()
            c.add_widget(lbl(f"📈 {p['item_name']}   {p['created_at']}",
                             size=14, color=ACCENT, bold=True, h=28))
            c.add_widget(lbl(
                f"አጠቃላይ ትርፍ: {p['total_profit']:,.2f} ብር\n"
                f"የሽያጭ ዋጋ: {p['sale_price']:.2f}  |  "
                f"ቀናት: {p['days_to_sell']}  |  ቀናዊ ሽያጭ: {p['daily_sales']:.1f}",
                size=12, color=TEXT, h=48))
            if p["exp_mon"] is not None:
                c.add_widget(divider())
                c.add_widget(lbl(
                    f"70% ማስፋፊያ(ወር):  {p['exp_mon']:,.2f} ብር\n"
                    f"20% ቋሚ(ወር):      {p['fix_mon']:,.2f} ብር\n"
                    f"5%  ድንገተኛ(ወር):  {p['emg_mon']:,.2f} ብር\n"
                    f"5%  ለግል(ወር):     {p['per_mon']:,.2f} ብር",
                    size=12, color=MUTED, h=88))
            self.body.add_widget(c)

# ══════════════════════════════════════════════════════════════════════════════
#  APP — FIX-1 + FIX-4
# ══════════════════════════════════════════════════════════════════════════════

class BusinessApp(App):
    title = "የንግድ ስራ ረዳት"

    def build(self):
        # FIX-1: user_data_dir is ALWAYS writable on Android and desktop
        setup_db(os.path.join(self.user_data_dir, "business.db"))

        Window.clearcolor = BG
        root = BoxLayout(orientation="vertical", spacing=0)

        self.sm = ScreenManager(transition=FadeTransition(duration=0.15))
        for cls, name in [
            (HomeScreen,     "home"),
            (ShipmentScreen, "shipment"),
            (ProfitScreen,   "profit"),
            (HistoryScreen,  "history"),
        ]:
            self.sm.add_widget(cls(name=name))

        self.nav = NavBar(self.sm)
        self.sm.bind(current=lambda inst, val: self.nav.mark(val))
        root.add_widget(self.sm)
        root.add_widget(self.nav)
        self.nav.mark("home")
        return root


# FIX-4: correct class name (was kelalApp)
if __name__ == "__main__":
    BusinessApp().run()
