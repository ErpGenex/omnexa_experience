app_name = "omnexa_experience"
app_title = "ErpGenEx — Experience"
app_publisher = "ErpGenEx"
app_description = "Public web, catalog, checkout, and booking for ErpGenEx (omnexa_experience)"
app_email = "dev@erpgenex.com"
app_license = "mit"

# Apps
# ------------------

required_apps = ["omnexa_core", "omnexa_accounting"]

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "omnexa_experience",
# 		"logo": "/assets/omnexa_experience/logo.png",
# 		"title": "Omnexa Experience",
# 		"route": "/omnexa_experience",
# 		"has_permission": "omnexa_experience.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# Desk theme (ERPGenEx Theme 0426) is loaded by omnexa_theme_manager.

# include js, css files in header of web template
web_include_css = [
	"/assets/omnexa_experience/css/design_tokens.css",
	"/assets/omnexa_experience/css/portal_shell.css",
]
web_include_js = "/assets/omnexa_experience/js/portal_shell.js"

doctype_js = {
	"Experience Portal Hub": "omnexa_experience/doctype/experience_portal_hub/experience_portal_hub.js",
}

website_route_rules = [
	{"from_route": "/portal/vertical/<vertical>", "to_route": "portal/vertical"},
]

role_home_page = {
	"Patient Portal User": "portal/patient",
	"Portal Customer": "portal/customer",
	"Portal Doctor": "portal/doctor",
	"Portal Supplier": "portal/supplier",
	"Portal Loan Client": "portal/loan",
	"Customer": "portal/customer",
}

# Tenant CSS token overrides on public web (see DocType Experience Tenant Theme)
update_website_context = [
	"omnexa_experience.omnexa_experience.web_theme.update_website_context",
]

# Public preview URL support for Experience Tenant Theme (query params)
before_request = [
	"omnexa_experience.omnexa_experience.theme_preview.before_request_theme_preview",
]

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "omnexa_experience/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views (Experience Tenant Theme: omnexa_theme_manager)
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "omnexa_experience/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "omnexa_experience.utils.jinja_methods",
# 	"filters": "omnexa_experience.utils.jinja_filters"
# }

# Installation
# ------------

before_install = "omnexa_experience.install.enforce_supported_frappe_version"
before_migrate = "omnexa_experience.install.enforce_supported_frappe_version"
after_install = "omnexa_experience.install.after_install"
after_migrate = "omnexa_experience.install.after_migrate"

# Uninstallation
# ------------

# before_uninstall = "omnexa_experience.uninstall.before_uninstall"
# after_uninstall = "omnexa_experience.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "omnexa_experience.utils.before_app_install"
# after_app_install = "omnexa_experience.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "omnexa_experience.utils.before_app_uninstall"
# after_app_uninstall = "omnexa_experience.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "omnexa_experience.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"omnexa_experience.tasks.all"
# 	],
# 	"daily": [
# 		"omnexa_experience.tasks.daily"
# 	],
# 	"hourly": [
# 		"omnexa_experience.tasks.hourly"
# 	],
# 	"weekly": [
# 		"omnexa_experience.tasks.weekly"
# 	],
# 	"monthly": [
# 		"omnexa_experience.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "omnexa_experience.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "omnexa_experience.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "omnexa_experience.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["omnexa_experience.utils.before_request"]
# after_request = ["omnexa_experience.utils.after_request"]

# Job Events
# ----------
# before_job = ["omnexa_experience.utils.before_job"]
# after_job = ["omnexa_experience.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"omnexa_experience.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

