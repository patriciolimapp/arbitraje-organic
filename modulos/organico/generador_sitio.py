# modulos/organico/generador_sitio.py (VERSIÓN CORREGIDA PARA CLOUDFLARE PAGES)
import json
import os
import shutil
import random
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from datetime import datetime, timedelta

# URL base para sitemap y feed (se sobreescribe en Cloudflare)
SITE_URL = os.environ.get("SITE_URL", "https://arbitraje-mexico.pages.dev")

BASE_DIR = Path(__file__).parent.parent.parent
DATA_JSON = BASE_DIR / "data" / "products.json"
SITIO_DIR = BASE_DIR / "sitio"
TEMPLATES_DIR = BASE_DIR / "modulos" / "organico" / "templates"

TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

def formatear_precio(valor):
    """Formatea un número con separador de miles y dos decimales."""
    return f"${'{:,.2f}'.format(valor)} MXN"

# ============================================================
# PLANTILLA BASE (igual que antes, pero con mejoras en CSS)
# ============================================================
BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=yes">
    <title>{% block title %}QuickBuy - Ofertas verificadas{% endblock %}</title>
    <meta name="description" content="{% block description %}Productos seleccionados con la mejor relación calidad-precio.{% endblock %}">
    <style>
        /* ===== RESET Y VARIABLES ===== */
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
        :root {
            --mp-blue: #009EE3;
            --mp-blue-dark: #0079b3;
            --whatsapp-green: #25D366;
            --danger-red: #e53935;
            --light-bg: #F8F9FA;
            --white: #FFFFFF;
            --max-width: 960px;
            --visa-blue: #1A1F71;
            --mc-red: #EB001B;
            --mc-orange: #F79E1B;
            --oxxo-orange: #F37021;
        }
        body { 
            background: var(--light-bg); 
            padding: 0; 
            margin: 0; 
            padding-bottom: 100px;
        }
        
        .container {
            max-width: var(--max-width);
            margin: 0 auto;
            padding: 16px;
            background: var(--white);
            border-radius: 0;
            min-height: 80vh;
        }
        @media (min-width: 768px) {
            .container { padding: 24px 32px; }
        }
        @media (min-width: 1024px) {
            .container { padding: 32px 40px; border-radius: 12px; margin-top: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
            body { padding-bottom: 120px; background: #e9ecef; }
        }

        /* INDEX GRID */
        .product-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 16px;
        }
        @media (min-width: 600px) {
            .product-grid { grid-template-columns: repeat(2, 1fr); }
        }
        @media (min-width: 1024px) {
            .product-grid { grid-template-columns: repeat(3, 1fr); gap: 24px; }
        }
        .grid-item {
            background: var(--white);
            border-radius: 12px;
            padding: 12px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.06);
            transition: transform 0.2s, box-shadow 0.2s;
            border: 1px solid #f0f0f0;
            text-decoration: none;
            color: inherit;
            display: flex;
            flex-direction: column;
        }
        .grid-item:hover { transform: translateY(-4px); box-shadow: 0 8px 25px rgba(0,0,0,0.08); }
        .grid-item img { width: 100%; aspect-ratio: 1/1; object-fit: contain; background: #f5f5f5; border-radius: 8px; }
        .grid-item .title { font-weight: 600; font-size: 0.95rem; margin: 10px 0 4px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
        .grid-item .price { color: var(--danger-red); font-weight: 700; font-size: 1.2rem; }
        .grid-item .meta { font-size: 0.8rem; color: #888; }

        /* PRODUCT DETAIL - 2 COLUMNAS */
        .product-detail-grid {
            display: grid;
            gap: 24px;
        }
        @media (min-width: 1024px) {
            .product-detail-grid {
                grid-template-columns: 1fr 1fr;
                align-items: start;
                gap: 40px;
            }
        }

        /* GALERÍA: contenedor del carrusel simple */
        .gallery {
            width: 100%;
            position: relative;
        }
        .gallery-slide {
            width: 100%;
            aspect-ratio: 1/1;
            background: #f0f0f0;
            border-radius: 12px;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .gallery-slide img, .gallery-slide video {
            width: 100%;
            height: 100%;
            object-fit: contain;
            display: block;
        }
        .gallery-slide video {
            background: #000;
        }
        .gallery-thumbs {
            display: flex;
            gap: 8px;
            margin-top: 10px;
            overflow-x: auto;
            padding-bottom: 4px;
        }
        .gallery-thumbs img, .gallery-thumbs .thumb-video {
            width: 60px;
            height: 60px;
            object-fit: cover;
            border-radius: 8px;
            border: 2px solid transparent;
            cursor: pointer;
            background: #eee;
            flex-shrink: 0;
        }
        .gallery-thumbs .active {
            border-color: var(--mp-blue);
        }
        .gallery-thumbs .thumb-video {
            display: flex;
            align-items: center;
            justify-content: center;
            background: #222;
            color: white;
            font-size: 1.5rem;
        }

        .product-info { display: flex; flex-direction: column; gap: 16px; }
        h1 { font-size: 1.6rem; font-weight: 700; line-height: 1.3; color: #222; }
        @media (max-width: 480px) { h1 { font-size: 1.3rem; } }

        .rating-row { display: flex; align-items: center; gap: 8px; font-size: 0.95rem; color: #555; flex-wrap: wrap; }
        .stars { color: #f9a825; letter-spacing: 2px; }

        .price-box { display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap; }
        .current-price { font-size: 2.4rem; font-weight: 800; color: var(--danger-red); }
        .original-price { font-size: 1.3rem; color: #999; text-decoration: line-through; }
        .discount-tag { background: var(--danger-red); color: white; padding: 2px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 700; }

        .delivery-box { background: #f0f7ff; border-radius: 10px; padding: 12px; display: flex; align-items: center; gap: 10px; border-left: 4px solid var(--mp-blue); }
        .delivery-box .text { font-size: 0.95rem; color: #222; }
        .delivery-box .text strong { color: var(--mp-blue); }

        .testimonials { border-top: 1px solid #eee; padding-top: 16px; }
        .testimonial { background: #f8f9fa; border-radius: 8px; padding: 12px; margin-bottom: 10px; font-size: 0.9rem; color: #333; border-left: 3px solid #ddd; }
        .testimonial .author { font-weight: 600; display: block; margin-top: 6px; color: #555; font-size: 0.8rem; }

        .guarantee-box { background: #f0faf0; border-radius: 10px; padding: 12px; display: flex; align-items: center; gap: 10px; border-left: 4px solid var(--whatsapp-green); font-size: 0.9rem; }

        .payment-methods {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            padding: 12px 0;
            border-top: 1px solid #eee;
            margin-top: 4px;
        }
        .payment-badge {
            padding: 6px 14px;
            border-radius: 30px;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.3px;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: #f1f3f5;
            color: #333;
            border: 1px solid transparent;
        }
        .payment-badge.visa { background: #1A1F71; color: white; }
        .payment-badge.mastercard { background: #EB001B; color: white; }
        .payment-badge.oxxo { background: #F37021; color: white; }
        .payment-badge.mercadopago { background: #009EE3; color: white; }
        .payment-badge.secure { background: #e8f5e9; color: #2e7d32; border-color: #a5d6a7; }
        .payment-badge.trust { background: #e3f2fd; color: #0d47a1; border-color: #90caf9; }

        .breadcrumb { font-size: 0.85rem; color: #888; margin-bottom: 10px; }
        .breadcrumb a { color: var(--mp-blue); text-decoration: none; }
        .footer-note { text-align: center; font-size: 0.75rem; color: #aaa; padding: 20px 0 10px; }

        /* STICKY CTA */
        .sticky-cta {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background: rgba(255,255,255,0.95);
            backdrop-filter: blur(10px);
            padding: 12px 16px;
            box-shadow: 0 -4px 20px rgba(0,0,0,0.08);
            border-top: 1px solid #eee;
            z-index: 999;
            display: flex;
            justify-content: center;
        }
        .sticky-cta-inner {
            max-width: var(--max-width);
            width: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
        }
        .sticky-cta .btn-primary {
            background: var(--mp-blue);
            color: white;
            border: none;
            padding: 14px 24px;
            border-radius: 50px;
            font-size: 1.1rem;
            font-weight: 700;
            width: 100%;
            max-width: 600px;
            text-align: center;
            text-decoration: none;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            transition: background 0.2s, transform 0.1s;
            box-shadow: 0 4px 12px rgba(0, 158, 227, 0.3);
            cursor: pointer;
        }
        .sticky-cta .btn-primary:active { background: var(--mp-blue-dark); transform: scale(0.98); }
        .cta-trust-badges {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            justify-content: center;
            font-size: 0.8rem;
            color: #555;
        }
        .cta-trust-badges span {
            display: flex;
            align-items: center;
            gap: 4px;
            background: #f8f9fa;
            padding: 4px 12px;
            border-radius: 20px;
            border: 1px solid #e9ecef;
        }
        .cta-trust-badges .secure-text { color: #2e7d32; background: #e8f5e9; border-color: #a5d6a7; }
        .cta-trust-badges .speed-text { color: #0d47a1; background: #e3f2fd; border-color: #90caf9; }

        @media (min-width: 768px) {
            .sticky-cta { padding: 16px 24px; }
            .sticky-cta .btn-primary { padding: 16px 32px; font-size: 1.2rem; }
        }
    </style>
</head>
<body>
    <div class="container">
        {% block content %}{% endblock %}
    </div>
    {% block sticky_cta %}{% endblock %}
</body>
</html>
"""

# ============================================================
# PLANTILLA DE INICIO
# ============================================================
INDEX_TEMPLATE = """
{% extends "base.html" %}
{% block title %}QuickBuy - Ofertas verificadas en México{% endblock %}
{% block content %}
    <h1 style="font-size: 2rem; margin-bottom: 20px;">⚡ Ofertas del día</h1>
    <div class="product-grid">
        {% for p in products %}
        <a href="/productos/{{ p.id }}/" class="grid-item">
            <img src="{{ p.image_url }}" alt="{{ p.title }}" loading="lazy" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22200%22 height=%22200%22%3E%3Crect width=%22200%22 height=%22200%22 fill=%22%23eee%22/%3E%3Ctext x=%2250%22 y=%22100%22 font-family=%22sans-serif%22 font-size=%2220%22 fill=%22%23999%22%3Esin imagen%3C/text%3E%3C/svg%3E'">
            <div class="title">{{ p.title }}</div>
            <div class="price">{{ p.price_formatted }}</div>
            <div class="meta">⭐ {{ p.rating }} · {{ p.sales }} ventas</div>
        </a>
        {% endfor %}
    </div>
    <div class="footer-note">Precios actualizados diariamente. Envío internacional disponible.</div>
{% endblock %}
"""

# ============================================================
# PLANTILLA DE PRODUCTO (CON GALERÍA Y DESCUENTO VARIABLE)
# ============================================================
PRODUCT_TEMPLATE = """
{% extends "base.html" %}
{% block title %}{{ product.title }} - Ofertas verificadas{% endblock %}
{% block description %}{{ product.comparison_text }}{% endblock %}

{% block content %}
    <div class="breadcrumb"><a href="/">Inicio</a> / {{ product.category }}</div>
    
    <div class="product-detail-grid">
        <!-- COLUMNA IZQUIERDA: GALERÍA -->
        <div class="gallery">
            <div class="gallery-slide" id="mainSlide">
                <img src="{{ product.image_url }}" alt="{{ product.title }}" id="mainImage">
            </div>
            <div class="gallery-thumbs">
                <img src="{{ product.image_url }}" alt="Imagen 1" class="active" onclick="changeSlide(this, 'image')">
                {% if product.video_url %}
                <div class="thumb-video" onclick="changeSlide(this, 'video')">▶</div>
                {% endif %}
            </div>
        </div>

        <!-- COLUMNA DERECHA: INFORMACIÓN -->
        <div class="product-info">
            <h1>{{ product.title }}</h1>
            
            <div class="rating-row">
                <span class="stars">⭐ {{ product.rating }}</span>
                <span>·</span>
                <span>{{ product.sales }} ventas</span>
                <span style="color: var(--mp-blue); font-size: 0.85rem;">✅ Comprador verificado</span>
            </div>

            <div class="price-box">
                <span class="current-price">{{ product.price_formatted }}</span>
                <span class="original-price">{{ product.original_price_formatted }}</span>
                <span class="discount-tag">-{{ product.discount_percent }}%</span>
            </div>

            <div class="delivery-box">
                <span style="font-size: 1.5rem;">🚚</span>
                <div class="text">
                    <strong>Envío Internacional Gratuito</strong><br>
                    Recíbelo en tu domicilio entre el <strong>{{ delivery_min }}</strong> y el <strong>{{ delivery_max }}</strong>
                </div>
            </div>

            <!-- TESTIMONIOS -->
            <div class="testimonials">
                <h3 style="font-size: 1rem; margin-bottom: 8px;">📝 Lo que dicen nuestros compradores</h3>
                {% for t in testimonios %}
                <div class="testimonial">
                    "{{ t.texto }}"
                    <span class="author">{{ t.autor }} · <span style="color: var(--mp-blue);">Comprador Verificado</span></span>
                </div>
                {% endfor %}
            </div>

            <div class="guarantee-box">
                <span style="font-size: 1.5rem;">🛡️</span>
                <div>
                    <strong>Garantía de Cero Riesgos por 30 Días</strong><br>
                    Si el producto llega dañado o no cumple lo mostrado, gestionamos tu reembolso total.
                </div>
            </div>

            <div class="payment-methods">
                <span class="payment-badge secure">🔒 Pago seguro</span>
                <span class="payment-badge visa">💳 Visa</span>
                <span class="payment-badge mastercard">💳 Mastercard</span>
                <span class="payment-badge oxxo">🏪 OXXO</span>
                <span class="payment-badge mercadopago">💙 Mercado Pago</span>
            </div>
        </div>
    </div>

    <!-- Script para cambiar entre imagen y video -->
    <script>
        function changeSlide(element, type) {
            var mainSlide = document.getElementById('mainSlide');
            var mainImage = document.getElementById('mainImage');
            var thumbs = document.querySelectorAll('.gallery-thumbs img, .gallery-thumbs .thumb-video');
            thumbs.forEach(function(t) { t.classList.remove('active'); });
            element.classList.add('active');

            if (type === 'image') {
                // Mostrar imagen estática
                mainSlide.innerHTML = '<img src="{{ product.image_url }}" alt="{{ product.title }}" style="width:100%;height:100%;object-fit:contain;">';
            } else if (type === 'video') {
                // Mostrar video con controles, sin autoplay, precargando metadata
                var videoHTML = '<video controls preload="metadata" style="width:100%;height:100%;object-fit:contain;background:#000;" poster="{{ product.image_url }}">';
                videoHTML += '<source src="{{ product.video_url }}" type="video/mp4">';
                videoHTML += '<img src="{{ product.image_url }}" alt="{{ product.title }}">';
                videoHTML += '</video>';
                mainSlide.innerHTML = videoHTML;
            }
        }
    </script>
{% endblock %}

{% block sticky_cta %}
    <div class="sticky-cta">
        <div class="sticky-cta-inner">
            <a href="/checkout?id={{ product.id }}" class="btn-primary">
                🔒 Pagar seguro con Mercado Pago
            </a>
            <div class="cta-trust-badges">
                <span class="secure-text">✅ Tus datos no se almacenan aquí</span>
                <span class="speed-text">⏱️ Pago rápido y sin complicaciones</span>
            </div>
        </div>
    </div>
{% endblock %}
"""

# ============================================================
# ESCRITURA DE PLANTILLAS
# ============================================================
with open(TEMPLATES_DIR / "base.html", "w", encoding="utf-8") as f:
    f.write(BASE_TEMPLATE)

with open(TEMPLATES_DIR / "index.html", "w", encoding="utf-8") as f:
    f.write(INDEX_TEMPLATE)

with open(TEMPLATES_DIR / "product.html", "w", encoding="utf-8") as f:
    f.write(PRODUCT_TEMPLATE)

# ============================================================
# BANCO DE TESTIMONIOS (20+ comentarios)
# ============================================================
TESTIMONIOS_CRUDOS = [
    {"texto": "Le pongo 4 estrellas porque tardó 12 días en llegar a CDMX y ya me andaba asustando. Pero por el precio está brutal, en tiendas físicas vale el triple. Funciona perfecto.", "autor": "Carlos M. · CDMX"},
    {"texto": "La caja llegó un poco aplastada, pero el aparato intacto. Tenía miedo de que fuera desechable por el precio, pero los plásticos se sienten resistentes. Sí vale la pena.", "autor": "Laura G. · Guadalajara"},
    {"texto": "Lo compré para el coche y aspira igual que en el video de TikTok. Me mandaron guía por WhatsApp a los 2 días. Volvería a comprar sin broncas.", "autor": "Jorge R. · Monterrey"},
    {"texto": "El instructivo viene en chino pero en YouTube encontré cómo armarlo. Tardó 15 días pero llegó bien empacado. 4 estrellas nomás por el idioma jaja.", "autor": "Ana S. · Puebla"},
    {"texto": "Soy de Tijuana y pensé que no llegaría por la aduana, pero sí pasó. Tardó 14 días. La calidad es buena para el precio, se siente original.", "autor": "Fernando G. · Tijuana"},
    {"texto": "Tenía desconfianza porque es una página que no conocía, pero mi pedido llegó completo. El cargador funcionó bien, solo que el cable es un poco corto.", "autor": "Martha R. · Estado de México"},
    {"texto": "El removedor de pelo funciona increíble, pero tardó casi 3 semanas en llegar. Mi perro es un pastor alemán y deja pelo por todos lados, esto me salvó la vida.", "autor": "Andrés L. · Querétaro"},
    {"texto": "El cepillo para perros es súper suave, mi chihuahua no se asusta. La entrega fue más o menos rápida (8 días). Lo recomiendo por el precio.", "autor": "Karen V. · Cancún"},
    {"texto": "Compré 2 sets, uno para mi mamá. Llegaron en 10 días, el empaque venía un poco roto pero los productos intactos. Buena relación costo-calidad.", "autor": "Luis F. · León"},
    {"texto": "Le doy 5 estrellas porque el precio es ridículamente bajo comparado con lo que venden en pet shops. Sí tarda en llegar, pero era de esperarse por el envío gratis.", "autor": "Daniela P. · Mérida"},
    {"texto": "Las tapas de las válvulas son de buen metal, no son de plástico como pensé. Tardaron 11 días en llegar a Monterrey. Quedan perfectas en mi coche.", "autor": "Ricardo S. · Monterrey"},
    {"texto": "Las luces LED para el tablero quedan muy bien, dan un ambiente chido. Solo que la instalación es un poco tediosa si no sabes de autos. 4 estrellas.", "autor": "Oscar J. · CDMX"},
    {"texto": "El kit de herramientas es completo, las llaves son duras. Lo pedí para tenerlo en la cajuela y no pesa nada. Llegó en 9 días, todo en orden.", "autor": "Miguel A. · Guadalajara"},
    {"texto": "El restaurador de plásticos dejó mi tablero como nuevo. Huele un poco fuerte al inicio pero se va. Tardó 15 días en llegar a Puebla.", "autor": "Gabriela R. · Puebla"},
    {"texto": "La toalla de microfibra es gigante y absorbe bien. Se sentía ligera al tacto pero seca el carro en chinga. El envío fue más rápido de lo que esperaba (8 días).", "autor": "David H. · Toluca"},
    {"texto": "Nunca había comprado por este tipo de páginas, pero me arriesgué. El producto llegó, eso es lo que importa. Tal vez tarde pero cumplen.", "autor": "Roberto N. · Morelia"},
    {"texto": "El vendedor se comunicó por WhatsApp para confirmar mi dirección, eso me dio confianza. El producto es exactamente el del video.", "autor": "Sandra T. · Querétaro"},
    {"texto": "Tiene muy buena calidad. Solo que pedí color negro y llegó gris, pero no lo voy a regresar porque la verdad no está tan mal.", "autor": "Eduardo C. · Aguascalientes"},
    {"texto": "El precio con descuento es una ganga. Llegó bien protegido con burbujas. Tardó 12 días a Mexicali, todo bien.", "autor": "Javier M. · Mexicali"},
    {"texto": "Lo compré para un regalo y le encantó. Llegó en la fecha estimada. El seguimiento por correo funcionó bien.", "autor": "Patricia L. · Culiacán"},
]

# ============================================================
# FUNCIÓN PRINCIPAL GENERADORA
# ============================================================
def generar_sitio():
    print("🚀 Generando sitio con galería, descuentos variables y precios formateados...")
    
    if not DATA_JSON.exists():
        print("❌ No se encuentra data/products.json.")
        return False
    
    with open(DATA_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    products_raw = data.get("products", [])
    
    if not products_raw:
        print("❌ No hay productos.")
        return False
    
    # Limpiar y crear carpetas
    if SITIO_DIR.exists():
        shutil.rmtree(SITIO_DIR)
    SITIO_DIR.mkdir(parents=True, exist_ok=True)
    productos_dir = SITIO_DIR / "productos"
    productos_dir.mkdir(exist_ok=True)
    
    # Preparar productos con descuentos variables y precios formateados
    productos_enriquecidos = []
    for p in products_raw:
        # Descuento aleatorio entre 20% y 55%
        descuento = random.randint(20, 55)
        # Precio original = precio / (1 - descuento/100)
        precio_original = p['price'] / (1 - descuento/100)
        # Formatear
        price_fmt = formatear_precio(p['price'])
        original_fmt = formatear_precio(precio_original)
        # Crear copia enriquecida
        prod = p.copy()
        prod['price_formatted'] = price_fmt
        prod['original_price_formatted'] = original_fmt
        prod['discount_percent'] = descuento
        productos_enriquecidos.append(prod)
    
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(['html', 'xml'])
    )
    env.filters['format'] = lambda x, f: f"{x:{f}}"
    
    # 1. Generar Index
    index_template = env.get_template("index.html")
    index_html = index_template.render(products=productos_enriquecidos)
    (SITIO_DIR / "index.html").write_text(index_html, encoding="utf-8")
    print(f"   ✅ index.html generado")
    
    # 2. Generar Productos
    product_template = env.get_template("product.html")
    hoy = datetime.now()
    
    for p in productos_enriquecidos:
        delivery_min = (hoy + timedelta(days=10)).strftime("%d de %B")
        delivery_max = (hoy + timedelta(days=16)).strftime("%d de %B")
        
        # Seleccionar 3 testimonios aleatorios
        testimonios_seleccionados = random.sample(TESTIMONIOS_CRUDOS, min(3, len(TESTIMONIOS_CRUDOS)))
        
        slug = f"{p['id']}"
        prod_dir = productos_dir / slug
        prod_dir.mkdir(exist_ok=True)
        
        prod_html = product_template.render(
            product=p,
            delivery_min=delivery_min,
            delivery_max=delivery_max,
            testimonios=testimonios_seleccionados
        )
        (prod_dir / "index.html").write_text(prod_html, encoding="utf-8")
    
    print(f"   ✅ {len(productos_enriquecidos)} páginas de producto generadas (con descuentos variables y galería)")
    
        # 3. Sitemap y feed
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap += f'  <url><loc>{SITE_URL}/</loc><lastmod>{datetime.utcnow().isoformat()[:10]}</lastmod></url>\n'
    for p in productos_enriquecidos:
        sitemap += f'  <url><loc>{SITE_URL}/productos/{p["id"]}/</loc><lastmod>{p["updated_at"][:10]}</lastmod></url>\n'
    sitemap += '</urlset>'
    (SITIO_DIR / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    print("   ✅ sitemap.xml generado")

    feed = '<?xml version="1.0" encoding="UTF-8"?>\n<rss xmlns:g="http://base.google.com/ns/1.0" version="2.0">\n  <channel>\n    <title>QuickBuy</title>\n    <link>' + SITE_URL + '</link>\n    <description>Productos verificados diariamente</description>\n'
    for p in productos_enriquecidos:
        feed += f'    <item>\n      <g:id>{p["id"]}</g:id>\n      <g:title>{p["title"][:150]}</g:title>\n      <g:link>{SITE_URL}/productos/{p["id"]}/</g:link>\n      <g:image_link>{p["image_url"]}</g:image_link>\n      <g:price>{p["price"]} MXN</g:price>\n      <g:availability>in stock</g:availability>\n      <g:description>{p["comparison_text"]}</g:description>\n    </item>\n'
    feed += '  </channel>\n</rss>'
    (SITIO_DIR / "feed.xml").write_text(feed, encoding="utf-8")
    print("   ✅ feed.xml generado")

    # 4. Generar robots.txt
    robots_txt = f"""User-agent: *
Allow: /
Sitemap: {SITE_URL}/sitemap.xml
"""
    (SITIO_DIR / "robots.txt").write_text(robots_txt, encoding="utf-8")
    print(f"   ✅ robots.txt generado")
    
    print(f"\n✅ Sitio generado en: {SITIO_DIR}")
    print("   ▶️  Previsualiza: python -m http.server --directory sitio 8000")
    print("   🖼️  Galería: imagen principal + opción de video (con controles, sin autoplay).")
    print("   💰 Descuentos variables entre 20% y 55% para cada producto.")
    print("   💱 Precios formateados con separador de miles y 'MXN'.")
    return True

if __name__ == "__main__":
    generar_sitio()