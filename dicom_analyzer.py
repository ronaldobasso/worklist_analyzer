import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import subprocess
import xml.etree.ElementTree as ET
import threading
import re
import os
import json
import sys
import glob
import shutil
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime

# ============================================================
# CONFIGURAÇÃO DAS CORES
# ============================================================
COLORS = {
    "PRIMARY_PURPLE": "#6c4bd6",
    "PRIMARY_PURPLE_DARK": "#4b2fa8",
    "PRIMARY_BLUE": "#3aa0e8",
    "PRIMARY_GREEN": "#21c89a",
    "PRIMARY_GREEN_DARK": "#1bb389",
    "BG_MAIN": "#eef1f7",
    "BG_CARD": "#ffffff",
    "BG_DARK": "#141f3d",
    "BG_INPUT": "#fbfcfe",
    "BG_ITEM": "#efeafc",
    "TEXT_DARK": "#141f3d",
    "TEXT_MEDIUM": "#1c2540",
    "TEXT_LIGHT": "#6b7694",
    "TEXT_WHITE": "#ffffff",
    "TEXT_MUTED": "#9fb0d4",
    "BORDER_LIGHT": "#dfe4f0",
    "BORDER_INPUT": "#ccd4e6",
    "BORDER_ITEM": "#e2e7f2",
    "BADGE_BG": "#efeafc",
    "BADGE_TEXT": "#4b2fa8",
    "HOVER_PURPLE": "#7a5ce0",
    "ROW_HOVER": "#f5f3ff",
    "ROW_ALT": "#fafafe",
}

def get_icon_path():
    """Retorna o caminho do ícone"""
    icon_path = Path(__file__).parent / "pixeon.ico"
    if icon_path.exists():
        return str(icon_path)
    return None

# ============================================================
# CLASSES DE WIDGETS PERSONALIZADOS
# ============================================================
class ModernButton(tk.Button):
    def __init__(self, master, text, command: Optional[Callable] = None, primary: bool = True, **kwargs):
        bg_color = COLORS["PRIMARY_PURPLE"] if primary else COLORS["PRIMARY_GREEN"]
        hover_color = COLORS["HOVER_PURPLE"] if primary else COLORS["PRIMARY_GREEN_DARK"]
        
        if command is None:
            command = lambda: None
        
        super().__init__(
            master,
            text=text,
            command=command,
            bg=bg_color,
            fg=COLORS["TEXT_WHITE"],
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2",
            **kwargs
        )
        
        self.bind("<Enter>", lambda e: self.config(bg=hover_color))
        self.bind("<Leave>", lambda e: self.config(bg=bg_color))

class ModernEntry(tk.Entry):
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            font=("Segoe UI", 10),
            bg=COLORS["BG_INPUT"],
            fg=COLORS["TEXT_DARK"],
            relief=tk.FLAT,
            highlightthickness=1,
            highlightcolor=COLORS["PRIMARY_PURPLE"],
            highlightbackground=COLORS["BORDER_INPUT"],
            **kwargs
        )
        self.config(insertbackground=COLORS["PRIMARY_PURPLE"])

# ============================================================
# CLASSE PRINCIPAL
# ============================================================
class DicomWorklistTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Worklist Analyzer")
        self.root.geometry("1400x900")
        self.root.configure(bg=COLORS["BG_MAIN"])
        
        # ============================================================
        # CONFIGURAR ÍCONE
        # ============================================================
        icon_path = get_icon_path()
        if icon_path:
            try:
                self.root.iconbitmap(default=icon_path)
            except:
                pass
        
        # ============================================================
        # VARIÁVEIS
        # ============================================================
        self.config_file = Path.home() / ".dicom_worklist_config.json"
        self.config = {}
        self.tree_items = {}
        self.log_entries = []
        self.worklist_entries = []
        self.processed_files = set()
        self.current_selected_patient = None
        self.temp_dir = None  # Pasta temporária para XMLs
        self.analysis_id = None  # ID único da análise
        
        # ============================================================
        # CARREGAR CONFIGURAÇÃO
        # ============================================================
        self.load_config()
        
        # ============================================================
        # CRIAR INTERFACE
        # ============================================================
        self.create_header()
        self.create_main_content()
        self.create_status_bar()
        self.center_window()
        
        # ============================================================
        # BIND DE TECLAS
        # ============================================================
        self.root.bind('<Control-q>', lambda e: self.root.quit())
        self.root.bind('<Control-Return>', lambda e: self.start_analysis())

    # ============================================================
    # CONFIGURAÇÃO
    # ============================================================
    def load_config(self):
        self.config = {
            "pacs_ae": "",
            "pacs_ip": "",
            "pacs_port": "104",
            "calling_ae": "WORKLIST_CLIENT",
            "dcmtk_path": "",
            "query_mode": "complete",
            "debug_mode": True
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    saved = json.load(f)
                    self.config.update(saved)
            except:
                pass

    def save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except:
            pass

    # ============================================================
    # HEADER
    # ============================================================
    def create_header(self):
        header = tk.Frame(self.root, bg=COLORS["BG_DARK"], height=80)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        
        title_frame = tk.Frame(header, bg=COLORS["BG_DARK"])
        title_frame.pack(side=tk.LEFT, padx=30, pady=15)
        
        icon_path = get_icon_path()
        if icon_path:
            try:
                icon_image = tk.PhotoImage(file=icon_path)
                icon_label = tk.Label(
                    title_frame,
                    image=icon_image,
                    bg=COLORS["BG_DARK"]
                )
                icon_label.image = icon_image  # type: ignore
                icon_label.pack(side=tk.LEFT, padx=(0, 10))
            except:
                icon_label = tk.Label(
                    title_frame,
                    text="DICOM",
                    font=("Segoe UI", 24, "bold"),
                    bg=COLORS["BG_DARK"],
                    fg=COLORS["PRIMARY_GREEN"]
                )
                icon_label.pack(side=tk.LEFT, padx=(0, 10))
        else:
            icon_label = tk.Label(
                title_frame,
                text="DICOM",
                font=("Segoe UI", 24, "bold"),
                bg=COLORS["BG_DARK"],
                fg=COLORS["PRIMARY_GREEN"]
            )
            icon_label.pack(side=tk.LEFT, padx=(0, 10))
        
        title_label = tk.Label(
            title_frame,
            text="Worklist Analyzer",
            font=("Segoe UI", 18, "bold"),
            bg=COLORS["BG_DARK"],
            fg=COLORS["TEXT_WHITE"]
        )
        title_label.pack(side=tk.LEFT)
        
        subtitle_label = tk.Label(
            title_frame,
            text="Worklist DICOM - Diagnóstico completo",
            font=("Segoe UI", 10),
            bg=COLORS["BG_DARK"],
            fg=COLORS["TEXT_MUTED"]
        )
        subtitle_label.pack(side=tk.LEFT, padx=(10, 0))
        
        version_label = tk.Label(
            header,
            text="⚡ Powered by Ronaldo",
            font=("Segoe UI", 9),
            bg=COLORS["BG_DARK"],
            fg=COLORS["TEXT_MUTED"]
        )
        version_label.pack(side=tk.RIGHT, padx=20)

    # ============================================================
    # CONTEÚDO PRINCIPAL
    # ============================================================
    def create_main_content(self):
        main_container = tk.Frame(self.root, bg=COLORS["BG_MAIN"])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        main_container.grid_rowconfigure(0, weight=0)
        main_container.grid_rowconfigure(1, weight=1)
        main_container.grid_columnconfigure(0, weight=2)
        main_container.grid_columnconfigure(1, weight=1)
        
        # ============================================================
        # CARD DE CONFIGURAÇÕES
        # ============================================================
        config_card = self.create_card(main_container, "🔧 Configurações do PACS")
        config_card.grid(row=0, column=0, sticky="ew", pady=(0, 20), padx=(0, 10))
        
        inputs_frame = tk.Frame(config_card, bg=COLORS["BG_CARD"])
        inputs_frame.pack(fill=tk.X, padx=20, pady=15)
        
        inputs_frame.grid_columnconfigure(1, weight=1)
        inputs_frame.grid_columnconfigure(3, weight=1)
        inputs_frame.grid_columnconfigure(5, weight=1)
        
        # Linha 1: PACS AE e IP
        tk.Label(inputs_frame, text="PACS AE Title:", font=("Segoe UI", 10), 
                bg=COLORS["BG_CARD"], fg=COLORS["TEXT_MEDIUM"]).grid(row=0, column=0, sticky="e", padx=(0, 10), pady=5)
        self.pacs_ae = ModernEntry(inputs_frame, width=20)
        self.pacs_ae.insert(0, self.config["pacs_ae"])
        self.pacs_ae.grid(row=0, column=1, sticky="ew", padx=(0, 20), pady=5)
        
        tk.Label(inputs_frame, text="PACS IP:", font=("Segoe UI", 10), 
                bg=COLORS["BG_CARD"], fg=COLORS["TEXT_MEDIUM"]).grid(row=0, column=2, sticky="e", padx=(0, 10), pady=5)
        self.pacs_ip = ModernEntry(inputs_frame, width=20)
        self.pacs_ip.insert(0, self.config["pacs_ip"])
        self.pacs_ip.grid(row=0, column=3, sticky="ew", padx=(0, 20), pady=5)
        
        tk.Label(inputs_frame, text="Porta:", font=("Segoe UI", 10), 
                bg=COLORS["BG_CARD"], fg=COLORS["TEXT_MEDIUM"]).grid(row=0, column=4, sticky="e", padx=(0, 10), pady=5)
        self.pacs_port = ModernEntry(inputs_frame, width=15)
        self.pacs_port.insert(0, self.config["pacs_port"])
        self.pacs_port.grid(row=0, column=5, sticky="ew", pady=5)
        
        # Linha 2: Calling AE e DCMTK Path
        tk.Label(inputs_frame, text="Calling AE Title:", font=("Segoe UI", 10), 
                bg=COLORS["BG_CARD"], fg=COLORS["TEXT_MEDIUM"]).grid(row=1, column=0, sticky="e", padx=(0, 10), pady=5)
        self.calling_ae = ModernEntry(inputs_frame, width=20)
        self.calling_ae.insert(0, self.config["calling_ae"])
        self.calling_ae.grid(row=1, column=1, sticky="ew", padx=(0, 20), pady=5)
        
        tk.Label(inputs_frame, text="DCMTK Path:", font=("Segoe UI", 10), 
                bg=COLORS["BG_CARD"], fg=COLORS["TEXT_MEDIUM"]).grid(row=1, column=2, sticky="e", padx=(0, 10), pady=5)
        
        dcmtk_frame = tk.Frame(inputs_frame, bg=COLORS["BG_CARD"])
        dcmtk_frame.grid(row=1, column=3, columnspan=2, sticky="ew", padx=(0, 20), pady=5)
        dcmtk_frame.grid_columnconfigure(0, weight=1)
        
        self.dcmtk_path = ModernEntry(dcmtk_frame)
        self.dcmtk_path.insert(0, self.config["dcmtk_path"])
        self.dcmtk_path.grid(row=0, column=0, sticky="ew")
        
        btn_browse = ModernButton(dcmtk_frame, text="📁", command=self.browse_dcmtk, primary=False, width=3)
        btn_browse.grid(row=0, column=1, padx=(5, 0))
        
        # Linha 3: Modo da Query
        tk.Label(inputs_frame, text="Modo da Query:", font=("Segoe UI", 10), 
                bg=COLORS["BG_CARD"], fg=COLORS["TEXT_MEDIUM"]).grid(row=2, column=0, sticky="e", padx=(0, 10), pady=5)
        
        self.query_mode = ttk.Combobox(
            inputs_frame,
            values=[
                "1. Mínimo (Apenas Paciente)",
                "2. Básico (Paciente + Estudo)",
                "3. Completo (sem sequências)",
                "4. GE Optimus 330 (com código)",
                "5. Busca com Data (últimos 30 dias)",
                "6. COMPLETO"
            ],
            state="readonly",
            width=50
        )
        self.query_mode.grid(row=2, column=1, columnspan=2, sticky="w", padx=(0, 20), pady=5)
        self.query_mode.set("6. COMPLETO")
        
        self.debug_mode = tk.BooleanVar(value=self.config.get("debug_mode", True))
        tk.Checkbutton(
            inputs_frame,
            text="🔍 Modo Debug (logs detalhados)",
            variable=self.debug_mode,
            bg=COLORS["BG_CARD"],
            fg=COLORS["TEXT_MEDIUM"],
            selectcolor=COLORS["BG_CARD"]
        ).grid(row=2, column=3, columnspan=2, sticky="w", padx=(0, 20), pady=5)
        
        btn_frame = tk.Frame(inputs_frame, bg=COLORS["BG_CARD"])
        btn_frame.grid(row=2, column=5, sticky="e", pady=5)
        
        self.btn_analyze = ModernButton(btn_frame, text="🔍 Analisar Worklist", command=self.start_analysis)
        self.btn_analyze.pack(side=tk.RIGHT)
        
        # ============================================================
        # CARD DE RESULTADOS
        # ============================================================
        results_card = self.create_card(main_container, "📋 Resultados da Análise")
        results_card.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        results_card.grid_rowconfigure(0, weight=1)
        results_card.grid_columnconfigure(0, weight=1)
        
        results_frame = tk.Frame(results_card, bg=COLORS["BG_CARD"])
        results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        self.notebook = ttk.Notebook(results_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        self.worklist_tab = tk.Frame(self.notebook, bg=COLORS["BG_CARD"])
        self.notebook.add(self.worklist_tab, text="📋 Worklist")
        
        self.tags_tab = tk.Frame(self.notebook, bg=COLORS["BG_CARD"])
        self.notebook.add(self.tags_tab, text="🏷️ Tags DICOM")
        
        self.create_worklist_view()
        self.create_tags_view()
        
        # ============================================================
        # CARD DE LOG
        # ============================================================
        log_card = self.create_card(main_container, "📝 Log de Comunicação")
        log_card.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(10, 0))
        log_card.grid_rowconfigure(0, weight=1)
        log_card.grid_columnconfigure(0, weight=1)
        
        log_frame = tk.Frame(log_card, bg=COLORS["BG_CARD"])
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        log_control_frame = tk.Frame(log_frame, bg=COLORS["BG_CARD"])
        log_control_frame.pack(fill=tk.X, pady=(0, 10))
        
        btn_clear_log = ModernButton(log_control_frame, text="🗑️ Limpar Log", command=self.clear_log, primary=False, width=12)
        btn_clear_log.pack(side=tk.LEFT)
        
        btn_save_log = ModernButton(log_control_frame, text="💾 Salvar Log", command=self.save_log, primary=False, width=12)
        btn_save_log.pack(side=tk.LEFT, padx=(10, 0))
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            font=("Consolas", 9),
            bg=COLORS["BG_DARK"],
            fg=COLORS["TEXT_WHITE"],
            height=20,
            wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        self.log_text.tag_config("INFO", foreground="#21c89a")
        self.log_text.tag_config("ERROR", foreground="#ff6b6b")
        self.log_text.tag_config("WARN", foreground="#ffd93d")
        self.log_text.tag_config("DEBUG", foreground="#3aa0e8")
        self.log_text.tag_config("COMMAND", foreground="#a29bfe")
        self.log_text.tag_config("RESPONSE", foreground="#fd79a8")

    # ============================================================
    # VIEWS
    # ============================================================
    def create_worklist_view(self):
        """Cria a visualização da worklist com suporte a scroll do mouse"""
        canvas = tk.Canvas(self.worklist_tab, bg=COLORS["BG_CARD"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.worklist_tab, orient="vertical", command=canvas.yview)
        self.worklist_container = tk.Frame(canvas, bg=COLORS["BG_CARD"])
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        canvas_window = canvas.create_window((0, 0), window=self.worklist_container, anchor="nw")
        
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas_window, width=event.width)
        
        # ============================================================
        # SUPORTE A SCROLL DO MOUSE
        # ============================================================
        def on_mousewheel(event):
            delta = -1 * (event.delta // 120) if event.delta else 0
            canvas.yview_scroll(delta, "units")
        
        def on_mousewheel_linux(event):
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")
        
        canvas.bind("<MouseWheel>", on_mousewheel)
        canvas.bind("<Button-4>", on_mousewheel_linux)
        canvas.bind("<Button-5>", on_mousewheel_linux)
        
        self.worklist_container.bind("<MouseWheel>", on_mousewheel)
        self.worklist_container.bind("<Button-4>", on_mousewheel_linux)
        self.worklist_container.bind("<Button-5>", on_mousewheel_linux)
        
        self.worklist_container.bind("<Configure>", on_frame_configure)

    def create_tags_view(self):
        """Cria a visualização das tags DICOM"""
        filter_frame = tk.Frame(self.tags_tab, bg=COLORS["BG_CARD"])
        filter_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        tk.Label(filter_frame, text="Filtrar:", font=("Segoe UI", 10),
                bg=COLORS["BG_CARD"], fg=COLORS["TEXT_MEDIUM"]).pack(side=tk.LEFT, padx=(0, 10))
        
        self.filter_entry = ModernEntry(filter_frame, width=30)
        self.filter_entry.pack(side=tk.LEFT)
        self.filter_entry.bind('<KeyRelease>', self.filter_results)
        
        btn_clear = ModernButton(filter_frame, text="✕ Limpar", command=self.clear_filter, primary=False, width=8)
        btn_clear.pack(side=tk.LEFT, padx=(10, 0))
        
        # ============================================================
        # INSTRUÇÃO PARA O USUÁRIO
        # ============================================================
        lbl_instrucao = tk.Label(
            filter_frame,
            text="💡 Clique em um paciente na guia Worklist para ver as tags",
            font=("Segoe UI", 9, "italic"),
            bg=COLORS["BG_CARD"],
            fg=COLORS["TEXT_MUTED"]
        )
        lbl_instrucao.pack(side=tk.RIGHT, padx=10)
        
        tree_frame = tk.Frame(self.tags_tab, bg=COLORS["BG_CARD"])
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        columns = ("Tag", "Nome", "VR", "Valor")
        
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="tree headings", height=20)
        
        self.tree.heading("#0", text="#")
        self.tree.heading("Tag", text="Tag (Group,Element)")
        self.tree.heading("Nome", text="Nome do Atributo")
        self.tree.heading("VR", text="VR")
        self.tree.heading("Valor", text="Valor")
        
        self.tree.column("#0", width=50, minwidth=50)
        self.tree.column("Tag", width=150, minwidth=120)
        self.tree.column("Nome", width=200, minwidth=150)
        self.tree.column("VR", width=80, minwidth=60)
        self.tree.column("Valor", width=400, minwidth=200)
        
        v_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        h_scroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        self.tree.bind('<Double-Button-1>', self.show_tag_details)

    # ============================================================
    # CARD
    # ============================================================
    def create_card(self, parent, title):
        card = tk.Frame(parent, bg=COLORS["BG_CARD"], relief=tk.FLAT,
                       highlightthickness=1, highlightcolor=COLORS["BORDER_LIGHT"],
                       highlightbackground=COLORS["BORDER_LIGHT"])
        
        title_frame = tk.Frame(card, bg=COLORS["BG_CARD"], height=45)
        title_frame.pack(fill=tk.X, side=tk.TOP)
        title_frame.pack_propagate(False)
        
        tk.Label(title_frame, text=title, font=("Segoe UI", 12, "bold"),
                bg=COLORS["BG_CARD"], fg=COLORS["TEXT_DARK"]).pack(side=tk.LEFT, padx=20)
        
        tk.Frame(card, bg=COLORS["BORDER_LIGHT"], height=1).pack(fill=tk.X, side=tk.TOP)
        return card

    # ============================================================
    # STATUS BAR
    # ============================================================
    def create_status_bar(self):
        status_frame = tk.Frame(self.root, bg=COLORS["BG_DARK"], height=30)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(status_frame, text="Pronto para análise",
                                    font=("Segoe UI", 9), bg=COLORS["BG_DARK"],
                                    fg=COLORS["TEXT_MUTED"], anchor="w")
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate', length=150)
        self.progress.pack(side=tk.RIGHT, padx=20)

    # ============================================================
    # UTILITÁRIOS
    # ============================================================
    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def browse_dcmtk(self):
        path = filedialog.askdirectory(title="Selecione a pasta do DCMTK")
        if path:
            self.dcmtk_path.delete(0, tk.END)
            self.dcmtk_path.insert(0, path)

    def clear_filter(self):
        self.filter_entry.delete(0, tk.END)
        self.filter_results()

    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
        self.log_entries.clear()

    def save_log(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"dicom_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                messagebox.showinfo("Sucesso", f"Log salvo em: {filename}")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar log: {str(e)}")

    def add_log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry, level)
        self.log_text.see(tk.END)
        self.log_text.update()
        
        if int(self.log_text.index('end-1c').split('.')[0]) > 1000:
            self.log_text.delete(1.0, 'end-1000l')

    def get_date_filter(self):
        from datetime import datetime, timedelta
        today = datetime.now()
        start_date = (today - timedelta(days=30)).strftime("%Y%m%d")
        end_date = today.strftime("%Y%m%d")
        return f"{start_date}-{end_date}"

    # ============================================================
    # ANÁLISE PRINCIPAL
    # ============================================================
    def start_analysis(self):
        if not all([self.pacs_ae.get(), self.pacs_ip.get(), self.pacs_port.get(), self.calling_ae.get()]):
            messagebox.showerror("Erro", "Preencha todos os campos obrigatórios")
            return
        
        self.config.update({
            "pacs_ae": self.pacs_ae.get(),
            "pacs_ip": self.pacs_ip.get(),
            "pacs_port": self.pacs_port.get(),
            "calling_ae": self.calling_ae.get(),
            "dcmtk_path": self.dcmtk_path.get(),
            "query_mode": self.query_mode.get(),
            "debug_mode": self.debug_mode.get()
        })
        self.save_config()
        
        # Limpar resultados anteriores
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.tree_items.clear()
        self.worklist_entries = []
        self.processed_files = set()
        self.current_selected_patient = None
        
        # ============================================================
        # CRIAR ID ÚNICO PARA ESTA ANÁLISE
        # ============================================================
        self.analysis_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        self.temp_dir = os.path.join(os.getcwd(), f"temp_{self.analysis_id}")
        
        # Criar pasta temporária
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        os.makedirs(self.temp_dir)
        
        if self.debug_mode.get():
            self.add_log(f"📁 Pasta temporária criada: {self.temp_dir}", "DEBUG")
        
        for widget in self.worklist_container.winfo_children():
            widget.destroy()
        
        loading_label = tk.Label(
            self.worklist_container,
            text="⏳ Carregando worklist...",
            font=("Segoe UI", 14),
            bg=COLORS["BG_CARD"],
            fg=COLORS["TEXT_MUTED"]
        )
        loading_label.pack(expand=True, pady=50)
        
        if self.debug_mode.get():
            self.add_log("="*60, "INFO")
            self.add_log("🚀 INICIANDO ANÁLISE", "INFO")
            self.add_log(f"PACS AE: {self.pacs_ae.get()}", "DEBUG")
            self.add_log(f"PACS IP: {self.pacs_ip.get()}:{self.pacs_port.get()}", "DEBUG")
            self.add_log(f"Calling AE: {self.calling_ae.get()}", "DEBUG")
            self.add_log(f"Modo: {self.query_mode.get()}", "DEBUG")
            self.add_log("="*60, "INFO")
        
        self.btn_analyze.config(state=tk.DISABLED)
        self.progress.start()
        self.status_label.config(text="Analisando worklist...")
        
        thread = threading.Thread(target=self.run_analysis)
        thread.daemon = True
        thread.start()

    def find_xml_files(self, search_dir=None):
        """Busca arquivos XML em múltiplos locais"""
        xml_files = []
        
        if search_dir and os.path.exists(search_dir):
            # Buscar apenas na pasta especificada
            for file in os.listdir(search_dir):
                if file.endswith('.xml'):
                    xml_files.append(os.path.join(search_dir, file))
            return xml_files
        
        # Busca normal em vários locais
        search_paths = [
            ".",
            os.path.dirname(os.path.abspath(__file__)),
            os.getcwd(),
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Documents"),
            os.path.dirname(os.path.abspath(sys.argv[0])),
        ]
        
        patterns = ["rsp*.xml", "findscu_*.xml", "response*.xml", "worklist*.xml", "*.xml"]
        
        for search_path in search_paths:
            if not os.path.exists(search_path):
                continue
                
            for pattern in patterns:
                search_pattern = os.path.join(search_path, pattern)
                found = glob.glob(search_pattern)
                for f in found:
                    abs_path = os.path.abspath(f)
                    if abs_path not in xml_files:
                        xml_files.append(abs_path)
        
        for search_path in search_paths:
            if not os.path.exists(search_path):
                continue
                
            for root, dirs, files in os.walk(search_path):
                for file in files:
                    if file.endswith('.xml') and ('rsp' in file.lower() or 'findscu' in file.lower()):
                        full_path = os.path.abspath(os.path.join(root, file))
                        if full_path not in xml_files:
                            xml_files.append(full_path)
        
        return xml_files

    def run_analysis(self):
        try:
            dcmtk_path = self.dcmtk_path.get()
            
            if dcmtk_path and os.path.exists(dcmtk_path):
                if os.name == 'nt':
                    findscu = os.path.join(dcmtk_path, "findscu.exe")
                else:
                    findscu = os.path.join(dcmtk_path, "findscu")
            else:
                findscu = "findscu"
            
            if not os.path.exists(findscu) and findscu != "findscu":
                raise FileNotFoundError(f"findscu não encontrado em: {findscu}")
            
            cmd = [
                findscu, "-v", "-W",
                "-aec", self.pacs_ae.get(),
                "-aet", self.calling_ae.get(),
                self.pacs_ip.get(),
                self.pacs_port.get(),
                "-k", "QueryRetrieveLevel=WORKLIST",
            ]
            
            mode = self.query_mode.get()
            
            # ============================================================
            # TAGS POR MODO
            # ============================================================
            if mode == "6. COMPLETO":
                tags = [
                    "0010,0010=*", "0010,0020=*", "0010,0030=*", "0010,0040=*",
                    "0010,1000=*", "0010,1001=*", "0010,1020=*", "0010,1030=*",
                    "0008,0020=*", "0008,0030=*", "0008,0050=*", "0008,0090=*",
                    "0008,1050=*", "0008,0005=*",
                    "0032,1032=*", "0032,1033=*", "0032,1060=*", "0040,1001=*",
                    "0008,0060=*",
                    "0020,000D=*", "0020,0010=*",
                    "0040,0002=*", "0040,0003=*", "0040,0004=*", "0040,0005=*",
                    "0040,0007=*", "0040,0020=*", "0040,0001=*", "0040,0010=*",
                    "0040,0006=*", "0010,0050=",
                ]
            elif mode == "1. Mínimo (Apenas Paciente)":
                tags = ["0010,0010=*", "0010,0020=*", "0010,0030=*", "0010,0040=*"]
            elif mode == "2. Básico (Paciente + Estudo)":
                tags = ["0008,0050=*", "0008,0020=*", "0008,0030=*", "0010,0010=*", "0010,0020=*", "0010,0030=*", "0010,0040=*", "0008,0090=*"]
            elif mode == "3. Completo (sem sequências)":
                tags = ["0008,0050=*", "0008,0020=*", "0008,0030=*", "0010,0010=*", "0010,0020=*", "0010,0030=*", "0010,0040=*", "0008,0090=*", "0032,1032=*"]
            elif mode == "4. GE Optimus 330 (com código)":
                tags = ["0008,0050=*", "0008,0020=*", "0008,0030=*", "0010,0010=*", "0010,0020=*", "0010,0030=*", "0010,0040=*", "0008,0090=*", "0032,1032=*"]
            elif mode == "5. Busca com Data (últimos 30 dias)":
                date_filter = self.get_date_filter()
                tags = ["0008,0050=*", f"0008,0020={date_filter}", "0008,0030=*", "0010,0010=*", "0010,0020=*", "0010,0030=*", "0010,0040=*", "0008,0090=*", "0032,1032=*"]
            
            for tag in tags:
                cmd.extend(["-k", tag])
            
            # ============================================================
            # TAG 0032,1064 COMO SEQUÊNCIA VAZIA
            # ============================================================
            if mode == "6. COMPLETO" or mode == "4. GE Optimus 330 (com código)":
                cmd.extend([
                    "-k", "0032,1064[0].0008,0100=",
                    "-k", "0032,1064[0].0008,0104=",
                    "-k", "0032,1064[0].0008,0102="
                ])
                if self.debug_mode.get():
                    self.add_log("📌 Enviando tag 0032,1064 como sequência vazia para teste", "INFO")
            
            cmd.append("--extract-xml")
                  
            if self.debug_mode.get():
                self.add_log("", "INFO")
                self.add_log(f"🔧 Comando completo:", "COMMAND")
                cmd_str = ' '.join(cmd)
                for i in range(0, len(cmd_str), 100):
                    self.add_log(f"  {cmd_str[i:i+100]}", "COMMAND")
                self.add_log("", "INFO")
                self.add_log("⏳ Aguardando resposta do PACS...", "INFO")
            
            # ============================================================
            # CORREÇÃO: Verificar se temp_dir existe antes de usar
            # ============================================================
            if self.temp_dir and os.path.exists(self.temp_dir):
                # Salvar o diretório atual e mudar para a pasta temporária
                original_dir = os.getcwd()
                os.chdir(self.temp_dir)
                
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                finally:
                    # Voltar para o diretório original
                    os.chdir(original_dir)
            else:
                # Fallback: executar no diretório atual
                self.add_log("⚠️ Pasta temporária não encontrada. Executando no diretório atual.", "WARN")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if self.debug_mode.get():
                self.add_log(f"✅ Comando executado. Código de retorno: {result.returncode}", "INFO")
                
                if result.stdout:
                    self.add_log("📥 STDOUT:", "DEBUG")
                    stdout_lines = result.stdout.split('\n')
                    for line in stdout_lines[:20]:
                        if line.strip():
                            self.add_log(f"  {line}", "RESPONSE")
                    if len(stdout_lines) > 20:
                        self.add_log(f"  ... e mais {len(stdout_lines) - 20} linhas", "DEBUG")
                
                if result.stderr:
                    self.add_log("⚠️ STDERR:", "WARN")
                    stderr_lines = result.stderr.split('\n')
                    for line in stderr_lines[:20]:
                        if line.strip():
                            if "Bad override key/path" in line or "Cannot insert value" in line:
                                self.add_log(f"  ❌ {line}", "ERROR")
                            else:
                                self.add_log(f"  {line}", "WARN")
                    if len(stderr_lines) > 20:
                        self.add_log(f"  ... e mais {len(stderr_lines) - 20} linhas", "WARN")
            
            # ============================================================
            # VERIFICAR SE OS XMLs FORAM GERADOS
            # ============================================================
            if self.temp_dir and os.path.exists(self.temp_dir):
                xml_files = self.find_xml_files(self.temp_dir)
                if self.debug_mode.get():
                    self.add_log(f"📁 XMLs na pasta temporária: {len(xml_files)}", "DEBUG")
                    for xml_file in xml_files:
                        self.add_log(f"  📄 {os.path.basename(xml_file)}", "DEBUG")
            
            self.root.after(0, self.process_results, result)
            
        except subprocess.TimeoutExpired:
            self.add_log("⏱️ TIMEOUT: O PACS não respondeu em 30 segundos", "ERROR")
            self.root.after(0, self.show_error, "Timeout: O PACS não respondeu em 30 segundos")
        except Exception as e:
            error_msg = f"Erro durante análise: {str(e)}"
            self.add_log(f"❌ {error_msg}", "ERROR")
            self.root.after(0, self.show_error, error_msg)

    # ============================================================
    # PROCESSAMENTO DOS RESULTADOS
    # ============================================================
    def process_results(self, result):
        self.progress.stop()
        self.btn_analyze.config(state=tk.NORMAL)
        
        if result.returncode != 0:
            error_msg = f"Erro ao executar findscu (código {result.returncode})"
            if result.stderr:
                error_msg += f"\n\nDetalhes:\n{result.stderr}"
            self.add_log(f"❌ {error_msg}", "ERROR")
            self.show_error(error_msg)
            
            # Limpar pasta temporária em caso de erro
            if self.temp_dir and os.path.exists(self.temp_dir):
                try:
                    shutil.rmtree(self.temp_dir)
                    self.add_log(f"🗑️ Pasta temporária removida: {self.temp_dir}", "DEBUG")
                except:
                    pass
            return
        
        # ============================================================
        # BUSCAR XMLs APENAS NA PASTA TEMPORÁRIA
        # ============================================================
        xml_files = []
        if self.temp_dir and os.path.exists(self.temp_dir):
            xml_files = self.find_xml_files(self.temp_dir)
        else:
            # Fallback: buscar no diretório atual
            xml_files = self.find_xml_files()
            self.add_log("⚠️ Pasta temporária não encontrada. Buscando XMLs no diretório atual.", "WARN")
        
        if self.debug_mode.get():
            self.add_log(f"📁 Arquivos XML encontrados: {len(xml_files)}", "DEBUG")
            for xml_file in xml_files:
                self.add_log(f"  📄 {os.path.basename(xml_file)}", "DEBUG")
        
        if not xml_files:
            self.status_label.config(text="Nenhum arquivo XML encontrado")
            self.add_log("⚠️ Nenhum arquivo XML encontrado", "WARN")
            messagebox.showinfo("Aviso", "Nenhum arquivo XML de resposta encontrado")
            
            # Limpar pasta temporária
            if self.temp_dir and os.path.exists(self.temp_dir):
                try:
                    shutil.rmtree(self.temp_dir)
                    self.add_log(f"🗑️ Pasta temporária removida: {self.temp_dir}", "DEBUG")
                except:
                    pass
            return
        
        tags_found = set()
        total_items = 0
        
        # ============================================================
        # CORREÇÃO: Usar set para rastrear combinações únicas
        # ============================================================
        processed_combinations = set()  # (patient_id, accession) ou (patient_id, study_date)
        
        for xml_file in set(xml_files):
            try:
                if not os.path.exists(xml_file):
                    continue
                
                self.add_log(f"📄 Processando: {os.path.basename(xml_file)}", "DEBUG")
                
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                patient_data = {}
                
                for elem in root.findall('.//element'):
                    tag = elem.get('tag', '')
                    name = elem.get('name', '')
                    vr = elem.get('vr', '')
                    value = elem.text.strip() if elem.text else ''
                    
                    if tag and name:
                        patient_data[tag] = {
                            "name": name,
                            "vr": vr,
                            "value": value
                        }
                        
                        existing = False
                        for item in self.tree.get_children():
                            values = self.tree.item(item)['values']
                            if values and values[0] == tag:
                                existing = True
                                break
                        
                        if not existing:
                            item_id = self.tree.insert(
                                "", "end",
                                values=(tag, name, vr, value[:100])
                            )
                            self.tree_items[item_id] = {
                                "full_value": value,
                                "tag": tag,
                                "name": name,
                                "vr": vr
                            }
                            tags_found.add(tag)
                
                if patient_data:
                    patient_id = patient_data.get("0010,0020", {}).get("value", "")
                    accession = patient_data.get("0008,0050", {}).get("value", "")
                    study_date = patient_data.get("0008,0020", {}).get("value", "")
                    
                    # ============================================================
                    # CORREÇÃO: Criar chave única combinando ID + Accession + Data
                    # ============================================================
                    unique_key = f"{patient_id}_{accession}_{study_date}"
                    
                    if unique_key in processed_combinations:
                        self.add_log(f"⏭️ Exame duplicado ignorado: {unique_key}", "DEBUG")
                    else:
                        processed_combinations.add(unique_key)
                        self.worklist_entries.append(patient_data)
                        total_items += 1
                        
                        patient_name = patient_data.get("0010,0010", {}).get("value", "N/A")
                        self.add_log(f"✅ Paciente: {patient_name} (ID: {patient_id}, Acc: {accession})", "DEBUG")
                        
                        if self.debug_mode.get():
                            self.add_log(f"   Tags encontradas: {len(patient_data)}", "DEBUG")
                            if "0032,1064" in patient_data:
                                self.add_log("   🎯 TAG (0032,1064) ENCONTRADA!", "INFO")
                                self.add_log(f"      Valor: {patient_data['0032,1064']['value'][:100]}", "INFO")
                
            except ET.ParseError as e:
                self.add_log(f"❌ Erro ao parsear XML {xml_file}: {str(e)}", "ERROR")
            except Exception as e:
                self.add_log(f"❌ Erro ao processar {xml_file}: {str(e)}", "ERROR")
        
        # ============================================================
        # REMOVER APENAS A PASTA TEMPORÁRIA COMPLETA
        # ============================================================
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                self.add_log(f"🗑️ Pasta temporária removida: {self.temp_dir}", "DEBUG")
            except Exception as e:
                self.add_log(f"⚠️ Não foi possível remover pasta temporária: {e}", "WARN")
        
        self.root.after(0, self.display_worklist)
        
        status_msg = f"✅ Análise concluída: {total_items} pacientes, {len(tags_found)} tags"
        self.status_label.config(text=status_msg)
        self.add_log(status_msg, "INFO")
        
        if total_items == 0:
            self.add_log("⚠️ Nenhum paciente encontrado", "WARN")
        else:
            self.add_log(f"📊 Total: {total_items} paciente(s)", "INFO")
        
        self.check_specific_tag()

    # ============================================================
    # EXIBIÇÃO DA WORKLIST
    # ============================================================
    def display_worklist(self):
        """Exibe a worklist com cards e seleciona o primeiro automaticamente"""
        for widget in self.worklist_container.winfo_children():
            widget.destroy()
        
        if not self.worklist_entries:
            empty_label = tk.Label(
                self.worklist_container,
                text="📭 Nenhum paciente encontrado na worklist",
                font=("Segoe UI", 14),
                bg=COLORS["BG_CARD"],
                fg=COLORS["TEXT_MUTED"]
            )
            empty_label.pack(expand=True, pady=50)
            return
        
        first_card = None
        
        for idx, entry in enumerate(self.worklist_entries, 1):
            card = self.create_patient_card(self.worklist_container, entry, idx)
            card.pack(fill=tk.X, pady=(0, 10), padx=5)
            
            if idx == 1:
                first_card = card
        
        # Selecionar o primeiro card automaticamente
        if first_card:
            first_card.event_generate("<Button-1>")

    def create_patient_card(self, parent, data, index):
        """Cria um card para um paciente com clique para selecionar"""
        card = tk.Frame(parent, bg=COLORS["BG_CARD"], relief=tk.FLAT,
                       highlightthickness=2, highlightcolor=COLORS["BORDER_LIGHT"],
                       highlightbackground=COLORS["BORDER_LIGHT"])
        
        # ============================================================
        # ARMAZENAR DADOS DO PACIENTE
        # ============================================================
        card.patient_data = data  # type: ignore
        card.patient_index = index  # type: ignore
        
        def select_patient(event=None):
            # Remover destaque de todos os cards
            for widget in parent.winfo_children():
                if hasattr(widget, 'patient_data'):
                    widget.config(highlightbackground=COLORS["BORDER_LIGHT"])
                    widget.config(highlightcolor=COLORS["BORDER_LIGHT"])
            
            # Destacar este card
            card.config(highlightbackground=COLORS["PRIMARY_PURPLE"])
            card.config(highlightcolor=COLORS["PRIMARY_PURPLE"])
            
            # Atualizar as tags na guia Tags DICOM
            self.display_patient_tags(data)
            
            # Mudar para a guia Tags DICOM automaticamente
            self.notebook.select(self.tags_tab)
        
        # ============================================================
        # BIND DE CLIQUE
        # ============================================================
        card.bind("<Button-1>", select_patient)
        
        # Cabeçalho
        header_frame = tk.Frame(card, bg=COLORS["PRIMARY_PURPLE"], height=35)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        header_frame.bind("<Button-1>", select_patient)
        
        # Nome do paciente
        patient_name = data.get("0010,0010", {}).get("value", "N/A")
        lbl_name = tk.Label(
            header_frame,
            text=f"👤 {patient_name}",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["PRIMARY_PURPLE"],
            fg=COLORS["TEXT_WHITE"],
            cursor="hand2"
        )
        lbl_name.pack(side=tk.LEFT, padx=15)
        lbl_name.bind("<Button-1>", select_patient)
        
        # ID
        patient_id = data.get("0010,0020", {}).get("value", "N/A")
        lbl_id = tk.Label(
            header_frame,
            text=f"ID: {patient_id}",
            font=("Segoe UI", 10),
            bg=COLORS["PRIMARY_PURPLE"],
            fg=COLORS["TEXT_WHITE"],
            cursor="hand2"
        )
        lbl_id.pack(side=tk.LEFT, padx=15)
        lbl_id.bind("<Button-1>", select_patient)
        
        # Accession
        accession = data.get("0008,0050", {}).get("value", "N/A")
        lbl_acc = tk.Label(
            header_frame,
            text=f"Acc: {accession}",
            font=("Segoe UI", 10),
            bg=COLORS["PRIMARY_PURPLE"],
            fg=COLORS["TEXT_WHITE"],
            cursor="hand2"
        )
        lbl_acc.pack(side=tk.LEFT, padx=15)
        lbl_acc.bind("<Button-1>", select_patient)
        
        # Conteúdo
        content_frame = tk.Frame(card, bg=COLORS["BG_CARD"])
        content_frame.pack(fill=tk.X, padx=15, pady=10)
        content_frame.bind("<Button-1>", select_patient)
        
        field_map = {
            "0010,0010": ("👤 Nome", "patient_name"),
            "0010,0020": ("🆔 ID", "patient_id"),
            "0010,0030": ("🎂 Nascimento", "birth_date"),
            "0010,0040": ("⚥ Sexo", "sex"),
            "0008,0020": ("📅 Data Estudo", "study_date"),
            "0008,0030": ("🕐 Hora Estudo", "study_time"),
            "0008,0050": ("📋 Accession", "accession"),
            "0008,0090": ("👨‍⚕️ Médico Solicitante", "referring"),
            "0032,1032": ("👨‍⚕️ Médico Requisitante", "requesting"),
            "0032,1060": ("📝 Descrição Procedimento", "req_procedure_desc"),
            "0032,1064": ("🔑 Código Procedimento", "req_procedure_code"),
            "0008,0060": ("📷 Modalidade", "modality"),
            "0020,0010": ("🔢 Study ID", "study_id"),
        }
        
        row = 0
        col = 0
        displayed = 0
        
        for tag, (display_name, _) in field_map.items():
            if tag in data:
                value = data[tag].get("value", "")
                if value and value != "*":
                    bg_color = COLORS["BG_ITEM"] if tag == "0032,1064" else COLORS["BG_CARD"]
                    
                    field_frame = tk.Frame(content_frame, bg=bg_color)
                    field_frame.grid(row=row, column=col, sticky="w", padx=(0, 20), pady=3)
                    field_frame.bind("<Button-1>", select_patient)
                    
                    lbl = tk.Label(
                        field_frame,
                        text=f"{display_name}:",
                        font=("Segoe UI", 9, "bold"),
                        bg=bg_color,
                        fg=COLORS["TEXT_MEDIUM"],
                        cursor="hand2"
                    )
                    lbl.pack(side=tk.LEFT)
                    lbl.bind("<Button-1>", select_patient)
                    
                    lbl_val = tk.Label(
                        field_frame,
                        text=value,
                        font=("Segoe UI", 9),
                        bg=bg_color,
                        fg=COLORS["TEXT_DARK"],
                        cursor="hand2"
                    )
                    lbl_val.pack(side=tk.LEFT, padx=(5, 0))
                    lbl_val.bind("<Button-1>", select_patient)
                    
                    displayed += 1
                    col += 1
                    if col >= 2:
                        col = 0
                        row += 1
        
        if displayed == 0:
            lbl_empty = tk.Label(
                content_frame,
                text="📭 Nenhum dado adicional disponível",
                font=("Segoe UI", 9, "italic"),
                bg=COLORS["BG_CARD"],
                fg=COLORS["TEXT_MUTED"],
                cursor="hand2"
            )
            lbl_empty.grid(row=0, column=0, columnspan=2, pady=5)
            lbl_empty.bind("<Button-1>", select_patient)
        
        return card

    # ============================================================
    # EXIBIÇÃO DAS TAGS DO PACIENTE SELECIONADO
    # ============================================================
    def display_patient_tags(self, data):
        """Exibe as tags DICOM do paciente selecionado na guia Tags DICOM"""
        # Limpar a treeview atual
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Limpar o dicionário de itens
        self.tree_items.clear()
        
        if not data:
            return
        
        # Adicionar todas as tags do paciente selecionado
        for tag, info in data.items():
            name = info.get("name", "")
            vr = info.get("vr", "")
            value = info.get("value", "")
            
            if tag and name:
                item_id = self.tree.insert(
                    "", "end",
                    values=(tag, name, vr, value[:100])
                )
                self.tree_items[item_id] = {
                    "full_value": value,
                    "tag": tag,
                    "name": name,
                    "vr": vr
                }
        
        # Verificar se a tag 0032,1064 está presente
        if "0032,1064" in data:
            self.add_log(f"✅ Tags do paciente exibidas (tag 0032,1064 encontrada)", "INFO")
        else:
            self.add_log(f"ℹ️ Tags do paciente exibidas (tag 0032,1064 não encontrada)", "DEBUG")

    # ============================================================
    # FILTRO E DETALHES
    # ============================================================
    def filter_results(self, event=None):
        filter_text = self.filter_entry.get().lower()
        
        if not filter_text:
            for item in self.tree.get_children():
                self.tree.reattach(item, "", "end")
            return
        
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            if not values:
                continue
                
            show = False
            for val in values:
                if filter_text in str(val).lower():
                    show = True
                    break
            
            if show:
                self.tree.reattach(item, "", "end")
            else:
                self.tree.detach(item)

    def show_tag_details(self, event):
        selection = self.tree.selection()
        if not selection:
            return
            
        item = selection[0]
        
        if item in self.tree_items:
            info = self.tree_items[item]
            tag_info = f"""
        Tag: {info['tag']}
        Nome: {info['name']}
        VR: {info['vr']}
        
        Valor Completo:
        {info['full_value']}
        """
        else:
            values = self.tree.item(item)['values']
            if not values:
                return
            tag_info = f"""
        Tag: {values[0]}
        Nome: {values[1]}
        VR: {values[2]}
        
        Valor:
        {values[3]}
        """
        
        messagebox.showinfo("Detalhes da Tag DICOM", tag_info)

    # ============================================================
    # VERIFICAÇÃO DA TAG ESPECÍFICA
    # ============================================================
    def check_specific_tag(self):
        found = False
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            if values and "0032,1064" in values[0]:
                found = True
                self.tree.item(item, tags=('highlight',))
                self.tree.tag_configure('highlight', background=COLORS["BG_ITEM"])
                self.add_log("🎯 TAG (0032,1064) ENCONTRADA na resposta do PACS!", "INFO")
                break
        
        if not found:
            self.add_log("⚠️ Tag (0032,1064) NÃO encontrada na resposta do PACS", "WARN")
            self.add_log("💡 O PACS não está enviando a tag Requested Procedure Code Sequence", "INFO")

    # ============================================================
    # ERROS
    # ============================================================
    def show_error(self, message):
        self.progress.stop()
        self.btn_analyze.config(state=tk.NORMAL)
        self.status_label.config(text=f"❌ Erro: {message[:50]}...")
        self.add_log(f"❌ {message}", "ERROR")
        messagebox.showerror("Erro", message)

# ============================================================
# MAIN
# ============================================================
def main():
    root = tk.Tk()
    app = DicomWorklistTool(root)
    root.mainloop()

if __name__ == "__main__":
    main()