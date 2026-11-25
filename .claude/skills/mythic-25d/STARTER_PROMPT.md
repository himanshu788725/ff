# Starter prompts — copy, paste, replace the brackets

Open Claude Code in this repo (the skill auto-loads from `.claude/skills/mythic-25d`) and paste one of these.

---

## 1. पूरी फ़िल्म — हिंदी स्क्रिप्ट से (long-form 16:9)

```
/mythic-25d
मेरी नीचे दी गई हिंदी स्क्रिप्ट से mythic-25d स्किल का उपयोग करके एक painted 2.5D puppet-theatre फ़िल्म बनाओ।
- प्रोजेक्ट नाम: [project_name], फ़ॉर्मेट 16:9, शीर्षक: "[फ़िल्म का शीर्षक]"
- curtain intro + outro रखो, outro टेक्स्ट: "[॥ जय श्री राम ॥]"
- narrator आवाज़: hi-IN-MadhurNeural, संवादों के लिए हर पात्र की अलग आवाज़/पिच
- हर वाक्य के लिए सही दृश्य (env) और समय (dawn/day/dusk/night), सही पात्र (catalog ids), हर बोलने वाले पात्र का अभिनय
- कैमरा मूवमेंट हर शॉट में अलग, जहाँ श्लोक हो वहाँ shloka card
- music mood: [devotional/epic_battle/...], युद्ध/दिव्य दृश्यों में mood बदलो
पहले storyboard.yaml लिखो, validate करो, 3 key shots के stills दिखाओ, फिर preview बनाओ, review पढ़कर सुधारो,
और अंत में final render करो। आख़िर में बताओ कि output files कहाँ हैं।

स्क्रिप्ट:
"""
[यहाँ अपनी पूरी हिंदी कहानी/स्क्रिप्ट पेस्ट करें]
"""
```

## 2. YouTube Short / Reel (9:16, 30–55 सेकंड)

```
/mythic-25d
इस विषय पर 9:16 का 45 सेकंड का Short बनाओ: "[विषय — जैसे: कर्ण का कवच-कुंडल दान]".
पहले 2 सेकंड में hook वाला सवाल, 5-7 शॉट, pop subtitles, पात्र बड़े (scale 1.25), epic_battle music,
अंत में एक लाइन का CTA. स्क्रिप्ट भी तुम ही लिखो (सरल, रोचक हिंदी), फिर पूरा pipeline चलाकर final दो।
```

## 3. Own voice-over (मेरी अपनी आवाज़)

```
/mythic-25d
मेरे पास अपनी रिकॉर्डिंग्स हैं: mythic_projects/[name]/vo/ में (01.wav, 02.wav ...), और script.txt में उनका टेक्स्ट
उसी क्रम में है। voice.engine: files लगाओ, हर शॉट की narration_audio सेट करो, word-timed subtitles align करो,
फिर फ़िल्म बनाओ।
```

## 4. Review / troubleshoot an existing project

```
/mythic-25d
mythic_projects/[name] का review चलाओ, qa.json और contact sheet देखो, हर warning ठीक करो
(subtitle speed, कटे हुए पात्र, static shots, loudness), सिर्फ़ बदले हुए shots दोबारा render करो, फिर final बनाओ।
```

## 5. New character / environment

```
/mythic-25d
एक नया पात्र जोड़ो: "[नाम]" — [रूप-रंग, मुकुट, वस्त्र, अस्त्र, वाहन]. पहले `mythic.py char` से pose sheet बनाकर दिखाओ,
फिर उसे catalog में स्थायी रूप से जोड़ो (gen_catalog.py) और docs regenerate करो।
```

---

## English version (any language works)

```
/mythic-25d
Turn the Hindi script below into a painted 2.5D Indian puppet-theatre film using the mythic-25d skill.
Project: [name], 16:9, title "[title]". Curtain intro/outro. Narrator hi-IN-MadhurNeural, distinct voices per
character. One shot per beat with the right environment & time of day, catalog characters only, real acting
for every speaker, varied camera moves, shloka cards for verses, music mood [mood] switching for battle/divine
beats. Write storyboard.yaml → validate → show me 3 key stills → preview → fix what the review flags → final.
Tell me where the outputs are.

Script:
"""
[paste]
"""
```

### Tips
- Keep sentences short; one image per sentence.
- Mention places & time of day in the script ("संध्या के समय, कुरुक्षेत्र में…") — Claude maps them to environments.
- Ask for `mythic.py gallery --cat devi` (or any category) to browse ready characters.
