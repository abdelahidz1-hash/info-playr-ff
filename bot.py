import os
import threading
import requests
import telebot
from flask import Flask

# توكن البوت الخاص بك
TOKEN = "7941526631:AAHRBSfpHUFLdw8GvlevvawKtL-16ciMCrs"
bot = telebot.TeleBot(TOKEN)

# إعداد خادم Flask وهمي لإرضاء Render Web Service المجاني وتجنب مهلة البورتات
app = Flask(__name__)


@app.route("/")
def home():
  return "Bot is running successfully!"


def run_web():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)


# قائمة معرفات البانرات المعتمدة الفارغة
VALID_BANNERS = set()


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


# أمر البداية /start
@bot.message_handler(commands=["start"])
def send_welcome(message):
  bot.reply_to(
      message,
      "ᴡᴇʟᴄᴏᴍᴇ! ʏᴏᴜʀ ʙᴏᴛ ɪs wᴏʀᴋɪɴɢ sᴜᴄᴄᴇssꜰᴜʟʟʏ.\n\n"
      "ᴛʏᴘᴇ /help ᴛᴏ sᴇᴇ ᴛʜᴇ ᴀᴠᴀɪʟᴀʙʟᴇ ᴄᴏᴍᴍᴀɴᴅs ᴀɴᴅ ʜᴏw ᴛᴏ ᴜsᴇ ᴛʜᴇᴍ.",
      parse_mode="Markdown",
  )


# أمر المساعدة /help
@bot.message_handler(commands=["help"])
def send_help(message):
  bot.reply_to(
      message,
      "🤖 **ᴀᴠᴀɪʟᴀʙʟᴇ ᴄᴏᴍᴍᴀɴْدs:**\n"
      "━━━━━━━━━━━━━━━━\n"
      "• **ᴘʟᴀʏᴇʀ ɪɴғᴏ:** `/info <UID>`\n"
      "  *ᴇxᴀᴍᴘʟᴇ:* `/info 7876206533`\n\n"
      "• **sᴇᴀʀᴄʜ by ɴᴀᴍᴇ:** `/search <Name>` أو `/ser <Name>`\n"
      "  *ᴇxᴀᴍᴘʟᴇ:* `/search xMaSrY`\n\n"
      "• **ᴄʟᴀɴ ɪɴғᴏ:** `/clan <Clan ID>`\n"
      "  *ᴇxᴀᴍᴘʟᴇ:* `/clan 30512345`\n\n"
      "• **ʟᴇᴠᴇʟ ɪɴғᴏ:** `/level <UID>`\n"
      "  *ᴇxᴀᴍᴘʟᴇ:* `/level 4485827054`\n\n"
      "• **ᴏᴜᴛғɪᴛ ɪɴғᴏ:** `/outfit <UID>`\n"
      "  *ᴇxᴀᴍᴘʟᴇ:* `/outfit 4485827054`\n"
      "━━━━━━━━━━━━━━━━",
      parse_mode="Markdown",
  )


# أمر لجلب البيانات من الـ API عبر إدخال الآي دي الخاص باللاعب
@bot.message_handler(commands=["info"])
def fetch_info(message):
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

      # استخدام رابط الصورة الثابت الذي طلبته فوق معلومات اللاعب
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

      text += "━━━━━━━━━━━━━━━━"
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
          f"━━━━━━━━━━━━━━━━"
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
          f"━━━━━━━━━━━━━━━━"
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
      message, "⏳ جاري جلب صورة المظهر، يرجى الانتظار...", parse_mode="Markdown"
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
        f"ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ wʜɪʟᴇ ᴄᴏɴɴᴇᴄᴛɪɴɢ ᴛᴏ ᴛʜᴇ sᴇʀᴠᴇʀ:\n{e}",
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
  
