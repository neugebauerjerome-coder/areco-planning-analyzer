from __future__ import annotations
from pathlib import Path
import json
from .excel_report import export_excel_report
from .mail import build_summary_mail
from .pdf_report import export_pdf_report

def export_all_reports(output_dir: Path, analyses, summary, dataset, rules_path: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    rules=json.loads(rules_path.read_text(encoding="utf-8"))
    analysis_date=summary["analysis_dates"][0]
    safe_date=analysis_date.replace("-","")
    mail_text=build_summary_mail(summary,analysis_date)
    excel_path=output_dir/f"ARECO_Planning_V4_{safe_date}.xlsx"
    pdf_path=output_dir/f"ARECO_Planning_V4_{safe_date}.pdf"
    mail_path=output_dir/f"ARECO_Planning_V4_{safe_date}_mail.txt"
    export_excel_report(excel_path,analyses,summary,dataset,rules,mail_text)
    export_pdf_report(pdf_path,analyses,summary,dataset,analysis_date)
    mail_path.write_text(mail_text,encoding="utf-8")
    return {"excel":excel_path,"pdf":pdf_path,"mail":mail_path,"mail_text":mail_text}
