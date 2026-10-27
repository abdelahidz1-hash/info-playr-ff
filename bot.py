import os
import threading
import requests
import telebot
from flask import Flask

# توكن البوت الخاص بك
TOKEN = "7989116766:AAHuvR5MYs8geGczCWCpAm22Vq8fLa4pnoc"
bot = telebot.TeleBot(TOKEN)

# إعداد خادم Flask وهمي لإرضاء Render Web Service المجاني وتجنب مهلة البورتات
app = Flask(__name__)

# إعدادات Supabase
SUPABASE_URL = "https://jtiuytnovkkvebmlcdme.supabase.co"
# ملاحظة: يفضل وضع مفتاح الـ Anon Key أو Service Role الخاص بك هنا للتعامل مع جدول المستخدمين
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "YOUR_SUPABASE_KEY_HERE")
SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

@app.route("/")
def home():
  return "Bot is running successfully!"


def run_web():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)


# قائمة معرفات البانرات المعتمدة الفارغة
VALID_BANNERS = set()


# دوال مساعدة للتعامل مع قاعدة بيانات Supabase (النقاط والأوامر المجانية)
def get_user_data(user_id):
  try:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/users?user_id=eq.{user_id}", headers=SUPABASE_HEADERS, timeout=10)
    if r.status_code == 200 and r.json():
      return r.json()[0]
  except Exception as e:
    print("Error fetching user:", e)
  return None

def create_or_update_user(user_id, data):
  try:
    existing = get_user_data(user_id)
    if existing:
      requests.patch(f"{SUPABASE_URL}/rest/v1/users?user_id=eq.{user_id}", json=data, headers=SUPABASE_HEADERS, timeout=10)
    else:
      data["user_id"] = user_id
      requests.post(f"{SUPABASE_URL}/rest/v1/users", json=data, headers=SUPabase_HEADERS, timeout=10)
  except Exception as e:
    print("Error updating user:", e)

def check_and_deduct(message, cost=2, is_info=False):
  user_id = message.from_user.id
  user = get_user_data(user_id)
  
  if not user:
    # إنشاء مستخدم جديد برصيد 0 و 3 محاولات مجانية لـ info
    user = {"user_id": user_id, "points": 0, "info_free_count": 0}
    create_or_update_user(user_id, user)
  
  info_free_count = user.get("info_free_count", 0)
  points = user.get("points", 0)
  
  if is_info and info_free_count < 3:
    # استخدام مجاني ضمن الثلاث مرات الأولى
    new_free_count = info_free_count + 1
    create_or_update_user(user_id, {"info_free_count": new_free_count})
    return True, f"🎁 تم استهلاك المحاولة المجانية ({new_free_count}/3) لأمر /info."
  
  # إذا انتهت المحاولات المجانية لـ info أو لأي أمر آخر، يتم خصم نقاط
  if points >= cost:
    new_points = points - cost
    create_or_update_user(user_id, {"points": new_points})
    return True, f"💳 تم خصم {cost} نقاط. رصيدك الحالي: {new_points} نقطة."
  else:
    return False, f"❌ رصيدك غير كافٍ! تحتاج إلى {cost} نقاط لاستخدام هذا الأمر.\n💡 للحصول على النقاط:\n1️⃣ اضغط على إعلان البانر وحل المهمة للحصول على 10 نقاط.\n2️⃣ شارك رابط الدعوة الخاص بك للحصول على 10 نقاط عند انضمام صديق."


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
  
  # التحقق من وجود مستخدم دعي عبر رابط (Referral)
  if len(args) > 1:
    referrer_id = args[1]
    if referrer_id.isdigit() and int(referrer_id) != user_id:
      # التحقق إن كان المستخدم الجديد مسجلاً من قبل أم لا
      existing_user = get_user_data(user_id)
      if not existing_user:
        # تسجيل المستخدم الجديد وإعطاء نقاط لصاحب الدعوة
        create_or_update_user(user_id, {"points": 0, "info_free_count": 0, "invited_by": int(referrer_id)})
        
        # إضافة 10 نقاط لصاحب الرابط (المُحيل)
        ref_user = get_user_data(int(referrer_id))
        if ref_user:
          ref_points = ref_user.get("points", 0) + 10
          create_or_update_user(int(referrer_id), {"points": ref_points})
          try:
            bot.send_message(int(referrer_id), f"🎉 مبروك! دخل شخص جديد عبر رابط الدعوة الخاص بك وتم التحقق منه، وحصلت على **10 نقاط**! رصيدك الحالي: {ref_points}", parse_mode="Markdown")
          except:
            pass

  # التأكد من تسجيل المستخدم الأساسي إذا لم يكن موجوداً
  if not get_user_data(user_id):
    create_or_update_user(user_id, {"points": 0, "info_free_count": 0})

  bot_username = bot.get_me().username
  ref_link = f"https://t.me/{bot_username}?start={user_id}"

  welcome_text = (
      "ᴡᴇʟᴄᴏᴍᴇ! ʏᴏᴜʀ ʙᴏᴛ ɪs wᴏʀᴋɪɴɢ sᴜᴄᴄᴇssꜰᴜʟʟʏ.\n\n"
      f"🔗 **رابط الدعوة الخاص بك:**\n`{ref_link}`\n"
      "شارك الرابط مع أصدقائك، واكسب **10 نقاط** عن كل شخص يدخل من خلاله!\n\n"
      "🎯 **كيف تحصل على النقاط؟**\n"
      "1️⃣ اضغط على زر (إعلان البانر) أدناه واضغط عليه مرة واحدة لحصد **10 نقاط**.\n"
      "2️⃣ شارك رابط البوت مع أصدقائك.\n\n"
      "ᴛʏᴘᴇ /help ᴛᴏ sᴇᴇ ᴛʜᴇ ᴀᴠᴀɪʟᴀʙʟᴇ ᴄᴏᴍᴍᴀɴᴅs."
  )

  # إنشاء أزرار تفاعلية (بانر إعلاني + زر النقاط)
  markup = telebot.types.InlineKeyboardMarkup()
  markup.add(telebot.types.InlineKeyboardButton("📢 اضغط هنا للإعلان والحصول على 10 نقاط", url="https://jtiuytnovkkvebmlcdme.supabase.co"))
  markup.add(telebot.types.InlineKeyboardButton("💰 رصيدي ونقاطي", callback_data="my_points"))

  bot.reply_to(message, welcome_text, parse_mode="Markdown", reply_main_markup=None, reply_markup=markup)


# زر استعلام النقاط عبر الـ Callback
@bot.callback_query_handler(func=lambda call: call.data == "my_points")
def callback_points(call):
  user_id = call.from_user.id
  user = get_user_data(user_id)
  points = user.get("points", 0) if user else 0
  info_free = user.get("info_free_count", 0) if user else 0
  
  bot.answer_callback_query(call.id, f"رصيدك الحالي: {points} نقطة\nمحاولات /info المجانية المستهلكة: {info_free}/3", show_alert=True)


# أمر المساعدة /help
@bot.message_handler(commands=["help"])
def send_help(message):
  bot.reply_to(
      message,
      "🤖 **ᴀᴠᴀɪʟᴀʙʟᴇ ᴄᴏᴍᴍᴀɴْدs:**\n"
      "━━━━━━━━━━━━━━━━\n"
      "• **ᴘʟᴀʏᴇʀ ɪɴғᴏ:** `/info <UID>` (أول 3 مرات مجاناً ثم خصم نقطتين)\n"
      "• **sᴇᴀʀᴄʜ by ɴᴀᴍᴇ:** `/search <Name>` أو `/ser <Name>` (خصم نقطتين)\n"
      "• **ᴄʟᴀɴ ɪɴғᴏ:** `/clan <Clan ID>` (خصم نقطتين)\n"
      "• **ʟᴇᴠᴇʟ ɪɴғᴏ:** `/level <UID>` (خصم نقطتين)\n"
      "• **ᴏᴜᴛғɪᴛ ɪɴғᴏ:** `/outfit <UID>` (خصم نقطتين)\n"
      "━━━━━━━━━━━━━━━━",
      parse_mode="Markdown",
  )


# أمر لجلب البيانات من الـ API عبر إدخال الآي دي الخاص باللاعب
@bot.message_handler(commands=["info"])
def fetch_info(message):
  allowed, msg = check_and_deduct(message, cost=2, is_info=True)
  if not allowed:
    bot.reply_to(message, msg, parse_mode="Markdown")
    return

  args = message.text.split()
  if len(args) > 1:
    uid = args[1]
  else:
    bot.reply_to(
        message,
        "⚠️ ᴘʟᴇᴀsᴇ wʀɪᴛᴇ ᴛʜᴇ ᴜɪᴅ ᴄᴏʀʀᴇᴄᴛʟʏ ɴᴇxᴛ ᴛᴏ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅ.\nᴇxᴀᴍᴘʟᴇ:\n`/info"
        " 7876206533`",
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

      name = escape_md(
          get_val("name", "nickname", "AccountName", "userName", "accountName")
      )
      level = get_val("level", "AccountLevel", "lvl", "accountLevel")
      uid_val = get_val("uid", "accountId", "account_id") or uid
      exp = get_val(
          "exp", "AccountExp", "experience", "accountExp", "currentExp"
      )
      likes = get_val(
          "likes", "AccountLikes", "like", "accountLikes", "liked", "counter"
      )
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
          f"━━━━━━━━━━━━━━━━\n\n"
          f"ℹ️ _{msg}_"
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
      bot.reply_to(
          message, f"sᴏʀʀʏ, ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ wɪᴛʜ sᴛᴀᴛᴜs ᴄᴏᴅᴇ: {r.status_code}"
      )

  except requests.exceptions.RequestException as e:
    bot.reply_to(
        message, f"ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ wʜɪʟᴇ ᴄᴏɴɴᴇᴄᴛɪɴɢ ᴛᴏ ᴛʜᴇ sᴇʀᴠᴇʀ:\n{e}"
    )


# أمر للبحث عن اللاعبين باستخدام اسم اللاعب (/search أو /ser)
@bot.message_handler(commands=["search", "ser"])
def search_player(message):
  allowed, msg = check_and_deduct(message, cost=2, is_info=False)
  if not allowed:
    bot.reply_to(message, msg, parse_mode="Markdown")
    return

  args = message.text.split(maxsplit=1)
  if len(args) > 1:
    player_name = args[1]
  else:
    bot.reply_to(
        message,
        "⚠️ ᴘʟᴇᴀsᴇ wʀɪᴛᴇ ᴛʜᴇ ɴᴀᴍᴇ ᴄᴏʀʀᴇᴄᴛʟʏ ɴᴇxᴛ ᴛᴏ ᴛʜᴇ"
        " ᴄᴏᴍᴍᴀɴᴅ.\nᴇxᴀᴍᴘʟᴇ:\n`/search xMaSrY`",
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

      results = []
      if isinstance(data, list):
        results = data
      elif isinstance(data, dict):
        for k, v in data.items():
          if isinstance(v, list):
            results = v
            break
        if not results:
          results = [data]

      if not results:
        bot.reply_to(message, "❌ ɴᴏ ᴘʟᴀʏᴇʀs ғᴏᴜɴᴅ wɪᴛʜ ᴛʜɪs ɴᴀᴍᴇ.")
        return

      text = (
          f"🔍 **sᴇᴀʀᴄʜ ʀᴇsᴜʟᴛs ғᴏʀ:** `{player_name}`\n━━━━━━━━━━━━━━━━\n"
      )
      for i, player in enumerate(results[:10], 1):
        if isinstance(player, dict):

          def get_p_val(*keys):
            for k in keys:
              if k in player and player[k] is not None:
                return player[k]
            return "ɴ/ᴀ"

          p_name = get_p_val("name", "nickname", "AccountName", "userName")
          p_uid = get_p_val("uid", "accountId", "account_id")
          p_lvl = get_p_val("level", "AccountLevel", "lvl")
          text += f"• **{i}.** {p_name} | UID: `{p_uid}` | Lvl: {p_lvl}\n"
        else:
          text += f"• **{i}.** {player}\n"

      text += f"━━━━━━━━━━━━━━━━\nℹ️ _{msg}_"
      bot.reply_to(
          message,
          text,
          parse_mode="Markdown",
          reply_to_message_id=message.message_id,
      )

    else:
      bot.reply_to(
          message, f"sᴏʀʀʏ, ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ wɪᴛʜ sᴛᴀᴛᴜs ᴄᴏᴅᴇ: {r.status_code}"
      )

  except requests.exceptions.RequestException as e:
    bot.reply_to(
        message, f"ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ wʜɪʟᴇ ᴄᴏɴɴᴇᴄᴛɪɴɢ ᴛᴏ ᴛʜᴇ sᴇʀᴠᴇʀ:\n{e}"
    )


# أمر لجلب بيانات المستوى (Level) عبر إدخال الآي دي الخاص باللاعب
@bot.message_handler(commands=["level"])
def fetch_level(message):
  allowed, msg = check_and_deduct(message, cost=2, is_info=False)
  if not allowed:
    bot.reply_to(message, msg, parse_mode="Markdown")
    return

  args = message.text.split()
  if len(args) > 1:
    uid = args[1]
  else:
    bot.reply_to(
        message,
        "⚠️ ᴘʟᴇᴀsᴇ wʀɪᴛᴇ ᴛʜᴇ ᴜɪᴅ ᴄᴏʀʀᴇᴄᴛʟʏ ɴᴇxᴛ ᴛᴏ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅ.\nᴇxᴀᴍᴘʟᴇ:\n`/level"
        " 4485827054`",
        parse_mode="Markdown",
    )
    return

  try:
    r = requests.get(
        "http://de26.spaceify.eu:26080/level", params={"uid": uid}, timeout=20
    )

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

      name = get_val(
          "name", "nickname", "AccountName", "userName", "accountName"
      )
      level_val = get_val("level", "AccountLevel", "lvl", "accountLevel")
      uid_val = get_val("uid", "accountId", "account_id") or uid

      text = (
          f"📊 **ᴘʟᴀʏᴇʀ ʟᴇᴠᴇʟ ɪɴғᴏʀᴍᴀᴛɪᴏɴ:**\n"
          f"━━━━━━━━━━━━━━━━\n"
          f"• **ɴᴀᴍᴇ:** {name}\n"
          f"• **ᴜɪᴅ:** `{uid_val}`\n"
          f"• **ʟᴇᴠᴇʟ:** {level_val}\n"
          f"━━━━━━━━━━━━━━━━\n\n"
          f"ℹ️ _{msg}_"
      )

      bot.reply_to(
          message,
          text,
          parse_mode="Markdown",
          reply_to_message_id=message.message_id,
      )

    else:
      bot.reply_to(
          message, f"sᴏʀʀʏ, ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ wɪᴛʜ sᴛᴀᴛᴜs ᴄᴏᴅᴇ: {r.status_code}"
      )

  except requests.exceptions.RequestException as e:
    bot.reply_to(
        message, f"ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ wʜɪʟᴇ ᴄᴏɴɴᴇᴄᴛɪɴɢ ᴛᴏ ᴛʜᴇ sᴇʀᴠᴇʀ:\n{e}"
    )


# أمر لجلب بيانات الكلأن (Guild/Clan) عبر إدخال معرف الكلأن
@bot.message_handler(commands=["clan"])
def fetch_clan(message):
  allowed, msg = check_and_deduct(message, cost=2, is_info=False)
  if not allowed:
    bot.reply_to(message, msg, parse_mode="Markdown")
    return

  args = message.text.split()
  if len(args) > 1:
    clan_id = args[1]
  else:
    bot.reply_to(
        message,
        "⚠️ ᴘʟᴇᴀsᴇ wʀɪᴛᴇ ᴛʜᴇ ᴄʟᴀɴ ɪᴅ ᴄᴏʀʀᴇᴄᴛʟʏ ɴᴇxᴛ ᴛᴏ ᴛʜᴇ"
        " ᴄᴏᴍᴍᴀɴᴅ.\nᴇxᴀᴍᴘʟᴇ:\n`/clan 30512345`",
        parse_mode="Markdown",
    )
    return

  try:
    r = requests.get(
        "http://de26.spaceify.eu:26080/clan",
        params={"clan_id": clan_id},
        timeout=20,
    )

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

      clan_name = get_val(
          "clanName", "name", "ClanName", "guildName", "guild_name"
      )
      clan_id_val = get_val("clanId", "clan_id", "id", "guildId") or clan_id
      clan_level = get_val(
          "clanLevel", "level", "lvl", "ClanLevel", "guildLevel", "guild_level"
      )
      member_count = get_val(
          "memberCount", "members", "member_count", "capacity", "currentMembers"
      )
      max_members = get_val(
          "maxMembers", "max_members", "capacityMax", "limit"
      )
      leader_name = get_val(
          "leaderName", "leader", "masterName", "captainName", "ownerName"
      )

      text = (
          f"🛡️ **ᴄʟᴀɴ ɪɴғᴏʀᴍᴀᴛɪᴏɴ:**\n"
          f"━━━━━━━━━━━━━━━━\n"
          f"• **ɴᴀᴍᴇ:** {clan_name}\n"
          f"• **ᴄʟᴀɴ ɪᴅ:** `{clan_id_val}`\n"
          f"• **ʟᴇᴠᴇʟ:** {clan_level}\n"
          f"• **ᴍᴇᴍʙᴇʀs:** {member_count}/{max_members}\n"
          f"• **ʟᴇᴀᴅᴇʀ:** {leader_name}\n"
          f"━━━━━━━━━━━━━━━━\n\n"
          f"ℹ️ _{msg}_"
      )

      bot.reply_to(
          message,
          text,
          parse_mode="Markdown",
          reply_to_message_id=message.message_id,
      )

    else:
      bot.reply_to(
          message, f"sᴏʀʀʏ, ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ wɪᴛʜ sᴛᴀᴛᴜs ᴄᴏᴅᴇ: {r.status_code}"
      )

  except requests.exceptions.RequestException as e:
    bot.reply_to(
        message, f"ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ wʜɪʟᴇ ᴄᴏɴɴᴇᴄᴛɪɴɢ ᴛᴏ ᴛʜᴇ sᴇʀᴠᴇʀ:\n{e}"
    )


# أمر لجلب مظهر / ملابس اللاعب (Outfit)
@bot.message_handler(commands=["outfit"])
def fetch_outfit(message):
  allowed, msg = check_and_deduct(message, cost=2, is_info=False)
  if not allowed:
    bot.reply_to(message, msg, parse_mode="Markdown")
    return

  args = message.text.split()
  if len(args) > 1:
    uid = args[1]
  else:
    bot.reply_to(
        message,
        "⚠️ ᴘʟᴇᴀsᴇ wʀɪᴛᴇ ᴛʜᴇ ᴜɪᴅ ᴄᴏʀʀᴇᴄᴛʟʏ ɴᴇxᴛ ᴛᴏ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅ.\nᴇxᴀᴍᴘʟᴇ:\n`/outfit 4485827054`",
        parse_mode="Markdown",
    )
    return

  wait_msg = bot.reply_to(
      message, f"⏳ جاري جلب صورة المظهر، يرجى الانتظار...\nℹ️ _{msg}_", parse_mode="Markdown"
  )

  try:
    r = requests.get(
        "http://de26.spaceify.eu:26080/outfit", params={"uid": uid}, timeout=45
    )

    if r.status_code == 200:
      open("outfit.png", "wb").write(r.content)
      try:
        bot.send_photo(
            message.chat.id,
            open("outfit.png", "rb"),
            caption=(
                f"👕 **ᴘʟᴀʏᴇʀ ᴏᴜᴛғɪᴛ ɪɴғᴏ:**\n━━━━━━━━━━━━━━━━\n• **ᴜɪᴅ:**"
                f" `{uid}`\n━━━━━━━━━━━━━━━━"
            ),
            parse_mode="Markdown",
            reply_to_message_id=message.message_id,
        )
        bot.delete_message(message.chat.id, wait_msg.message_id)
      except Exception:
        bot.edit_message_text(
            "✅ ᴛʜᴇ ᴏᴜᴛғɪᴛ ɪᴍᴀɢᴇ wᴀs sᴀᴠᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ.",
            message.chat.id,
            wait_msg.message_id,
        )
    else:
      bot.edit_message_text(
          f"sᴏʀʀʏ, ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ wɪᴛʜ sᴛᴀᴛᴜs ᴄᴏᴅᴇ: {r.status_code}",
          message.chat.id,
          wait_msg.message_id,
      )

  except requests.exceptions.Timeout:
    bot.edit_message_text(
        "⏱️ انتهت مهلة الانتظار، الخادم المجاني بطيء جداً حالياً ولم يستجب في الوقت المحدد. يرجى المحاولة لاحقاً.",
        message.chat.id,
        wait_msg.message_id,
    )
  except requests.exceptions.RequestException as e:
    bot.edit_message_text(
        f"ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ wʜɪʟེ་ ᴄᴏɴɴᴇᴄᴛɪɴɢ ᴛᴏ ᴛʜᴇ sᴇʀᴠᴇʀ:\n{e}",
        message.chat.id,
        wait_msg.message_id,
    )


# تشغيل البوت باستمرار مع خادم الويب في الخلفية
if __name__ == "__main__":
  print("جاري تشغيل خادم الويب وبوت التليجرام...")

  # تشغيل خادم Flask في مسار خلفي (Thread) ليفتح البورت الذي تحتاجه منصة Render
  t = threading.Thread(target=run_web)
  t.daemon = True
  t.start()

  bot.remove_webhook()

  # فحص الـ Check الذي طلبته سابقاً
  try:
    uid = 4485827054
    check_r = requests.get(
        "http://de26.spaceify.eu:26080/check", params={"uid": uid}, timeout=20
    )
    print("Check Response:", check_r.json())
  except Exception as e:
    print("Check failed:", e)

  print("البوت قيد التشغيل الآن مع خادم الويب...")
  bot.infinity_polling()
      
