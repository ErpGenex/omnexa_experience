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
			const cta = (cfg.nav || []).find((n) => n.cta);

			document.getElementById("act-header").innerHTML = `
				<div class="act-wrap act-header-inner">
					<a class="act-brand" href="${this.esc(cfg.base_path)}${q}">${logo}<span>${this.esc(this.name())}</span></a>
					<nav class="act-nav">${nav}</nav>
					<div style="display:flex;gap:10px;align-items:center;">
						<button type="button" class="act-lang" id="act-lang">${this.lang === "ar" ? "EN" : "AR"}</button>
						${cta ? `<a class="act-btn act-btn-primary" href="${this.esc(cta.href)}${q}">${this.esc(this.t(cta.ar, cta.en))}</a>` : ""}
					</div>
				</div>`;
			document.getElementById("act-lang")?.addEventListener("click", () => {
				this.lang = this.lang === "ar" ? "en" : "ar";
				localStorage.setItem(LANG, this.lang);
				this.render();
			});

			document.getElementById("act-footer").innerHTML = `
				<div class="act-wrap">
					<h3>${this.esc(this.name())}</h3>
					<p>${this.esc(this.t(cfg.tagline_ar, cfg.tagline_en))}</p>
					<p>${this.esc((cfg.contact || {}).phone || "")} · ${this.esc((cfg.contact || {}).email || "")}</p>
				</div>`;
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

			const products = cfg.products || cfg.programs || cfg.loan_products || [];
			const cards = products.slice(0, 4).map((p) =>
				`<div class="act-card act-product-card">
					<div class="act-card-img" style="background:var(--act-accent);display:flex;align-items:center;justify-content:center;font-size:2.5rem;">📦</div>
					<div class="act-card-body"><strong>${this.esc(p.title_ar || p.title_en || p.institution_name || p.product_name || p.name)}</strong></div>
				</div>`
			).join("");

			const serviceImgs = (cfg.service_cards || []).map((s) =>
				`<div class="act-card"><img class="act-card-img" src="${this.esc(s.image)}" alt=""><div class="act-card-body"><strong>${this.esc(s.key)}</strong><p class="text-muted" style="margin:8px 0 0;">${this.lang === "ar" ? "خدمة احترافية" : "Professional service"}</p></div></div>`
			).join("");

			document.getElementById("act-main").innerHTML = `
				<section class="act-hero-pro">
					<div class="act-hero-bg" style="background-image:url('${heroImg}')"></div>
					<div class="act-wrap act-hero-content">
						<h1>${this.esc(this.t(cfg.tagline_ar, cfg.tagline_en))}</h1>
						<p>${this.esc(this.t(cfg.hero_text_ar, cfg.hero_text_en))}</p>
						<div class="act-hero-actions">
							<a class="act-btn act-btn-primary" href="${this.esc(cfg.base_path)}/products${q}">${this.lang === "ar" ? "استكشف" : "Explore"}</a>
							<a class="act-btn act-btn-outline" style="color:#fff;border-color:#fff;" href="#contact">${this.lang === "ar" ? "تواصل" : "Contact"}</a>
						</div>
					</div>
				</section>
				<div class="act-wrap"><div class="act-features-bar">${features}</div></div>
				<section class="act-stats"><div class="act-wrap act-stats-grid">${stats}</div></section>
				<section class="act-section"><div class="act-wrap">
					<div class="act-section-title"><h2>${this.lang === "ar" ? "خدماتنا / منتجاتنا" : "Our offerings"}</h2></div>
					<div class="act-grid-4">${serviceImgs || cards || `<div class="act-card act-card-body">${this.lang === "ar" ? "قريباً" : "Coming soon"}</div>`}</div>
				</div></section>
				<section class="act-section" id="contact"><div class="act-wrap act-card act-card-body" style="text-align:center;padding:32px;">
					<h2>${this.lang === "ar" ? "تواصل معنا" : "Contact us"}</h2>
					<p>${this.esc((cfg.contact || {}).phone || "")} · ${this.esc((cfg.contact || {}).email || "")}</p>
				</div></section>`;
		},

		renderProducts() {
			const cfg = this.config;
			const items = cfg.products || [];
			document.getElementById("act-main").innerHTML = `
				<section class="act-section"><div class="act-wrap">
					<div class="act-section-title"><h2>${this.lang === "ar" ? "المنتجات" : "Products"}</h2></div>
					<div class="act-grid-3">${items.map((p, i) => {
						const title = p.title_ar || p.title_en || p.service_title || p.name || "";
						const cards = cfg.service_cards || [];
						const img = (cards[i] && cards[i].image) || (cards[0] && cards[0].image) || "";
						const visual = img
							? `<img class="act-card-img" src="${this.esc(img)}" alt="">`
							: `<div class="act-card-img" style="background:linear-gradient(135deg,var(--act-accent),#fff);display:flex;align-items:center;justify-content:center;font-size:3rem;">🛍️</div>`;
						return `<div class="act-card act-product-card">${visual}
							<div class="act-card-body">
								<strong>${this.esc(this.t(p.title_ar || title, p.title_en || title))}</strong>
								<p class="text-muted">${this.esc(p.item_type || p.service_code || "")}</p>
								<a class="act-btn act-btn-primary" style="margin-top:10px;" href="${this.esc(cfg.base_path)}/order${this.q()}">${this.lang === "ar" ? "اطلب" : "Order"}</a>
							</div>
						</div>`;
					}).join("") || `<p>${this.lang === "ar" ? "لا منتجات منشورة" : "No published products"}</p>`}
					</div>
				</div></section>`;
		},

		renderPrograms() {
			const cfg = this.config;
			const items = cfg.programs || [];
			document.getElementById("act-main").innerHTML = `
				<section class="act-section"><div class="act-wrap">
					<div class="act-section-title"><h2>${this.lang === "ar" ? "البرامج الدراسية" : "Programs"}</h2></div>
					<div class="act-grid-3">${items.map((p) =>
						`<div class="act-card act-card-body"><strong>${this.esc(p.institution_name || p.name)}</strong>
						<a class="act-btn act-btn-primary" href="${this.esc(cfg.base_path)}/apply${this.q()}">${this.lang === "ar" ? "قدّم الآن" : "Apply"}</a></div>`
					).join("")}</div>
				</div></section>`;
		},

		renderOrder() {
			document.getElementById("act-main").innerHTML = `
				<section class="act-section"><div class="act-wrap act-card act-card-body" style="max-width:640px;margin:0 auto;padding:32px;">
					<h2>${this.lang === "ar" ? "طلب / تقديم" : "Request / Apply"}</h2>
					<p>${this.lang === "ar" ? "سجّل الدخول أو تواصل معنا لإتمام طلبك." : "Sign in or contact us to complete your request."}</p>
					<a class="act-btn act-btn-primary" href="/login?redirect-to=${encodeURIComponent(window.location.pathname + window.location.search)}">${this.lang === "ar" ? "دخول" : "Login"}</a>
				</div></section>`;
		},
	};
})();
