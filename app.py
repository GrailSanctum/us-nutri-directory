import os
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

import datetime
import requests
import pandas as pd
from flask import Flask, render_template_string, request

app = Flask(__name__)
app.secret_key = "sup_production_secret_key_2026_pro"

CSV_FILE = "supplements_clean.csv"
LEADS_FILE = "leads_database.csv"

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

def send_telegram_alert(lead_info):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    text = (
        f"🚨 <b>ГОРЯЧИЙ RFQ-ЛИД С САЙТА!</b>\n\n"
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

BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}USA Supplement Contract Manufacturing B2B Sourcing{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .hero-section { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: white; padding: 80px 0; }
        .card-supplier { transition: transform 0.2s, box-shadow 0.2s; border: 1px solid #e2e8f0; }
        .card-supplier:hover { transform: translateY(-3px); box-shadow: 0 10px 25px rgba(0,0,0,0.08); }
        .badge-form { background-color: #f1f5f9; color: #334155; font-weight: 500; }
        .trust-badge { background: #f8fafc; border-left: 4px solid #0d6efd; padding: 15px; border-radius: 4px; }
    </style>
</head>
<body class="bg-light">
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark sticky-top shadow-sm">
        <div class="container">
            <a class="navbar-brand fw-bold" href="/">💊 USA Nutraceutical Directory</a>
            <div class="collapse navbar-collapse">
                <ul class="navbar-nav ms-auto align-items-center">
                    <li class="nav-item"><a class="nav-link" href="/">Directory</a></li>
                    <li class="nav-item"><a class="nav-link" href="/contact">Support & Desk</a></li>
                    <li class="nav-item ms-2"><a class="btn btn-primary text-white px-3" href="/#search-section">Get Matched</a></li>
                </ul>
            </div>
        </div>
    </nav>
    {{ content | safe }}
    <footer class="bg-dark text-white py-5 mt-5">
        <div class="container text-center text-secondary small">
            &copy; 2026 USA Supplement Contract Manufacturing Network. Secure B2B Digital Sourcing Desk.
        </div>
    </footer>
</body>
</html>
"""

INDEX_TEMPLATE = """
<div class="hero-section text-center" id="search-section">
    <div class="container" style="max-width: 900px;">
        <span class="badge bg-primary text-white mb-3 px-3 py-2">Verified US B2B Sourcing Desk</span>
        <h1 class="display-5 fw-bold mb-3">Connect with Verified US Supplement Contract Manufacturers</h1>
        <p class="lead text-secondary mb-4">Direct RFQ routing to FDA-registered, cGMP-certified facilities across 35 US states. Scale your brand with verified domestic partners.</p>
        
        <form action="/" method="GET" class="card p-4 shadow-lg border-0 bg-white text-dark">
            <div class="row g-3">
                <div class="col-md-4">
                    <label class="form-label small fw-bold text-start w-100">Keyword / Name</label>
                    <input type="text" name="q" class="form-control" placeholder="e.g. Gummies, Softgels..." value="{{ query }}">
                </div>
                <div class="col-md-3">
                    <label class="form-label small fw-bold text-start w-100">Supplement Form</label>
                    <select name="form" class="form-select">
                        <option value="">All Forms</option>
                        <option value="Capsules" {% if selected_form == 'Capsules' %}selected{% endif %}>Capsules</option>
                        <option value="Tablets" {% if selected_form == 'Tablets' %}selected{% endif %}>Tablets</option>
                        <option value="Gummies" {% if selected_form == 'Gummies' %}selected{% endif %}>Gummies</option>
                        <option value="Powders" {% if selected_form == 'Powders' %}selected{% endif %}>Powders</option>
                        <option value="Liquids" {% if selected_form == 'Liquids' %}selected{% endif %}>Liquids</option>
                        <option value="Softgels" {% if selected_form == 'Softgels' %}selected{% endif %}>Softgels</option>
                    </select>
                </div>
                <div class="col-md-3">
                    <label class="form-label small fw-bold text-start w-100">US State</label>
                    <select name="state" class="form-select">
                        <option value="">All States</option>
                        {% for st in states %}
                        <option value="{{ st }}" {% if selected_state == st %}selected{% endif %}>{{ st }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="col-md-2 d-flex align-items-end">
                    <button type="submit" class="btn btn-primary w-100 fw-bold py-2">Filter</button>
                </div>
            </div>
        </form>
    </div>
</div>

<div class="container my-5">
    <div class="row text-center g-4">
        <div class="col-md-4">
            <div class="card p-4 h-100 border-0 shadow-sm">
                <div class="h1 text-primary mb-3">1</div>
                <h5 class="fw-bold">Select Facility</h5>
                <p class="text-secondary small">Filter verified US plants by product form, certifications, and minimum batch sizes.</p>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card p-4 h-100 border-0 shadow-sm">
                <div class="h1 text-primary mb-3">2</div>
                <h5 class="fw-bold">Submit Digital RFQ</h5>
                <p class="text-secondary small">Send structured project parameters securely through our automated routing desk.</p>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card p-4 h-100 border-0 shadow-sm">
                <div class="h1 text-primary mb-3">3</div>
                <h5 class="fw-bold">Fast Direct Quote</h5>
                <p class="text-secondary small">Receive priority commercial responses directly from manufacturing executives.</p>
            </div>
        </div>
    </div>
</div>

<div class="container my-5">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h3 class="fw-bold text-dark">Verified Facilities ({{ suppliers|length }})</h3>
        <span class="text-muted small">Vetted US contract manufacturing network</span>
    </div>
    
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
                        <span class="fw-bold small text-dark">Capabilities:</span>
                        <div class="d-flex flex-wrap gap-1 mt-1">
                            {% for form in s.supplement_forms.split(', ') %}
                            <span class="badge badge-form">{{ form }}</span>
                            {% endfor %}
                        </div>
                    </div>
                    <div class="trust-badge my-3 small text-secondary">
                        🔒 Verified FDA / cGMP compliant facility network.
                    </div>
                    <div class="d-flex justify-content-between align-items-center mt-3 pt-3 border-top">
                        <span class="small fw-bold text-primary">MOQ: {{ "{:,}".format(s.min_moq|int) }} units</span>
                        <a href="/supplier/{{ s.slug }}" class="btn btn-dark btn-sm px-3">Request Quote</a>
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
                
                <div class="trust-badge mb-4">
                    <h6 class="fw-bold text-dark mb-1">🛡️ Secure Sourcing Desk Protection</h6>
                    <p class="small text-secondary mb-0">To ensure service quality, prevent data leaks, and secure priority executive routing, all project inquiries for this facility are handled exclusively through our digital matchmaking platform.</p>
                </div>

                <ul class="list-group list-group-flush mb-4">
                    <li class="list-group-item d-flex justify-content-between py-3"><span>Supported Forms:</span> <strong>{{ supplier.supplement_forms }}</strong></li>
                    <li class="list-group-item d-flex justify-content-between py-3"><span>Minimum Order Quantity (MOQ):</span> <strong>{{ "{:,}".format(supplier.min_moq|int) }} units</strong></li>
                    <li class="list-group-item d-flex justify-content-between py-3"><span>Certifications:</span> <strong>{{ supplier.certifications }}</strong></li>
                </ul>
            </div>
        </div>
        <div class="col-lg-4" id="rfq">
            <div class="card p-4 shadow-sm border-0 bg-white sticky-top" style="top: 90px;">
                <h3 class="h4 fw-bold mb-3 text-dark">Request a Quote (RFQ)</h3>
                <p class="small text-muted mb-3">Submit parameters to route directly to {{ supplier.name }}.</p>
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
                        <label class="form-label small fw-bold">Project Details & Formulation</label>
                        <textarea name="details" class="form-control" rows="3" placeholder="Describe ingredients, packaging requirements..."></textarea>
                    </div>
                    <button type="submit" class="btn btn-primary btn-lg w-100 fw-bold">Submit RFQ Lead</button>
                </form>
            </div>
        </div>
    </div>
</div>
"""

CONTACT_TEMPLATE = """
<div class="container my-5" style="max-width: 800px;">
    <div class="card p-5 shadow-sm border-0">
        <h1 class="fw-bold mb-4">Support & Partnership Desk</h1>
        <p class="text-secondary lead">USA Nutraceutical Directory operates as a secure digital B2B sourcing and matchmaking gateway, bridging emerging health brands with FDA-registered, cGMP-compliant manufacturing facilities across the US.</p>
        
        <div class="trust-badge my-4">
            <h6 class="fw-bold text-dark">ℹ️ Asynchronous Digital Operations Policy</h6>
            <p class="small text-secondary mb-0">To guarantee data precision, protect proprietary supplement formulations, and provide rapid turnaround for all participating manufacturers, our platform operates on an <strong>exclusive asynchronous digital model</strong>. We do not provide phone support; all project reviews, RFQ routings, and partnership inquiries are handled digitally with a 24-hour response window.</p>
        </div>

        <h5 class="fw-bold mt-4">Official Contact Channels:</h5>
        <p class="text-secondary mb-2">📧 <strong>General & Partnership Inquiries:</strong> admin@usanutricontracts.com</p>
        <p class="text-secondary mb-4">💼 <strong>Sourcing Desk:</strong> active 24/7 via automated digital routing.</p>

        <div class="mt-4"><a href="/" class="btn btn-dark px-4">Back to Directory</a></div>
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
    selected_form = request.args.get("form", "").strip()

    if query:
        df = df[df.apply(lambda r: r.astype(str).str.lower().str.contains(query).any(), axis=1)]
    if selected_state:
        df = df[df["state_code"] == selected_state]
    if selected_form:
        df = df[df["supplement_forms"].str.contains(selected_form, case=False, na=False)]

    states = sorted(load_data()["state_code"].unique().tolist())
    return render_page(INDEX_TEMPLATE, suppliers=df.to_dict(orient="records"), states=states, query=query, selected_state=selected_state, selected_form=selected_form)

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
    
    df_lead = pd.DataFrame([lead_data])
    if os.path.exists(LEADS_FILE):
        df_lead.to_csv(LEADS_FILE, mode='a', header=False, index=False, encoding='utf-8-sig')
    else:
        df_lead.to_csv(LEADS_FILE, index=False, encoding='utf-8-spec')
        
    send_telegram_alert(lead_data)
    
    success_html = """
    <div class="container my-5 text-center">
        <div class="card p-5 shadow-sm border-0 mx-auto" style="max-width: 600px;">
            <h2 class="fw-bold mb-3 text-success">✓ RFQ Successfully Submitted!</h2>
            <p class="text-secondary mb-4">Your project specifications have been securely routed to the manufacturer's matching desk. Our team will coordinate the follow-up shortly.</p>
            <a href="/" class="btn btn-primary btn-lg px-4">Back to Directory</a>
        </div>
    </div>
    """
    return render_page(success_html)

if __name__ == "__main__":
    app.run(port=5000, debug=False)
