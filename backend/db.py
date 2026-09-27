"""SQLite schema, bilingual seed content and synthetic demo history."""
import hashlib
import hmac
import json
import os
import random
import secrets
import sqlite3
from datetime import date, timedelta

import srs

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "data", "ranksyar.db"))
DEMO_PASSWORD = "demo1234"

SCHEMA = """
CREATE TABLE teams(id INTEGER PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE users(id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, pw TEXT, name TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'learner', team_id INTEGER REFERENCES teams(id));
CREATE TABLE tokens(token TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id));
CREATE TABLE tracks(id TEXT PRIMARY KEY, pos INTEGER, title TEXT, descr TEXT, color TEXT, icon TEXT);
CREATE TABLE lessons(id INTEGER PRIMARY KEY, track_id TEXT REFERENCES tracks(id), pos INTEGER,
  title TEXT, body TEXT, minutes INTEGER);
CREATE TABLE questions(id INTEGER PRIMARY KEY, lesson_id INTEGER REFERENCES lessons(id),
  prompt TEXT, choices TEXT, answer INTEGER, explain TEXT);
CREATE TABLE reviews(user_id INTEGER, question_id INTEGER, box INTEGER, due TEXT, PRIMARY KEY(user_id, question_id));
CREATE TABLE answers(id INTEGER PRIMARY KEY, user_id INTEGER, question_id INTEGER, correct INTEGER, xp INTEGER, day TEXT);
CREATE INDEX answers_day ON answers(day);
CREATE TABLE badges(user_id INTEGER, code TEXT, day TEXT, PRIMARY KEY(user_id, code));
CREATE TABLE demo_requests(id INTEGER PRIMARY KEY, name TEXT, company TEXT, contact TEXT, size TEXT, created TEXT);
"""


def J(fa, en):
    return json.dumps({"fa": fa, "en": en}, ensure_ascii=False)


def connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def hash_pw(pw, salt=None):
    salt = salt or secrets.token_hex(16)
    return salt + "$" + hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), 200_000).hex()


def check_pw(pw, stored):
    return bool(stored) and hmac.compare_digest(hash_pw(pw, stored.split("$")[0]), stored)


# (id, color, icon, title, description, lessons[(title, minutes, body, questions[(prompt, [correct, *wrong], explain)])])
TRACKS = [
    ("sales", "#FF4F8B", "trending-up", ("فروش مشاوره‌ای", "Consultative Selling"),
     ("از کشف نیاز تا بستن قرارداد", "From discovery to a signed deal"), [
        (("پرسیدن به‌جای گفتن", "Ask before you tell"), 3,
         ("فروشنده‌های موفق بیشتر از آنکه حرف بزنند، گوش می‌دهند.\nسؤال‌های باز (چه، چطور، چرا) نیاز واقعی مشتری را آشکار می‌کنند.\nقاعده سرانگشتی: ۳۰٪ صحبت، ۷۰٪ شنیدن.",
          "Top sellers listen more than they talk.\nOpen questions (what, how, why) reveal the customer's real need.\nRule of thumb: talk 30%, listen 70%."), [
            (("کدام گزینه یک سؤال باز است؟", "Which one is an open question?"),
             [("چه چیزی در راهکار فعلی‌تان آزارتان می‌دهد؟", "What frustrates you about your current solution?"),
              ("آیا این محصول را می‌خواهید؟", "Do you want this product?"),
              ("بودجه‌تان ۱۰۰ میلیون تومان است؟", "Is your budget 100 million toman?"),
              ("امروز قرارداد را امضا می‌کنید؟", "Will you sign the contract today?")],
             ("سؤال باز با «چه» یا «چطور» شروع می‌شود و جوابش بله یا خیر نیست.", "Open questions start with “what” or “how” and can't be answered with yes or no.")),
            (("در جلسه کشف نیاز، نسبت پیشنهادی صحبت به شنیدن چقدر است؟", "In a discovery call, what's the recommended talk-to-listen ratio?"),
             [("۳۰٪ صحبت، ۷۰٪ شنیدن", "30% talk, 70% listen"), ("۷۰٪ صحبت، ۳۰٪ شنیدن", "70% talk, 30% listen"),
              ("۵۰٪ صحبت، ۵۰٪ شنیدن", "50% talk, 50% listen"), ("۹۰٪ صحبت، ۱۰٪ شنیدن", "90% talk, 10% listen")],
             ("هرچه مشتری بیشتر حرف بزند، نیاز واقعی‌اش روشن‌تر می‌شود.", "The more the customer talks, the clearer their real need becomes.")),
        ]),
        (("مدیریت اعتراض", "Handling objections"), 4,
         ("اعتراض یعنی مشتری به اطلاعات یا اطمینان بیشتری نیاز دارد.\nاول گوش بدهید و احساس مشتری را تایید کنید.\nبا یک سؤال، ریشه اعتراض را پیدا کنید و بعد پاسخ دهید.",
          "An objection means the customer needs more information or confidence.\nListen first and acknowledge how they feel.\nAsk one question to find the root cause, then respond."), [
            (("مشتری می‌گوید «خیلی گران است». بهترین قدم اول چیست؟", "The customer says “it's too expensive.” What's the best first step?"),
             [("بپرسید قیمت را با چه چیزی مقایسه می‌کند", "Ask what they're comparing the price to"),
              ("فوراً تخفیف بدهید", "Offer a discount right away"), ("موضوع را عوض کنید", "Change the subject"),
              ("روی کیفیت پافشاری کنید", "Insist on the quality")],
             ("بدون فهمیدن مبنای مقایسه، هر پاسخی فقط یک حدس است.", "Without knowing the comparison point, any answer is a guess.")),
            (("اعتراض مشتری معمولاً به چه معناست؟", "What does a customer objection usually mean?"),
             [("به اطلاعات یا اطمینان بیشتری نیاز دارد", "They need more information or confidence"),
              ("اصلاً علاقه‌ای ندارد", "They're not interested at all"), ("باید جلسه را تمام کرد", "The meeting should end"),
              ("قیمت حتماً باید کم شود", "The price must be lowered")],
             ("اعتراض نشانه درگیر بودن مشتری است، نه پایان گفتگو.", "An objection shows engagement, not the end of the conversation.")),
        ]),
        (("بستن فروش با اطمینان", "Closing with confidence"), 3,
         ("ارزشی را که روی آن توافق کردید خلاصه کنید.\nیک قدم بعدی مشخص با تاریخ پیشنهاد دهید.\nبا یک «بستن آزمایشی» آمادگی مشتری را بسنجید.",
          "Summarize the value you've agreed on.\nPropose a concrete next step with a date.\nUse a “trial close” to test readiness."), [
            (("بعد از یک دموی موفق، بهترین حرکت کدام است؟", "After a successful demo, what's the best move?"),
             [("ارزش توافق‌شده را خلاصه و قدم بعدی مشخص پیشنهاد کنید", "Summarize the agreed value and propose a concrete next step"),
              ("منتظر تماس مشتری بمانید", "Wait for the customer to call"), ("یک بروشور عمومی بفرستید", "Send a generic brochure"),
              ("تخفیف بیشتری پیشنهاد دهید", "Offer a bigger discount")],
             ("قدم بعدی مشخص، شتاب تصمیم‌گیری را حفظ می‌کند.", "A concrete next step keeps the decision moving.")),
            (("«بستن آزمایشی» چیست؟", "What is a “trial close”?"),
             [("سؤالی که آمادگی مشتری برای خرید را می‌سنجد", "A question that tests readiness to buy"),
              ("امضای نهایی قرارداد", "The final contract signature"), ("نسخه رایگان محصول", "A free version of the product"),
              ("یک تخفیف ویژه", "A special discount")],
             ("مثال: «جلسه شروع را برای شنبه بگذاریم؟»", "Example: “Shall we schedule the kickoff for Saturday?”")),
        ]),
    ]),
    ("service", "#7B5CFF", "heart-handshake", ("تجربه مشتری", "Customer Experience"),
     ("همدلی، حل مسئله و اعتمادسازی", "Empathy, resolution and trust"), [
        (("اول همدلی", "Empathy first"), 3,
         ("قبل از حل مسئله، احساس مشتری را به رسمیت بشناسید.\nبرای تجربه‌ای که داشته عذرخواهی کنید، حتی اگر مقصر نبوده‌اید.\nمسئولیت قدم بعدی را خودتان بپذیرید.",
          "Acknowledge the customer's feelings before fixing anything.\nApologize for the experience, even if it wasn't your fault.\nOwn the next step yourself."), [
            (("سفارش مشتری دیر رسیده و عصبانی است. جمله اول شما؟", "A customer is angry about a late order. Your first sentence?"),
             [("می‌فهمم دیر رسیدن سفارش چقدر آزاردهنده است؛ همین الان بررسی می‌کنم", "I understand how frustrating a late order is; I'll check it right now"),
              ("تقصیر ما نیست، پیک دیر کرده", "It's not our fault, the courier was late"), ("لطفاً آرام باشید", "Please calm down"),
              ("فردا تماس بگیرید", "Please call back tomorrow")],
             ("همدلی به‌همراه اقدام فوری، تنش را سریع پایین می‌آورد.", "Empathy plus immediate action de-escalates fast.")),
            (("عذرخواهی برای «تجربه» مشتری یعنی چه؟", "What does apologizing for the “experience” mean?"),
             [("به رسمیت شناختن احساس مشتری درباره اتفاقی که افتاده", "Acknowledging how the customer feels about what happened"),
              ("پذیرفتن مسئولیت حقوقی", "Accepting legal liability"), ("پیشنهاد بازپرداخت وجه", "Offering a refund"),
              ("مقصر دانستن همکار", "Blaming a colleague")],
             ("می‌توانید همدلی کنید بدون اینکه تقصیر را گردن بگیرید.", "You can empathize without admitting fault.")),
        ]),
        (("حل در اولین تماس", "First contact resolution"), 4,
         ("FCR یعنی درصد مشکلاتی که در همان تماس اول حل می‌شوند.\nاین شاخص قوی‌ترین عامل رضایت مشتری است.\nقبل از پایان تماس، از حل شدن مشکل مطمئن شوید.",
          "FCR is the share of issues solved in the very first contact.\nIt's the strongest driver of customer satisfaction.\nBefore ending, confirm the issue is actually resolved."), [
            (("شاخص FCR چه چیزی را می‌سنجد؟", "What does FCR measure?"),
             [("درصد مشکلاتی که در اولین تماس حل می‌شوند", "Share of issues solved in the first contact"),
              ("میانگین مدت تماس", "Average call duration"), ("تعداد تماس در ساعت", "Calls per hour"),
              ("تعداد شکایت‌های ماهانه", "Monthly complaints")],
             ("FCR بالا یعنی مشتری مجبور نیست دوباره تماس بگیرد.", "High FCR means customers don't have to call back.")),
            (("قبل از پایان تماس چه کاری باید انجام دهید؟", "What should you do before ending a call?"),
             [("از مشتری بپرسید آیا مشکلش کاملاً حل شده است", "Confirm the issue is fully resolved"),
              ("تماس را به واحد دیگری منتقل کنید", "Transfer to another department"),
              ("اول درخواست امتیاز ۵ ستاره کنید", "Ask for a 5-star rating first"),
              ("برای کاهش زمان، سریع قطع کنید", "Hang up fast to cut handle time")],
             ("تایید نهایی از تماس‌های تکراری جلوگیری می‌کند.", "A final check prevents repeat calls.")),
        ]),
        (("بستن حلقه", "Closing the loop"), 3,
         ("اگر قول تماس دوباره می‌دهید، زمان دقیق بگویید و سر قولتان بمانید.\nیک پیام کوتاه با خلاصه راه‌حل، اعتماد می‌سازد.\nمشتری همیشه باید بداند قدم بعدی چیست.",
          "If you promise a callback, give an exact time and keep it.\nA short message summarizing the fix builds trust.\nThe customer should always know what happens next."), [
            (("به مشتری قول تماس دوباره داده‌اید. بهترین کار؟", "You promised a callback. Best practice?"),
             [("یک بازه زمانی مشخص بگویید و به آن پایبند باشید", "Give a specific time window and keep it"),
              ("بگویید «به‌زودی» تماس می‌گیریم", "Say “we'll call you soon”"), ("منتظر بمانید خودش تماس بگیرد", "Wait for them to call again"),
              ("فقط نظرسنجی خودکار بفرستید", "Only send an automatic survey")],
             ("قول مشخص و عمل به آن، پایه اعتماد است.", "A specific promise, kept, is the foundation of trust.")),
            (("بعد از حل یک مشکل پیچیده، بهترین پیگیری کدام است؟", "After solving a complex issue, what's the best follow-up?"),
             [("پیامی کوتاه با خلاصه راه‌حل و قدم‌های بعدی", "A short message summarizing the fix and next steps"),
              ("هیچ کاری لازم نیست", "Nothing is needed"), ("یک پیشنهاد تبلیغاتی", "A marketing offer"), ("تماس در ماه بعد", "A call next month")],
             ("خلاصه مکتوب، ابهام و تماس تکراری را کم می‌کند.", "A written summary reduces confusion and repeat contacts.")),
        ]),
    ]),
    ("security", "#12B8E0", "shield-check", ("امنیت اطلاعات", "Information Security"),
     ("فیشینگ، رمز عبور و امنیت روزمره", "Phishing, passwords and everyday safety"), [
        (("فیشینگ را بشناسید", "Spot the phish"), 4,
         ("نشانه‌ها: عجله، دامنه‌های شبیه (bank-me11i.ir) و پیوست غیرمنتظره.\nهیچ سازمانی رمز عبور یا کد تایید شما را نمی‌خواهد.\nدر صورت شک، از یک مسیر مستقل تایید بگیرید.",
          "Red flags: urgency, lookalike domains (bank-me11i.ir), unexpected attachments.\nNo organization will ever ask for your password or OTP.\nWhen in doubt, verify through an independent channel."), [
            (("ایمیلی از طرف «واحد IT» فوراً کد تایید پیامکی شما را می‌خواهد. چه می‌کنید؟", "An email “from IT” urgently asks for your SMS verification code. What do you do?"),
             [("کد را نمی‌دهم و ایمیل را به واحد امنیت گزارش می‌کنم", "Don't share it and report the email to security"),
              ("کد را می‌فرستم", "Send the code"), ("جواب می‌دهم و دلیلش را می‌پرسم", "Reply and ask why"),
              ("برای همکارانم هم می‌فرستم", "Forward it to colleagues")],
             ("کد تایید مثل کلید خانه است؛ هیچ‌وقت آن را به کسی ندهید.", "A verification code is like a house key — never hand it over.")),
            (("کدام مورد نشانه فیشینگ است؟", "Which one is a phishing sign?"),
             [("دامنه فرستنده تقریباً شبیه دامنه واقعی است", "The sender's domain almost matches the real one"),
              ("ایمیل مدیرتان از نشانی همیشگی درباره جلسه‌ای برنامه‌ریزی‌شده", "Your manager's usual address about a planned meeting"),
              ("خبرنامه‌ای که عضوش شده‌اید", "A newsletter you subscribed to"),
              ("اطلاعیه‌ای در اینترانت شرکت", "An announcement on the company intranet")],
             ("مهاجمان با تغییر یک حرف، دامنه جعلی می‌سازند.", "Attackers change a single character to fake a domain.")),
        ]),
        (("رمز عبور قوی", "Strong passwords"), 3,
         ("عبارت عبور بلند از رمز کوتاه و پیچیده امن‌تر است.\nبرای هر سرویس یک رمز عبور جداگانه داشته باشید.\nاز مدیر رمز عبور و ورود دومرحله‌ای استفاده کنید.",
          "A long passphrase beats a short, complex password.\nUse a unique password for every service.\nTurn on a password manager and two-step login."), [
            (("امن‌ترین گزینه کدام است؟", "Which is the strongest option?"),
             [("یک عبارت عبور بلند از چهار کلمه تصادفی", "A long passphrase of four random words"),
              ("P@ss1", "P@ss1"), ("تاریخ تولدتان", "Your birthday"), ("همان رمز ایمیل شخصی", "Your personal email password")],
             ("طول، مهم‌ترین عامل قدرت رمز عبور است.", "Length is the biggest factor in password strength.")),
            (("چرا برای هر سرویس رمز عبور جداگانه لازم است؟", "Why use a unique password for each service?"),
             [("تا لو رفتن یکی، بقیه حساب‌ها را به خطر نیندازد", "So one leak doesn't expose your other accounts"),
              ("چون راحت‌تر به خاطر می‌ماند", "It's easier to remember"), ("چون قانون الزام کرده", "The law requires it"),
              ("چون ورود سریع‌تر می‌شود", "It makes login faster")],
             ("مهاجمان رمزهای لورفته را روی سرویس‌های دیگر امتحان می‌کنند.", "Attackers replay leaked passwords on other services.")),
        ]),
        (("میز و دستگاه امن", "Clean desk, safe devices"), 3,
         ("هنگام ترک میز، صفحه را قفل کنید (Win+L).\nاسناد مشتری را روی میز رها نکنید.\nگم شدن دستگاه کاری را فوراً گزارش دهید.",
          "Lock your screen when you step away (Win+L).\nNever leave customer documents on your desk.\nReport a lost work device immediately."), [
            (("دو دقیقه از میزتان دور می‌شوید. چه می‌کنید؟", "You step away for two minutes. What do you do?"),
             [("صفحه را قفل می‌کنم", "Lock the screen"), ("همین‌طور رهایش می‌کنم", "Leave it as is"),
              ("فقط مانیتور را خاموش می‌کنم", "Just turn off the monitor"), ("از همکارم می‌خواهم مراقب باشد", "Ask a colleague to watch it")],
             ("قفل صفحه یک ثانیه طول می‌کشد و بیشترین خطر را حذف می‌کند.", "Locking takes a second and removes most of the risk.")),
            (("لپ‌تاپ کاری‌تان گم شده. اولین اقدام؟", "Your work laptop is lost. First action?"),
             [("فوراً به واحد IT یا امنیت گزارش می‌دهم", "Report it to IT/security immediately"),
              ("چند روز صبر می‌کنم شاید پیدا شود", "Wait a few days in case it turns up"),
              ("یک لپ‌تاپ جدید می‌خرم", "Buy a new one"), ("به کسی نمی‌گویم", "Tell no one")],
             ("گزارش سریع اجازه می‌دهد دستگاه از راه دور قفل یا پاک شود.", "Fast reporting lets IT lock or wipe the device remotely.")),
        ]),
    ]),
    ("compliance", "#FF9F1A", "scale", ("انطباق و اخلاق حرفه‌ای", "Compliance & Ethics"),
     ("تعارض منافع، پول‌شویی و حریم خصوصی", "Conflicts, AML and data privacy"), [
        (("هدیه و تعارض منافع", "Gifts & conflicts of interest"), 3,
         ("هر رابطه شخصی با تامین‌کننده یا مشتری را اعلام کنید.\nهدیه‌های بالاتر از سقف مجاز را نپذیرید یا گزارش دهید.\nدر تصمیم‌هایی که منافع شخصی دارید، مشارکت نکنید.",
          "Disclose any personal relationship with a supplier or customer.\nDecline or report gifts above the policy limit.\nStep out of decisions where you have a personal interest."), [
            (("یک تامین‌کننده در دوره مناقصه هدیه گرانی پیشنهاد می‌دهد. چه می‌کنید؟", "A supplier offers you an expensive gift during a tender. What do you do?"),
             [("طبق سیاست هدیه، آن را رد یا گزارش می‌کنم", "Decline or report it per the gifts policy"),
              ("بی‌سروصدا می‌پذیرم", "Accept it quietly"), ("می‌پذیرم و با تیم تقسیم می‌کنم", "Accept it and share with the team"),
              ("به‌جایش وجه نقد می‌خواهم", "Ask for cash instead")],
             ("هدیه در زمان مناقصه، ظاهر تعارض منافع ایجاد می‌کند.", "A gift during a tender creates an appearance of conflict.")),
            (("شرکت پسرعمویتان در مناقصه تیم شما شرکت کرده است. درست‌ترین کار؟", "Your cousin's company is bidding on your team's contract. The right move?"),
             [("رابطه را اعلام و از تصمیم‌گیری کناره‌گیری می‌کنم", "Disclose it and step out of the decision"),
              ("چیزی نمی‌گویم", "Say nothing"), ("کمکشان می‌کنم برنده شوند", "Help them win"),
              ("برای احتیاط علیه‌شان رای می‌دهم", "Vote against them to be safe")],
             ("شفافیت و کناره‌گیری، هم از شما و هم از سازمان محافظت می‌کند.", "Transparency and recusal protect both you and the company.")),
        ]),
        (("مشتری را بشناسید", "Know your customer (AML)"), 4,
         ("نشانه‌های هشدار: خرد کردن واریز نقدی بزرگ، منشأ نامشخص پول و اصرار بر دور زدن احراز هویت.\nفعالیت مشکوک را به واحد انطباق گزارش دهید.\nهرگز مشتری را از گزارش مطلع نکنید.",
          "Red flags: split cash deposits, unclear source of funds, pressure to skip identity checks.\nReport suspicious activity to compliance.\nNever tip off the customer about a report."), [
            (("مشتری در یک روز چند واریز درست زیر سقف گزارش‌دهی انجام می‌دهد. این چیست؟", "A customer makes several deposits just under the reporting threshold in one day. This is:"),
             [("یک نشانه هشدار به نام «خرد کردن» تراکنش", "A red flag known as structuring"),
              ("پس‌انداز عادی", "Normal saving"), ("خطای سیستم", "A system bug"), ("برنامه‌ریزی مالی خوب", "Good financial planning")],
             ("خرد کردن تراکنش برای فرار از گزارش‌دهی، نشانه کلاسیک پول‌شویی است.", "Structuring to avoid reporting is a classic money-laundering sign.")),
            (("بعد از گزارش فعالیت مشکوک، چه باید کرد؟", "After reporting suspicious activity, you should:"),
             [("موضوع را محرمانه نگه می‌دارم", "Keep it confidential"), ("به مشتری اطلاع می‌دهم", "Tell the customer"),
              ("خودم حساب را می‌بندم", "Close the account myself"), ("در گروه تیم به اشتراک می‌گذارم", "Post it in the team chat")],
             ("مطلع کردن مشتری، تحقیقات را خراب می‌کند و خودش تخلف است.", "Tipping off the customer ruins the investigation and is itself a violation.")),
        ]),
        (("حریم خصوصی داده", "Data privacy"), 3,
         ("فقط داده‌ای را جمع کنید که برای هدف مشخص لازم است.\nداده را فقط برای همان هدف استفاده کنید.\nدسترسی را بر اساس «نیاز به دانستن» بدهید.",
          "Collect only the data you need for a stated purpose.\nUse it only for that purpose.\nShare on a strict need-to-know basis."), [
            (("همکاری از واحد دیگر برای کاری شخصی، شماره تلفن یک مشتری را می‌خواهد.", "A colleague from another department wants a customer's phone number for a personal matter."),
             [("رد می‌کنم؛ نیاز کاری وجود ندارد", "Decline — there's no business need"), ("شماره را می‌دهم", "Share it"),
              ("فقط چند رقم آخر را می‌دهم", "Share only the last digits"), ("بعداً از مشتری اجازه می‌گیرم", "Ask the customer later")],
             ("داده مشتری فقط برای هدف کاری مشخص قابل استفاده است.", "Customer data may only be used for a defined business purpose.")),
            (("«حداقل‌سازی داده» یعنی چه؟", "What does “data minimization” mean?"),
             [("جمع‌آوری فقط داده‌های لازم برای هدف", "Collecting only the data needed for the purpose"),
              ("حذف همه داده‌ها", "Deleting all data"), ("فشرده‌سازی فایل‌ها", "Compressing files"),
              ("نگهداری داده در خارج از کشور", "Storing data abroad")],
             ("داده کمتر یعنی ریسک کمتر در صورت نشت.", "Less data means less risk if there's a leak.")),
        ]),
    ]),
]

TEAMS = [("فروش تهران", "Sales · Tehran"), ("فروش اصفهان", "Sales · Isfahan"),
         ("مرکز تماس", "Call Center"), ("عملیات شعب", "Branch Ops")]

PEOPLE = [("سارا احمدی", "Sara Ahmadi"), ("علی محمدی", "Ali Mohammadi"), ("مریم حسینی", "Maryam Hosseini"),
          ("رضا کریمی", "Reza Karimi"), ("نگار موسوی", "Negar Mousavi"), ("امیر جعفری", "Amir Jafari"),
          ("زهرا صادقی", "Zahra Sadeghi"), ("حسین رحیمی", "Hossein Rahimi"), ("فاطمه نوری", "Fatemeh Nouri"),
          ("مهدی قاسمی", "Mahdi Ghasemi"), ("الهام طاهری", "Elham Taheri"), ("پویا شریفی", "Pouya Sharifi"),
          ("نیلوفر اکبری", "Niloufar Akbari"), ("بهراد کاظمی", "Behrad Kazemi"), ("شیما رستمی", "Shima Rostami"),
          ("آرش یزدانی", "Arash Yazdani"), ("ترانه فرهادی", "Taraneh Farhadi"), ("سینا بهرامی", "Sina Bahrami"),
          ("مینا عباسی", "Mina Abbasi"), ("کیان نادری", "Kian Naderi"), ("لیلا مرادی", "Leila Moradi"),
          ("بابک زمانی", "Babak Zamani"), ("هانیه سلطانی", "Hanieh Soltani"), ("دانیال امینی", "Danial Amini")]

DEMO_USERS = {"learner@ranksyar.ir": (0, "learner"), "manager@ranksyar.ir": (None, "manager")}


def init():
    """Create and seed the database on first run. Returns True when freshly seeded."""
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    con = connect()
    fresh = not con.execute("SELECT 1 FROM sqlite_master WHERE name='users'").fetchone()
    if fresh:
        con.executescript(SCHEMA)
        with con:
            seed(con, date.today())
    con.close()
    return fresh


def seed(con, today):
    rng = random.Random(42)
    qids = []  # (question_id, track_id)
    for tpos, (tid, color, icon, title, descr, lessons) in enumerate(TRACKS):
        con.execute("INSERT INTO tracks VALUES(?,?,?,?,?,?)", (tid, tpos, J(*title), J(*descr), color, icon))
        for lpos, (ltitle, minutes, body, questions) in enumerate(lessons):
            lid = con.execute("INSERT INTO lessons(track_id,pos,title,body,minutes) VALUES(?,?,?,?,?)",
                              (tid, lpos, J(*ltitle), J(*body), minutes)).lastrowid
            for prompt, choices, explain in questions:
                order = list(range(len(choices)))
                rng.shuffle(order)  # correct choice is authored first; shuffle both languages identically
                shuffled = [choices[i] for i in order]
                qid = con.execute("INSERT INTO questions(lesson_id,prompt,choices,answer,explain) VALUES(?,?,?,?,?)",
                                  (lid, J(*prompt), J([c[0] for c in shuffled], [c[1] for c in shuffled]),
                                   order.index(0), J(*explain))).lastrowid
                qids.append((qid, tid))

    for fa, en in TEAMS:
        con.execute("INSERT INTO teams(name) VALUES(?)", (J(fa, en),))
    people = [(f"user{i}@ranksyar.ir", i % 4, "learner", p) for i, p in enumerate(PEOPLE)]
    people[0] = ("learner@ranksyar.ir", 0, "learner", PEOPLE[0])
    people.append(("manager@ranksyar.ir", 0, "manager", ("کاوه رضایی", "Kaveh Rezaei")))

    team_bias = {(t, tid): rng.uniform(-0.18, 0.08) for t in range(4) for tid, *_ in TRACKS}
    demo_pw = hash_pw(DEMO_PASSWORD)
    for email, team, role, name in people:
        uid = con.execute("INSERT INTO users(email,pw,name,role,team_id) VALUES(?,?,?,?,?)",
                          (email, demo_pw if email in DEMO_USERS else None, J(*name), role, team + 1)).lastrowid
        demo = email in DEMO_USERS
        skill, active = rng.uniform(0.55, 0.9), rng.uniform(0.2, 0.95)
        state = {}  # qid -> (box, due)
        pool = qids[:12] if demo else qids  # demo accounts keep two tracks unseen, so lesson cards show up
        for back in range(27, -1, -1):
            day = today - timedelta(back)
            if demo:  # demo accounts: a 4-day streak ending yesterday, today left for the visitor
                if back == 0 or (back > 4 and rng.random() > 0.55):
                    continue
            elif rng.random() > active * (0.6 if back < 7 and active < 0.45 else 1):
                continue
            due = [q for q, (_, d) in state.items() if d <= day][:6]
            new = [q for q, _ in pool if q not in state][: rng.randint(1, 4)]
            for q in due + new or [rng.choice(list(state))]:  # nothing due or new: a practice card
                tid = next(t for i, t in qids if i == q)
                box = state.get(q, (0, day))[0]
                ok = rng.random() < skill + team_bias[(team, tid)] + 0.04 * box
                box, gap = srs.review(box, ok)
                state[q] = (box, day + timedelta(gap))
                con.execute("INSERT INTO answers(user_id,question_id,correct,xp,day) VALUES(?,?,?,?,?)",
                            (uid, q, ok, srs.xp(ok), day.isoformat()))
        con.executemany("INSERT INTO reviews VALUES(?,?,?,?)",
                        [(uid, q, b, d.isoformat()) for q, (b, d) in state.items()])
