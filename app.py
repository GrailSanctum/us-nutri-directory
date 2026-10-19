import sys
import subprocess

for pkg_name, import_name in [
    ("curl_cffi", "curl_cffi"),
    ("zipcodes", "zipcodes"),
    ("phonenumbers", "phonenumbers"),
    ("beautifulsoup4", "bs4"),
    ("flask", "flask"),
    ("requests", "requests")
]:
    try:
        __import__(import_name)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", pkg_name])

import warnings
warnings.filterwarnings("ignore")

import threading
import datetime
import requests
import pandas as pd
from flask import Flask, render_template_string, request, url_for, redirect

app = Flask(__name__)
app.secret_key = "sup_production_secret_key_2026"

CSV_FILE = "supplements_clean.csv"
LEADS_FILE = "leads_database.csv"

# Вставьте сюда данные вашего Telegram-бота, если хотите получать уведомления о лидах
TELEGRAM_BOT_TOKEN = "ЗАМЕНИТЕ_НА_ВАШ_ТОКЕН_БОТА"
TELEGRAM_CHAT_ID = "ЗАМЕНИТЕ_НА_ВАШ_ID"

def send_telegram_alert(lead_info):
    if "ЗАМЕНИТЕ" in TELEGRAM_BOT_TOKEN or not TELEGRAM_BOT_TOKEN:
        return
    text = (
        f"🚨 <b>НОВЫЙ RFQ-ЛИД С САЙТА!</b>\n\n"
        f"🏢 <b>Завод:</b> {lead_info['supplier_slug']}\n"
        f"👤 <b>Бренд:</b> {lead_info['brand_name']}\n"
        f"📧 <b>Email:</b> {lead_info['email']}\n"
        f"💊 <b>Форма:</b> {lead_info['supplement_form']}\n"
        f"📦 <b>Партия:</b> {lead_info['batch_size']} шт.\n"
        f"📝 <b>Детали:</b> {lead_info['details']}"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=5)
    except Exception as e:
        print("Ошибка отправки в Telegram:", e)

def load_data():
    if not os.path.exists(CSV_FILE):
        return pd.DataFrame()
    df = pd.read_csv(CSV_FILE)
    df = df.fillna("")
    return df

def save_lead_to_db(lead_data):
    df_lead = pd.DataFrame([lead_data])
    if os.path.exists(LEADS_FILE):
        df_lead.to_csv(LEADS_FILE, mode='a', header=False, index=False, encoding='utf-8-sig')
    else:
        df_lead.to_csv(LEADS_FILE, index=False, encoding='utf-8-sig')
    send_telegram_alert(lead_data)

BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}US Supplement Contract Manufacturing B2B Directory{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .hero-section { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: white; padding: 70px 0; }
        .card-supplier { transition: transform 0.2s, box-shadow 0.2s; border: 1px solid #e2e8f0; }
        .card-supplier:hover { transform: translateY(-3px); box-shadow: 0 10px 25px rgba(0,0,0,0.08); }
        .badge-form { background-color: #f1f5f9; color: #334155; font-weight: 500; }
    </style>
</head>
<body class="bg-light">
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark sticky-top shadow-sm">
        <div class="container">
            <a class="navbar-brand fw-bold" href="/">💊 USA Nutraceutical Directory</a>
            <div class="collapse navbar-collapse">
                <ul class="navbar-nav ms-auto align-items-center">
                    <li class="nav-item"><a class="nav-link" href="/">Directory</a></li>
                    <li class="nav-item"><a class="nav-link" href="/contact">Contacts</a></li>
                    <li class="nav-item ms-2"><a class="btn btn-primary text-white px-3" href="/#search-section">Find Manufacturer</a></li>
                </ul>
            </div>
        </div>
    </nav>
    {{ content | safe }}
    <footer class="bg-dark text-white py-5 mt-5">
        <div class="container text-center text-secondary small">
            &copy; 2026 US Supplement Directory. Free B2B Lead Generation Platform.
        </div>
    </footer>
</body>
</html>
"""

INDEX_TEMPLATE = """
<div class="hero-section text-center" id="search-section">
    <div class="container">
        <h1 class="display-5 fw-bold mb-3">Find Verified US Supplement Contract Manufacturers</h1>
        <p class="lead text-secondary mb-4">Connect directly with FDA-registered, cGMP-certified facilities across 35 US states.</p>
        <form action="/" method="GET" class="row g-3 justify-content-center">
            <div class="col-md-4">
                <input type="text" name="q" class="form-control form-control-lg" placeholder="Search by name, form, city..." value="{{ query }}">
            </div>
            <div class="col-md-3">
                <select name="state" class="form-select form-control-lg">
                    <option value="">All US States ({{ states|length }})</option>
                    {% for st in states %}
                    <option value="{{ st }}" {% if selected_state == st %}selected{% endif %}>{{ st }}</option>
                    {% endfor %}
                </select>
            </div>
            <div class="col-md-2">
                <button type="submit" class="btn btn-primary btn-lg w-100">Filter</button>
            </div>
        </form>
    </div>
</div>
<div class="container my-5">
    <div class="row row-cols-1 row-cols-md-3 g-4">
        {% for s in suppliers %}
        <div class="col">
            <div class="card card-supplier h-100 p-3">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h4 class="card-title h5 fw-bold text-dark">{{ s.name }}</h4>
                        <span class="badge bg-success">{{ s.state_code }}</span>
                    </div>
                    <p class="text-muted small mb-2">📍 {{ s.city }}, {{ s.state }}</p>
                    <p class="card-text text-secondary small">{{ s.short_description }}</p>
                    <div class="mb-3">
                        <span class="fw-bold small text-dark">Forms:</span>
                        <div class="d-flex flex-wrap gap-1 mt-1">
                            {% for form in s.supplement_forms.split(', ') %}
                            <span class="badge badge-form">{{ form }}</span>
                            {% endfor %}
                        </div>
                    </div>
                    <div class="d-flex justify-content-between align-items-center mt-3 pt-3 border-top">
                        <span class="small fw-bold text-primary">MOQ: {{ "{:,}".format(s.min_moq|int) }} units</span>
                        <a href="/supplier/{{ s.slug }}" class="btn btn-outline-dark btn-sm">View Profile</a>
                    </div>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
"""

DETAIL_TEMPLATE = """
<div class="container my-5">
    <nav aria-label="breadcrumb" class="mb-4">
        <ol class="breadcrumb">
            <li class="breadcrumb-item"><a href="/">Directory</a></li>
            <li class="breadcrumb-item active" aria-current="page">{{ supplier.name }}</li>
        </ol>
    </nav>
    <div class="row g-4">
        <div class="col-lg-8">
            <div class="card p-4 shadow-sm border-0 mb-4">
                <h1 class="h2 fw-bold text-dark mb-2">{{ supplier.name }}</h1>
                <p class="text-muted fs-5 mb-3">📍 Location: <strong>{{ supplier.city }}, {{ supplier.state }}</strong></p>
                <p class="text-secondary mb-4">{{ supplier.short_description }}</p>
                <ul class="list-group list-group-flush mb-4">
                    <li class="list-group-item d-flex justify-content-between"><span>Website:</span> <a href="{{ supplier.website }}" target="_blank">{{ supplier.website }}</a></li>
                    <li class="list-group-item d-flex justify-content-between"><span>Forms:</span> <strong>{{ supplier.supplement_forms }}</strong></li>
                    <li class="list-group-item d-flex justify-content-between"><span>Min MOQ:</span> <strong>{{ "{:,}".format(supplier.min_moq|int) }} units</strong></li>
                    <li class="list-group-item d-flex justify-content-between"><span>Certifications:</span> <strong>{{ supplier.certifications }}</strong></li>
                </ul>
            </div>
        </div>
        <div class="col-lg-4" id="rfq">
            <div class="card p-4 shadow-sm border-0 bg-white sticky-top" style="top: 90px;">
                <h3 class="h4 fw-bold mb-3 text-dark">Request a Quote (RFQ)</h3>
                <form method="POST" action="/rfq/{{ supplier.slug }}">
                    <div class="mb-3">
                        <label class="form-label small fw-bold">Your Brand Name</label>
                        <input type="text" name="brand_name" class="form-control" required placeholder="e.g. Apex Health">
                    </div>
                    <div class="mb-3">
                        <label class="form-label small fw-bold">Business Email</label>
                        <input type="email" name="email" class="form-control" required placeholder="name@brand.com">
                    </div>
                    <div class="mb-3">
                        <label class="form-label small fw-bold">Target Supplement Form</label>
                        <select name="form" class="form-select">
                            <option>Capsules</option><option>Tablets</option><option>Gummies</option><option>Powders</option><option>Liquids</option><option>Softgels</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label class="form-label small fw-bold">Estimated Batch Size (Units)</label>
                        <input type="number" name="batch_size" class="form-control" value="{{ supplier.min_moq }}">
                    </div>
                    <div class="mb-3">
                        <label class="form-label small fw-bold">Project Details</label>
                        <textarea name="details" class="form-control" rows="3" placeholder="Describe requirements..."></textarea>
                    </div>
                    <button type="submit" class="btn btn-primary btn-lg w-100">Submit RFQ Lead</button>
                </form>
            </div>
        </div>
    </div>
</div>
"""

CONTACT_TEMPLATE = """
<div class="container my-5" style="max-width: 800px;">
    <div class="card p-5 shadow-sm border-0">
        <h1 class="fw-bold mb-4">Contacts & Support</h1>
        <p class="text-secondary">For any questions regarding directory listings or partnerships, reach out via Telegram or Email.</p>
        <p class="fw-bold">📧 Email: admin@usanutricontracts.com</p>
        <div class="mt-4"><a href="/" class="btn btn-dark">Back to Directory</a></div>
    </div>
</div>
"""

def render_page(inner_html, **context):
    return render_template_string(BASE_LAYOUT, content=render_template_string(inner_html, **context))

@app.route("/")
def index():
    df = load_data()
    if df.empty: return "Dataset not found."
    query = request.args.get("q", "").strip().lower()
    selected_state = request.args.get("state", "").strip()
    if query: df = df[df.apply(lambda r: r.astype(str).str.lower().str.contains(query).any(), axis=1)]
    if selected_state: df = df[df["state_code"] == selected_state]
    states = sorted(load_data()["state_code"].unique().tolist())
    return render_page(INDEX_TEMPLATE, suppliers=df.to_dict(orient="records"), states=states, query=query, selected_state=selected_state)

@app.route("/supplier/<slug>")
def detail(slug):
    df = load_data()
    match = df[df["slug"] == slug]
    if match.empty: return "Not found", 404
    return render_page(DETAIL_TEMPLATE, supplier=match.iloc[0].to_dict())

@app.route("/contact")
def contact():
    return render_page(CONTACT_TEMPLATE)

@app.route("/rfq/<slug>", methods=["POST"])
def submit_rfq(slug):
    lead_data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "supplier_slug": slug,
        "brand_name": request.form.get("brand_name"),
        "email": request.form.get("email"),
        "supplement_form": request.form.get("form"),
        "batch_size": request.form.get("batch_size"),
        "details": request.form.get("details")
    }
    save_lead_to_db(lead_data)
    success_html = """
    <div class="container my-5 text-center">
        <div class="card p-5 shadow-sm border-0 mx-auto" style="max-width: 600px;">
            <h2 class="fw-bold mb-3 text-success">✓ RFQ Lead Submitted!</h2>
            <p class="text-secondary mb-4">Your request has been saved and sent to administration.</p>
            <a href="/" class="btn btn-primary btn-lg">Back to Directory</a>
        </div>
    </div>
    """
    return render_page(success_html)

if __name__ == "__main__":
    app.run(port=5000, debug=False)
