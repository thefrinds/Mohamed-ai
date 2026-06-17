ماريك فىالكود الذي import streamlit as st
import requests
import os
import tempfile
import time
import matplotlib.pyplot as plt
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip
from io import BytesIO
import base64

# ==========================================
# 🔐 1. إعدادات الأمان والبيئة
# ==========================================
st.set_page_config(page_title="إمبراطورية ستايل ستور الفائقة", page_icon="👑", layout="wide")

# استخدم st.secrets لوضع التوكن، أو اتركه فارغاً واطلب من المستخدم إدخاله
if "HF_TOKEN" in st.secrets:
    HF_TOKEN = st.secrets["HF_TOKEN"]
else:
    HF_TOKEN = st.text_input("🔑 أدخل توكن Hugging Face الخاص بك (للوصول المجاني للـ API):", type="password")
    if not HF_TOKEN:
        st.warning("الرجاء إدخال توكن Hugging Face للمتابعة.")
        st.stop()

headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# قائمة بالسيرفرات الاحتياطية (نموذج واحد لكل مهمة، يمكن إضافة المزيد)
TEXT_SERVERS = [
    "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct",
    "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"  # احتياطي
]
IMAGE_SERVERS = [
    "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
    "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"  # احتياطي
]
WHISPER_SERVER = "https://api-inference.huggingface.co/models/openai/whisper-large-v3"  # لتحويل الصوت

# ==========================================
# 📦 2. دوال الاتصال بالسيرفرات مع إعادة المحاولة
# ==========================================
def request_with_retry(servers, payload, headers, retries=2, timeout=20):
    """محاولة استدعاء السيرفرات مع إعادة المحاولة والتبديل بينها."""
    for attempt in range(retries):
        for server in servers:
            try:
                res = requests.post(server, json=payload, headers=headers, timeout=timeout)
                if res.status_code == 200:
                    return res
                elif res.status_code == 503 and "waiting" in res.text:
                    # السيرفر مشغول، ننتظر قليلاً ثم نحاول مجدداً
                    time.sleep(3)
                    continue
            except Exception:
                continue
    return None

def request_text_cloud(prompt_content, system_instruction):
    payload = {
        "inputs": f"<|system|>\n{system_instruction}\n<|user|>\n{prompt_content}\n<|assistant|>",
        "parameters": {"max_new_tokens": 750, "return_full_text": False}
    }
    res = request_with_retry(TEXT_SERVERS, payload, headers)
    if res and res.status_code == 200:
        try:
            return res.json()[0]['generated_text']
        except:
            pass
    st.error("فشل الاتصال بالسيرفر النصي، حاول مجدداً.")
    return "حدث خطأ في معالجة النص."

def request_image_cloud(prompt_text):
    payload = {"inputs": prompt_text}
    res = request_with_retry(IMAGE_SERVERS, payload, headers, timeout=30)
    if res and res.status_code == 200:
        return res.content
    st.error("فشل توليد الصورة، حاول مجدداً.")
    return None

def transcribe_audio(audio_bytes):
    """تحويل الصوت إلى نص باستخدام Whisper."""
    if audio_bytes is None:
        return ""
    files = {"audio": audio_bytes}
    try:
        res = requests.post(WHISPER_SERVER, headers=headers, files=files, timeout=30)
        if res.status_code == 200:
            return res.json().get("text", "")
        else:
            st.warning("تعذر تحويل الصوت، استخدم النص المكتوب.")
    except:
        st.warning("خطأ في تحويل الصوت.")
    return ""

# ==========================================
# 📐 3. محرك الباترون الهندسي (تحسين عدم استخدام matplotlib في كل مرة)
# ==========================================
def draw_perfect_pattern(piece_name, size, width, length, shrinkage):
    plt.rcParams['font.sans-serif'] = 'Arial'
    plt.rcParams['axes.unicode_minus'] = False
    fig, ax = plt.subplots(figsize=(4.5, 5.5))
    w = (float(width) * shrinkage) / 20.0  
    l = (float(length) * shrinkage) / 20.0
    
    if any(word in piece_name for word in ["فستان", "بدلة", "عباءة"]):
        x = [0, w, w, w*0.8, w*0.8, 0, 0]
        y = [l, l, l*0.8, l*0.3, 0, 0, l]
    else: 
        x = [0, w, w, w*0.7, 0, 0]
        y = [l, l, l*0.2, 0, 0, l]
        
    ax.plot(x, y, linewidth=2, color='#0D47A1', linestyle='--')
    ax.fill(x, y, alpha=0.1, color='#0D47A1')
    ax.text(w/2, l+0.1, f"طول القص: {float(length)*shrinkage:.1f} سم", ha='center', fontsize=9)
    ax.text(w+0.1, l/2, f"عرض القص: {float(width)*shrinkage:.1f} سم", va='center', fontsize=9)
    ax.axis('off')
    
    # حفظ في ملف مؤقت
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        plt.savefig(tmp.name, bbox_inches='tight', dpi=100)
        plt.close()
        return tmp.name

# ==========================================
# 🎨 4. واجهة المستخدم (UI) مع تحسين التخطيط
# ==========================================
st.markdown("<h1 style='text-align: right; color: #0D47A1;'>👑 STYLE STORE INFINITE - مركز الابتكار والمحاكاة المطلقة</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: right;'>أنتِ الآن تتحكمين بأقوى نظام ذكاء اصطناعي تفاعلي للأزياء في العالم: دمج تريندات عواصم العالم، تعديل الأجزاء الهيكلية، وإلباس العارضين اللحظي.</p>", unsafe_allow_html=True)

# تهيئة session state لتخزين النتائج
if 'analysis' not in st.session_state:
    st.session_state.analysis = ""
if 'generated_images' not in st.session_state:
    st.session_state.generated_images = {}
if 'pattern_file' not in st.session_state:
    st.session_state.pattern_file = ""
if 'video_path' not in st.session_state:
    st.session_state.video_path = ""
if 'audio_transcription' not in st.session_state:
    st.session_state.audio_transcription = ""
if 'last_submit' not in st.session_state:
    st.session_state.last_submit = None  # لتجنب إعادة الحساب

col_output, col_input = st.columns([1.55, 1.45])

with col_input:
    st.markdown("<h3 style='text-align: right;'>🌐 1. رادار استيراد تريندات العواصم العالمية</h3>", unsafe_allow_html=True)
    target_country = st.selectbox(
        "📍 اختر الدولة المستهدفة لاستلهام فلسفتها التصميمية ومتاجرها:",
        ["فرنسا - باريس (Luxury Couture الأنيقة)", "الإمارات - دبي (Luxury Eastern والعبايات الفاخرة)", "اليابان - طوكيو (Streetwear والبساطة العصرية)", "كوريا الجنوبية - سول (Oversized والقصات الحديثة)"]
    )
    
    fusion_mode = st.checkbox("🔄 تفعيل محرك الدمج العابر للقارات (Cross-Culture Fusion)")
    second_country = ""
    if fusion_mode:
        second_country = st.selectbox("🤝 اختر الثقافة الثانية لدمجها مع الثقافة الأولى تزامناً:", ["الإمارات - دبي (لمسة شرقية فاخرة)", "فرنسا - باريس (أناقة كلاسيكية فرنسية)", "اليابان - طوكيو (عصرية وبساطة يابانية)"])

    st.divider()
    st.markdown("<h3 style='text-align: right;'>✂️ 2. لوحة التحكم التفاعلية بالأجزاء والإكسسوارات</h3>", unsafe_allow_html=True)
    user_idea = st.text_area("✍️ فكرة التصميم المراد تشكيله وتعديله:", placeholder="مثال: فستان سهرة راقٍ انسيابي...")
    audio_file = st.audio_input("🎙️ أو اشرحي تعديلاتك وفكرتك فوراً بالصوت:")
    
    # معالجة الصوت فوراً إذا تم رفعه (بدون زر)
    if audio_file is not None:
        with st.spinner("جاري تحويل الصوت إلى نص..."):
            transcription = transcribe_audio(audio_file.getvalue())
            if transcription:
                st.session_state.audio_transcription = transcription
                st.info(f"📝 تم التعرف على النص: {transcription}")
                # نقترح إضافته للمدخل النصي
                if not user_idea:
                    user_idea = transcription
            else:
                st.warning("لم يتم التعرف على الصوت، اكتب الفكرة يدوياً.")

    col_c1, col_c2 = st.columns(2)
    with col_c2:
        sleeve_style = st.selectbox("شكل وستايل الكم التميزي:", ["أكمام طويلة ضيقة (Classic Long)", "أكمام منفوخة ملكية (Puff Royal)", "أكمام واسعة انسيابية (Flared Angel)", "بدون أكمام (Sleeveless)"])
        collar_style = st.selectbox("نوع وتفصيل اللياقة (الياقة):", ["ياقة دائرية كلاسيكية (Crew Neck)", "ياقة ملكية مرتفعة (High Victorian)", "ياقة سبعة مفتوحة (V-Neck)", "ياقة البدلة الرسمية (Lapel Collar)"])
    with col_c1:
        bottom_style = st.selectbox("قصة نهاية وذيل القطعة:", ["قصة مستقيمة صك (Straight Cut)", "قصة كلوش واسعة (Voluminous A-Line)", "قصة ذيل السمكة الفاخرة (Mermaid Tail)", "قصة غير متماثلة (Asymmetrical)"])
        accessory_choice = st.selectbox("إضافة مستلزمات وإكسسوارات تجريبية للمعاينة:", ["بدون إكسسوار إضافي", "حزام جلدي عريض بمشبك ذهبي (Golden Belt)", "أزرار لؤلؤية فاخرة على الصدر (Pearl Buttons)", "بروش كريستالي راقٍ على الياقة (Crystal Brooch)"])

    st.divider()
    st.markdown("<h3 style='text-align: right;'>🧶 3. مصفوفة الأقمشة المحلية والأبعاد الفنية</h3>", unsafe_allow_html=True)
    selected_fabrics = st.multiselect(
        "اختر الأقمشة لمعاينتها ومقارنتها فوراً على أجساد العارضين:",
        ["قماش كريب انسيابي ناعم (Crepe)", "قماش قطيفة مخملي ثقيل (Velvet)", "قماش ستان حرير ملكي (Silk Satin)", "قماش كتان طبيعي ممتاز (Linen)"],
        default=["قماش كريب انسيابي ناعم (Crepe)", "قماش قطيفة مخملي ثقيل (Velvet)"]
    )
    
    fabric_type = st.selectbox("نوع القماش لضبط حاسبة الأمان التلقائية بالورشة:", ["أقمشة ثابتة ومستقرة (0%)", "كتان نقي (ينكمش 5%)", "أقطان ناعمة (ينكمش 3%)"])
    shrinkage_factor = 1.05 if "كتان" in fabric_type else (1.03 if "أقطان" in fabric_type else 1.0)
    
    style_type = st.radio("النمط الهيكلي الكلي للقطعة:", ["قياسي (Regular)", "مريح وفضفاض (Oversized)", "كلاسيك ومجسم (Slim Fit)"])
    selected_size = st.selectbox("المقاس المستهدف لخط الإنتاج:", ["S", "M", "L", "XL", "XXL"])
    custom_width = st.number_input("عرض الصدر التقديري (سم):", value=54)
    custom_length = st.number_input("الطول الإجمالي التقديري (سم):", value=95)

    st.divider()
    st.markdown("<h4 style='text-align: right;'>💰 التكلفة والتسعير المحلي والربحية (ج.م)</h4>", unsafe_allow_html=True)
    fabric_price = st.number_input("سعر متر القماش الحالي بمصر:", value=150)
    fabric_needed = st.number_input("كمية الأمتار المطلوبة للقص:", value=2.5, step=0.5)
    tailor_cost = st.number_input("تكلفة الورشة والقص والخياطة:", value=130)
    notions_cost = st.number_input("تكلفة الإكسسوارات والمستلزمات المضافة:", value=40)
    profit_margin = st.slider("نسبة الربح المستهدفة لبراندك (%):", 10, 200, 60)

    submit_button = st.button("🚀 إطلاق العقل الابتكاري وتشغيل الاستوديو الافتراضي والمصفوفة", use_container_width=True)

# ==========================================
# 🚀 5. المحرك السحابي الذكي مع استخدام Session State
# ==========================================
# نقوم بتوليد مفتاح فريد للمدخلات الحالية لتحديد ما إذا تغيرت
def get_inputs_hash():
    return hash((target_country, second_country, user_idea, fusion_mode, sleeve_style, collar_style, bottom_style, accessory_choice, tuple(selected_fabrics), fabric_type, style_type, selected_size, custom_width, custom_length))

if submit_button:
    if not selected_fabrics:
        st.warning("من فضلك حدد خامة محلية واحدة على الأقل لرؤية التعديلات الهيكلية الفورية!")
    else:
        # التحقق مما إذا كانت المدخلات تغيرت منذ آخر ضغطة
        current_hash = get_inputs_hash()
        if st.session_state.last_submit != current_hash:
            # مسح النتائج السابقة لتجنب الالتباس
            st.session_state.generated_images = {}
            st.session_state.pattern_file = ""
            st.session_state.video_path = ""
            st.session_state.analysis = ""
            st.session_state.last_submit = current_hash

            with st.spinner("🌐 يتصل الاستوديو الافتراضي الفائق بالسيرفرات السحابية.."):
                # صياغة البرومبت
                design_context = (
                    f"High fashion lookbook editorial photoshoot. A professional model wearing a luxury piece inspired by {target_country}. "
                    f"Core design idea: {user_idea if user_idea else 'A unique elegant outfit'}. "
                    f"Structural custom modifications: Crafted with {sleeve_style}, combined with a stunning {collar_style}, and styled with a elegant {bottom_style}. "
                    f"Featuring refined elements of {accessory_choice}. 3d depth, clear texture details, realistic fabric drape, studio lighting background."
                )
                if fusion_mode:
                    design_context += f" Seamlessly fused with stylistic cultural elements from {second_country}."

                # 1. التقرير الفني
                with st.status("🤖 العقل النصي يحلل الأبعاد ويبتكر البوستات...", expanded=True) as status:
                    system_instruction = (
                        "You are an AI master fashion designer. Respond in Arabic with these exact headings:\n"
                        "1) اسم التصميم الهيكلي المبتكر الفاخر\n"
                        "2) تقرير التعديلات الفنية والأبعاد (الأكمام، اللياقة، النهاية، والإكسسوار)\n"
                        "3) بوست تسويقي مبهر وجذاب جداً لجمهور وسائل التواصل الاجتماعي (Instagram/TikTok)\n"
                        "4) ردود خدمة العملاء التلقائية والبيع السريع الفوري\n"
                        "And at the very end, write 'PROMPT:' followed by the refined English prompt."
                    )
                    analysis = request_text_cloud(design_context, system_instruction)
                    st.session_state.analysis = analysis
                    base_prompt = analysis.split("PROMPT:")[1].strip() if "PROMPT:" in analysis else design_context

                    # 2. توليد صور العارضين
                    status.update(label="🧍 إلباس العارضين وتطبيق التعديلات...")
                    generated_images = {}
                    for fabric in selected_fabrics:
                        fabric_eng = fabric.split("(")[1].replace(")", "") if "(" in fabric else "luxury textile"
                        specific_prompt = f"{base_prompt}, tailored perfectly in premium textured {fabric_eng}, presenting a highly sophisticated outfit silhouette, realistic drape"
                        img_data = request_image_cloud(specific_prompt)
                        if img_data:
                            # حفظ الصورة في ملف مؤقت
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                                tmp.write(img_data)
                                generated_images[fabric] = tmp.name
                    st.session_state.generated_images = generated_images

                    # 3. الباترون
                    status.update(label="📐 تحديث أبعاد الباترون...")
                    pattern_file = draw_perfect_pattern(user_idea[:12] or "قطعة", selected_size, custom_width, custom_length, shrinkage_factor)
                    st.session_state.pattern_file = pattern_file

                    # 4. مقطع فيديو (اختياري، مع إمكانية إلغاء لتوفير الوقت)
                    status.update(label="🎙️ توليد المقطع الصوتي والترويجي...")
                    try:
                        tts = gTTS(text="أحدث ابتكارات الموضة العالمية، صممت وهندست خصيصاً لتناسب أرقى الأذواق، متوفرة الآن وحصرياً من ستايل ستور", lang='ar')
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_audio:
                            tts.save(tmp_audio.name)
                            audio_path = tmp_audio.name
                        # فيديو من أول صورة متاحة
                        if generated_images:
                            first_img = list(generated_images.values())[0]
                            audio_clip = AudioFileClip(audio_path)
                            clip = ImageClip(first_img).set_duration(audio_clip.duration).set_audio(audio_clip)
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
                                clip.write_videofile(tmp_video.name, fps=15, codec='libx264', audio_codec='aac', logger=None, preset='ultrafast', verbose=False)
                                st.session_state.video_path = tmp_video.name
                    except Exception as e:
                        st.warning(f"تعذر إنشاء الفيديو: {e}")
                        st.session_state.video_path = ""

                    status.update(label="✨ اكتملت المحاكاة!", state="complete")

        else:
            st.info("✅ تم تحميل النتائج السابقة (لم تتغير المدخلات).")

# ==========================================
# 🎯 6. لوحة التحكم وعرض النتائج من Session State
# ==========================================
with col_output:
    st.markdown("<h2 style='text-align: right;'>🎯 غطاء التحكم والمحاكاة الافتراضية المطلقة</h2>", unsafe_allow_html=True)
    
    if st.session_state.analysis or st.session_state.generated_images:
        tab1, tab2, tab3 = st.tabs(["🧍 صالة العرض", "📐 الباترون", "💰 التحليل المالي"])
        
        with tab1:
            st.markdown("<h3 style='text-align: right;'>📸 العارضون الافتراضيون بالتعديلات الهيكلية</h3>", unsafe_allow_html=True)
            st.write(f"المعاينة والمقارنة: **{sleeve_style}** مع **{collar_style}** ونهاية **{bottom_style}** وإكسسوار **{accessory_choice}**")
            
            if st.session_state.generated_images:
                cols = st.columns(len(st.session_state.generated_images))
                for idx, (fabric_name, img_path) in enumerate(st.session_state.generated_images.items()):
                    with cols[idx]:
                        st.markdown(f"<p style='text-align: center; font-weight: bold; color: #0D47A1;'>🧵 {fabric_name}</p>", unsafe_allow_html=True)
                        st.image(img_path, use_container_width=True)
                        st.caption("تجسيد متكامل للقطعة")
            else:
                st.info("لا توجد صور حالياً، اضغط زر التشغيل.")
            
            st.divider()
            # مصفوفة تقييم القماش (نفسها مع إصلاح التنسيق)
            st.markdown("<h3 style='text-align: right;'>📊 مصفوفة تقييم الملاءمة</h3>", unsafe_allow_html=True)
            col_v1, col_v2 = st.columns([1.2, 1.8])
            with col_v2:
                st.markdown("<p style='text-align: right; font-size:13px; font-weight:bold;'>📋 تقرير الملاءمة الفني:</p>", unsafe_allow_html=True)
                st.markdown(f"""
                <table style='width: 100%; text-align: right; border-collapse: collapse; font-size: 12px;'>
                    <tr style='background-color: #0D47A1; color: white;'>
                        <th>العنصر</th><th>التناسق</th><th>السقوط</th><th>التنفيذ</th>
                    </tr>
                    <tr><td><b>{sleeve_style.split(' ')[0]}</b></td><td>ممتاز</td><td>انسيابي</td><td>يحتاج خبرة</td></tr>
                    <tr style='background-color: #F5F5F5;'><td><b>{collar_style.split(' ')[0]}</b></td><td>ممتاز</td><td>ثابت</td><td>سهل</td></tr>
                </table>
                """, unsafe_allow_html=True)
            with col_v1:
                if st.session_state.generated_images:
                    selected_fabric = st.radio("اعتمد الخامة الفائزة:", list(st.session_state.generated_images.keys()))
                    if st.button("✅ اعتماد هذا اللوك"):
                        st.success(f"تم اعتماد خامة {selected_fabric} وتحديث أمر الشغل!")
            
            # عرض الفيديو إن وجد
            if st.session_state.video_path and os.path.exists(st.session_state.video_path):
                st.divider()
                st.markdown("<h3 style='text-align: right;'>🎬 فيديو الـ Reel الترويجي</h3>", unsafe_allow_html=True)
                st.video(st.session_state.video_path)
        
        with tab2:
            col_p1, col_p2 = st.columns([1, 1])
            with col_p2:
                st.markdown("<h3 style='text-align: right;'>📐 الباترون الهندسي</h3>", unsafe_allow_html=True)
                if st.session_state.pattern_file and os.path.exists(st.session_state.pattern_file):
                    st.image(st.session_state.pattern_file, use_container_width=True)
                    with open(st.session_state.pattern_file, "rb") as f:
                        st.download_button("تحميل الباترون", data=f, file_name="pattern.png")
                else:
                    st.info("لم يتم توليد الباترون بعد.")
            with col_p1:
                st.markdown("<h3 style='text-align: right;'>📋 كارت أمر الشغل</h3>", unsafe_allow_html=True)
                st.write(f"**المصدر:** {target_country}" + (f" | **دمج:** {second_country}" if fusion_mode else ""))
                st.write(f"**الأكمام:** {sleeve_style}")
                st.write(f"**الياقة:** {collar_style} | **النهاية:** {bottom_style}")
                st.write(f"**المقاس:** {selected_size} | **النمط:** {style_type}")
                st.write(f"**الأبعاد:** {custom_width*shrinkage_factor:.1f} عرض × {custom_length*shrinkage_factor:.1f} طول")
                st.write(f"**الإكسسوار:** {accessory_choice}")
        
        with tab3:
            st.markdown("<h3 style='text-align: right;'>💰 الهيكل المالي والأرباح</h3>", unsafe_allow_html=True)
            cost_production = (fabric_price * fabric_needed) + tailor_cost + notions_cost
            sell_price = cost_production * (1 + (profit_margin / 100))
            profit = sell_price - cost_production
            
            c1, c2, c3 = st.columns(3)
            c3.metric("التكلفة الكلية", f"{cost_production:.2f} ج.م")
            c2.metric("سعر البيع المقترح", f"{sell_price:.2f} ج.م")
            c1.metric("صافي الربح", f"{profit:.2f} ج.م")
            
            st.divider()
            st.markdown("<h3 style='text-align: right;'>📋 التقرير الفني والبوست التسويقي</h3>", unsafe_allow_html=True)
            if st.session_state.analysis:
                parts = st.session_state.analysis.split("3)")
                st.text_area("1-2) التقرير الفني والأبعاد:", value=parts[0], height=160)
                if len(parts) > 1:
                    marketing_parts = parts[1].split("4)")
                    st.text_area("3) البوست التسويقي:", value=marketing_parts[0], height=150)
                    if len(marketing_parts) > 1:
                        st.text_area("4) ردود خدمة العملاء:", value=marketing_parts[1].split("PROMPT:")[0], height=150)
            else:
                st.info("لم يتم توليد التقرير بعد.")
    else:
        st.info("👈 قم بإدخال البيانات واضغط زر التشغيل لرؤية النتائج هنا.")

# ==========================================
# 🧹 7. تنظيف الملفات المؤقتة (اختياري - سيتم حذفها عند إنهاء الجلسة)
# ==========================================
# يمكن إضافة دالة لحذف الملفات عند إعادة التشغيل، لكنها ليست ضرورية لأن Streamlit ينشئ بيئة جديدة لكل جلسة.
