/* global frappe */
(function () {
	const LANG_KEY = "ox_portal_lang";

	window.OmnexaPortal = {
		config: null,
		lang: localStorage.getItem(LANG_KEY) || "ar",
		params: new URLSearchParams(window.location.search),
		page: "home",
		vertical: null,

		init(page, vertical) {
			this.page = page || "home";
			this.vertical = vertical || null;
			this.load().then(() => this.render());
		},

		t(key) {
			const m = {
				home: { ar: "الرئيسية", en: "Home" },
				activities: { ar: "الأنشطة", en: "Activities" },
				portals: { ar: "البوابات", en: "Portals" },
				login: { ar: "دخول", en: "Login" },
				loading: { ar: "جاري التحميل...", en: "Loading..." },
				shop: { ar: "المتجر", en: "Shop" },
				book: { ar: "احجز", en: "Book" },
			};
			return (m[key] && m[key][this.lang]) || key;
		},

		esc(v) { return frappe.utils.escape_html(v == null ? "" : String(v)); },

		args() {
			const a = {};
			if (this.params.get("site")) a.site = this.params.get("site");
			if (this.params.get("company")) a.company = this.params.get("company");
			if (this.params.get("branch")) a.branch = this.params.get("branch");
			return a;
		},

		q(extra) {
			const p = new URLSearchParams(this.args());
			Object.entries(extra || {}).forEach(([k, v]) => { if (v) p.set(k, v); });
			const s = p.toString();
			return s ? `?${s}` : "";
		},

		name() {
			const c = this.config || {};
			return c[this.lang === "ar" ? "portal_name_ar" : "portal_name_en"] || c.company || "Portal";
		},

		text(base) {
			const c = this.config || {};
			return c[this.lang === "ar" ? `${base}_ar` : `${base}_en`] || "";
		},

		async load() {
			const r = await frappe.call({
				method: "omnexa_experience.omnexa_experience.public_portal.get_portal_config",
				args: this.args(),
			});
			this.config = r.message || {};
			this.syncTenantUrl();
			if (this.config.primary_color) {
				document.documentElement.style.setProperty("--oxp-primary", this.config.primary_color);
			}
			document.querySelector(".ox-portal")?.setAttribute("dir", this.lang === "ar" ? "rtl" : "ltr");
		},

		syncTenantUrl() {
			const cfg = this.config || {};
			const url = new URL(window.location.href);
			let changed = false;
			if (cfg.site_slug && !url.searchParams.get("site")) {
				url.searchParams.set("site", cfg.site_slug);
				changed = true;
			} else if (!url.searchParams.get("site") && !url.searchParams.get("company") && cfg.company) {
				url.searchParams.set("company", cfg.company);
				if (cfg.branch) url.searchParams.set("branch", cfg.branch);
				changed = true;
			}
			if (changed) {
				window.history.replaceState({}, "", url);
				this.params = url.searchParams;
			}
		},

		toggleLang() {
			this.lang = this.lang === "ar" ? "en" : "ar";
			localStorage.setItem(LANG_KEY, this.lang);
			this.render();
		},

		renderChrome() {
			const cfg = this.config || {};
			const logo = cfg.logo ? `<img src="${this.esc(cfg.logo)}" alt="">` : "🌐";
			const suffix = this.q();
			const subPortals = cfg.sub_portals || [];
			const header = document.getElementById("oxp-header");
			if (!header) return;
			header.innerHTML = `
				<div class="oxp-wrap oxp-header-inner">
					<a class="oxp-brand" href="/portal${suffix}">${logo}<span>${this.esc(this.name())}</span></a>
					<nav class="oxp-nav">
						<a href="/portal${suffix}" class="${this.page === "home" ? "active" : ""}">${this.t("home")}</a>
						${subPortals.map((p) =>
							`<a href="${this.esc(p.route)}${suffix}" class="${this.page === p.id ? "active" : ""}">${this.esc(this.lang === "ar" ? p.name_ar : p.name_en)}</a>`
						).join("")}
					</nav>
					<div style="display:flex;gap:10px;align-items:center;">
						<button type="button" class="oxp-lang" id="oxp-lang">${this.lang === "ar" ? "EN" : "AR"}</button>
						${frappe.session.user === "Guest"
							? `<a class="oxp-btn oxp-btn-outline" href="/login?redirect-to=${encodeURIComponent(window.location.pathname + window.location.search)}">${this.t("login")}</a>`
							: `<a class="oxp-btn oxp-btn-light" href="/me">${this.esc(frappe.session.user)}</a>`}
					</div>
				</div>`;
			document.getElementById("oxp-lang")?.addEventListener("click", () => this.toggleLang());

			const footer = document.getElementById("oxp-footer");
			if (footer) {
				footer.innerHTML = `
					<div class="oxp-wrap">
						<h3>${this.esc(this.name())}</h3>
						<p>${this.esc(this.text("tagline"))}</p>
						<p>${this.esc((cfg.contact || {}).phone || "")} · ${this.esc((cfg.contact || {}).email || "")}</p>
					</div>`;
			}
		},

		async render() {
			this.renderChrome();
			if (this.page === "home") return this.renderHome();
			if (this.page === "vertical") return this.renderVertical();
			return this.renderSubPortal(this.page);
		},

		async renderHome() {
			const cfg = this.config || {};
			const hero = document.getElementById("oxp-main");
			if (!hero) return;
			const verticals = cfg.verticals || [];
			const subPortals = cfg.sub_portals || [];
			const urls = cfg.urls || {};
			const primary = verticals.find((v) => v.is_primary) || verticals[0];
			const activity = cfg.business_activity || "General";
			const heroText = this.lang === "ar" ? (cfg.hero_text_ar || "") : (cfg.hero_text_en || "");
			const tagline = this.text("tagline");
			const icon = primary ? primary.icon : "🌐";

			const activitySite = urls.activity_site || urls.hospital;
			if (activitySite && this.page === "home" && cfg.layout_mode === "single_activity") {
				window.location.replace(activitySite);
				return;
			}

			const primaryCta = this.buildPrimaryCta(primary, urls, subPortals);
			const subPortalCards = subPortals.map((p) =>
				`<a class="oxp-card oxp-card-link" href="${this.esc(p.route)}${this.q()}">
					<div class="oxp-icon">${p.icon}</div>
					<strong>${this.esc(this.lang === "ar" ? p.name_ar : p.name_en)}</strong>
				</a>`
			).join("");

			hero.innerHTML = `
				<section class="oxp-hero oxp-hero-single"><div class="oxp-wrap oxp-hero-single-grid">
					<div>
						<div class="oxp-activity-badge">${icon} ${this.esc(activity)}</div>
						<h1>${this.esc(tagline)}</h1>
						<p class="oxp-hero-lead">${this.esc(heroText)}</p>
						<p class="oxp-hero-sub">${this.esc(this.name())}</p>
						<div class="oxp-hero-actions">${primaryCta}</div>
					</div>
					<div class="oxp-hero-panel">
						<div class="oxp-hero-panel-icon">${icon}</div>
						<h3>${this.esc(primary ? (this.lang === "ar" ? primary.name_ar : primary.name_en) : this.name())}</h3>
					</div>
				</div></section>
				${subPortals.length ? `
				<section class="oxp-section"><div class="oxp-wrap">
					<div class="oxp-section-title"><h2>${this.t("portals")}</h2></div>
					<div class="oxp-grid-${Math.min(subPortals.length, 4)}">${subPortalCards}</div>
				</div></section>` : ""}
				<div id="oxp-home-snapshot" class="oxp-wrap oxp-section"></div>`;

			if (primary) {
				const snap = await frappe.call({
					method: "omnexa_experience.omnexa_experience.public_portal.get_vertical_page",
					args: { ...this.args(), vertical: primary.id },
				});
				const data = snap.message || {};
				const items = data.items || [];
				const actions = data.actions || [];
				const el = document.getElementById("oxp-home-snapshot");
				if (el && (items.length || actions.length)) {
					el.innerHTML = `
						<div class="oxp-section-title"><h2>${this.lang === "ar" ? "خدماتنا" : "Our services"}</h2></div>
						${actions.length ? `<div class="oxp-hero-actions" style="margin-bottom:16px;">${actions.map((a) =>
							`<a class="oxp-btn oxp-btn-primary" href="${this.esc(a.url)}">${this.esc(a.label)}</a>`
						).join("")}</div>` : ""}
						<div class="oxp-grid-3">${items.slice(0, 6).map((item) =>
							`<div class="oxp-card"><strong>${this.esc(item.service_title || item.title_en || item.title_ar || item.resource_name || item.project_name || item.name || "")}</strong>
							${item.default_rate ? `<div>${this.esc(String(item.default_rate))}</div>` : ""}</div>`
						).join("")}</div>`;
				}
			}
		},

		buildPrimaryCta(primary, urls, subPortals) {
			const q = this.q();
			if (primary && primary.id === "healthcare" && urls.hospital) {
				return `<a class="oxp-btn oxp-btn-primary" href="${this.esc(urls.hospital)}">${this.lang === "ar" ? "الموقع الطبي" : "Medical site"}</a>`;
			}
			if (primary && primary.id === "trading") {
				return `<a class="oxp-btn oxp-btn-primary" href="/portal/customer${q}">${this.t("shop")}</a>`;
			}
			if (primary && primary.id === "education") {
				return `<a class="oxp-btn oxp-btn-primary" href="/education/apply${q}">${this.lang === "ar" ? "التقديم الأونلاين" : "Apply online"}</a>
					<a class="oxp-btn oxp-btn-outline" href="${this.esc(urls.student_portal || "/app/education-student-portal")}">${this.lang === "ar" ? "بوابة الطالب" : "Student portal"}</a>`;
			}
			if (primary && primary.id === "finance") {
				return `<a class="oxp-btn oxp-btn-primary" href="/portal/loan${q}">${this.lang === "ar" ? "طلب تمويل" : "Apply for finance"}</a>`;
			}
			if (primary && primary.id === "tourism") {
				return `<a class="oxp-btn oxp-btn-primary" href="/tourism${q}">${this.lang === "ar" ? "احجز الآن" : "Book now"}</a>`;
			}
			const customer = subPortals.find((p) => p.id === "customer");
			if (customer) {
				return `<a class="oxp-btn oxp-btn-primary" href="${this.esc(customer.route)}${q}">${this.t("shop")}</a>`;
			}
			if (primary) {
				return `<a class="oxp-btn oxp-btn-primary" href="/portal/vertical/${this.esc(primary.id)}${q}">${this.lang === "ar" ? "استكشف" : "Explore"}</a>`;
			}
			return "";
		},

		async renderVertical() {
			const main = document.getElementById("oxp-main");
			if (!main || !this.vertical) return;
			main.innerHTML = `<div class="oxp-wrap oxp-section"><div class="oxp-empty">${this.t("loading")}</div></div>`;
			const r = await frappe.call({
				method: "omnexa_experience.omnexa_experience.public_portal.get_vertical_page",
				args: { ...this.args(), vertical: this.vertical },
			});
			const data = r.message || {};
			const items = data.items || [];
			const actions = data.actions || [];
			main.innerHTML = `
				<section class="oxp-section"><div class="oxp-wrap">
					<div class="oxp-section-title"><h2>${this.esc(data.vertical || this.vertical)}</h2></div>
					<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:20px;">
						${actions.map((a) => `<a class="oxp-btn oxp-btn-primary" href="${this.esc(a.url)}">${this.esc(a.label)}</a>`).join("")}
					</div>
					<div class="oxp-grid-3">${items.map((item) =>
						`<div class="oxp-card"><strong>${this.esc(item.service_title || item.title_en || item.title_ar || item.resource_name || item.property_name || item.institution_name || item.product_name || item.label || item.name || "")}</strong>
						${item.default_rate ? `<div>${this.esc(String(item.default_rate))}</div>` : ""}
						${item.count != null ? `<div>${this.esc(String(item.count))}</div>` : ""}
						</div>`
					).join("") || `<div class="oxp-empty">${this.lang === "ar" ? "لا توجد عناصر منشورة بعد" : "No published items yet"}</div>`}
					</div>
				</div></section>`;
		},

		async renderSubPortal(subPortal) {
			const main = document.getElementById("oxp-main");
			if (!main) return;
			main.innerHTML = `<div class="oxp-wrap oxp-section"><div class="oxp-empty">${this.t("loading")}</div></div>`;

			if (frappe.session.user === "Guest") {
				main.innerHTML = `
					<section class="oxp-section"><div class="oxp-wrap oxp-card" style="text-align:center;">
						<h2>${this.lang === "ar" ? "يلزم تسجيل الدخول" : "Login required"}</h2>
						<p>${this.lang === "ar" ? "سجّل الدخول للوصول إلى لوحة حسابك" : "Sign in to access your dashboard"}</p>
						<a class="oxp-btn oxp-btn-primary" href="/login?redirect-to=${encodeURIComponent(window.location.pathname + window.location.search)}">${this.t("login")}</a>
					</section>`;
				return;
			}

			try {
				const r = await frappe.call({
					method: "omnexa_experience.omnexa_experience.public_portal.get_sub_portal_home",
					args: { ...this.args(), sub_portal: subPortal },
				});
				const data = r.message || {};
				const cards = data.cards || [];
				const lists = data.lists || [];
				main.innerHTML = `
					<section class="oxp-section"><div class="oxp-wrap">
						<div class="oxp-grid-3">${cards.map((c) =>
							`<div class="oxp-card">
								<h3>${this.esc(c.title || "")}</h3>
								<p>${this.esc(c.text || "")}</p>
								${c.url ? `<a class="oxp-btn oxp-btn-primary" href="${this.esc(c.url)}">${this.t("book")}</a>` : ""}
							</div>`
						).join("")}</div>
						${lists.map((block) =>
							`<div class="oxp-card" style="margin-top:16px;">
								<h3>${this.esc(block.title || "")}</h3>
								<ul class="oxp-list">${(block.rows || []).map((row) =>
									`<li><span>${this.esc(row.name || row.service_title || row.status || "")}</span><span>${this.esc(row.appointment_date || row.modified || row.start_datetime || "")}</span></li>`
								).join("")}</ul>
							</div>`
						).join("")}
					</div></section>`;
			} catch (err) {
				main.innerHTML = `<div class="oxp-wrap oxp-section"><div class="oxp-empty">${this.esc((err && err.message) || "Error")}</div></div>`;
			}
		},
	};
})();
