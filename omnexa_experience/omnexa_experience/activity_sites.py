# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Dedicated public website routes per Company business activity."""

from __future__ import annotations

import frappe
from frappe.utils import get_url

from omnexa_experience.omnexa_experience.portal_registry import (
	get_company_business_activity,
	primary_vertical_id_for_activity,
)

# Default professional hero images (Unsplash, stable URLs)
DEFAULT_HERO_IMAGES: dict[str, str] = {
	"Healthcare": "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?auto=format&fit=crop&w=1600&q=80",
	"Trading": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=1600&q=80",
	"Education": "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?auto=format&fit=crop&w=1600&q=80",
	"Manufacturing": "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&w=1600&q=80",
	"Financial Services": "https://images.unsplash.com/photo-1601597111158-2fceff29277d?auto=format&fit=crop&w=1600&q=80",
	"Tourism": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1600&q=80",
	"Hotel Assets": "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=1600&q=80",
	"Services": "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1600&q=80",
	"Construction": "https://images.unsplash.com/photo-1504307651254-35680f356dfd?auto=format&fit=crop&w=1600&q=80",
	"Engineering Consulting": "https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=1600&q=80",
	"Agriculture": "https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=1600&q=80",
	"Bakeries": "https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=1600&q=80",
	"General": "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1600&q=80",
}

SERVICE_CARD_IMAGES: dict[str, list[dict]] = {
	"Healthcare": [
		{"key": "Emergency", "image": "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&w=800&q=80"},
		{"key": "Laboratory", "image": "https://images.unsplash.com/photo-1579154204601-01588f351e67?auto=format&fit=crop&w=800&q=80"},
		{"key": "Radiology", "image": "https://images.unsplash.com/photo-1516549655169-df83a0774514?auto=format&fit=crop&w=800&q=80"},
		{"key": "Pharmacy", "image": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?auto=format&fit=crop&w=800&q=80"},
	],
	"Trading": [
		{"key": "Products", "image": "https://images.unsplash.com/photo-1472851294607-062f824d29cc?auto=format&fit=crop&w=800&q=80"},
		{"key": "Delivery", "image": "https://images.unsplash.com/photo-1566576912321-d58ddd7a6088?auto=format&fit=crop&w=800&q=80"},
		{"key": "Support", "image": "https://images.unsplash.com/photo-1556740758-90de374c12ad?auto=format&fit=crop&w=800&q=80"},
		{"key": "Offers", "image": "https://images.unsplash.com/photo-1607082348824-0a96f2a4b9da?auto=format&fit=crop&w=800&q=80"},
	],
	"Education": [
		{"key": "Programs", "image": "https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&w=800&q=80"},
		{"key": "Admissions", "image": "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?auto=format&fit=crop&w=800&q=80"},
		{"key": "Campus", "image": "https://images.unsplash.com/photo-1562774053-701939374585?auto=format&fit=crop&w=800&q=80"},
		{"key": "Student Life", "image": "https://images.unsplash.com/photo-1529390079861-591de354faf5?auto=format&fit=crop&w=800&q=80"},
	],
	"Manufacturing": [
		{"key": "Production", "image": "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&w=800&q=80"},
		{"key": "Quality", "image": "https://images.unsplash.com/photo-1581092160562-40aa08e78837?auto=format&fit=crop&w=800&q=80"},
		{"key": "Supply", "image": "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?auto=format&fit=crop&w=800&q=80"},
		{"key": "Support", "image": "https://images.unsplash.com/photo-1504917595217-d4dc5ebe6122?auto=format&fit=crop&w=800&q=80"},
	],
	"Tourism": [
		{"key": "Rooms", "image": "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?auto=format&fit=crop&w=800&q=80"},
		{"key": "Dining", "image": "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?auto=format&fit=crop&w=800&q=80"},
		{"key": "Spa", "image": "https://images.unsplash.com/photo-1540555700478-4be289fbecef?auto=format&fit=crop&w=800&q=80"},
		{"key": "Events", "image": "https://images.unsplash.com/photo-1519167758481-83f550bb49b3?auto=format&fit=crop&w=800&q=80"},
	],
	"Financial Services": [
		{"key": "Loans", "image": "https://images.unsplash.com/photo-1554224155-6726b3ff858f?auto=format&fit=crop&w=800&q=80"},
		{"key": "Accounts", "image": "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?auto=format&fit=crop&w=800&q=80"},
		{"key": "Cards", "image": "https://images.unsplash.com/photo-1563013544-824ae1b704d3?auto=format&fit=crop&w=800&q=80"},
		{"key": "Advisory", "image": "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=800&q=80"},
	],
	"Services": [
		{"key": "Consulting", "image": "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=800&q=80"},
		{"key": "Support", "image": "https://images.unsplash.com/photo-1556740758-90de374c12ad?auto=format&fit=crop&w=800&q=80"},
		{"key": "Audit", "image": "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=800&q=80"},
		{"key": "Advisory", "image": "https://images.unsplash.com/photo-1521737711867-e3b97375f902?auto=format&fit=crop&w=800&q=80"},
	],
	"Construction": [
		{"key": "Villas", "image": "https://images.unsplash.com/photo-1504307651254-35680f356dfd?auto=format&fit=crop&w=800&q=80"},
		{"key": "Commercial", "image": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=800&q=80"},
		{"key": "Renovation", "image": "https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=800&q=80"},
		{"key": "MEP", "image": "https://images.unsplash.com/photo-1581092160562-40aa08e78837?auto=format&fit=crop&w=800&q=80"},
	],
	"Agriculture": [
		{"key": "Produce", "image": "https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=800&q=80"},
		{"key": "Organic", "image": "https://images.unsplash.com/photo-1464226184884-fa280b87ee0b?auto=format&fit=crop&w=800&q=80"},
		{"key": "Advisory", "image": "https://images.unsplash.com/photo-1625246333195-78d9c38ad449?auto=format&fit=crop&w=800&q=80"},
		{"key": "Supply", "image": "https://images.unsplash.com/photo-1574943329822-c7972593c83e?auto=format&fit=crop&w=800&q=80"},
	],
	"Bakeries": [
		{"key": "Artisan", "image": "https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=800&q=80"},
		{"key": "Pastry", "image": "https://images.unsplash.com/photo-1486427944299-195ffd833053?auto=format&fit=crop&w=800&q=80"},
		{"key": "Catering", "image": "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?auto=format&fit=crop&w=800&q=80"},
		{"key": "Custom", "image": "https://images.unsplash.com/photo-1555507036-ab1f4038808a?auto=format&fit=crop&w=800&q=80"},
	],
	"Engineering Consulting": [
		{"key": "Structural", "image": "https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=800&q=80"},
		{"key": "MEP", "image": "https://images.unsplash.com/photo-1581092160562-40aa08e78837?auto=format&fit=crop&w=800&q=80"},
		{"key": "Supervision", "image": "https://images.unsplash.com/photo-1504307651254-35680f356dfd?auto=format&fit=crop&w=800&q=80"},
		{"key": "Design", "image": "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=800&q=80"},
	],
}

ACTIVITY_FEATURES: dict[str, list[dict]] = {
	"Trading": [
		{"icon": "🛍️", "ar": "منتجات مختارة", "en": "Curated products"},
		{"icon": "🚚", "ar": "توصيل سريع", "en": "Fast delivery"},
		{"icon": "💳", "ar": "دفع آمن", "en": "Secure payment"},
		{"icon": "⭐", "ar": "جودة مضمونة", "en": "Quality assured"},
		{"icon": "📦", "ar": "تتبع الطلب", "en": "Order tracking"},
		{"icon": "🎁", "ar": "عروض حصرية", "en": "Exclusive offers"},
	],
	"Education": [
		{"icon": "🎓", "ar": "برامج معتمدة", "en": "Accredited programs"},
		{"icon": "📚", "ar": "مناهج حديثة", "en": "Modern curricula"},
		{"icon": "👨‍🏫", "ar": "هيئة تدريس", "en": "Expert faculty"},
		{"icon": "🏫", "ar": "حرم جامعي", "en": "Campus life"},
		{"icon": "🌐", "ar": "تعليم إلكتروني", "en": "E-learning"},
		{"icon": "🤝", "ar": "دعم الطلاب", "en": "Student support"},
	],
	"Manufacturing": [
		{"icon": "🏭", "ar": "إنتاج صناعي", "en": "Industrial production"},
		{"icon": "✅", "ar": "جودة ISO", "en": "ISO quality"},
		{"icon": "🔧", "ar": "صيانة", "en": "Maintenance"},
		{"icon": "📊", "ar": "تخطيط إنتاج", "en": "Production planning"},
		{"icon": "🚛", "ar": "توزيع", "en": "Distribution"},
		{"icon": "🛡️", "ar": "ضمان", "en": "Warranty"},
	],
	"Tourism": [
		{"icon": "🏨", "ar": "إقامة فاخرة", "en": "Luxury stay"},
		{"icon": "🍽️", "ar": "مطاعم", "en": "Fine dining"},
		{"icon": "🧖", "ar": "سبا واسترخاء", "en": "Spa & wellness"},
		{"icon": "📅", "ar": "حجز فوري", "en": "Instant booking"},
		{"icon": "🌴", "ar": "تجارب سياحية", "en": "Experiences"},
		{"icon": "⭐", "ar": "خدمة 5 نجوم", "en": "5-star service"},
	],
	"Financial Services": [
		{"icon": "💳", "ar": "تمويل مرن", "en": "Flexible finance"},
		{"icon": "📈", "ar": "استثمار", "en": "Investment"},
		{"icon": "🏦", "ar": "حسابات", "en": "Accounts"},
		{"icon": "🔒", "ar": "أمان عالي", "en": "High security"},
		{"icon": "📱", "ar": "خدمة رقمية", "en": "Digital service"},
		{"icon": "🤝", "ar": "استشارات", "en": "Advisory"},
	],
	"Services": [
		{"icon": "💼", "ar": "استشارات", "en": "Consulting"},
		{"icon": "📋", "ar": "تدقيق", "en": "Audit"},
		{"icon": "⚡", "ar": "استجابة سريعة", "en": "Fast response"},
		{"icon": "🎯", "ar": "حلول مخصصة", "en": "Tailored solutions"},
		{"icon": "🌍", "ar": "خبرة محلية", "en": "Local expertise"},
		{"icon": "✅", "ar": "جودة مؤسسية", "en": "Enterprise quality"},
	],
	"Construction": [
		{"icon": "🏗️", "ar": "مشاريع إنشائية", "en": "Construction projects"},
		{"icon": "📐", "ar": "تصميم هندسي", "en": "Engineering design"},
		{"icon": "⏱️", "ar": "التزام بالمواعيد", "en": "On-time delivery"},
		{"icon": "🛡️", "ar": "سلامة وجودة", "en": "Safety & quality"},
		{"icon": "👷", "ar": "فرق محترفة", "en": "Professional teams"},
		{"icon": "📊", "ar": "إدارة مشاريع", "en": "Project management"},
	],
	"Agriculture": [
		{"icon": "🌾", "ar": "منتجات طازجة", "en": "Fresh produce"},
		{"icon": "🌱", "ar": "زراعة عضوية", "en": "Organic farming"},
		{"icon": "🚜", "ar": "استشارات زراعية", "en": "Farm advisory"},
		{"icon": "📦", "ar": "توزيع موثوق", "en": "Reliable distribution"},
		{"icon": "💧", "ar": "ري مستدام", "en": "Sustainable irrigation"},
		{"icon": "⭐", "ar": "جودة معتمدة", "en": "Certified quality"},
	],
	"Bakeries": [
		{"icon": "🥖", "ar": "خبز طازج", "en": "Fresh bread"},
		{"icon": "🥐", "ar": "معجنات فاخرة", "en": "Premium pastries"},
		{"icon": "🎂", "ar": "تصاميم مخصصة", "en": "Custom designs"},
		{"icon": "🍽️", "ar": "تموين مناسبات", "en": "Event catering"},
		{"icon": "✨", "ar": "مكونات طبيعية", "en": "Natural ingredients"},
		{"icon": "🚚", "ar": "توصيل سريع", "en": "Fast delivery"},
	],
	"Engineering Consulting": [
		{"icon": "📐", "ar": "تصميم إنشائي", "en": "Structural design"},
		{"icon": "⚙️", "ar": "MEP", "en": "MEP engineering"},
		{"icon": "🏗️", "ar": "إشراف ميداني", "en": "Site supervision"},
		{"icon": "📊", "ar": "دراسات جدوى", "en": "Feasibility studies"},
		{"icon": "✅", "ar": "امتثال للكود", "en": "Code compliance"},
		{"icon": "🤝", "ar": "شراكة طويلة", "en": "Long-term partnership"},
	],
	"Hotel Assets": [
		{"icon": "🏨", "ar": "إدارة أصول", "en": "Asset management"},
		{"icon": "📈", "ar": "عائد استثماري", "en": "Investment yield"},
		{"icon": "🔧", "ar": "صيانة تشغيلية", "en": "Operational maintenance"},
		{"icon": "📋", "ar": "حوكمة", "en": "Governance"},
		{"icon": "🌟", "ar": "ضيافة فاخرة", "en": "Luxury hospitality"},
		{"icon": "🤝", "ar": "شركاء موثوقون", "en": "Trusted partners"},
	],
	"Statutory Audit": [
		{"icon": "📋", "ar": "تدقيق قانوني", "en": "Statutory audit"},
		{"icon": "📊", "ar": "تقارير IFRS", "en": "IFRS reporting"},
		{"icon": "🔒", "ar": "سرية تامة", "en": "Full confidentiality"},
		{"icon": "⚖️", "ar": "امتثال", "en": "Compliance"},
		{"icon": "🎯", "ar": "دقة", "en": "Precision"},
		{"icon": "🤝", "ar": "فريق خبير", "en": "Expert team"},
	],
	"General": [
		{"icon": "⭐", "ar": "جودة", "en": "Quality"},
		{"icon": "🤝", "ar": "ثقة", "en": "Trust"},
		{"icon": "⚡", "ar": "سرعة", "en": "Speed"},
		{"icon": "💼", "ar": "احترافية", "en": "Professionalism"},
		{"icon": "🌍", "ar": "تغطية", "en": "Coverage"},
		{"icon": "✅", "ar": "التزام", "en": "Commitment"},
	],
}

ACTIVITY_STATS: dict[str, list[dict]] = {
	"Trading": [
		{"value": "500+", "ar": "منتج", "en": "Products"},
		{"value": "50+", "ar": "مورد", "en": "Suppliers"},
		{"value": "10K+", "ar": "عميل", "en": "Customers"},
		{"value": "15+", "ar": "سنة خبرة", "en": "Years"},
	],
	"Education": [
		{"value": "20+", "ar": "برنامج", "en": "Programs"},
		{"value": "80+", "ar": "مدرس", "en": "Faculty"},
		{"value": "5K+", "ar": "طالب", "en": "Students"},
		{"value": "10+", "ar": "سنة", "en": "Years"},
	],
	"Manufacturing": [
		{"value": "100+", "ar": "منتج", "en": "Products"},
		{"value": "30+", "ar": "خط إنتاج", "en": "Lines"},
		{"value": "200+", "ar": "عميل", "en": "Clients"},
		{"value": "20+", "ar": "سنة", "en": "Years"},
	],
	"Tourism": [
		{"value": "120+", "ar": "غرفة", "en": "Rooms"},
		{"value": "4.8", "ar": "تقييم", "en": "Rating"},
		{"value": "50K+", "ar": "ضيف", "en": "Guests"},
		{"value": "10+", "ar": "سنة", "en": "Years"},
	],
	"Financial Services": [
		{"value": "15+", "ar": "منتج تمويلي", "en": "Loan products"},
		{"value": "5K+", "ar": "عميل", "en": "Clients"},
		{"value": "98%", "ar": "رضا العملاء", "en": "Satisfaction"},
		{"value": "12+", "ar": "سنة", "en": "Years"},
	],
	"Services": [
		{"value": "200+", "ar": "عميل", "en": "Clients"},
		{"value": "50+", "ar": "مشروع", "en": "Projects"},
		{"value": "15+", "ar": "سنة خبرة", "en": "Years"},
		{"value": "24/7", "ar": "دعم", "en": "Support"},
	],
	"Construction": [
		{"value": "80+", "ar": "مشروع", "en": "Projects"},
		{"value": "500+", "ar": "عامل", "en": "Workforce"},
		{"value": "20+", "ar": "سنة", "en": "Years"},
		{"value": "100%", "ar": "التزام", "en": "Commitment"},
	],
	"Agriculture": [
		{"value": "1000+", "ar": "فدان", "en": "Acres"},
		{"value": "50+", "ar": "منتج", "en": "Products"},
		{"value": "300+", "ar": "مزارع", "en": "Farmers"},
		{"value": "10+", "ar": "سنة", "en": "Years"},
	],
	"Bakeries": [
		{"value": "40+", "ar": "صنف", "en": "Items"},
		{"value": "5K+", "ar": "عميل يومي", "en": "Daily customers"},
		{"value": "4.9", "ar": "تقييم", "en": "Rating"},
		{"value": "15+", "ar": "سنة", "en": "Years"},
	],
	"Engineering Consulting": [
		{"value": "120+", "ar": "مشروع", "en": "Projects"},
		{"value": "30+", "ar": "مهندس", "en": "Engineers"},
		{"value": "15+", "ar": "سنة", "en": "Years"},
		{"value": "100%", "ar": "امتثال", "en": "Compliance"},
	],
	"Hotel Assets": [
		{"value": "25+", "ar": "عقار", "en": "Properties"},
		{"value": "95%", "ar": "إشغال", "en": "Occupancy"},
		{"value": "12+", "ar": "سنة", "en": "Years"},
		{"value": "4.7", "ar": "تقييم", "en": "Rating"},
	],
	"Statutory Audit": [
		{"value": "100+", "ar": "عميل", "en": "Clients"},
		{"value": "20+", "ar": "مدقق", "en": "Auditors"},
		{"value": "15+", "ar": "سنة", "en": "Years"},
		{"value": "100%", "ar": "امتثال", "en": "Compliance"},
	],
	"General": [
		{"value": "100+", "ar": "عميل", "en": "Clients"},
		{"value": "10+", "ar": "سنة", "en": "Years"},
		{"value": "98%", "ar": "رضا", "en": "Satisfaction"},
		{"value": "24/7", "ar": "دعم", "en": "Support"},
	],
}

# business_activity → public site base path
ACTIVITY_SITE_PATHS: dict[str, str] = {
	"Healthcare": "/hospital",
	"Trading": "/store",
	"Education": "/campus",
	"Manufacturing": "/factory",
	"Tourism": "/stay",
	"Hotel Assets": "/stay",
	"Financial Services": "/finance-site",
	"Services": "/services-site",
	"Statutory Audit": "/services-site",
	"Agriculture": "/farm",
	"Construction": "/build",
	"Engineering Consulting": "/engineering-site",
	"Bakeries": "/menu",
	"General": "/services-site",
}

ACTIVITY_NAV: dict[str, list[dict]] = {
	"Trading": [
		{"key": "home", "ar": "الرئيسية", "en": "Home", "href": "/store"},
		{"key": "products", "ar": "المنتجات", "en": "Products", "href": "/store/products"},
		{"key": "order", "ar": "اطلب الآن", "en": "Order now", "href": "/store/order", "cta": True},
	],
	"Education": [
		{"key": "home", "ar": "الرئيسية", "en": "Home", "href": "/campus"},
		{"key": "programs", "ar": "البرامج", "en": "Programs", "href": "/campus/programs"},
		{"key": "apply", "ar": "قدّم الآن", "en": "Apply now", "href": "/campus/apply", "cta": True},
	],
	"Manufacturing": [
		{"key": "home", "ar": "الرئيسية", "en": "Home", "href": "/factory"},
		{"key": "products", "ar": "المنتجات", "en": "Products", "href": "/factory/products"},
		{"key": "order", "ar": "اطلب", "en": "Order", "href": "/factory/order", "cta": True},
	],
	"Tourism": [
		{"key": "home", "ar": "الرئيسية", "en": "Home", "href": "/stay"},
		{"key": "rooms", "ar": "الغرف", "en": "Rooms", "href": "/stay/products"},
		{"key": "book", "ar": "احجز", "en": "Book", "href": "/stay/order", "cta": True},
	],
	"Hotel Assets": [
		{"key": "home", "ar": "الرئيسية", "en": "Home", "href": "/stay"},
		{"key": "properties", "ar": "العقارات", "en": "Properties", "href": "/stay/products"},
		{"key": "contact", "ar": "تواصل", "en": "Contact", "href": "/stay/order", "cta": True},
	],
	"Financial Services": [
		{"key": "home", "ar": "الرئيسية", "en": "Home", "href": "/finance-site"},
		{"key": "products", "ar": "المنتجات", "en": "Products", "href": "/finance-site/products"},
		{"key": "apply", "ar": "قدّم", "en": "Apply", "href": "/finance-site/apply", "cta": True},
	],
	"Services": [
		{"key": "home", "ar": "الرئيسية", "en": "Home", "href": "/services-site"},
		{"key": "services", "ar": "الخدمات", "en": "Services", "href": "/services-site/products"},
		{"key": "contact", "ar": "تواصل", "en": "Contact", "href": "/services-site/order", "cta": True},
	],
	"Agriculture": [
		{"key": "home", "ar": "الرئيسية", "en": "Home", "href": "/farm"},
		{"key": "products", "ar": "المنتجات", "en": "Products", "href": "/farm/products"},
		{"key": "order", "ar": "اطلب", "en": "Order", "href": "/farm/order", "cta": True},
	],
	"Construction": [
		{"key": "home", "ar": "الرئيسية", "en": "Home", "href": "/build"},
		{"key": "projects", "ar": "المشاريع", "en": "Projects", "href": "/build/products"},
		{"key": "contact", "ar": "تواصل", "en": "Contact", "href": "/build/order", "cta": True},
	],
	"Engineering Consulting": [
		{"key": "home", "ar": "الرئيسية", "en": "Home", "href": "/engineering-site"},
		{"key": "services", "ar": "الخدمات", "en": "Services", "href": "/engineering-site/products"},
		{"key": "contact", "ar": "تواصل", "en": "Contact", "href": "/engineering-site/order", "cta": True},
	],
	"Bakeries": [
		{"key": "home", "ar": "الرئيسية", "en": "Home", "href": "/menu"},
		{"key": "menu", "ar": "القائمة", "en": "Menu", "href": "/menu/products"},
		{"key": "order", "ar": "اطلب", "en": "Order", "href": "/menu/order", "cta": True},
	],
	"General": [
		{"key": "home", "ar": "الرئيسية", "en": "Home", "href": "/services-site"},
		{"key": "services", "ar": "الخدمات", "en": "Services", "href": "/services-site/products"},
		{"key": "contact", "ar": "تواصل", "en": "Contact", "href": "/services-site/order", "cta": True},
	],
	"Statutory Audit": [
		{"key": "home", "ar": "الرئيسية", "en": "Home", "href": "/services-site"},
		{"key": "services", "ar": "الخدمات", "en": "Services", "href": "/services-site/products"},
		{"key": "contact", "ar": "تواصل", "en": "Contact", "href": "/services-site/order", "cta": True},
	],
}


def activity_site_path(activity: str) -> str:
	return ACTIVITY_SITE_PATHS.get(activity, "/services-site")


def default_hero_image(activity: str) -> str:
	return DEFAULT_HERO_IMAGES.get(activity, DEFAULT_HERO_IMAGES["General"])


def _query_suffix(*, site_slug: str | None = None, company: str | None = None, branch: str | None = None) -> str:
	if site_slug:
		return f"?site={site_slug}"
	if company:
		q = f"company={company}"
		if branch:
			q += f"&branch={branch}"
		return f"?{q}"
	return ""


def build_activity_site_url(
	*,
	company: str,
	activity: str | None = None,
	branch: str | None = None,
	site_slug: str | None = None,
) -> str:
	activity = activity or get_company_business_activity(company)
	path = activity_site_path(activity)

	# Healthcare uses Healthcare Branch Website slug when available
	if activity == "Healthcare" and branch and frappe.db.exists("DocType", "Healthcare Branch Website"):
		hospital_slug = frappe.db.get_value(
			"Healthcare Branch Website",
			{"branch": branch, "is_enabled": 1},
			"site_slug",
		)
		if hospital_slug:
			return get_url(f"{path}?site={hospital_slug}")

	if site_slug:
		return get_url(f"{path}?site={site_slug}")
	return get_url(f"{path}{_query_suffix(company=company, branch=branch)}")


def resolve_public_site_url(
	site: str | None = None,
	company: str | None = None,
	branch: str | None = None,
) -> str:
	from omnexa_experience.omnexa_experience.public_portal import resolve_portal

	ctx = resolve_portal(site=site, company=company, branch=branch)
	activity = get_company_business_activity(ctx["company"])
	return build_activity_site_url(
		company=ctx["company"],
		activity=activity,
		branch=ctx.get("branch"),
		site_slug=ctx.get("site_slug"),
	)


def activity_nav(activity: str) -> list[dict]:
	return ACTIVITY_NAV.get(activity, ACTIVITY_NAV["General"])


def activity_features(activity: str) -> list[dict]:
	return ACTIVITY_FEATURES.get(activity) or ACTIVITY_FEATURES.get("General", ACTIVITY_FEATURES["Trading"])


def activity_stats(activity: str) -> list[dict]:
	return ACTIVITY_STATS.get(activity) or ACTIVITY_STATS.get("General", ACTIVITY_STATS["Trading"])


def service_cards(activity: str) -> list[dict]:
	return SERVICE_CARD_IMAGES.get(activity, SERVICE_CARD_IMAGES.get("Trading", []))


def vertical_id_for_activity(activity: str) -> str:
	return primary_vertical_id_for_activity(activity) or "services"
