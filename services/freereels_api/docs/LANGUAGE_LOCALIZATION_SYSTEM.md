# FreeReels Language Localization System

## 1. Total Languages Supported

**24 bahasa** didukung dalam APK, dengan kondisi availability berbeda per region.

## 2. Complete Language List

| # | Locale | String ID | Restricted | Notes |
|---|--------|-----------|-----------|-------|
| 1 | en-US | R.string.f | ❌ No | English (Default) |
| 2 | es-MX | R.string.g | ❌ No | Spanish (Mexico) |
| 3 | fr-FR | R.string.h | ❌ No | French |
| 4 | pt-PT | R.string.u | ❌ No | Portuguese |
| 5 | de-DE | R.string.e | ❌ No | German |
| 6 | it-IT | R.string.k | ❌ No | Italian |
| 7 | ja-JP | R.string.l | ❌ No | Japanese |
| 8 | ko-KR | R.string.n | ❌ No | Korean |
| 9 | zh-TW | R.string.G | ❌ No | Chinese (Traditional) |
| 10 | ar-SA | R.string.a | ✅ **Yes** | Arabic |
| 11 | pl-PL | R.string.t | ✅ **Yes** | Polish |
| 12 | cs-CZ | R.string.c | ✅ **Yes** | Czech |
| 13 | ru-RU | R.string.w | ❌ No | Russian |
| 14 | tr-TR | R.string.D | ❌ No | Turkish |
| 15 | ms-MY | R.string.q | ❌ No | Malay |
| 16 | ro-RO | R.string.v | ✅ **Yes** | Romanian |
| 17 | in-ID | R.string.j | ❌ No | Indonesian |
| 18 | vi-VN | R.string.F | ❌ No | Vietnamese |
| 19 | th-TH | R.string.B | ❌ No | Thai |
| 20 | tl-PH | R.string.C | ❌ No | Tagalog |
| 21 | hi-IN | R.string.i | ❌ No | Hindi |
| 22 | bn-BD | R.string.b | ✅ **Yes** | Bengali |
| 23 | ta-IN | R.string.z | ✅ **Yes** | Tamil |
| 24 | te-IN | R.string.A | ✅ **Yes** | Telugu |

**Restricted Languages:** 9 bahasa (ar, pl, cs, ro, bn, ta, te) memiliki availability flag yang dapat dikontrol per region atau app variant.

## 3. Language Availability Control

Availability diatur melalui `CommonStore` feature flags:

```java
// Restricted language checks
getSupportAr()   // Arabic
getSupportCs()   // Czech
getSupportPl()   // Polish
getSupportRo()   // Romanian
getSupportBn()   // Bengali
getSupportTa()   // Tamil
getSupportTe()   // Telugu
```

Juga ada logic regional:
```java
com.dramawave.core.config.a.l("freereels")  // Check if app is "freereels" variant
```

Jika restricted language tapi flag disabled → **tidak muncul di language picker**.

## 4. Language Selection Flow

### A. User Selects Language

```
LanguageSettingActivity
  ↓
LanguageSettingScreenKt.b() (Compose Screen)
  ↓
User clicks language item
  ↓
analytics: "profile_settings_language_choose_click" (languagetype=XX)
  ↓
MutableState updated
  ↓
User clicks "Done" button
  ↓
analytics: "profile_setting_language_done_click" (languagetype=XX)
```

### B. API Call to Save

**Endpoint:** `POST /user/setting/language`

```kotlin
// From LanguageSettingActivity.access$initObserver$handleIntentEvent
com.dramawave.feature.profile.viewmodel.c.setLanguage(Locale locale)
  ↓
CommonStore.setUserRealLanguage(locale.getLanguage())
CommonStore.setUserRealCountry(locale.getCountry())
  ↓
Call ProfileViewModel → save via /user/setting/language
```

### C. Content Localization Applied

```java
// After successful API response:
t2.a.g()  // Refresh language pool cache
dg.g.b(l2.a.b())  // Get app language
dg.g.d(context, t2.a.h(newLocale))  // Apply locale to context
  ↓
// Force app restart to reload resources
Intent(context, MainActivity::class.java)
startActivity(intent with FLAG_ACTIVITY_CLEAR_TOP | FLAG_ACTIVITY_NEW_TASK)
```

## 5. Localization Implementation

### Resource Strings Mapping

Language picker displays localized string names:
```
R.string.f  → Display name for en-US (loaded from strings.xml)
R.string.g  → Display name for es-MX
... etc
```

Strings are loaded via `StringResources_androidKt.a()` in Compose.

### Content Localization

After language selection:
1. **App Restart Triggered** (visible to user)
2. **Locale Applied** via `LocaleUtils.setLocale(context, new Locale(lang, country))`
3. **API Requests Sent** with new `app-language` header
4. **Content Reloaded** in new language

### Special Case: India Languages

India languages (hi, ta, te, bn) have additional logic:

```java
// Check if india lang to english conversion enabled
boolean indiaLangToEnPersisted = CommonStore.INSTANCE.getIndiaLangToEnPersistedRaw()

// If enabled: convert India languages to US English internally
public static Locale h(Locale locale) {
    if (f() && d.contains(locale.getLanguage())) {
        return Locale.US;  // Replace with English
    }
    return locale;
}
```

This allows server-side to track which India language is selected, while the app UI shows English content (if the flag is set).

## 6. API Integration

### Request Parameter

Language sent in headers:
```
app-language: {language-code}  // e.g., "en-US", "fr-FR", "id-ID"
```

### Special Cases

- Indonesian (`in-ID`) is converted to `id-ID` for API calls
- Used in content requests: `/drama/info_v2`, `/search`, `/homepage`, etc.

### Response Localization

Content returned from API is localized:
```json
GET /drama/info_v2 with app-language: fr-FR
Response: {
  "data": {
    "info": {
      "name": "[TITRE EN FRANCAIS]",
      "desc": "[DESCRIPTION EN FRANCAIS]",
      "subtitle_list": [
        { "language": "fr-FR", "vtt": "..." }
      ]
    }
  }
}
```

## 7. Language Pool Entry Point

```java
// Get current language
t2.a.i()  → Returns current Locale from CommonStore

// Get all available languages (filtered)
t2.a.e()  → Returns List<Pair<Pair<Integer, Locale>, Boolean>>
            → Filters by availability flags

// Convert Locale to API format
t2.a.c(locale)  → Returns "en-US", "fr-FR", etc.
t2.a.d(locale)  → Returns "en", "fr", etc.

// Get display name of current language
t2.a.b()  → Returns localized language name
```

## 8. Testing Localization

```python
# Pseudo-code for testing language flow

# 1. Get available languages
GET /user/setting/config
→ Returns list of supported languages

# 2. Select language
POST /user/setting/language
{
  "language": "fr-FR",
  "country": "FR"
}

# 3. Request content in new language
GET /drama/info_v2?series_id=X
Headers: app-language: fr-FR
→ Response should be in French

# 4. Verify subtitle tracks match language
→ Check subtitle_list contains fr-FR track
```

## 9. Summary

- **Total Languages:** 24
- **Restricted:** 9 (controlled by feature flags)
- **Selection:** Via `LanguageSettingActivity` UI
- **Persistence:** `CommonStore` (local device storage) + server via `/user/setting/language`
- **Application:** Full app restart + all subsequent API calls use new language
- **Content Localization:** Drama titles, descriptions, subtitles, UI all localized per language selection
