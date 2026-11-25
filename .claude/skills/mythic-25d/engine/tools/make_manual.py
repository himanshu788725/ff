"""Build the bilingual (Hindi + English) PDF manual of the mythic-25d skill.

    python .claude/skills/mythic-25d/engine/tools/make_manual.py [--images DIR] [--out docs/Mythic25D_Manual.pdf]

HTML is generated from the live engine data (catalog, environments, actions, camera moves, music, SFX)
and printed to PDF by Chromium (Playwright via Node) so Devanagari is shaped correctly (HarfBuzz).
"""
import argparse
import html
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1]
SKILL = ENGINE.parent
sys.path.insert(0, str(ENGINE))

from mythic25d.actions import ACTION_HELP  # noqa: E402
from mythic25d.catalog import all_entities  # noqa: E402
from mythic25d.envs import LIFE, LOCALES, list_envs  # noqa: E402
from mythic25d.grade import GRADES  # noqa: E402
from mythic25d.music import MOODS, RAGAS  # noqa: E402
from mythic25d.render import CAM_PRESETS  # noqa: E402
from mythic25d.sfx import GEN  # noqa: E402
from mythic25d.util import FONT_DIR  # noqa: E402

e = html.escape

CAM_HI = {
    "drift": "धीमा सरकना (default)", "push_in": "धीरे पास जाना", "pull_out": "धीरे पीछे हटना", "pan_left": "बाएँ सरकना",
    "pan_right": "दाएँ सरकना", "tilt_up": "ऊपर झुकना", "tilt_down": "नीचे झुकना", "close_up": "क्लोज़-अप", "static": "स्थिर",
    "truck_right": "दाएँ ट्रक — सबसे गहरा parallax", "truck_left": "बाएँ ट्रक — सबसे गहरा parallax",
    "crane_down": "आसमान से नीचे पात्र पर", "crane_up": "पात्र से ऊपर आसमान तक", "establish": "पूरा सेट → पात्र पर धकेलना",
    "reveal": "पात्र से पीछे हटकर पूरा सेट", "push_to": "चेहरे पर धीमा push", "follow": "चलते पात्र के साथ चलना",
    "float": "स्वप्न जैसा तैरता कैमरा", "dolly_zoom": "झटका / अहसास",
}


def img(path, cls="full", cap=None):
    if not path or not Path(path).exists():
        return ""
    c = f'<figcaption>{cap}</figcaption>' if cap else ""
    return f'<figure class="{cls}"><img src="file://{Path(path).resolve()}">{c}</figure>'


def table(head, rows, cls=""):
    h = "".join(f"<th>{x}</th>" for x in head)
    b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<table class="{cls}"><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>'


def build_html(images: Path, out_html: Path):
    docs = SKILL / "docs"
    I = lambda name: next((p for p in (images / name, docs / name) if p.exists()), None)  # noqa: E731
    ents = all_entities()
    chars = [x for x in ents.values() if x.get("kind", "humanoid") == "humanoid"]
    beasts = [x for x in ents.values() if x.get("kind") in ("quadruped", "serpent", "fish")]
    birds = [x for x in ents.values() if x.get("kind") == "bird"]
    cats = {}
    for c in chars:
        cats.setdefault(c.get("cat", "?"), []).append(c)
    demo = (SKILL.parents[2] / "mythic_projects/demo_hanuman_bhima/storyboard.yaml")
    demo_txt = demo.read_text(encoding="utf-8") if demo.exists() else ""
    demo_snip = demo_txt[demo_txt.find("  - id: s2_bhima"):demo_txt.find("  - id: s3_vinti")] if demo_txt else ""
    starter = (SKILL / "STARTER_PROMPT.md").read_text(encoding="utf-8")
    p1 = starter[starter.find("```", starter.find("## 1.")) + 3:]
    p1 = p1[:p1.find("```")].strip()

    S = []
    # ------------------------------------------------------------------ cover
    S.append(f'''<section class="cover">
<div class="kicker">Claude Code Skill · mythic-25d</div>
<h1>मिथिक 2.5D</h1>
<div class="sub">पेंटेड कठपुतली-रंगमंच फ़िल्में — हिंदी स्क्रिप्ट से पूरी वीडियो</div>
<div class="sub2">Painted 2.5D Indian-mythology puppet-theatre films from a Hindi script</div>
{img(I("film_cover.jpg") or I("film_8.5.jpg"), "hero")}
<div class="nums"><div><b>{len(chars)}</b>पात्र<br><small>characters</small></div><div><b>{len(beasts) + len(birds)}</b>पशु-पक्षी<br><small>animals & birds</small></div>
<div><b>{len(list_envs())}</b>दृश्य<br><small>environments</small></div><div><b>{len(ACTION_HELP)}</b>अभिनय<br><small>actions</small></div>
<div><b>{len(CAM_PRESETS)}</b>कैमरा मूव<br><small>camera moves</small></div><div><b>{len(GEN)}</b>ध्वनि प्रभाव<br><small>SFX</small></div></div>
<div class="foot">उपयोग-पुस्तिका · <span class="lat">User manual</span></div></section>''')
    # ------------------------------------------------------------------ 1 intro
    S.append(f'''<section><h2>१. यह क्या है <span>What it is</span></h2>
<p>यह एक <b>Claude Code skill + render engine</b> है। आप हिंदी में कहानी/स्क्रिप्ट देते हैं, Claude उसे <code>storyboard.yaml</code> में बदलता है,
और engine उससे पूरी फ़िल्म बनाता है — कठपुतली पात्र, चलता-फिरता 2.5D background, कैमरा मूव्स, हिंदी आवाज़, शब्द-दर-शब्द चमकते
देवनागरी subtitles, राग-आधारित संगीत, SFX, mixing, color grading और review रिपोर्ट।</p>
<p class="en">A Claude Code skill plus a Python render engine: Hindi script → storyboard → finished film with jointed paper
puppets, a living layered background, reference-style camera, Hindi voice, word-timed Devanagari subtitles, raga music,
SFX, a first-pass mix, grading and an HTML review page. Output: 16:9 YouTube or 9:16 Shorts/Reels.</p>
{table(["क्या मिलता है / What you get", "विवरण / Details"], [
        ["पात्र / Characters", f"{len(chars)} — त्रिदेव, त्रिदेवी, 57 देवी रूप, दशावतार, देवता, रामायण, महाभारत, कृष्ण-लीला, ऋषि-मुनि, राक्षस-असुर, नाग, अप्सरा, राजा, सैनिक, ग्रामीण"],
        ["पशु-पक्षी / Animals & birds", f"{len(beasts)} पशु/सर्प/मछली (ऐरावत, नंदी, कामधेनु, उच्चैःश्रवा, शेषनाग…) + {len(birds)} पक्षी (गरुड़, जटायु, हंस, मोर…)"],
        ["दृश्य / Environments", f"{len(list_envs())} — {len(LOCALES)} स्थान × सुबह/दिन/संध्या/रात/अग्नि/दिव्य/तूफ़ान/ब्रह्माण्ड"],
        ["कैमरा / Camera", "crane, truck, establish, follow, push_to, reveal… + foreground wipe + silhouette"],
        ["आवाज़ / Voice", "edge-tts हिंदी neural आवाज़ें (word boundaries) या अपनी रिकॉर्डिंग"],
        ["Subtitles", "karaoke / keyword / pop · श्लोक card (शब्दार्थ सहित) · SRT"],
        ["संगीत / Music", f"{len(RAGAS)} राग, {len(MOODS)} mood — तानपुरा, बाँसुरी, शहनाई, संतूर, सितार, तबला, ढोल"],
        ["Mix · Grade · Review", "ducking, −14 LUFS, stems · 10 grade presets + .cube LUT · HTML review + QA"],
    ])}</section>''')
    # ------------------------------------------------------------------ 2 look
    S.append(f'''<section><h2>२. लुक — पात्र बाहर क्यों उभरते हैं <span>The pop-out 2.5D look</span></h2>
<ol class="big">
<li><b>मोटी गहरी outline</b> — हर अंग का अलग कटा हुआ काग़ज़, overlap साफ़ दिखता है। <i>Thick cut-paper outline per limb piece.</i></li>
<li><b>Volume shading</b> — किनारे गहरे, नीचे-दाएँ छाया, ऊपर-बाएँ रोशनी (bevel + rim)। <i>Bevelled, painted volume.</i></li>
<li><b>जोड़ों पर कीलें</b> — बाँह, जाँघ, पिंडली, पशुओं के घुटने अलग टुकड़े; चलते समय घुटने मुड़ते हैं। <i>Segmented limbs with rivets.</i></li>
<li><b>रोशन कठपुतली, धीमा सेट</b> — पात्र के चारों ओर गर्म आभा + तेज़ rim glow + light wrap; पीछे का सेट हल्का धुँधला/मद्धम। <i>Lit puppet, dimmed set.</i></li>
<li><b>गर्म अँधेरा</b> — रात भूरी-गर्म, दीयों जैसी रोशनी; धूल, धुंध, किरणें, film grain। <i>Warm darkness, haze, grain.</i></li>
</ol>
<h3>हर कठपुतली की बनावट <span class="en">Puppet anatomy</span></h3>
{table(["अंग / piece", "विवरण / detail"], [
    ["मुकुट", "ऊपर पतले होते गोल सुनहरे छल्ले, हर छल्ले पर रत्न, कमल-कली शिखर, रत्न-जड़ित पट्टी, पीछे लाल लौ-पंख · <i>stacked gold rings, lotus finial, red flame plume</i>"],
    ["चेहरा · कान", "profile, बड़ी बादामी आँख काजल सहित, घुमावदार मूँछ, तिलक; गाल पर गोल सुनहरा कुंडल लाल रत्न के साथ; स्त्रियों की बड़ी नथ और झुमका · <i>kundal disc, nath, jhumka</i>"],
    ["केश", "पुरुष: पीठ पर लंबे केश; स्त्री: गजरे वाली लंबी चोटी, लाल फुंदना; ऋषि: ऊँचा जटा-मुकुट · <i>locks, braid with gajra, jata dome</i>"],
    ["धड़", "हँसली, कई लड़ियों के हार, जनेऊ या क्रॉस पट्टे, मनकों की कमरबंद · <i>necklaces, crossed straps, beaded belt</i>"],
    ["भुजाएँ", "कंधे की टोपी + दोहरा बाजूबंद → कंगन वाली कलाई → अलग हाथ; कंधा/कोहनी/कलाई पर कीलें; अस्त्र हाथ में · <i>riveted shoulder, elbow, wrist</i>"],
    ["कमर · पैर", "धोती/लहँगा, धारीदार पटका फुंदने सहित; जाँघ → पिंडली + पायल, घुटने पर कील · <i>striped flap, riveted knee</i>"],
    ["आसन", "<code>pose: seated</code> — पत्थर के चबूतरे पर लाल गद्दी; स्त्रियाँ एक ओर बैठती हैं · <i>cushion on stone block</i>"],
    ["अतिरिक्त", "अतिरिक्त भुजाएँ पंखे की तरह, रावण के सिर मुकुट के चारों ओर चाप में, धनुष के साथ तरकश, कीलों वाली पूँछ · <i>arm fan, head arc, quiver</i>"],
], "small")}
{img(I("pop_look.jpg"), "full", "रावण (रात का जंगल) · नंदी (कैलाश) · आश्रम (संध्या) · भीम-हनुमान (कदली वन)")}
<div class="row">{img(I("film_18.5.jpg"), "half")}{img(I("film_59.5.jpg"), "half")}</div></section>''')
    # ------------------------------------------------------------------ 3 install
    S.append('''<section><h2>३. इंस्टॉल <span>Install</span></h2>
<table><thead><tr><th>चरण / Step</th><th>Windows</th><th>macOS / Linux</th></tr></thead><tbody>
<tr><td>Python 3.9+</td><td>python.org (Add to PATH ✔)</td><td>पहले से / brew install python</td></tr>
<tr><td>ffmpeg (libass सहित)</td><td><code>winget install Gyan.FFmpeg</code></td><td><code>brew install ffmpeg</code> · <code>sudo apt install ffmpeg</code></td></tr>
<tr><td>Skill फ़ोल्डर</td><td><code>C:\\Users\\&lt;you&gt;\\.claude\\skills\\mythic-25d\\</code></td><td><code>~/.claude/skills/mythic-25d/</code></td></tr>
<tr><td>Packages</td><td colspan="2"><code>pip install -r ~/.claude/skills/mythic-25d/requirements.txt</code></td></tr>
<tr><td>जाँच / Check</td><td colspan="2"><code>python ~/.claude/skills/mythic-25d/mythic.py doctor</code> → सब ✔</td></tr>
</tbody></table>
<p>प्रोजेक्ट-विशेष उपयोग के लिए फ़ोल्डर को <code>&lt;project&gt;/.claude/skills/mythic-25d/</code> में भी रख सकते हैं।
Claude Code उसे अपने-आप पहचान लेता है (<code>/mythic-25d</code>)।</p>
<h3>पहली फ़िल्म <span>First film</span></h3>
<pre>python mythic.py new meri_katha --title "हनुमान और भीम"        # नया प्रोजेक्ट
python mythic.py validate mythic_projects/meri_katha             # जाँच
python mythic.py voice mythic_projects/meri_katha                # हिंदी आवाज़ + word timing
python mythic.py still mythic_projects/meri_katha --shot s2      # एक frame देखें
python mythic.py make mythic_projects/meri_katha --quality preview   # तेज़ preview
python mythic.py make mythic_projects/meri_katha --quality final     # 1080p final</pre>
<p>Output: <code>out/&lt;name&gt;_final.mp4</code> (subtitles सहित), <code>_clean.mp4</code>, <code>subs/subs.srt</code>, <code>audio/stems/</code>, <code>review/index.html</code>.</p>
</section>''')
    # ------------------------------------------------------------------ 4 workflow + prompt
    S.append(f'''<section><h2>४. Claude के साथ काम करने का तरीका <span>Workflow with Claude</span></h2>
<ol class="steps">
<li><b>doctor</b> — मशीन की जाँच</li><li><b>new</b> — प्रोजेक्ट बनाएँ, <code>script.txt</code> में कहानी</li>
<li><b>storyboard</b> — Claude हर वाक्य को shot में बदलता है (env, पात्र, अभिनय, कैमरा, transition)</li>
<li><b>validate</b> — ग़लत id/कैमरा/transition पकड़े जाते हैं</li><li><b>voice</b> — आवाज़ + शब्द-समय</li>
<li><b>still</b> — 2-3 key frames देखकर सुधार</li><li><b>make preview</b> → review पढ़कर सुधार</li><li><b>make final</b> — 1080p / Shorts</li></ol>
<h3>Starter prompt (हिंदी) — कॉपी करें</h3><pre class="prompt">{e(p1)}</pre></section>''')
    # ------------------------------------------------------------------ 5 storyboard
    S.append(f'''<section><h2>५. Storyboard का रूप <span>Storyboard format</span></h2>
<p>हर shot = एक दृश्य-विचार। मुख्य fields: <code>env</code>, <code>camera</code>, <code>transition</code>, <code>narration</code>,
<code>lines</code> (संवाद), <code>cast</code> (पात्र + <code>actions</code>), <code>props</code>, <code>fx</code>, <code>sfx</code>,
<code>shloka</code>, <code>music</code>, <code>life</code>.</p>
<pre>{e(demo_snip)}</pre>
<p class="en">Full field reference: <code>references/storyboard-schema.md</code>. Speaker <code>who</code> must equal a cast <code>id</code> —
then the puppet animates (talks) automatically while its line plays.</p></section>''')
    # ------------------------------------------------------------------ 6 camera
    cam_rows = [[f"<code>{k}</code>", CAM_HI.get(k, "")] for k in CAM_PRESETS]
    S.append(f'''<section><h2>६. कैमरा भाषा — reference जैसी <span>Camera language</span></h2>
<p>Reference वीडियो में 13 मिनट में केवल ~17 hard cuts थे — लंबे लगातार shots, धीमे truck/crane/push मूव्स, आगे से गुज़रते
पत्ते/खंभे (foreground wipe), चलते पात्र के साथ कैमरा, और रोशनी मद्धम होकर silhouette। यही सब engine में है।</p>
<div class="cols2">{table(["move", "अर्थ / meaning"], cam_rows, "small")}
<div>{table(["transition", "प्रभाव"], [["<code>crossfade</code>", "धीमा dissolve"], ["<code>wipe</code>", "आगे से पत्ते/खंभा/पेड़/बादल गुज़रता है"],
                                       ["<code>dip</code>", "काले से होकर (समय बदलना)"], ["<code>flash</code>", "सफ़ेद चमक (दिव्य/युद्ध)"],
                                       ["<code>cut</code>", "सीधा cut"]], "small")}
<pre>camera: {{move: establish, on: arjuna, frame: medium}}
camera: {{move: follow, on: bhima, frame: full}}
transition: wipe
fx: ["dim@4"]     # पात्र silhouette</pre></div></div>
{img(I("camera_moves.jpg"), "full", "crane_down · push_to · reveal (शुरू → अंत)")}
{img(I("wipe_and_silhouette.jpg"), "full", "foreground wipe (पेड़ गुज़रता है) · establish · dim → silhouettes")}</section>''')
    # ------------------------------------------------------------------ 7 living background
    life_rows = [[f"<code>{loc}</code>", ", ".join(f"{w} <small>({m})</small>" for w, m, kw, t in items)] for loc, items in LIFE.items() if items]
    S.append(f'''<section><h2>७. ज़िंदा background <span>Living 2.5D background</span></h2>
<p>हवा के झोंकों में पेड़-केले के पत्ते-घास-फूल-झंडे हिलते हैं (झोंका बाएँ से दाएँ चलता है), कमल डोलते हैं, बादल और हवा वाले
घुमावदार बादल चलते हैं, पक्षी उड़ते हैं — और हर स्थान के अपने जीव अपने-आप: जंगल में हिरन दौड़ते हैं, आश्रम में गाय चरती है,
सरोवर में हंस तैरते हैं और मछलियाँ उछलती हैं, कुरुक्षेत्र में सैनिक मार्च करते हैं और गिद्ध मँडराते हैं।</p>
{img(I("living_background.jpg"), "full")}
{table(["स्थान / locale", "अपने-आप आने वाले जीव / automatic creatures"], life_rows, "small")}
<pre>life: [{{who: golden_deer, mode: run_across, depth: 0.6}}]   # अपने जीव जोड़ें
life: false                                                 # शांत shot</pre></section>''')
    # ------------------------------------------------------------------ 8 characters
    cat_rows = [[f"<code>{c}</code>", str(len(v)), ", ".join(e(x.get("hi", "")) for x in v[:9]) + (" …" if len(v) > 9 else "")]
                for c, v in cats.items()]
    S.append(f'''<section><h2>८. पात्र <span>Characters ({len(chars)})</span></h2>
{table(["श्रेणी / category", "संख्या", "उदाहरण / examples"], cat_rows, "small")}
{img(I("gallery_gods_heroes.jpg"), "full", "देवता, अवतार, शिव-परिवार — catalog से सीधे render")}
{img(I("gallery_devi.jpg"), "full", "देवी रूप")}
{img(I("gallery_rakshasa.jpg"), "full", "राक्षस")}
<p>नया पात्र: storyboard में <code>characters: {{mera_rishi: {{base: vasishtha, beard_color: "#e6e0d0"}}}}</code> या पूरा custom spec
(सिर, मुकुट, रंग, वस्त्र, अस्त्र, भुजाएँ, सिर, पूँछ, पंख, प्रभामंडल…)। Pose sheet: <code>mythic.py char hanuman</code>.</p>
{img(I("pose_sheet_hanuman.jpg"), "full", "हनुमान — stand · talk · bless · namaste · raise · seated")}</section>''')
    S.append(f'''<section><h2>९. पशु-पक्षी <span>Animals & birds</span></h2>
{img(I("gallery_animals.jpg"), "full")}{img(I("gallery_birds.jpg"), "full")}</section>''')
    # ------------------------------------------------------------------ 10 envs
    env_rows = [[f"<code>{loc}</code>", e(desc), ", ".join(times)] for loc, (fn, times, desc) in LOCALES.items()]
    S.append(f'''<section><h2>१०. दृश्य <span>Environments ({len(list_envs())})</span></h2>
<p>id = <code>&lt;स्थान&gt;_&lt;समय&gt;</code>, जैसे <code>kurukshetra_dusk</code>, <code>ashram_dawn</code>, <code>lanka_fire</code>.
हर दृश्य में 6 parallax परतें: आसमान · दूर (धुँधला) · मध्य · सेट · ज़मीन · आगे (गहरा, soft-focus)।</p>
{table(["स्थान", "विवरण", "समय / times"], env_rows, "small")}
{img(I("envs_a.jpg"), "full")}{img(I("envs_b.jpg"), "full")}</section>''')
    # ------------------------------------------------------------------ 11 actions
    S.append(f'''<section><h2>११. अभिनय <span>Puppet actions</span></h2>
{table(["action", "params / अर्थ"], [[f"<code>{k}</code>", e(v)] for k, v in ACTION_HELP.items()], "small cols")}
<pre>actions:
  - {{do: walk, to: 0.7, at: 0.2, dur: 2.5}}
  - {{do: point, at: 3.0, dur: 2}}
  - {{do: bless, at: 6, dur: 2, keep: true}}</pre></section>''')
    # ------------------------------------------------------------------ 12 voice/subs
    S.append('''<section><h2>१२. हिंदी आवाज़ और subtitles <span>Voice & Devanagari subtitles</span></h2>
<ul><li><b>edge</b> (default): Microsoft neural आवाज़ें — <code>hi-IN-MadhurNeural</code> (पुरुष कथावाचक), <code>hi-IN-SwaraNeural</code> (स्त्री)।
TTS से ही हर शब्द का समय → subtitles frame-सटीक। इंटरनेट चाहिए।</li>
<li><b>files</b>: अपनी रिकॉर्डिंग (<code>narration_audio</code>, <code>lines[].audio</code>) — faster-whisper या built-in aligner से शब्द-समय।</li>
<li><b>none</b>: बिना आवाज़ preview (अंदाज़े से समय)।</li></ul>
<table><thead><tr><th>style</th><th>रूप</th><th>कहाँ</th></tr></thead><tbody>
<tr><td><code>karaoke</code></td><td>बोला जा रहा शब्द सुनहरा, नाम हरे-नीले</td><td>16:9 default</td></tr>
<tr><td><code>keyword</code></td><td>reference जैसा: पूरी पंक्ति, नाम रंगीन</td><td>शांत कथा</td></tr>
<tr><td><code>pop</code></td><td>1-2 बड़े शब्द, उछाल के साथ</td><td>Shorts default</td></tr></tbody></table>
<p>फ़ॉन्ट (साथ में, OFL): Tiro Devanagari Hindi, Noto Serif Devanagari, Yatra One, Rozha One, Cinzel।
<b>ज़रूरी:</b> ASS styles में letter-spacing कभी न लगाएँ — मात्राएँ ◌ बन जाती हैं।
<code>shloka:</code> — ऊपर श्लोक, शब्दों के नीचे छोटे अर्थ, और हिंदी भावार्थ।</p></section>''')
    # ------------------------------------------------------------------ 13 audio + grade
    mood_rows = [[f"<code>{k}</code>", v[0], str(v[1]), v[2], v[3]] for k, v in MOODS.items()]
    S.append(f'''<section><h2>१३. संगीत, ध्वनि, mixing <span>Music, SFX, mix</span></h2>
{table(["mood", "राग", "bpm", "lead", "ताल/percussion"], mood_rows, "small")}
<p>SFX ({len(GEN)}): {", ".join(f"<code>{k}</code>" for k in sorted(GEN))}.</p>
<p>Auto SFX: actions (strike → mace_hit, shoot → arrow_whoosh, appear → divine_shimmer…), fx (lightning → thunder), हर दृश्य का
ambience। असली रिकॉर्डिंग <code>&lt;project&gt;/sfx/&lt;name&gt;.wav</code> में रखें — अपने-आप बदल जाती है। लाइसेंस वाला संगीत:
<code>music: {{file: ...}}</code>.</p>
<p>Mix: VO EQ + compression, संगीत आवाज़ के नीचे ducking (−10 dB), loudnorm <b>−14 LUFS / −1.5 dBTP</b> (YouTube), stems।</p>
<h3>Color grading</h3>{table(["preset", "रूप / look"], [[f"<code>{k}</code>", e(v["desc"])] for k, v in GRADES.items()], "small")}
<p><code>mythic.py lut all</code> → Resolve/Premiere के लिए .cube LUTs।</p></section>''')
    # ------------------------------------------------------------------ 14 review + troubleshooting
    trows = [["ffmpeg नहीं मिला", "Windows: <code>winget install Gyan.FFmpeg</code> · mac: <code>brew install ffmpeg</code>"],
             ["हिंदी में ◌ (टूटी मात्राएँ)", "letter-spacing 0 रखें; full ffmpeg build (libass + HarfBuzz)"],
             ["हिंदी में □ boxes", "fonts फ़ोल्डर engine में ही रहे (fontsdir)"],
             ["edge-tts failed / Cannot connect", "इंटरनेट/firewall; फिर <code>voice --force</code>; या अपनी रिकॉर्डिंग"],
             ["पात्र बोलते समय हिलता नहीं", "line का <code>who</code> = cast <code>id</code>"],
             ["पात्र सेट में घुल जाते हैं", "<code>light: {bg_dim: 0.72, bg_desat: 0.7}</code>"],
             ["render धीमा", "<code>--quality preview</code>, <code>--shots s3,s4</code>, <code>--workers N</code>"],
             ["ऊपर से मुकुट कटता है", "<code>scale</code> घटाएँ, <code>pull_out</code>, camera <code>y</code>"],
             ["आवाज़ धीमी/तेज़", "<code>mix --lufs -14</code>; संगीत <code>volume_db: -20</code>"]]
    S.append(f'''<section><h2>१४. Review और समस्या-समाधान <span>Review & troubleshooting</span></h2>
<p><code>mythic.py review &lt;proj&gt;</code> → <code>review/index.html</code>: video player, हर shot के 3 thumbnails, subtitle गति (cps),
loudness, true peak, काले/जमे frames, A/V sync। Checklist: आवाज़ बंद करके भी कहानी समझ आए; हर बोलता पात्र हिले; मुकुट न कटे;
नाम/श्लोक सही; कैमरा विविध; संगीत आवाज़ के नीचे; पहले 3 सेकंड में hook।</p>
{table(["समस्या / problem", "हल / fix"], trows)}</section>''')
    # ------------------------------------------------------------------ appendix
    def idx(lst):
        return "".join(f'<div><code>{e(x["id"])}</code> {e(x.get("hi", ""))} <small>{e(x.get("en", ""))}</small></div>' for x in lst)
    S.append(f'''<section><h2>परिशिष्ट क — सभी पात्र <span>Appendix A — all character ids</span></h2><div class="index">{idx(chars)}</div></section>''')
    S.append(f'''<section><h2>परिशिष्ट ख — पशु-पक्षी <span>Appendix B — animals & birds</span></h2><div class="index">{idx(beasts + birds)}</div></section>''')

    fd = FONT_DIR.resolve()
    css = f"""
@font-face{{font-family:'Tiro';src:url('file://{fd}/TiroDevanagariHindi-Regular.ttf')}}
@font-face{{font-family:'Tiro';font-style:italic;src:url('file://{fd}/TiroDevanagariHindi-Italic.ttf')}}
@font-face{{font-family:'Rozha';src:url('file://{fd}/RozhaOne-Regular.ttf')}}
@font-face{{font-family:'Cinzel';src:url('file://{fd}/Cinzel.ttf')}}
@font-face{{font-family:'NotoDeva';src:url('file://{fd}/NotoSerifDevanagari.ttf')}}
:root{{--ink:#2a1a10;--mut:#7a5a3e;--acc:#b8501e;--gold:#c8902c;--paper:#f7eedc;--card:#efe2c6}}
@page{{size:A4;margin:14mm 13mm 16mm 13mm}}
html{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
body{{font-family:'Tiro','NotoDeva',serif;color:var(--ink);font-size:11pt;line-height:1.55;background:var(--paper);margin:0}}
section{{page-break-before:always}} section.cover{{page-break-before:avoid}}
h1{{font-family:'Rozha';font-size:52pt;margin:6mm 0 0;color:var(--acc);font-weight:400}}
h2{{font-family:'Rozha';font-weight:400;font-size:21pt;color:var(--acc);border-bottom:2px solid var(--gold);margin:0 0 4mm;padding-bottom:1mm}}
h2 span,h3 span{{font-family:'Cinzel';font-size:10pt;color:var(--mut);letter-spacing:.06em;margin-left:3mm}}
h3{{font-family:'Rozha';font-weight:400;font-size:14pt;color:var(--ink);margin:5mm 0 2mm}}
p.en,.en{{color:var(--mut);font-size:9.6pt}} small{{color:var(--mut)}}
code{{font-family:'JetBrains Mono','NotoDeva',monospace;font-size:8.6pt;background:#ead9b8;padding:0 2px;border-radius:2px}}
pre{{font-family:'JetBrains Mono','NotoDeva',monospace;font-size:8.2pt;line-height:1.4;background:#2a1c12;color:#f3e6c8;padding:3mm 4mm;
border-radius:2mm;white-space:pre-wrap;page-break-inside:avoid}}
pre.prompt{{background:#3a2416}}
table{{border-collapse:collapse;width:100%;margin:2mm 0 4mm;font-size:9.6pt;page-break-inside:auto}}
th{{background:var(--acc);color:#fff7e6;text-align:left;padding:1.5mm 2mm;font-weight:400}}
td{{border-bottom:1px solid #dcc6a0;padding:1.2mm 2mm;vertical-align:top}} tr{{page-break-inside:avoid}}
table.small{{font-size:8.6pt}} table.small td{{padding:.8mm 1.6mm}}
figure{{margin:2mm 0 4mm;page-break-inside:avoid;text-align:center}}
figure img{{max-width:100%;max-height:118mm;border-radius:1.5mm;display:inline-block;box-shadow:0 1mm 3mm #0003}}
figure.hero img{{max-height:105mm}}
figcaption{{font-size:8.6pt;color:var(--mut);text-align:center;margin-top:1mm}}
.row{{display:flex;gap:3mm}} .row figure.half{{flex:1}}
.cols2{{display:grid;grid-template-columns:1fr 1fr;gap:4mm}}
.cover{{text-align:center;padding-top:6mm}} .cover .kicker{{font-family:'Cinzel';color:var(--mut);letter-spacing:.2em;font-size:10pt}}
.cover .sub{{font-size:15pt;margin-top:2mm}} .cover .sub2{{font-family:'Cinzel';font-size:10pt;color:var(--mut);margin-bottom:5mm}}
.cover figure.hero img{{box-shadow:0 2mm 6mm #0005}}
.nums{{display:grid;grid-template-columns:repeat(3,1fr);gap:3mm;margin-top:5mm}}
.nums div{{background:var(--card);border-radius:2mm;padding:3mm;font-size:11pt}} .nums b{{display:block;font-family:'Rozha';font-size:24pt;color:var(--acc);font-weight:400}}
.cover .foot{{margin-top:6mm;color:var(--mut);font-size:12pt}} .cover .foot .lat{{font-family:'Cinzel';letter-spacing:.15em;font-size:10pt}}
ol.big li,ol.steps li{{margin:1.5mm 0}} ol.steps{{columns:2;column-gap:8mm}}
.index{{columns:3;column-gap:5mm;font-size:7.8pt;line-height:1.35}} .index div{{break-inside:avoid}} .index code{{font-size:7pt}}
"""
    out_html.write_text(f'<!doctype html><html lang="hi"><head><meta charset="utf-8"><title>Mythic 2.5D Manual</title>'
                        f'<style>{css}</style></head><body>{"".join(S)}</body></html>', encoding="utf-8")
    return out_html


NODE = """
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto(process.argv[2], { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  await p.pdf({ path: process.argv[3], format: 'A4', printBackground: true,
    margin: { top: '14mm', bottom: '16mm', left: '13mm', right: '13mm' }, displayHeaderFooter: true,
    headerTemplate: '<div></div>',
    footerTemplate: '<div style="font-size:8px;width:100%;text-align:center;color:#8a6a4a;font-family:serif">Mythic 2.5D · <span class=pageNumber></span> / <span class=totalPages></span></div>' });
  await b.close();
})();
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", default=str(SKILL / "docs"))
    ap.add_argument("--out", default=str(SKILL / "docs" / "Mythic25D_Manual.pdf"))
    a = ap.parse_args()
    tmp = Path(tempfile.mkdtemp(prefix="mythic_manual_"))
    html_path = build_html(Path(a.images), tmp / "manual.html")
    js = tmp / "pdf.js"
    js.write_text(NODE)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["node", str(js), f"file://{html_path}", str(out)], check=True)
    shutil.copy(html_path, out.with_suffix(".html")) if "--keep-html" in sys.argv else None
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
