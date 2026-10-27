import os
import threading
import requests
import telebot
from flask import Flask
from supabase import create_client, Client

# توكن البوت الخاص بك
TOKEN = "7989116766:AAHuvR5MYs8geGczCWCpAm22Vq8fLa4pnoc"
bot = telebot.TeleBot(TOKEN)

# إعداد Supabase
SUPABASE_URL = "https://jtiuytnovkkvebmlcdme.supabase.co"
# ⚠️ ضع هنا مفتاح الـ Anon/Service_Role الخاص بك في Supabase لتتمكن من الاتصال بجدول المستخدمين
SUPABASE_KEY = "sb_publishable_BWpG4gMKivRFrf8XLTcFZw_nTtfUu2U" 
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# إعداد خادم Flask وهمي لإرضاء Render Web Service المجاني وتجنب مهلة البورتات
app = Flask(__name__)


@app.route("/")
def home():
  return "Bot is running successfully!"


def run_web():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)


# دالة لجلب أو إنشاء بيانات المستخدم في قاعدة البيانات
def get_or_create_user(user_id, referrer_id=None):
  try:
    res = supabase.table("users").select("*").eq("user_id", user_id).execute()
    if res.data and len(res.data) > 0:
      return res.data[0]
    else:
      # مستخدم جديد
      new_user = {
        "user_id": user_id,
        "points": 0,
        "info_free_count": 0,
        "banner_clicked": False
      }
      supabase.table("users").insert(new_user).execute()
      
      # إذا دخل برابط دعوة شخص آخر
      if referrer_id and int(referrer_id) != int(user_id):
        ref_user = supabase.table("users").select("*").eq("user_id", referrer_id).execute()
        if ref_user.data:
          # إضافة 10 نقاط لصاحب الدعوة
          current_pts = ref_user.data[0].get("points", 0)
          supabase.table("users").update({"points": current_pts + 10}).eq("user_id", referrer_id).execute()
          
      return new_user
  except Exception as e:
    print("Database Error:", e)
    return {"user_id": user_id, "points": 10, "info_free_count": 0}

def update_user_field(user_id, fields_dict):
  try:
    supabase.table("users").update(fields_dict).eq("user_id", user_id).execute()
  except Exception as e:
    print("Update Error:", e)


# دالة لتأمين رموز الماركدون لمنع أخطاء التليجرام
def escape_md(val):
  if val is None or val == "ɴ/ᴀ":
    return "ɴ/ᴀ"
  return (
      str(val)
      .replace("_", "\\_")
      .replace("*", "\\*")
      .replace("`", "\\`")
  )


# أمر البداية /start مع دعم نظام الدعوات (Referral)
@bot.message_handler(commands=["start"])
def send_welcome(message):
  user_id = message.from_user.id
  args = message.text.split()
  
  referrer_id = None
  if len(args) > 1:
    try:
      referrer_id = int(args[1])
    except ValueError:
      pass

  get_or_create_user(user_id, referrer_id)
  bot_username = bot.get_me().username
  ref_link = f"https://t.me/{bot_username}?start={user_id}"

  welcome_text = (
      f"ᴡᴇʟᴄᴏᴍᴇ! ʏᴏᴜʀ ʙᴏᴛ ɪs wᴏʀᴋɪɴɢ sᴜᴄᴄᴇssꜰᴜʟʟʏ.\n\n"
      f"🎁 **نظام النقاط والمهام:**\n"
      f"• أضف أصدقاء عبر رابط دعواتك واحصل على **10 نقاط** لكل شخص!\n"
      f"• رابط الدعوة الخاص بك:\n`{ref_link}`\n\n"
      f"ᴛʏᴘᴇ /help ᴛᴏ sᴇᴇ ᴛʜᴇ ᴀᴠᴀɪʟᴀʙʟᴇ ᴄᴏᴍᴍᴀɴᴅs ᴀɴᴅ ʜᴏw ᴛᴏ ᴜsᴇ ᴛʜᴇᴍ."
  )
  
  bot.reply_to(message, welcome_text, parse_mode="Markdown")


# أمر الرصيد /points لمعرفة النقاط
@bot.message_handler(commands=["points", "balance"])
def check_points(message):
  user_id = message.from_user.id
  user_data = get_or_create_user(user_id)
  pts = user_data.get("points", 0)
  
  bot.reply_to(
      message,
      f"💰 **رصيدك الحالي:** `{pts}` نقطة\n\n"
      f"📌 **طرق زيادة النقاط:**\n"
      f"1️⃣ قم بزيارة موقع البانر واضغط عليه مرة للحصول على 10 نقاط عبر أمر: `/banner`\n"
      f"2️⃣ شارك رابط بوتك مع أصدقائك عبر أمر `/start`",
      parse_mode="Markdown"
  )


# أمر مهمة البانر /banner للحصول على 10 نقاط
@bot.message_handler(commands=["banner"])
def banner_task(message):
  user_id = message.from_user.id
  user_data = get_or_create_user(user_id)
  
  if user_data.get("banner_clicked", False):
    bot.reply_to(message, "⚠️ لقد قمت بإتمام مهمة البانر مسبقاً ولا يمكنك تكرارها للحصول على نقاط أخرى.")
    return

  bot.reply_to(
      message,
      "🎯 **مهمة البانر:**\n\n"
      "للحصول على **10 نقاط مجانية**، اضغط على الرابط أدناه وقم بزيارة الموقع والضغط على إعلان البانر مرة واحدة:\n"
      "🔗 https://abdelahidz1-hash.github.io/craftland_01/\n\n"
      "بعد إتمام ذلك، اضغط على الزر أدناه لتأكيد حصولك على النقاط!",
      parse_mode="Markdown",
      reply_markup=telebot.types.InlineKeyboardMarkup([
          [telebot.types.InlineKeyboardButton("✅ تأكيد إتمام المهمة (+10 نقاط)", callback_data="claim_banner")]
      ])
  )


@bot.callback_query_handler(func=lambda call: call.data == "claim_banner")
def claim_banner_callback(call):
  user_id = call.from_user.id
  user_data = get_or_create_user(user_id)
  
  if user_data.get("banner_clicked", False):
    bot.answer_callback_query(call.id, "لقد استلمت مكافأة هذه المهمة مسبقاً!", show_alert=True)
    return

  current_pts = user_data.get("points", 0)
  update_user_field(user_id, {"points": current_pts + 10, "banner_clicked": True})
  
  bot.answer_callback_query(call.id, "🎉 تهانينا! تمت إضافة 10 نقاط إلى رصيدك بنجاح.", show_alert=True)
  bot.edit_message_text(
      "✅ **تم التحقق بنجاح وتمت إضافة 10 نقاط إلى رصيدك!**",
      call.message.chat.id,
      call.message.message_id
  )


# أمر المساعدة /help
@bot.message_handler(commands=["help"])
def send_help(message):
  bot.reply_to(
      message,
      "🤖 **ᴀᴠᴀɪʟᴀʙʟᴇ ᴄᴏᴍᴍᴀɴْدs:**\n"
      "━━━━━━━━━━━━━━━━\n"
      "• **ᴘʟᴀʏᴇʀ ɪɴғᴏ:** `/info <UID>`\n"
      "  *(مجاني أول 3 مرات، ثم يخصم نقطتين)*\n\n"
      "• **sᴇᴀʀᴄʜ by ɴᴀᴍᴇ:** `/search <Name>` أو `/ser <Name>`\n"
      "  *(يكلف نقطتين)*\n\n"
      "• **ᴄʟᴀɴ ɪɴғᴏ:** `/clan <Clan ID>`\n"
      "  *(يكلف نقطتين)*\n\n"
      "• **ʟᴇᴠᴇʟ ɪɴғᴏ:** `/level <UID>`\n"
      "  *(يكلف نقطتين)*\n\n"
      "• **ᴏᴜᴛғɪᴛ ɪɴғᴏ:** `/outfit <UID>`\n"
      "  *(يكلف نقطتين)*\n\n"
      "• **الرصيد والنقاط:** `/points` أو `/banner`\n"
      "━━━━━━━━━━━━━━━━",
      parse_mode="Markdown",
  )


# أمر لجلب البيانات من الـ API عبر إدخال الآي دي الخاص باللاعب (/info) -> مجاني أول 3 مرات ثم يخصم نقطتين
@bot.message_handler(commands=["info"])
def fetch_info(message):
  user_id = message.from_user.id
  user_data = get_or_create_user(user_id)
  free_count = user_data.get("info_free_count", 0)
  current_pts = user_data.get("points", 0)

  # نظام المجاني والخصم
  if free_count < 3:
    update_user_field(user_id, {"info_free_count": free_count + 1})
  else:
    if current_pts < 2:
      bot.reply_to(message, "❌ رصيدك غير كافٍ! لقد استهلكت محاولاتك المجانية الـ 3 لـ /info. يرجى جمع نقاط عبر دعوة أصدقائك أو زيارة البانر عبر `/banner`.")
      return
    update_user_field(user_id, {"points": current_pts - 2})

  args = message.text.split()
  if len(args) > 1:
    uid = args[1]
  else:
    bot.reply_to(
        message,
        "⚠️ ᴘʟᴇᴀsᴇ wʀɪᴛᴇ ᴛʜᴇ ᴜɪᴅ ᴄᴏʀʀᴇᴄᴛʟʏ ɴᴇxᴛ ᴛᴏ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅ.\nᴇxᴀᴍᴘʟᴇ:\n`/info 7876206533`",
        parse_mode="Markdown",
    )
    return

  try:
    r = requests.get(f"http://de26.spaceify.eu:26080/info?uid={uid}", timeout=20)

    if r.status_code == 200:
      data = r.json()

      def get_val(*keys):
        def search_dict(d):
          if not isinstance(d, dict):
            return None
          for k in keys:
            if k in d and d[k] is not None:
              return d[k]
          for k, v in d.items():
            if isinstance(v, dict):
              res = search_dict(v)
              if res is not None:
                return res
          return None

        val = search_dict(data)
        return val if val is not None else "ɴ/ᴀ"

      name = escape_md(get_val("name", "nickname", "AccountName", "userName", "accountName"))
      level = get_val("level", "AccountLevel", "lvl", "accountLevel")
      uid_val = get_val("uid", "accountId", "account_id") or uid
      exp = get_val("exp", "AccountExp", "experience", "accountExp", "currentExp")
      likes = get_val("likes", "AccountLikes", "like", "accountLikes", "liked", "counter")
      region = get_val("region", "AccountRegion", "server", "accountRegion")

      banner_url = "https://i.ibb.co/MyNThqFz/1793135688578.jpg"

      text = (
          f"👤 **ᴘʟᴀʏᴇʀ ɪɴғᴏʀᴍᴀᴛɪᴏɴ:**\n"
          f"━━━━━━━━━━━━━━━━\n"
          f"• **ɴᴀᴍᴇ:** {name}\n"
          f"• **ᴜɪᴅ:** `{uid_val}`\n"
          f"• **ʟᴇᴠᴇʟ:** {level}\n"
          f"• **ᴇxᴘ:** {exp}\n"
          f"• **ʟɪᴋᴇs:** {likes}\n"
          f"• **ʀᴇɢɪᴏɴ:** {region}\n"
          f"━━━━━━━━━━━━━━━━"
      )

      try:
        bot.send_photo(
            message.chat.id,
            banner_url,
            caption=text,
            parse_mode="Markdown",
            reply_to_message_id=message.message_id,
        )
      except Exception:
        bot.reply_to(message, text, parse_mode="Markdown")

    else:
      bot.reply_to(message, f"sᴏʀʀʏ, ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ wɪᴛʜ sᴛᴀᴛᴜs ᴄᴏᴅᴇ: {r.status_code}")

  except requests.exceptions.RequestException as e:
    bot.reply_to(message, f"ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ wʜɪʟᴇ ᴄᴏɴɴᴇᴄᴛɪɴɢ ᴛᴏ ᴛʜᴇ sᴇʀᴠᴇʀ:\n{e}")


# دالة مساعدة لخصم نقطتين لأي أمر مدفوع (search, level, clan, outfit)
def check_and_deduct_points(message):
  user_id = message.from_user.id
  user_data = get_or_create_user(user_id)
  current_pts = user_data.get("points", 0)

  if current_pts < 2:
    bot.reply_to(message, "❌ رصيدك غير كافٍ! تحتاج إلى **نقطتين** على الأقل لاستخدام هذا الأمر.\nيمكنك جمع النقاط عبر زيارة البانر `/banner` أو دعوة أصدقائك عبر `/start`.")
    return False

  update_user_field(user_id, {"points": current_pts - 2})
  return True


# أمر للبحث عن اللاعبين باستخدام اسم اللاعب (/search أو /ser) -> يخصم نقطتين
@bot.message_handler(commands=["search", "ser"])
def search_player(message):
  if not check_and_deduct_points(message):
    return

  args = message.text.split(maxsplit=1)
  if len(args) > 1:
    player_name = args[1]
  else:
    bot.reply_to(
        message,
        "⚠️ ᴘʟᴇᴀsᴇ wʀɪᴛᴇ ᴛʜᴇ ɴᴀᴍᴇ ᴄᴏʀʀᴇᴄᴛʟʏ ɴᴇxᴛ ᴛᴏ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅ.\nᴇxᴀᴍᴘʟᴇ:\n`/search xMaSrY`",
        parse_mode="Markdown",
    )
    return

  try:
    r = requests.get(
        "http://de26.spaceify.eu:26080/ser",
        params={"name": player_name},
        timeout=20,
    )

    if r.status_code == 200:
      data = r.json()
      results = data if isinstance(data, list) else []
      if not results and isinstance(data, dict):
        for k, v in data.items():
          if isinstance(v, list):
            results = v
            break

      if not results:
        bot.reply_to(message, "❌ ɴᴏ ᴘʟᴀʏᴇʀs ғᴏᴜɴᴅ wɪᴛʜ ᴛʜɪs ɴᴀᴍᴇ.")
        return

      text = f"🔍 **sᴇᴀʀᴄʜ ʀᴇsᴜʟᴛs ғᴏʀ:** `{player_name}`\n━━━━━━━━━━━━━━━━\n"
      for i, player in enumerate(results[:10], 1):
        if isinstance(player, dict):
          p_name = player.get("name", "ɴ/ᴀ")
          p_uid = player.get("uid", "ɴ/ᴀ")
          p_lvl = player.get("level", "ɴ/ᴀ")
          text += f"• **{i}.** {p_name} | UID: `{p_uid}` | Lvl: {p_lvl}\n"

      text += "━━━━━━━━━━━━━━━━"
      bot.reply_to(message, text, parse_mode="Markdown", reply_to_message_id=message.message_id)
    else:
      bot.reply_to(message, f"sᴏʀʀʏ, ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ wɪᴛʜ sᴛᴀᴛᴜs ᴄᴏᴅᴇ: {r.status_code}")
  except requests.exceptions.RequestException as e:
    bot.reply_to(message, f"ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ wʜɪʟᴇ ᴄᴏɴɴᴇᴄᴛɪɴɢ ᴛᴏ ᴛʜᴇ sᴇʀᴠᴇʀ:\n{e}")


# أمر لجلب بيانات المستوى (Level) -> يخصم نقطتين
@bot.message_handler(commands=["level"])
def fetch_level(message):
  if not check_and_deduct_points(message):
    return

  args = message.text.split()
  if len(args) > 1:
    uid = args[1]
  else:
    bot.reply_to(message, "⚠️ ᴘʟᴇᴀsᴇ wʀɪᴛᴇ ᴛʜᴇ ᴜɪᴅ ᴄᴏʀʀᴇᴄᴛʟʏ.\nᴇxᴀᴍᴘʟᴇ:\n`/level 4485827054`", parse_mode="Markdown")
    return

  try:
    r = requests.get("http://de26.spaceify.eu:26080/level", params={"uid": uid}, timeout=20)
    if r.status_code == 200:
      data = r.json()
      name = data.get("name", "ɴ/ᴀ")
      level_val = data.get("level", "ɴ/ᴀ")
      text = (
          f"📊 **ᴘʟᴀʏᴇʀ ʟᴇᴠᴇʟ ɪɴғᴏʀᴍᴀᴛɪᴏɴ:**\n"
          f"━━━━━━━━━━━━━━━━\n"
          f"• **ɴᴀᴍᴇ:** {name}\n"
          f"• **ᴜɪᴅ:** `{uid}`\n"
          f"• **ʟᴇᴠᴇʟ:** {level_val}\n"
          f"━━━━━━━━━━━━━━━━"
      )
      bot.reply_to(message, text, parse_mode="Markdown", reply_to_message_id=message.message_id)
    else:
      bot.reply_to(message, f"sᴏʀʀʏ, ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ wɪᴛʜ sᴛᴀᴛᴜs ᴄᴏᴅᴇ: {r.status_code}")
  except requests.exceptions.RequestException as e:
    bot.reply_to(message, f"ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ wʜɪʟᴇ ᴄᴏɴɴᴇᴄᴛɪɴɢ ᴛᴏ ᴛʜᴇ sᴇʀᴠᴇʀ:\n{e}")


# أمر لجلب بيانات الكلأن (Guild/Clan) -> يخصم نقطتين
@bot.message_handler(commands=["clan"])
def fetch_clan(message):
  if not check_and_deduct_points(message):
    return

  args = message.text.split()
  if len(args) > 1:
    clan_id = args[1]
  else:
    bot.reply_to(message, "⚠️ ᴘʟᴇᴀsᴇ wʀɪᴛᴇ ᴛʜᴇ ᴄʟᴀɴ ɪᴅ ᴄᴏʀʀᴇᴄᴛʟʏ.\nᴇxᴀᴍᴘʟᴇ:\n`/clan 30512345`", parse_mode="Markdown")
    return

  try:
    r = requests.get("http://de26.spaceify.eu:26080/clan", params={"clan_id": clan_id}, timeout=20)
    if r.status_code == 200:
      data = r.json()
      clan_name = data.get("clanName", "ɴ/ᴀ")
      clan_level = data.get("clanLevel", "ɴ/ᴀ")
      member_count = data.get("memberCount", "ɴ/ᴀ")
      max_members = data.get("maxMembers", "ɴ/ᴀ")
      leader_name = data.get("leaderName", "ɴ/ᴀ")

      text = (
          f"🛡️ **ᴄʟᴀɴ ɪɴғᴏʀᴍᴀᴛɪᴏɴ:**\n"
          f"━━━━━━━━━━━━━━━━\n"
          f"• **ɴᴀᴍᴇ:** {clan_name}\n"
          f"• **ᴄʟᴀɴ ɪᴅ:** `{clan_id}`\n"
          f"• **ʟᴇᴠᴇʟ:** {clan_level}\n"
          f"• **ᴍᴇᴍʙᴇʀs:** {member_count}/{max_members}\n"
          f"• **ʟᴇᴀᴅᴇʀ:** {leader_name}\n"
          f"━━━━━━━━━━━━━━━━"
      )
      bot.reply_to(message, text, parse_mode="Markdown", reply_to_message_id=message.message_id)
    else:
      bot.reply_to(message, f"sᴏʀʀʏ, ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ wɪᴛʜ sᴛᴀᴛᴜs ᴄᴏᴅᴇ: {r.status_code}")
  except requests.exceptions.RequestException as e:
    bot.reply_to(message, f"ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ wʜɪʟᴇ ᴄᴏɴɴᴇᴄᴛɪɴɢ ᴛᴏ ᴛʜᴇ sᴇʀᴠᴇʀ:\n{e}")


# أمر لجلب مظهر / ملابس اللاعب (Outfit) -> يخصم نقطتين
@bot.message_handler(commands=["outfit"])
def fetch_outfit(message):
  if not check_and_deduct_points(message):
    return

  args = message.text.split()
  if len(args) > 1:
    uid = args[1]
  else:
    bot.reply_to(message, "⚠️ ᴘʟᴇᴀsᴇ wʀɪᴛᴇ ᴛʜᴇ ᴜɪᴅ ᴄᴏʀʀᴇᴄᴛʟʏ.\nᴇxᴀᴍᴘʟᴇ:\n`/outfit 4485827054`", parse_mode="Markdown")
    return

  wait_msg = bot.reply_to(message, "⏳ جاري جلب صورة المظهر، يرجى الانتظار...", parse_mode="Markdown")

  try:
    r = requests.get("http://de26.spaceify.eu:26080/outfit", params={"uid": uid}, timeout=45)
    if r.status_code == 200:
      open("outfit.png", "wb").write(r.content)
      try:
        bot.send_photo(
            message.chat.id,
            open("outfit.png", "rb"),
            caption=f"👕 **ᴘʟᴀʏᴇʀ ᴏᴜᴛғɪᴛ ɪɴғᴏ:**\n━━━━━━━━━━━━━━━━\n• **ᴜɪᴅ:** `{uid}`\n━━━━━━━━━━━━━━━━",
            parse_mode="Markdown",
            reply_to_message_id=message.message_id,
        )
        bot.delete_message(message.chat.id, wait_msg.message_id)
      except Exception:
        bot.edit_message_text("✅ ᴛʜᴇ ᴏᴜᴛғɪᴛ ɪᴍᴀɢᴇ wᴀs sᴀᴠᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ.", message.chat.id, wait_msg.message_id)
    else:
      bot.edit_message_text(f"sᴏʀʀʏ, ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ wɪᴛʜ sᴛᴀട്ടus ᴄᴏᴅᴇ: {r.status_code}", message.chat.id, wait_msg.message_id)
  except requests.exceptions.Timeout:
    bot.edit_message_text("⏱️ انتهت مهلة الانتظار، الخادم بطيء حالياً.", message.chat.id, wait_msg.message_id)
  except requests.exceptions.RequestException as e:
    bot.edit_message_text(f"ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ:\n{e}", message.chat.id, wait_msg.message_id)


# تشغيل البوت باستمرار مع خادم الويب في الخلفية
if __name__ == "__main__":
  print("جاري تشغيل خادم الويب وبوت التليجرام...")

  t = threading.Thread(target=run_web)
  t.daemon = True
  t.start()

  bot.remove_webhook()
  print("البوت قيد التشغيل الآن مع نظام النقاط والمهام...")
  bot.infinity_polling()
