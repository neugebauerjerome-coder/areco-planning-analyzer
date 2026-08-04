from __future__ import annotations

import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from areco_planning.analyzer.service import analyze_with_routes
from areco_planning.core.service import build_dataset
from areco_planning.reports.service import export_all_reports
from areco_planning.route_engine.cache import RouteCache
from areco_planning.route_engine.ors_client import OpenRouteServiceClient


APP_DIR = Path(__file__).resolve().parents[2]
TEAMS_PATH = APP_DIR / "areco_planning" / "data" / "toutes_les_equipes_areco.xlsx"
RULES_PATH = APP_DIR / "areco_planning" / "config" / "rules_v4.json"
CACHE_PATH = APP_DIR / "data" / "route_cache.sqlite"
CONFIG_PATH = APP_DIR / "data" / "ors_key.txt"


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ARECO Planning Suite V4.0.5")
        self.geometry("860x580")
        self.minsize(780, 520)

        self.planning_path = tk.StringVar()
        self.api_key = tk.StringVar(value=self._load_key())
        self.optimize_order = tk.BooleanVar(value=True)
        self.status = tk.StringVar(value="Prêt.")
        self.output_folder = tk.StringVar()

        self._build()

    def _build(self):
        header = tk.Frame(self, bg="#1F4E78", height=86)
        header.pack(fill="x")
        tk.Label(
            header,
            text="ARECO Planning Suite V4.0.5",
            bg="#1F4E78",
            fg="white",
            font=("Segoe UI", 20, "bold"),
        ).pack(pady=(16, 0))
        tk.Label(
            header,
            text="Analyse V4 avec trajets réels, Excel, PDF et mail",
            bg="#1F4E78",
            fg="white",
            font=("Segoe UI", 10),
        ).pack()

        body = ttk.Frame(self, padding=24)
        body.pack(fill="both", expand=True)

        ttk.Label(body, text="1. Planning Excel ARFITEC", font=("Segoe UI", 11, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Entry(body, textvariable=self.planning_path, width=76).grid(
            row=1, column=0, sticky="ew", pady=(6, 8)
        )
        ttk.Button(body, text="Choisir", command=self.choose_planning).grid(
            row=1, column=1, padx=(10, 0)
        )

        ttk.Label(body, text="2. Clé OpenRouteService", font=("Segoe UI", 11, "bold")).grid(
            row=2, column=0, sticky="w", pady=(14, 0)
        )
        ttk.Entry(body, textvariable=self.api_key, show="•", width=76).grid(
            row=3, column=0, sticky="ew", pady=(6, 8)
        )
        ttk.Button(body, text="Enregistrer", command=self.save_key).grid(
            row=3, column=1, padx=(10, 0)
        )

        ttk.Label(body, text="3. Dossier de sortie", font=("Segoe UI", 11, "bold")).grid(
            row=4, column=0, sticky="w", pady=(14, 0)
        )
        ttk.Entry(body, textvariable=self.output_folder, width=76).grid(
            row=5, column=0, sticky="ew", pady=(6, 8)
        )
        ttk.Button(body, text="Choisir", command=self.choose_output).grid(
            row=5, column=1, padx=(10, 0)
        )

        ttk.Checkbutton(
            body,
            text="Optimiser l'ordre des magasins par proximité",
            variable=self.optimize_order,
        ).grid(row=6, column=0, sticky="w", pady=(12, 0))

        self.progress = ttk.Progressbar(body, mode="indeterminate")
        self.progress.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(26, 8))

        ttk.Button(
            body,
            text="ANALYSER ET GÉNÉRER LES RAPPORTS",
            command=self.start_analysis,
        ).grid(row=8, column=0, columnspan=2, sticky="ew", ipady=12)

        ttk.Label(body, textvariable=self.status, foreground="#444444").grid(
            row=9, column=0, columnspan=2, sticky="w", pady=(18, 0)
        )
        ttk.Label(
            body,
            text="Résultats : rapport Excel, rapport PDF et mail prêt à envoyer.",
            foreground="#666666",
        ).grid(row=10, column=0, columnspan=2, sticky="w", pady=(6, 0))

        body.columnconfigure(0, weight=1)

    def choose_planning(self):
        file_path = filedialog.askopenfilename(
            title="Choisir le planning ARFITEC",
            filetypes=[("Fichiers Excel", "*.xlsx")],
        )
        if file_path:
            self.planning_path.set(file_path)
            if not self.output_folder.get():
                self.output_folder.set(str(Path(file_path).parent / "Rapports_ARECO"))

    def choose_output(self):
        folder = filedialog.askdirectory(title="Choisir le dossier de sortie")
        if folder:
            self.output_folder.set(folder)

    def _load_key(self) -> str:
        if CONFIG_PATH.exists():
            return CONFIG_PATH.read_text(encoding="utf-8").strip()
        return os.getenv("ORS_API_KEY", "")

    def save_key(self):
        key = self.api_key.get().strip()
        if not key:
            messagebox.showwarning("Clé manquante", "Saisissez la clé OpenRouteService.")
            return
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(key, encoding="utf-8")
        messagebox.showinfo("Clé enregistrée", "La clé a été enregistrée sur ce PC.")

    def start_analysis(self):
        planning = Path(self.planning_path.get().strip())
        if not planning.exists():
            messagebox.showwarning("Planning manquant", "Choisissez un fichier Excel ARFITEC.")
            return
        if not self.api_key.get().strip():
            messagebox.showwarning("Clé manquante", "Saisissez la clé OpenRouteService.")
            return

        output = Path(self.output_folder.get().strip() or planning.parent / "Rapports_ARECO")
        self.output_folder.set(str(output))
        self.progress.start(10)
        self.status.set("Calcul des trajets et génération des rapports…")
        threading.Thread(target=self._run, args=(planning, output), daemon=True).start()

    def _run(self, planning: Path, output: Path):
        cache = None
        try:
            cache = RouteCache(CACHE_PATH)
            provider = OpenRouteServiceClient(self.api_key.get().strip(), cache)
            analyses, summary = analyze_with_routes(
                planning,
                TEAMS_PATH,
                RULES_PATH,
                provider,
                optimize_order=self.optimize_order.get(),
            )
            dataset = build_dataset(planning, TEAMS_PATH, RULES_PATH)
            reports = export_all_reports(output, analyses, summary, dataset, RULES_PATH)
            self.after(0, self._success, reports, summary)
        except Exception as exc:
            self.after(0, self._failure, str(exc))
        finally:
            if cache is not None:
                cache.close()

    def _success(self, reports, summary):
        self.progress.stop()
        self.status.set("Analyse terminée.")
        messagebox.showinfo(
            "Analyse terminée",
            f"Interventions : {summary['interventions']}\n"
            f"Temps trajet : {summary['travel_hours']:.2f} h\n"
            f"Distance : {summary['distance_km']:.1f} km\n"
            f"Total : {summary['total_hours']:.2f} h\n\n"
            f"Rapport Excel : {reports['excel']}\n"
            f"Rapport PDF : {reports['pdf']}",
        )
        os.startfile(reports["excel"])

    def _failure(self, message: str):
        self.progress.stop()
        self.status.set("Échec de l'analyse.")
        messagebox.showerror("Erreur", message)


def main() -> int:
    MainWindow().mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
