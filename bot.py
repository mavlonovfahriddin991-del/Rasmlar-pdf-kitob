import os
import shutil
import time
from datetime import datetime
import telebot
from telebot import types
from PIL import Image as PILImage
from PIL import ImageOps

# ReportLab imports for beautiful PDF generation
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak, KeepTogether, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# Bot API Token
API_TOKEN = '8945856972:AAGp2AG07eSwcgc4rDvu0h355DCT3PoQ_8M'
bot = telebot.TeleBot(API_TOKEN)

# In-memory sessions dictionary
sessions = {}

# Ensure folders exist
TEMP_DIR = 'temp'
os.makedirs(TEMP_DIR, exist_ok=True)

def cleanup_temp():
    """Starts with a clean temp directory on bot startup."""
    if os.path.exists(TEMP_DIR):
        try:
            shutil.rmtree(TEMP_DIR)
        except Exception as e:
            print(f"Error cleaning temp directory: {e}")
    os.makedirs(TEMP_DIR, exist_ok=True)

def get_session(chat_id):
    """Retrieves or creates a session for the user."""
    if chat_id not in sessions:
        sessions[chat_id] = {
            'title': '',
            'author': '',
            'theme': 'classic', # 'classic', 'modern', 'playful'
            'photos': [],       # list of dicts: {'path': str, 'caption': str, 'file_id': str}
            'cover_index': -1,  # index of cover photo
            'state': 'idle',    # 'idle', 'waiting_title', 'waiting_author', 'waiting_caption'
            'edit_index': -1    # photo index currently being captioned
        }
    return sessions[chat_id]

def clear_session(chat_id):
    """Cleans up the user session and deletes their temporary folder."""
    if chat_id in sessions:
        user_dir = os.path.join(TEMP_DIR, str(chat_id))
        if os.path.exists(user_dir):
            try:
                shutil.rmtree(user_dir)
            except Exception as e:
                print(f"Error cleaning user temp folder: {e}")
        del sessions[chat_id]

# Numbered Canvas pattern for ReportLab to support "Page X of Y" and themes
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_elements(num_pages)
            super().showPage()
        super().save()

    def draw_page_elements(self, page_count):
        theme = getattr(self, 'theme_name', 'classic')
        title = getattr(self, 'book_title', 'Kitob')
        author = getattr(self, 'book_author', 'Muallif')

        # We do not draw headers and footers on the cover page (Page 1)
        if self._pageNumber == 1:
            self.draw_cover_decorations(theme)
            return

        self.saveState()

        # Styles based on theme
        if theme == 'classic':
            # Elegant page border
            self.setStrokeColor(colors.HexColor('#2C3E50'))
            self.setLineWidth(1)
            self.rect(36, 36, 523, 769) # margins: 36pt (0.5 inch)
            self.rect(40, 40, 515, 761)

            # Header text
            self.setFont('Times-Italic', 9)
            self.setFillColor(colors.HexColor('#2C3E50'))
            self.drawCentredString(297.5, 805, f"{title} — {author}")

            # Footer page number
            self.setFont('Times-Roman', 10)
            self.drawCentredString(297.5, 55, f"— {self._pageNumber} / {page_count} —")

        elif theme == 'modern':
            # Stylish thick primary color strip on the left side
            self.setFillColor(colors.HexColor('#3498DB'))
            self.rect(36, 36, 6, 769, fill=True, stroke=False)

            # Modern header
            self.setFont('Helvetica-Bold', 8)
            self.setFillColor(colors.HexColor('#7F8C8D'))
            self.drawString(54, 805, title.upper())
            self.drawRightString(541, 805, author)
            
            # Subtle header separator line
            self.setStrokeColor(colors.HexColor('#BDC3C7'))
            self.setLineWidth(0.5)
            self.line(54, 798, 541, 798)

            # Modern footer
            self.setFont('Helvetica', 9)
            self.setFillColor(colors.HexColor('#7F8C8D'))
            self.drawRightString(541, 50, f"Sahifa {self._pageNumber} / {page_count}")

        elif theme == 'playful':
            # Playful cartoon-like yellow border
            self.setStrokeColor(colors.HexColor('#F1C40F'))
            self.setLineWidth(4)
            self.rect(36, 36, 523, 769)

            # Playful Header
            self.setFont('Courier-Bold', 10)
            self.setFillColor(colors.HexColor('#E67E22'))
            self.drawString(54, 805, f"✨ {title}")
            self.drawRightString(541, 805, f"Muallif: {author} ✨")

            # Playful Footer
            self.setFont('Courier', 10)
            self.setFillColor(colors.HexColor('#2C3E50'))
            self.drawCentredString(297.5, 50, f"🎈 {self._pageNumber}-sahifa / {page_count} 🎈")

        self.restoreState()

    def draw_cover_decorations(self, theme):
        self.saveState()
        if theme == 'classic':
            # Rich deep purple/gold cover border
            self.setStrokeColor(colors.HexColor('#2C3E50'))
            self.setLineWidth(2)
            self.rect(36, 36, 523, 769)
            self.setStrokeColor(colors.HexColor('#D4AF37')) # Gold accent
            self.setLineWidth(1)
            self.rect(42, 42, 511, 757)
        elif theme == 'modern':
            # Clean blue accent block at the top
            self.setFillColor(colors.HexColor('#F8F9F9'))
            self.rect(0, 0, 595, 841, fill=True, stroke=False)
            self.setFillColor(colors.HexColor('#3498DB'))
            self.rect(0, 810, 595, 31, fill=True, stroke=False)
        elif theme == 'playful':
            # Bold orange / yellow double frame
            self.setStrokeColor(colors.HexColor('#F1C40F'))
            self.setLineWidth(5)
            self.rect(36, 36, 523, 769)
            self.setStrokeColor(colors.HexColor('#E67E22'))
            self.setLineWidth(2)
            self.rect(46, 46, 503, 749)
        self.restoreState()

def make_numbered_canvas(title, author, theme):
    """Dynamic canvas class creator pre-configured with book metadata."""
    class CustomNumberedCanvas(NumberedCanvas):
        theme_name = theme
        book_title = title
        book_author = author
    return CustomNumberedCanvas

def open_and_correct_image(path):
    """Opens image using Pillow and applies EXIF orientation transpose."""
    img = PILImage.open(path)
    try:
        img = ImageOps.exif_transpose(img)
    except Exception as e:
        print(f"Error transposing image orientation: {e}")
    return img

def generate_pdf(chat_id, session):
    """Compiles the beautiful PDF book using ReportLab and Pillow."""
    title = session['title'] or "Ajoyib Kitob"
    author = session['author'] or "Muallif"
    theme = session['theme']
    photos = session['photos']
    cover_index = session['cover_index']

    user_dir = os.path.join(TEMP_DIR, str(chat_id))
    pdf_filename = os.path.join(user_dir, f"{title.replace(' ', '_')}.pdf")

    # A4 dimensions: 595.27 x 841.89 points
    # Margins: 54 points (0.75 in) top/bottom, left/right
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=A4,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Theme definitions
    if theme == 'classic':
        title_font = 'Times-Bold'
        body_font = 'Times-Roman'
        italic_font = 'Times-Italic'
        accent_color = colors.HexColor('#2C3E50') # Navy
        text_color = colors.HexColor('#2C3E50')
        line_color = colors.HexColor('#D4AF37')   # Gold
    elif theme == 'modern':
        title_font = 'Helvetica-Bold'
        body_font = 'Helvetica'
        italic_font = 'Helvetica-Oblique'
        accent_color = colors.HexColor('#2C3E50') # Dark slate
        text_color = colors.HexColor('#34495E')
        line_color = colors.HexColor('#3498DB')   # Blue
    else: # playful
        title_font = 'Courier-Bold'
        body_font = 'Courier'
        italic_font = 'Courier-Oblique'
        accent_color = colors.HexColor('#E67E22') # Orange
        text_color = colors.HexColor('#2C3E50')
        line_color = colors.HexColor('#F1C40F')   # Yellow

    # Styling paragraph definitions
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName=title_font,
        fontSize=30,
        leading=36,
        alignment=TA_CENTER,
        textColor=accent_color,
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName=italic_font,
        fontSize=15,
        leading=18,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#7F8C8D'),
        spaceAfter=30
    )
    
    author_style = ParagraphStyle(
        'CoverAuthor',
        parent=styles['Normal'],
        fontName=title_font,
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        textColor=text_color,
        spaceAfter=8
    )

    caption_style = ParagraphStyle(
        'ImageCaption',
        parent=styles['Normal'],
        fontName=italic_font,
        fontSize=12,
        leading=16,
        alignment=TA_CENTER,
        textColor=text_color,
        spaceBefore=12,
        spaceAfter=12
    )

    story = []

    # --- 1. COVER PAGE ---
    story.append(Spacer(1, 80))
    story.append(Paragraph(title, title_style))
    story.append(HRFlowable(
        width="65%",
        thickness=2,
        color=line_color,
        spaceBefore=10,
        spaceAfter=25,
        hAlign='CENTER'
    ))
    story.append(Paragraph("Rasmlar to'plami va xotiralar albomi", subtitle_style))
    story.append(Spacer(1, 30))

    # Add cover photo if selected
    if 0 <= cover_index < len(photos):
        cover_path = photos[cover_index]['path']
        try:
            img = open_and_correct_image(cover_path)
            w, h = img.size
            # Max dimensions for cover image: 320x320
            scale = min(320 / w, 320 / h)
            new_w, new_h = w * scale, h * scale
            story.append(RLImage(cover_path, width=new_w, height=new_h, hAlign='CENTER'))
            story.append(Spacer(1, 40))
        except Exception as e:
            print(f"Error loading cover photo: {e}")

    story.append(Paragraph(f"Muallif: {author}", author_style))
    current_date = datetime.now().strftime("%d.%m.%Y")
    date_style = ParagraphStyle(
        'CoverDate',
        parent=styles['Normal'],
        fontName=body_font,
        fontSize=11,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#95A5A6')
    )
    story.append(Paragraph(current_date, date_style))
    story.append(PageBreak())

    # --- 2. CONTENT PAGES ---
    for i, p in enumerate(photos):
        photo_path = p['path']
        caption = p['caption'] or f"{i+1}-rasm"
        
        story.append(Spacer(1, 20))
        
        try:
            img = open_and_correct_image(photo_path)
            w, h = img.size
            
            # Max boundary for page photo: width=450, height=480
            max_w, max_h = 450, 480
            scale = min(max_w / w, max_h / h)
            new_w, new_h = w * scale, h * scale
            
            # Use KeepTogether to ensure photo and caption stay on the same page
            page_elements = []
            page_elements.append(RLImage(photo_path, width=new_w, height=new_h, hAlign='CENTER'))
            page_elements.append(Spacer(1, 15))
            page_elements.append(Paragraph(caption, caption_style))
            
            story.append(KeepTogether(page_elements))
        except Exception as e:
            print(f"Error inserting image {i+1}: {e}")
            story.append(Paragraph(f"[Yuklashda xatolik yuz berdi: {e}]", caption_style))

        if i < len(photos) - 1:
            story.append(PageBreak())

    # Build PDF with dynamic class binding for NumberedCanvas
    CustomNumberedCanvas = make_numbered_canvas(title, author, theme)
    doc.build(story, canvasmaker=CustomNumberedCanvas)
    
    return pdf_filename

# --- TELEGRAM BOT HANDLERS ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    chat_id = message.chat.id
    clear_session(chat_id)
    
    welcome_text = (
        "👋 **Assalomu alaykum!**\n\n"
        "**Kitob PDF Yaratuvchi Bot**ga xush kelibsiz! 📚✨\n\n"
        "Ushbu bot yordamida rasmlaringizdan chiroyli va kitob ko'rinishidagi PDF fayl yaratishingiz mumkin.\n\n"
        "**Asosiy imkoniyatlar:**\n"
        "🎨 3 xil kitob dizayni (Klassik, Zamonaviy, Quvnoq)\n"
        "✍️ Har bir rasmga alohida izoh yozish\n"
        "🖼 Muqova uchun maxsus rasm tanlash\n"
        "📄 Sahifalash va avtomatik sarlavhalar qo'shish\n\n"
        "Kitob yaratishni boshlash uchun quyidagi **🆕 Yangi kitob yaratish** tugmasini bosing yoki /new buyrug'ini yuboring."
    )
    
    markup = types.InlineKeyboardMarkup()
    btn_new = types.InlineKeyboardButton("🆕 Yangi kitob yaratish", callback_data="start_new")
    btn_help = types.InlineKeyboardButton("ℹ️ Yo'riqnoma", callback_data="help_info")
    markup.row(btn_new)
    markup.row(btn_help)
    
    bot.send_message(chat_id, welcome_text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(commands=['new'])
def start_new_book_cmd(message):
    chat_id = message.chat.id
    clear_session(chat_id)
    session = get_session(chat_id)
    session['state'] = 'waiting_title'
    
    markup = types.InlineKeyboardMarkup()
    btn_cancel = types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_book")
    markup.add(btn_cancel)
    
    bot.send_message(
        chat_id, 
        "✍️ **1-qadam: Kitobingiz uchun sarlavha (nom) kiriting:**\n\n*Masalan: Mening oilam, Yozgi ta'tillar, Fotoportfoliom*", 
        parse_mode="Markdown", 
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id = call.message.chat.id
    session = get_session(chat_id)
    data = call.data

    # Acknowledge callback to avoid loading states in client
    bot.answer_callback_query(call.id)

    if data == "start_new":
        clear_session(chat_id)
        session = get_session(chat_id)
        session['state'] = 'waiting_title'
        
        markup = types.InlineKeyboardMarkup()
        btn_cancel = types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_book")
        markup.add(btn_cancel)
        
        bot.send_message(
            chat_id, 
            "✍️ **1-qadam: Kitobingiz uchun sarlavha (nom) kiriting:**\n\n*Masalan: Mening oilam, Yozgi ta'tillar, Fotoportfoliom*", 
            parse_mode="Markdown", 
            reply_markup=markup
        )
        
    elif data == "help_info":
        help_text = (
            "📖 **Qo'llanma:**\n\n"
            "1. Botga /new yuboring.\n"
            "2. Kitob sarlavhasi va muallifini kiriting.\n"
            "3. O'zingizga yoqqan dizayn (Mavzu)ni tanlang.\n"
            "4. Kitobga qo'shmoqchi bo'lgan rasmlaringizni bittadan yoki bir nechta qilib botga yuboring.\n"
            "5. Boshqaruv paneli orqali har bir rasm ostiga izoh yozishingiz, muqova rasmini tanlashingiz mumkin.\n"
            "6. Tayyor bo'lgach, **'PDF Kitobni yaratish'** tugmasini bosing va bot sizga kitobingizni yuboradi."
        )
        markup = types.InlineKeyboardMarkup()
        btn_back = types.InlineKeyboardButton("⬅️ Bosh sahifa", callback_data="back_welcome")
        markup.add(btn_back)
        bot.edit_message_text(help_text, chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    elif data == "back_welcome":
        welcome_text = (
            "👋 **Assalomu alaykum!**\n\n"
            "**Kitob PDF Yaratuvchi Bot**ga xush kelibsiz! 📚✨\n\n"
            "Kitob yaratishni boshlash uchun quyidagi **🆕 Yangi kitob yaratish** tugmasini bosing yoki /new buyrug'ini yuboring."
        )
        markup = types.InlineKeyboardMarkup()
        btn_new = types.InlineKeyboardButton("🆕 Yangi kitob yaratish", callback_data="start_new")
        btn_help = types.InlineKeyboardButton("ℹ️ Yo'riqnoma", callback_data="help_info")
        markup.row(btn_new)
        markup.row(btn_help)
        bot.edit_message_text(welcome_text, chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    elif data.startswith("theme_"):
        theme_name = data.split("_")[1]
        session['theme'] = theme_name
        session['state'] = 'collecting'
        send_control_panel(chat_id, call.message.message_id)

    elif data == "back_to_panel":
        session['state'] = 'collecting'
        send_control_panel(chat_id, call.message.message_id)

    elif data == "edit_captions_menu":
        if not session['photos']:
            bot.answer_callback_query(call.id, "⚠️ Hali rasmlar yuklanmagan!", show_alert=True)
            return
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        for idx, p in enumerate(session['photos']):
            cap = p['caption'] or "Izohsiz"
            markup.add(types.InlineKeyboardButton(f"📸 {idx+1}-rasm: {cap[:15]}...", callback_data=f"editcap_{idx}"))
        markup.add(types.InlineKeyboardButton("⬅️ Orqaga", callback_data="back_to_panel"))
        
        bot.edit_message_text(
            "✍️ Qaysi rasmning izohini o'zgartirmoqchisiz? Tanlang:", 
            chat_id, 
            call.message.message_id, 
            reply_markup=markup
        )

    elif data.startswith("editcap_"):
        idx = int(data.split("_")[1])
        session['state'] = 'waiting_caption'
        session['edit_index'] = idx
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⬅️ Orqaga", callback_data="edit_captions_menu"))
        
        bot.edit_message_text(
            f"✍️ **{idx+1}-rasm uchun izoh matnini yuboring:**\n"
            f"*(Hozirgi izoh: '{session['photos'][idx]['caption']}')*\n\n"
            "O'chirish uchun /skip deb yozing.",
            chat_id, 
            call.message.message_id, 
            parse_mode="Markdown",
            reply_markup=markup
        )

    elif data == "select_cover_menu":
        if not session['photos']:
            bot.answer_callback_query(call.id, "⚠️ Hali rasmlar yuklanmagan!", show_alert=True)
            return

        markup = types.InlineKeyboardMarkup(row_width=2)
        for idx in range(len(session['photos'])):
            prefix = "✅ " if session['cover_index'] == idx else ""
            markup.add(types.InlineKeyboardButton(f"{prefix}📸 {idx+1}-rasm", callback_data=f"setcover_{idx}"))
        
        prefix_none = "✅ " if session['cover_index'] == -1 else ""
        markup.add(types.InlineKeyboardButton(f"{prefix_none}🚫 Muqovasiz (Faqat matn)", callback_data="setcover_-1"))
        markup.add(types.InlineKeyboardButton("⬅️ Orqaga", callback_data="back_to_panel"))

        bot.edit_message_text(
            "🖼 **Kitob muqovasi (Bosh sahifa) uchun rasmni tanlang:**",
            chat_id, 
            call.message.message_id, 
            parse_mode="Markdown",
            reply_markup=markup
        )

    elif data.startswith("setcover_"):
        idx = int(data.split("_")[1])
        session['cover_index'] = idx
        bot.answer_callback_query(call.id, "Muqova rasmi o'rnatildi! 👍")
        send_control_panel(chat_id, call.message.message_id)

    elif data == "generate_pdf":
        if not session['photos']:
            bot.answer_callback_query(call.id, "⚠️ Iltimos, kamida 1 ta rasm yuklang!", show_alert=True)
            return

        loading_msg = bot.send_message(chat_id, "⏳ **Kitobingiz tayyorlanmoqda, iltimos kuting...**", parse_mode="Markdown")
        
        try:
            pdf_path = generate_pdf(chat_id, session)
            
            with open(pdf_path, 'rb') as pdf_file:
                # Beautiful summary
                theme_uz = "Klassik 🏛" if session['theme'] == 'classic' else "Zamonaviy 📱" if session['theme'] == 'modern' else "Quvnoq 🎨"
                caption = (
                    "🎉 **Kitobingiz muvaffaqiyatli yaratildi!**\n\n"
                    f"📖 **Nomi:** {session['title']}\n"
                    f"✍️ **Muallif:** {session['author']}\n"
                    f"🎨 **Mavzu:** {theme_uz}\n"
                    f"📄 **Sahifalar:** {len(session['photos']) + 1} ta\n\n"
                    "Kitobingizni o'qib zavqlaning! 📚"
                )
                
                bot.send_document(
                    chat_id, 
                    pdf_file, 
                    caption=caption, 
                    parse_mode="Markdown",
                    visible_file_name=f"{session['title']}.pdf"
                )
            
            # Clean up user temp space and session
            bot.delete_message(chat_id, loading_msg.message_id)
            clear_session(chat_id)
            
            # Show finish button
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🆕 Yangi kitob yaratish", callback_data="start_new"))
            bot.send_message(chat_id, "Yana yangi kitob yaratmoqchimisiz? 👇", reply_markup=markup)
            
        except Exception as e:
            bot.delete_message(chat_id, loading_msg.message_id)
            bot.send_message(chat_id, f"❌ **Afsuski kitobni yaratishda xatolik yuz berdi:**\n{e}", parse_mode="Markdown")
            print(f"Error compiling PDF: {e}")

    elif data == "cancel_book":
        clear_session(chat_id)
        bot.edit_message_text(
            "❌ Jarayon bekor qilindi. Boshlash uchun /new buyrug'ini bosing.", 
            chat_id, 
            call.message.message_id
        )

@bot.message_handler(content_types=['text'])
def handle_text(message):
    chat_id = message.chat.id
    session = get_session(chat_id)
    state = session['state']
    text = message.text.strip()

    if state == 'waiting_title':
        if not text:
            bot.send_message(chat_id, "⚠️ Iltimos, kitob sarlavhasini matn ko'rinishida yuboring.")
            return
        
        session['title'] = text
        session['state'] = 'waiting_author'
        
        markup = types.InlineKeyboardMarkup()
        btn_cancel = types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_book")
        markup.add(btn_cancel)
        
        bot.send_message(
            chat_id, 
            f"Sarlavha: **{text}** ✅\n\n✍️ **2-qadam: Muallif ismini (ismingizni) yozing:**",
            parse_mode="Markdown",
            reply_markup=markup
        )

    elif state == 'waiting_author':
        if not text:
            bot.send_message(chat_id, "⚠️ Iltimos, muallif ismini yozib yuboring.")
            return

        session['author'] = text
        session['state'] = 'waiting_theme'

        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("🏛 Klassik (Classic)", callback_data="theme_classic"),
            types.InlineKeyboardButton("📱 Zamonaviy (Modern)", callback_data="theme_modern")
        )
        markup.row(
            types.InlineKeyboardButton("🎨 Quvnoq (Playful)", callback_data="theme_playful")
        )
        markup.row(
            types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_book")
        )

        bot.send_message(
            chat_id,
            f"Muallif: **{text}** ✅\n\n🎨 **3-qadam: Kitob dizaynini (Mavzusini) tanlang:**",
            parse_mode="Markdown",
            reply_markup=markup
        )

    elif state == 'waiting_caption':
        idx = session['edit_index']
        if text.lower() == '/skip':
            session['photos'][idx]['caption'] = ""
            bot.send_message(chat_id, f"✅ {idx+1}-rasm izohi o'chirildi.")
        else:
            session['photos'][idx]['caption'] = text
            bot.send_message(chat_id, f"✅ {idx+1}-rasm izohi saqlandi!")

        session['state'] = 'collecting'
        session['edit_index'] = -1
        send_control_panel(chat_id)

    else:
        # Default fallback
        bot.send_message(
            chat_id, 
            "Iltimos, yangi kitob yaratish uchun /new buyrug'ini bosing yoki quyidagi yo'riqnomani ko'ring.",
            reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("ℹ️ Yo'riqnoma", callback_data="help_info"))
        )

@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    chat_id = message.chat.id
    session = get_session(chat_id)
    
    # If the user has not initialized a book, ask them to do so
    if session['state'] == 'idle' or not session['title']:
        bot.send_message(
            chat_id, 
            "⚠️ Avval kitob tafsilotlarini kiriting! Yangi kitob yaratish uchun /new buyrug'ini bosing."
        )
        return

    # Check state - if they are in setup, tell them to complete setup first
    if session['state'] in ['waiting_title', 'waiting_author', 'waiting_theme']:
        bot.send_message(
            chat_id,
            "⚠️ Iltimos, oldin kitob nomi, muallif va dizaynni tanlang! So'ngra rasmlar yuklaysiz."
        )
        return

    try:
        # Get the largest available photo version
        photo_info = message.photo[-1]
        file_info = bot.get_file(photo_info.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        user_dir = os.path.join(TEMP_DIR, str(chat_id))
        os.makedirs(user_dir, exist_ok=True)
        
        # Unique local file path
        photo_index = len(session['photos'])
        local_path = os.path.join(user_dir, f"photo_{photo_index}_{int(time.time())}.jpg")
        
        with open(local_path, 'wb') as f:
            f.write(downloaded_file)

        # Store photo info
        session['photos'].append({
            'path': local_path,
            'caption': '',
            'file_id': photo_info.file_id
        })

        # By default, set the first uploaded image as the cover image
        if session['cover_index'] == -1:
            session['cover_index'] = 0

        # Notify user (silently using message replacement if possible, or new message)
        bot.send_message(
            chat_id, 
            f"📸 **{photo_index+1}-rasm qabul qilindi!**", 
            parse_mode="Markdown"
        )
        
        # Show updated control panel
        send_control_panel(chat_id)

    except Exception as e:
        bot.send_message(chat_id, f"❌ Rasm yuklashda xatolik yuz berdi: {e}")
        print(f"Error handling photo: {e}")

def send_control_panel(chat_id, edit_message_id=None):
    """Sends or edits the primary book creation control panel."""
    session = get_session(chat_id)
    photos = session['photos']
    
    theme_uz = "Klassik 🏛" if session['theme'] == 'classic' else "Zamonaviy 📱" if session['theme'] == 'modern' else "Quvnoq 🎨"
    
    # Compile photo preview list
    photo_list_text = ""
    if photos:
        photo_list_text = "🖼 **Yuklangan rasmlar va izohlar:**\n"
        for idx, p in enumerate(photos):
            cap = p['caption'] or "Izoh yozilmagan ✍️"
            cover_lbl = " 🖼 [MUQOVA]" if session['cover_index'] == idx else ""
            photo_list_text += f"{idx+1}. {cap}{cover_lbl}\n"
    else:
        photo_list_text = "⚠️ *Hali rasmlar yuklanmadi. Rasmlarni botga yuboring!*"

    panel_text = (
        f"📖 **Kitob:** {session['title']}\n"
        f"✍️ **Muallif:** {session['author']}\n"
        f"🎨 **Mavzu:** {theme_uz}\n"
        f"📊 **Yuklangan rasmlar:** {len(photos)} ta\n\n"
        f"{photo_list_text}\n\n"
        "👇 Quyidagi tugmalardan foydalanib kitobingizni sozlang:"
    )

    markup = types.InlineKeyboardMarkup()
    
    if photos:
        btn_caption = types.InlineKeyboardButton("✍️ Izohlarni tahrirlash", callback_data="edit_captions_menu")
        btn_cover = types.InlineKeyboardButton("🖼 Muqova rasmini tanlash", callback_data="select_cover_menu")
        btn_generate = types.InlineKeyboardButton("📚 PDF Kitobni yaratish", callback_data="generate_pdf")
        markup.row(btn_caption, btn_cover)
        markup.row(btn_generate)

    btn_cancel = types.InlineKeyboardButton("❌ Kitobni o'chirish", callback_data="cancel_book")
    markup.row(btn_cancel)

    if edit_message_id:
        try:
            bot.edit_message_text(panel_text, chat_id, edit_message_id, parse_mode="Markdown", reply_markup=markup)
        except Exception:
            # Fallback if content did not change
            bot.send_message(chat_id, panel_text, parse_mode="Markdown", reply_markup=markup)
    else:
        bot.send_message(chat_id, panel_text, parse_mode="Markdown", reply_markup=markup)

if __name__ == '__main__':
    print("Cleaning up older temp directories...")
    cleanup_temp()
    print("Bot muvaffaqiyatli ishga tushdi! Telegram botni sinab ko'ring...")
    bot.infinity_polling()
