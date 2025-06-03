from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
import os
import logging
from functools import wraps
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash
import json
import paho.mqtt.publish as mqtt_publish
import ssl

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.verify_mode = ssl.CERT_REQUIRED
ssl_context.check_hostname = True
ssl_context.load_default_certs()

logging.basicConfig(format='%(asctime)s - CRUD - %(levelname)s - %(message)s', level=logging.INFO)

app = Flask(__name__)

app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)

app.secret_key = os.environ["FLASK_SECRET_KEY"]
app.config["MYSQL_USER"] = os.environ["MYSQL_USER"]
app.config["MYSQL_PASSWORD"] = os.environ["MYSQL_PASSWORD"]
app.config["MYSQL_DB"] = os.environ["MYSQL_DB"]
app.config["MYSQL_HOST"] = os.environ["MYSQL_HOST"]
app.config['PERMANENT_SESSION_LIFETIME']=180
mysql = MySQL(app)

# rutas

def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/registrar", methods=["GET", "POST"])
def registrar():
    """Registrar usuario"""
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("usuario"):
            return "el campo usuario es oblicatorio"

        # Ensure password was submitted
        elif not request.form.get("password"):
            return "el campo contraseña es oblicatorio"

        passhash=generate_password_hash(request.form.get("password"), method='scrypt', salt_length=16)
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO usuarios (usuario, hash) VALUES (%s,%s)", (request.form.get("usuario"), passhash[17:]))
        if mysql.connection.affected_rows():
            flash('Se agregó un usuario')  # usa sesión
            logging.info("se agregó un usuario")
        mysql.connection.commit()
        return redirect(url_for('index'))

    return render_template('registrar.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("usuario"):
            return "el campo usuario es oblicatorio"
        # Ensure password was submitted
        elif not request.form.get("password"):
            return "el campo contraseña es oblicatorio"

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM usuarios WHERE usuario LIKE %s", (request.form.get("usuario"),))
        rows=cur.fetchone()
        if(rows):
            if (check_password_hash('scrypt:32768:8:1$' + rows[2],request.form.get("password"))):
                session.permanent = True
                session["user_id"]=request.form.get("usuario")
                logging.info("se autenticó correctamente")
                return redirect(url_for('index'))
            else:
                flash('usuario o contraseña incorrecto')
                return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/')
@require_login
def index():
    cur = mysql.connection.cursor()
    cur.execute('SELECT sensor_id FROM sensores_remotos.mediciones GROUP BY sensor_id ORDER BY sensor_id ASC')
    nodos = [nodo[0] for nodo in cur.fetchall()]
    cur.close()
    logging.info(f"se consultaron los nodos: {nodos}")
    return render_template('index.html', nodos = nodos)

@app.route('/publish', methods=['POST'])
@require_login
def publish():
    if request.method == 'POST':
        nodo = request.form.get('nodo-select')
        comando = request.form.get('comando')
        if comando == "destello":
            mensaje = json.dumps({"destello": 1})
        else:
            mensaje = json.dumps({
                "temperatura": float(request.form.get('temperatura'))})
        try:
            mqtt_publish.single(
            topic=f"{nodo}/{comando}",
            payload=mensaje,
            hostname=os.environ["MQTT_HOST"],
            port=int(os.environ["MQTT_PORT"]),
            auth={
                'username': os.environ["MQTT_USER"],
                'password': os.environ["MQTT_PASSWORD"],
            },
            tls=ssl_context)
        except Exception as e:
            logging.error(f"Error al publicar en el nodo {nodo}: {repr(e)}.")
            flash(f"Error al publicar en el nodo {nodo}: {e}.", "danger")
            return redirect(url_for('index'))
        flash("Mensaje publicado con éxito.", "success")
        logging.info(f"se publicó un mensaje en '{nodo}/{comando}': {mensaje} ")
    return redirect(url_for('index'))

@app.route("/logout")
@require_login
def logout():
    session.clear()
    logging.info("el usuario {} cerró su sesión".format(session.get("user_id")))
    return redirect(url_for('index'))

@app.route("/tema_claro", methods=["GET"])
@require_login
def tema_claro():
    session["theme"] = "light"
    logging.info("el usuario {} cambió a tema claro".format(session.get("user_id")))
    return redirect(request.referrer or url_for('index'))

@app.route("/tema_oscuro", methods=["GET"])
@require_login
def tema_oscuro():
    session["theme"] = "dark"
    logging.info("el usuario {} cambió a tema oscuro".format(session.get("user_id")))
    return redirect(request.referrer or url_for('index'))