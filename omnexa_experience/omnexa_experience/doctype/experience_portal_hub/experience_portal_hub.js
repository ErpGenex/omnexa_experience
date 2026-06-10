frappe.ui.form.on("Experience Portal Hub", {
	refresh(frm) {
		if (frm.is_new()) return;
		frm.add_custom_button(__("Copy activity website"), () => copy_link(frm, "activity_site"), __("Share"));
		frm.add_custom_button(__("Copy portal link"), () => copy_link(frm, "home"), __("Share"));
		frm.add_custom_button(__("Copy customer portal"), () => copy_link(frm, "customer"), __("Share"));
		frm.add_custom_button(__("Share website"), () => share_link(frm), __("Share"));
		if (frm.doc.is_enabled && frm.doc.site_slug) {
			frappe.call({
				method: "omnexa_experience.omnexa_experience.public_portal.get_portal_urls",
				args: { company: frm.doc.company },
				callback(r) {
					const siteUrl = (r.message.urls && r.message.urls.activity_site) || r.message.public_url;
					const portalUrl = `/portal?site=${encodeURIComponent(frm.doc.site_slug)}`;
					frm.dashboard.add_comment(
						__("Activity website: {0}", [`<a href="${siteUrl}" target="_blank">${siteUrl}</a>`]),
						"blue",
						true
					);
					frm.dashboard.add_comment(
						__("Unified portal: {0}", [`<a href="${portalUrl}" target="_blank">${portalUrl}</a>`]),
						"blue",
						true
					);
				},
			});
		}
	},
});

function copy_link(frm, key) {
	frappe.call({
		method: "omnexa_experience.omnexa_experience.public_portal.get_portal_urls",
		args: { company: frm.doc.company },
		callback(r) {
			const url = (r.message.urls && r.message.urls[key]) || r.message.public_url;
			frappe.utils.copy_to_clipboard(url);
			frappe.show_alert({ message: __("Link copied"), indicator: "green" });
		},
	});
}

function share_link(frm) {
	frappe.call({
		method: "omnexa_experience.omnexa_experience.public_portal.get_portal_urls",
		args: { company: frm.doc.company },
		callback(r) {
			const url = r.message.public_url;
			const title = frm.doc.portal_name_ar || frm.doc.portal_name_en;
			if (navigator.share) {
				navigator.share({ title, url }).catch(() => {
					frappe.utils.copy_to_clipboard(url);
					frappe.show_alert({ message: __("Link copied"), indicator: "green" });
				});
			} else {
				frappe.utils.copy_to_clipboard(url);
				frappe.show_alert({ message: __("Link copied"), indicator: "green" });
			}
		},
	});
}
