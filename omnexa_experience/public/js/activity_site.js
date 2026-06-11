/* global frappe */
(function () {
	const LANG = "act_site_lang";

	window.ActivitySite = {
		config: null,
		lang: localStorage.getItem(LANG) || "ar",
		params: new URLSearchParams(window.location.search),
		page: "home",
		apiMethod: "omnexa_experience.omnexa_experience.activity_site_api.get_activity_site_pack_api",

		init(page, apiMethod) {
			this.page = page || "home";
			if (apiMethod) this.apiMethod = apiMethod;
			this.load().then(() => this.render());
		},

		esc(v) { return frappe.utils.escape_html(v == null ? "" : String(v)); },
		t(ar, en) { return this.lang === "ar" ? ar : en; },

		args() {
			const a = {};
			if (this.params.get("site")) a.site = this.params.get("site");
			if (this.params.get("company")) a.company = this.params.get("company");
			return a;
		},

		q() {
			const p = new URLSearchParams(this.args());
			const s = p.toString();
			return s ? `?${s}` : "";
		},

		ctaPath() {
			const cfg = this.config || {};
			const nav = cfg.nav || [];
			const cta = nav.find((n) => n.cta);
			if (cta && cta.href) return cta.href;
			const order = nav.find((n) => ["order", "apply", "book"].includes(n.key));
			return order ? order.href : `${cfg.base_path || ""}/order`;
		},

		ctaLabel() {
			const cfg = this.config || {};
			const cta = (cfg.nav || []).find((n) => n.cta);
			if (cta) return this.t(cta.ar, cta.en);
			return this.lang === "ar" ? "ابدأ الآن" : "Get started";
		},

		productTitle(p) {
			return this.t(p.title_ar || p.title_en || p.institution_name || p.product_name || p.name, p.title_en || p.title_ar || p.name);
		},

		async load() {
			const r = await frappe.call({ method: this.apiMethod, args: this.args() });
			this.config = r.message || {};
			if (this.config.primary_color) {
				document.documentElement.style.setProperty("--act-primary", this.config.primary_color);
			}
			const root = document.querySelector(".act-site");
			if (root) {
				root.dir = this.lang === "ar" ? "rtl" : "ltr";
				root.lang = this.lang;
			}
			this.syncUrl();
		},

		syncUrl() {
			const cfg = this.config || {};
			const url = new URL(window.location.href);
			if (cfg.site_slug && !url.searchParams.get("site")) {
				url.searchParams.set("site", cfg.site_slug);
				window.history.replaceState({}, "", url);
				this.params = url.searchParams;
			}
		},

		name() { return this.t(this.config.name_ar, this.config.name_en); },

		renderChrome() {
			const cfg = this.config || {};
			const logo = cfg.logo ? `<img src="${this.esc(cfg.logo)}" alt="">` : "🌐";
			const q = this.q();
			const nav = (cfg.nav || []).map((n) =>
				`<a href="${this.esc(n.href)}${q}" class="${this.page === n.key ? "active" : ""}">${this.esc(this.t(n.ar, n.en))}</a>`
			).join("");

			document.getElementById("act-header").innerHTML = `
				<div class="act-wrap act-header-inner">
					<a class="act-brand" href="${this.esc(cfg.base_path)}${q}">${logo}<span>${this.esc(this.name())}</span></a>
					<nav class="act-nav">${nav}</nav>
					<div class="act-header-actions">
						<button type="button" class="act-lang" id="act-lang">${this.lang === "ar" ? "EN" : "AR"}</button>
						<a class="act-btn act-btn-primary" href="${this.esc(this.ctaPath())}${q}">${this.esc(this.ctaLabel())}</a>
					</div>
				</div>`;
			document.getElementById("act-lang")?.addEventListener("click", () => {
				this.lang = this.lang === "ar" ? "en" : "ar";
				localStorage.setItem(LANG, this.lang);
				this.render();
			});

			document.getElementById("act-footer").innerHTML = `
				<div class="act-wrap act-footer-grid">
					<div>
						<h3>${this.esc(this.name())}</h3>
						<p>${this.esc(this.t(cfg.tagline_ar, cfg.tagline_en))}</p>
					</div>
					<div>
						<h4>${this.lang === "ar" ? "روابط سريعة" : "Quick links"}</h4>
						${(cfg.nav || []).map((n) => `<a href="${this.esc(n.href)}${q}">${this.esc(this.t(n.ar, n.en))}</a>`).join("")}
					</div>
					<div>
						<h4>${this.lang === "ar" ? "تواصل" : "Contact"}</h4>
						<p>${this.esc((cfg.contact || {}).phone || "")}</p>
						<p>${this.esc((cfg.contact || {}).email || "")}</p>
					</div>
				</div>
				<div class="act-wrap act-footer-copy">© ${new Date().getFullYear()} ${this.esc(this.name())}</div>`;
		},

		render() {
			this.renderChrome();
			if (this.page === "home") return this.renderHome();
			if (this.page === "products") return this.renderProducts();
			if (this.page === "order" || this.page === "apply") return this.renderOrder();
			if (this.page === "programs") return this.renderPrograms();
		},

		renderHome() {
			const cfg = this.config;
			const q = this.q();
			const heroImg = this.esc(cfg.hero_image || "");
			const features = (cfg.features || []).map((f) =>
				`<div class="act-feature"><span>${f.icon}</span>${this.esc(this.t(f.ar, f.en))}</div>`
			).join("");
			const stats = (cfg.stats || []).map((s) =>
				`<div><div class="act-stat-num">${this.esc(s.value)}</div><div class="act-stat-label">${this.esc(this.t(s.ar, s.en))}</div></div>`
			).join("");

			const serviceImgs = (cfg.service_cards || []).map((s) =>
				`<div class="act-card act-service-card">
					<img class="act-card-img" src="${this.esc(s.image)}" alt="">
					<div class="act-card-body"><strong>${this.esc(s.key)}</strong>
					<p class="act-muted">${this.lang === "ar" ? "خدمة احترافية بمعايير عالمية" : "Professional service at global standards"}</p></div>
				</div>`
			).join("");

			const products = cfg.products || cfg.programs || cfg.loan_products || [];
			const productCards = products.slice(0, 4).map((p, i) => {
				const cards = cfg.service_cards || [];
				const img = (cards[i] && cards[i].image) || (cards[0] && cards[0].image) || "";
				const visual = img
					? `<img class="act-card-img" src="${this.esc(img)}" alt="">`
					: `<div class="act-card-img act-card-placeholder">📦</div>`;
				return `<div class="act-card act-product-card">${visual}
					<div class="act-card-body"><strong>${this.esc(this.productTitle(p))}</strong>
					<a class="act-link-btn" href="${this.esc(cfg.base_path)}/products${q}">${this.lang === "ar" ? "التفاصيل" : "Details"}</a></div></div>`;
			}).join("");

			const testimonials = (cfg.testimonials || []).map((row) =>
				`<div class="act-testimonial act-card act-card-body">
					<p class="act-quote">“${this.esc(this.t(row.quote_ar, row.quote_en))}”</p>
					<strong>${this.esc(this.t(row.name_ar, row.name_en))}</strong>
				</div>`
			).join("");

			document.getElementById("act-main").innerHTML = `
				<section class="act-hero-pro">
					<div class="act-hero-bg" style="background-image:url('${heroImg}')"></div>
					<div class="act-wrap act-hero-content">
						<p class="act-hero-kicker">${this.esc(this.name())}</p>
						<h1>${this.esc(this.t(cfg.tagline_ar, cfg.tagline_en))}</h1>
						<p>${this.esc(this.t(cfg.hero_text_ar, cfg.hero_text_en))}</p>
						<div class="act-hero-actions">
							<a class="act-btn act-btn-primary" href="${this.esc(cfg.base_path)}/products${q}">${this.lang === "ar" ? "استكشف" : "Explore"}</a>
							<a class="act-btn act-btn-outline act-btn-hero-outline" href="#contact">${this.lang === "ar" ? "تواصل معنا" : "Contact us"}</a>
						</div>
					</div>
				</section>
				<div class="act-wrap"><div class="act-features-bar">${features}</div></div>
				<section class="act-stats"><div class="act-wrap act-stats-grid">${stats}</div></section>
				<section class="act-section">
					<div class="act-wrap">
						<div class="act-section-title">
							<h2>${this.lang === "ar" ? "خدماتنا / منتجاتنا" : "Our offerings"}</h2>
							<p>${this.lang === "ar" ? "حلول متكاملة بجودة مؤسسية" : "Integrated solutions with enterprise quality"}</p>
						</div>
						<div class="act-grid-4">${serviceImgs || productCards || `<div class="act-card act-card-body act-empty">${this.lang === "ar" ? "قريباً" : "Coming soon"}</div>`}</div>
					</div>
				</section>
				${products.length ? `<section class="act-section act-section-alt">
					<div class="act-wrap">
						<div class="act-section-title">
							<h2>${this.lang === "ar" ? "مختارات مميزة" : "Featured picks"}</h2>
							<p>${this.lang === "ar" ? "أبرز ما نقدمه لعملائنا" : "Highlights from our catalog"}</p>
						</div>
						<div class="act-grid-4">${productCards}</div>
					</div>
				</section>` : ""}
				${testimonials ? `<section class="act-section">
					<div class="act-wrap">
						<div class="act-section-title">
							<h2>${this.lang === "ar" ? "آراء العملاء" : "Client testimonials"}</h2>
							<p>${this.lang === "ar" ? "ثقة شركائنا هي شهادتنا" : "Our partners' trust is our credential"}</p>
						</div>
						<div class="act-grid-2">${testimonials}</div>
					</div>
				</section>` : ""}
				<section class="act-section act-cta-banner">
					<div class="act-wrap act-card act-cta-inner">
						<h2>${this.lang === "ar" ? "جاهز للبدء؟" : "Ready to get started?"}</h2>
						<p>${this.esc(this.t(cfg.hero_text_ar, cfg.hero_text_en))}</p>
						<a class="act-btn act-btn-primary act-btn-lg" href="${this.esc(this.ctaPath())}${q}">${this.esc(this.ctaLabel())}</a>
					</div>
				</section>
				<section class="act-section" id="contact">
					<div class="act-wrap act-card act-card-body act-contact-card">
						<h2>${this.lang === "ar" ? "تواصل معنا" : "Contact us"}</h2>
						<p>${this.esc((cfg.contact || {}).phone || "")} · ${this.esc((cfg.contact || {}).email || "")}</p>
					</div>
				</section>`;
		},

		renderProducts() {
			const cfg = this.config;
			const q = this.q();
			const items = cfg.products || cfg.programs || cfg.loan_products || [];
			const title = cfg.programs ? (this.lang === "ar" ? "البرامج / المنتجات" : "Programs / Products") : (this.lang === "ar" ? "المنتجات والخدمات" : "Products & services");
			document.getElementById("act-main").innerHTML = `
				<section class="act-section act-page-hero">
					<div class="act-wrap">
						<h1>${title}</h1>
						<p>${this.esc(this.t(cfg.tagline_ar, cfg.tagline_en))}</p>
					</div>
				</section>
				<section class="act-section"><div class="act-wrap">
					<div class="act-grid-3">${items.map((p, i) => {
						const cards = cfg.service_cards || [];
						const img = (cards[i] && cards[i].image) || (cards[0] && cards[0].image) || "";
						const visual = img
							? `<img class="act-card-img" src="${this.esc(img)}" alt="">`
							: `<div class="act-card-img act-card-placeholder">🛍️</div>`;
						const path = cfg.programs ? `${cfg.base_path}/apply` : `${cfg.base_path}/order`;
						const btn = cfg.programs ? (this.lang === "ar" ? "قدّم" : "Apply") : (this.lang === "ar" ? "اطلب" : "Order");
						return `<div class="act-card act-product-card">${visual}
							<div class="act-card-body">
								<strong>${this.esc(this.productTitle(p))}</strong>
								<p class="act-muted">${this.esc(p.item_type || p.service_code || p.degree_level || "")}</p>
								<a class="act-btn act-btn-primary" href="${this.esc(path)}${q}">${btn}</a>
							</div>
						</div>`;
					}).join("") || `<p class="act-empty">${this.lang === "ar" ? "لا منتجات منشورة — شغّل ديمو موقع النشاط من إعدادات الشركة" : "No published items — seed activity website demo from Company settings"}</p>`}
					</div>
				</div></section>`;
		},

		renderPrograms() {
			const cfg = this.config;
			const q = this.q();
			const items = cfg.programs || [];
			document.getElementById("act-main").innerHTML = `
				<section class="act-section act-page-hero"><div class="act-wrap">
					<h1>${this.lang === "ar" ? "البرامج الدراسية" : "Academic programs"}</h1>
					<p>${this.esc(this.t(cfg.tagline_ar, cfg.tagline_en))}</p>
				</div></section>
				<section class="act-section"><div class="act-wrap">
					<div class="act-grid-3">${items.map((p, i) => {
						const cards = cfg.service_cards || [];
						const img = (cards[i] && cards[i].image) || (cards[0] && cards[0].image) || "";
						const visual = img ? `<img class="act-card-img" src="${this.esc(img)}" alt="">` : "";
						return `<div class="act-card act-product-card">${visual}
						<div class="act-card-body"><strong>${this.esc(p.institution_name || p.program_name || p.name)}</strong>
						<p class="act-muted">${this.esc(p.degree_level || "")}</p>
						<a class="act-btn act-btn-primary" href="${this.esc(cfg.base_path)}/apply${q}">${this.lang === "ar" ? "قدّم الآن" : "Apply now"}</a></div></div>`;
					}).join("")}</div>
				</div></section>`;
		},

		renderOrder() {
			const q = this.q();
			document.getElementById("act-main").innerHTML = `
				<section class="act-section"><div class="act-wrap act-card act-card-body act-order-card">
					<h2>${this.lang === "ar" ? "طلب / تقديم" : "Request / Apply"}</h2>
					<p>${this.lang === "ar" ? "سجّل الدخول أو تواصل معنا لإتمام طلبك." : "Sign in or contact us to complete your request."}</p>
					<a class="act-btn act-btn-primary" href="/login?redirect-to=${encodeURIComponent(window.location.pathname + window.location.search)}">${this.lang === "ar" ? "دخول" : "Login"}</a>
					<a class="act-btn act-btn-outline" style="margin-inline-start:10px;" href="${this.esc(this.config.base_path)}${q}">${this.lang === "ar" ? "العودة للرئيسية" : "Back to home"}</a>
				</div></section>`;
		},
	};
})();
