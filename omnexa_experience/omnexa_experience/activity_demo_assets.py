# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Premium hero and showcase images for public activity websites (non-healthcare)."""

from __future__ import annotations

# Curated Unsplash URLs — stable, high-quality, activity-specific
ACTIVITY_HERO_IMAGES: dict[str, str] = {
	"Trading": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=1920&q=85",
	"Education": "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?auto=format&fit=crop&w=1920&q=85",
	"Manufacturing": "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&w=1920&q=85",
	"Financial Services": "https://images.unsplash.com/photo-1601597111158-2fceff29277d?auto=format&fit=crop&w=1920&q=85",
	"Tourism": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1920&q=85",
	"Hotel Assets": "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=1920&q=85",
	"Services": "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1920&q=85",
	"Statutory Audit": "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=1920&q=85",
	"Construction": "https://images.unsplash.com/photo-1504307651254-35680f356dfd?auto=format&fit=crop&w=1920&q=85",
	"Engineering Consulting": "https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=1920&q=85",
	"Agriculture": "https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=1920&q=85",
	"Bakeries": "https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=1920&q=85",
	"General": "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1920&q=85",
}

ACTIVITY_TESTIMONIALS: dict[str, list[dict]] = {
	"Trading": [
		{"name_ar": "سارة العتيبي", "name_en": "Sarah Al-Otaibi", "quote_ar": "تجربة تسوق سلسة وتوصيل في نفس اليوم.", "quote_en": "Smooth shopping and same-day delivery."},
		{"name_ar": "محمد الحربي", "name_en": "Mohammed Al-Harbi", "quote_ar": "منتجات أصلية وأسعار منافسة.", "quote_en": "Authentic products at competitive prices."},
	],
	"Education": [
		{"name_ar": "نورة القحطاني", "name_en": "Noura Al-Qahtani", "quote_ar": "برامج أكاديمية قوية ودعم طلابي ممتاز.", "quote_en": "Strong academic programs and excellent student support."},
		{"name_ar": "فهد الدوسري", "name_en": "Fahad Al-Dossari", "quote_ar": "بيئة تعليمية محفّزة وحديثة.", "quote_en": "A modern, inspiring learning environment."},
	],
	"Manufacturing": [
		{"name_ar": "خالد الشمري", "name_en": "Khaled Al-Shammari", "quote_ar": "جودة إنتاج عالية والتزام بالمواعيد.", "quote_en": "High production quality and on-time delivery."},
		{"name_ar": "ريم الغامدي", "name_en": "Reem Al-Ghamdi", "quote_ar": "شريك صناعي موثوق لسلسلة التوريد.", "quote_en": "A trusted industrial supply-chain partner."},
	],
	"Tourism": [
		{"name_ar": "لينا الزهراني", "name_en": "Lina Al-Zahrani", "quote_ar": "إقامة فاخرة وخدمة استثنائية.", "quote_en": "Luxury stay with exceptional service."},
		{"name_ar": "عبدالله المطيري", "name_en": "Abdullah Al-Mutairi", "quote_ar": "تجربة ضيافة لا تُنسى.", "quote_en": "An unforgettable hospitality experience."},
	],
	"Financial Services": [
		{"name_ar": "منى السبيعي", "name_en": "Mona Al-Subaie", "quote_ar": "إجراءات تمويل واضحة وسريعة.", "quote_en": "Clear and fast financing process."},
		{"name_ar": "يوسف العنزي", "name_en": "Youssef Al-Anzi", "quote_ar": "فريق استشاري محترف.", "quote_en": "A professional advisory team."},
	],
	"Services": [
		{"name_ar": "هند البلوي", "name_en": "Hind Al-Balawi", "quote_ar": "خدمات احترافية بجودة مؤسسية.", "quote_en": "Professional services at enterprise quality."},
		{"name_ar": "طارق السديري", "name_en": "Tariq Al-Sudairi", "quote_ar": "استجابة سريعة وحلول عملية.", "quote_en": "Fast response and practical solutions."},
	],
	"Construction": [
		{"name_ar": "بندر العمري", "name_en": "Bandar Al-Omari", "quote_ar": "تنفيذ مشاريع بمعايير عالية.", "quote_en": "Projects delivered to high standards."},
		{"name_ar": "Amal Al-Rashidi", "name_en": "Amal Al-Rashidi", "quote_ar": "التزام بالجدول الزمني والجودة.", "quote_en": "Committed to schedule and quality."},
	],
	"Agriculture": [
		{"name_ar": "سعد القرني", "name_en": "Saad Al-Qarni", "quote_ar": "منتجات طازجة وموثوقة.", "quote_en": "Fresh, trusted produce."},
		{"name_ar": "جواهر الحازمي", "name_en": "Jawaher Al-Hazmi", "quote_ar": "استشارات زراعية عملية.", "quote_en": "Practical farm advisory."},
	],
	"Bakeries": [
		{"name_ar": "لمى الشهري", "name_en": "Lama Al-Shehri", "quote_ar": "معجنات طازجة يومياً.", "quote_en": "Fresh pastries every day."},
		{"name_ar": "Rakan Al-Fahad", "name_en": "Rakan Al-Fahad", "quote_ar": "تموين مناسبات بمستوى فاخر.", "quote_en": "Premium event catering."},
	],
	"Engineering Consulting": [
		{"name_ar": "Eng. Sami", "name_en": "Eng. Sami", "quote_ar": "تصاميم هندسية دقيقة.", "quote_en": "Precise engineering designs."},
		{"name_ar": "Eng. Dina", "name_en": "Eng. Dina", "quote_ar": "إشراف ميداني محترف.", "quote_en": "Professional site supervision."},
	],
}


def premium_hero_image(activity: str) -> str:
	return ACTIVITY_HERO_IMAGES.get(activity, ACTIVITY_HERO_IMAGES["General"])


def activity_testimonials(activity: str) -> list[dict]:
	base = ACTIVITY_TESTIMONIALS.get("Services", [])
	return ACTIVITY_TESTIMONIALS.get(activity, base)
