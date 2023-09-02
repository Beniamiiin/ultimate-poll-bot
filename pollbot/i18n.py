"""Translation module."""
import i18n

i18n.set("filename_format", "{locale}.{format}")
i18n.set("skip_locale_root_data", True)
i18n.set("locale", "Russian")
i18n.set("fallback", "Russian")
i18n.load_path.append("./i18n/")

#    "Persian",
supported_languages = [
    "English",
    "Russian",
    "Catalan",
    "Czech",
    "German",
    "Italian",
    "Polish",
    "Portuguese (Brazil)",
    "Spanish",
    "Turkish",
]
