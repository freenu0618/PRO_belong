from flask import Blueprint, render_template

web_bp = Blueprint("web", __name__)

@web_bp.route("/")
def index():
    return render_template("dashboard.html")

@web_bp.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@web_bp.route("/region/<region>")
def region_detail(region):
    return render_template("region_deatil.html", region=region)

@web_bp.route("/correlation")
def correlation():
    return render_template("correlation.html")