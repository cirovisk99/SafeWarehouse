"""
SafeWarehouse — Interface Gráfica (CP5)
Monitoramento de Risco em Área de Estoque
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
from datetime import datetime

ARQUIVO_CSV_PADRAO = "dados_safewarehouse.csv"
DISTANCIA_PRESENCA = 100   # cm — presença detectada (abaixo disso, mas acima do limite de risco)


class SafeWarehouseApp:

    def __init__(self, root):
        self.root = root
        self.root.title("SafeWarehouse — Monitoramento de Risco")
        self.root.geometry("960x680")
        self.root.resizable(True, True)

        self.registros = []

        self.var_limite_eventos = tk.IntVar(value=5)

        self._build_menu()
        self._build_analise()
        self._mostrar_menu()

    # =========================================================================
    # MENU PRINCIPAL
    # =========================================================================
    def _build_menu(self):
        self.frame_menu = tk.Frame(self.root, bg="#1e2a38")

        tk.Label(
            self.frame_menu, text="SafeWarehouse",
            font=("Segoe UI", 30, "bold"), bg="#1e2a38", fg="white"
        ).pack(pady=(60, 5))

        tk.Label(
            self.frame_menu, text="Monitoramento de Risco em Área de Estoque",
            font=("Segoe UI", 12), bg="#1e2a38", fg="#aab8c2"
        ).pack(pady=(0, 50))

        estilo_btn = dict(font=("Segoe UI", 13), width=26, height=2,
                          cursor="hand2", bd=0, relief="flat", fg="white")

        tk.Button(
            self.frame_menu, text="  Carregar Dados",
            bg="#2980b9", command=self._carregar_dados, **estilo_btn
        ).pack(pady=12)

        tk.Button(
            self.frame_menu, text="  Analisar Registros",
            bg="#27ae60", command=self._mostrar_analise, **estilo_btn
        ).pack(pady=12)

        self.label_status_menu = tk.Label(
            self.frame_menu, text="Nenhum dado carregado.",
            font=("Segoe UI", 10), bg="#1e2a38", fg="#aab8c2"
        )
        self.label_status_menu.pack(pady=(40, 0))

    # =========================================================================
    # ABA DE ANÁLISE
    # =========================================================================
    def _build_analise(self):
        self.frame_analise = tk.Frame(self.root, bg="#f0f2f5")

        # ── Barra superior ────────────────────────────────────────────────────
        barra = tk.Frame(self.frame_analise, bg="#1e2a38", pady=8)
        barra.pack(fill="x")

        tk.Button(
            barra, text="  Menu", font=("Segoe UI", 10),
            bg="#34495e", fg="white", bd=0, padx=14, pady=5,
            cursor="hand2", command=self._mostrar_menu
        ).pack(side="left", padx=10)

        tk.Label(
            barra, text="Análise de Registros",
            font=("Segoe UI", 13, "bold"), bg="#1e2a38", fg="white"
        ).pack(side="left", padx=8)

        # ── Área de conteúdo com scroll ───────────────────────────────────────
        conteudo = tk.Frame(self.frame_analise, bg="#f0f2f5")
        conteudo.pack(fill="both", expand=True, padx=20, pady=12)

        # ── Filtro de período ─────────────────────────────────────────────────
        filtro = ttk.LabelFrame(conteudo, text=" Período de análise ", padding=10)
        filtro.pack(fill="x", pady=(0, 10))

        tk.Label(filtro, text="Início:").grid(row=0, column=0, padx=5)
        self.entry_inicio = ttk.Entry(filtro, width=20)
        self.entry_inicio.insert(0, "2026-01-01 00:00:00")
        self.entry_inicio.grid(row=0, column=1, padx=5)

        tk.Label(filtro, text="Fim:").grid(row=0, column=2, padx=(20, 5))
        self.entry_fim = ttk.Entry(filtro, width=20)
        self.entry_fim.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.entry_fim.grid(row=0, column=3, padx=5)

        tk.Label(filtro, text="formato: AAAA-MM-DD HH:MM:SS", fg="gray",
                 font=("Segoe UI", 8)).grid(row=0, column=4, padx=12)

        ttk.Button(filtro, text="Filtrar", command=self._aplicar_filtro
                   ).grid(row=0, column=5, padx=10)

        # ── Indicadores ───────────────────────────────────────────────────────
        ind = ttk.LabelFrame(conteudo, text=" Indicadores ", padding=12)
        ind.pack(fill="x", pady=(0, 10))

        self.var_total   = tk.StringVar(value="—")
        self.var_riscos  = tk.StringVar(value="—")
        self.var_seguros = tk.StringVar(value="—")
        self.var_pct     = tk.StringVar(value="—")

        cards = [
            ("Total de Leituras", self.var_total,   "#2980b9"),
            ("Eventos RISCO",     self.var_riscos,  "#e74c3c"),
            ("Eventos SEGURO",    self.var_seguros, "#27ae60"),
            ("% Risco",           self.var_pct,     "#e67e22"),
        ]
        for i, (titulo, var, cor) in enumerate(cards):
            f = tk.Frame(ind, bg=cor, padx=20, pady=10)
            f.grid(row=0, column=i, padx=8, sticky="nsew")
            ind.columnconfigure(i, weight=1)
            tk.Label(f, textvariable=var, font=("Segoe UI", 24, "bold"),
                     bg=cor, fg="white").pack()
            tk.Label(f, text=titulo, font=("Segoe UI", 9),
                     bg=cor, fg="white").pack()

        # ── Configuração de limites ───────────────────────────────────────────
        cfg = ttk.LabelFrame(conteudo, text=" Configuração de limites ", padding=10)
        cfg.pack(fill="x", pady=(0, 10))

        tk.Label(cfg, text="Máx. eventos RISCO:").grid(row=0, column=0, padx=5, sticky="w")
        ttk.Entry(cfg, textvariable=self.var_limite_eventos, width=8
                  ).grid(row=0, column=1, padx=5)

        ttk.Button(cfg, text="Aplicar", command=self._aplicar_filtro
                   ).grid(row=0, column=2, padx=20)

        # ── Banner de alerta (sempre presente, muda de aparência) ────────────
        self.label_alerta = tk.Label(
            conteudo, text="",
            font=("Segoe UI", 12, "bold"), bg="#f0f2f5", fg="#f0f2f5"
        )
        self.label_alerta.pack(fill="x")

        # ── Botões de listagem ────────────────────────────────────────────────
        btns = tk.Frame(conteudo, bg="#f0f2f5")
        btns.pack(fill="x", pady=(0, 10))

        ttk.Button(
            btns, text="  Listar Eventos de Risco",
            command=self._listar_risco
        ).pack(side="left", padx=(0, 10))

        ttk.Button(
            btns, text="  Listar Registros de Presença",
            command=self._listar_presenca
        ).pack(side="left")

        self.label_descricao_tabela = tk.Label(
            btns, text="", font=("Segoe UI", 9, "italic"),
            bg="#f0f2f5", fg="#666"
        )
        self.label_descricao_tabela.pack(side="left", padx=15)

        # ── Tabela de resultados ──────────────────────────────────────────────
        tab_frame = tk.Frame(conteudo, bg="#f0f2f5")
        tab_frame.pack(fill="both", expand=True)

        colunas = ("timestamp", "temp", "umidade", "distancia", "estado")
        self.tree = ttk.Treeview(tab_frame, columns=colunas, show="headings", height=10)

        cabecalhos = {
            "timestamp": ("Timestamp",      170),
            "temp":      ("Temp (°C)",       90),
            "umidade":   ("Umidade (%)",    100),
            "distancia": ("Distância (cm)", 120),
            "estado":    ("Estado",          90),
        }
        for col, (texto, largura) in cabecalhos.items():
            self.tree.heading(col, text=texto)
            self.tree.column(col, width=largura, anchor="center")

        self.tree.tag_configure("risco",   background="#fde8e8", foreground="#c0392b")
        self.tree.tag_configure("seguro",  background="#e8f8ee", foreground="#1e8449")
        self.tree.tag_configure("presenca", background="#fef9e7", foreground="#9a6a00")

        scroll_y = ttk.Scrollbar(tab_frame, orient="vertical",   command=self.tree.yview)
        scroll_x = ttk.Scrollbar(tab_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        scroll_y.pack(side="right",  fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

    # =========================================================================
    # NAVEGAÇÃO
    # =========================================================================
    def _mostrar_menu(self):
        self.frame_analise.pack_forget()
        self.frame_menu.pack(fill="both", expand=True)

    def _mostrar_analise(self):
        if not self.registros:
            messagebox.showwarning("Sem dados", "Carregue um arquivo CSV antes de analisar.")
            return
        self.frame_menu.pack_forget()
        self.frame_analise.pack(fill="both", expand=True)
        self._aplicar_filtro()

    # =========================================================================
    # CARREGAR CSV
    # =========================================================================
    def _carregar_dados(self):
        caminho = filedialog.askopenfilename(
            title="Selecionar arquivo CSV",
            filetypes=[("CSV files", "*.csv"), ("Todos os arquivos", "*.*")],
            initialfile=ARQUIVO_CSV_PADRAO
        )
        if not caminho:
            return

        try:
            self.registros = []
            with open(caminho, newline="", encoding="utf-8") as f:
                for linha in csv.DictReader(f):
                    self.registros.append({
                        "timestamp": linha["timestamp"],
                        "temp":      float(linha["temp"]),
                        "umidade":   float(linha["umidade"]),
                        "distancia": int(linha["distancia"]),
                        "estado":    linha["estado"].strip()
                    })

            nome = caminho.replace("\\", "/").split("/")[-1]
            self.label_status_menu.config(
                text=f"  {len(self.registros)} registros carregados — {nome}",
                fg="#2ecc71"
            )
            messagebox.showinfo("Dados carregados",
                                f"{len(self.registros)} registros carregados com sucesso.")
        except Exception as e:
            messagebox.showerror("Erro ao carregar", str(e))

    # =========================================================================
    # FILTROS E INDICADORES
    # =========================================================================
    def _registros_filtrados(self):
        fmt = "%Y-%m-%d %H:%M:%S"
        try:
            inicio = datetime.strptime(self.entry_inicio.get().strip(), fmt)
            fim    = datetime.strptime(self.entry_fim.get().strip(),    fmt)
        except ValueError:
            messagebox.showerror("Formato inválido",
                                 "Use o formato: AAAA-MM-DD HH:MM:SS")
            return None

        return [
            r for r in self.registros
            if inicio <= datetime.strptime(r["timestamp"], fmt) <= fim
        ]

    def _aplicar_filtro(self):
        filtrados = self._registros_filtrados()
        if filtrados is None:
            return

        total   = len(filtrados)
        riscos  = sum(1 for r in filtrados if r["estado"] == "RISCO")
        seguros = total - riscos
        pct     = (riscos / total * 100) if total > 0 else 0

        self.var_total.set(str(total))
        self.var_riscos.set(str(riscos))
        self.var_seguros.set(str(seguros))
        self.var_pct.set(f"{pct:.1f}%")

        if riscos > self.var_limite_eventos.get():
            self.label_alerta.config(
                text="  ALERTA: alto número de eventos de risco no depósito",
                bg="#e74c3c", fg="white", pady=10
            )
        else:
            self.label_alerta.config(text="", bg="#f0f2f5", fg="#f0f2f5", pady=0)

        self._limpar_tabela()
        self.label_descricao_tabela.config(text="")

    # =========================================================================
    # TABELA
    # =========================================================================
    def _limpar_tabela(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

    def _preencher_tabela(self, registros, tag_padrao="seguro"):
        self._limpar_tabela()
        for r in registros:
            if r["estado"] == "RISCO":
                tag = "risco"
            elif tag_padrao == "presenca":
                tag = "presenca"
            else:
                tag = "seguro"
            self.tree.insert("", "end", values=(
                r["timestamp"],
                f"{r['temp']:.1f}",
                f"{r['umidade']:.0f}",
                r["distancia"],
                r["estado"]
            ), tags=(tag,))

    # =========================================================================
    # LISTAGENS
    # =========================================================================
    def _listar_risco(self):
        filtrados = self._registros_filtrados()
        if filtrados is None:
            return
        eventos = [r for r in filtrados if r["estado"] == "RISCO"]
        self._preencher_tabela(eventos)
        self.label_descricao_tabela.config(
            text=f"Eventos de Risco  ({len(eventos)} registros)"
        )
        if not eventos:
            messagebox.showinfo("Resultado", "Nenhum evento de risco no período selecionado.")

    def _listar_presenca(self):
        filtrados = self._registros_filtrados()
        if filtrados is None:
            return
        # Presença: SEGURO mas com distância < 100 cm (objeto próximo, sem risco)
        presenca = [r for r in filtrados
                    if r["estado"] == "SEGURO" and r["distancia"] < DISTANCIA_PRESENCA]
        self._preencher_tabela(presenca, tag_padrao="presenca")
        self.label_descricao_tabela.config(
            text=f"Registros de Presença — distância < {DISTANCIA_PRESENCA} cm  ({len(presenca)} registros)"
        )
        if not presenca:
            messagebox.showinfo("Resultado", "Nenhum registro de presença no período selecionado.")


# =============================================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = SafeWarehouseApp(root)
    root.mainloop()
