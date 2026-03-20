import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.environ.get("POSTER_TOKEN") or os.environ.get("TELEGRAM_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

FB_TOKEN = os.environ.get("FB_TOKEN")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
IFTTT_KEY = os.environ.get("IFTTT_KEY")
MASTODON_TOKEN = os.environ.get("MASTODON_TOKEN")
MASTODON_URL = os.environ.get("MASTODON_URL")
REDDIT_CLIENT = os.environ.get("REDDIT_CLIENT")
REDDIT_SECRET = os.environ.get("REDDIT_SECRET")
REDDIT_USER = os.environ.get("REDDIT_USER")
REDDIT_PASS = os.environ.get("REDDIT_PASS")
REDDIT_SUB = os.environ.get("REDDIT_SUB")


def clean(text):
    c = text.replace("**", "").replace("*", "")
    c = c.replace("###", "").replace("##", "").replace("#", "")
    return c.strip()


def post_facebook(text):
    if not FB_TOKEN or not FB_PAGE_ID:
        return "⚪ Facebook: Not set"
    try:
        url = "https://graph.facebook.com/" + FB_PAGE_ID + "/feed"
        r = requests.post(url, data={"message": clean(text), "access_token": FB_TOKEN}, timeout=30)
        if r.status_code == 200:
            return "✅ Facebook: Posted!"
        return "❌ Facebook: " + r.json().get("error", {}).get("message", "Error")[:60]
    except Exception as e:
        return "❌ Facebook: " + str(e)[:60]


def post_telegram(text):
    if not CHANNEL_ID:
        return "⚪ Telegram: CHANNEL_ID not set"
    try:
        url = "https://api.telegram.org/bot" + BOT_TOKEN + "/sendMessage"
        r = requests.post(url, data={"chat_id": CHANNEL_ID, "text": clean(text)}, timeout=30)
        if r.status_code == 200:
            return "✅ Telegram Channel: Posted!"
        return "❌ Telegram: " + r.text[:60]
    except Exception as e:
        return "❌ Telegram: " + str(e)[:60]


def post_ifttt(event, text):
    if not IFTTT_KEY:
        return "⚪ " + event + ": IFTTT not set"
    try:
        url = "https://maker.ifttt.com/trigger/" + event + "/with/key/" + IFTTT_KEY
        r = requests.post(url, json={"value1": clean(text)[:500]}, timeout=30)
        name = event.replace("post_", "").title()
        if r.status_code == 200:
            return "✅ " + name + ": Posted!"
        return "❌ " + name + ": " + r.text[:60]
    except Exception as e:
        return "❌ " + event + ": " + str(e)[:60]


def post_mastodon(text):
    if not MASTODON_TOKEN:
        return "⚪ Mastodon: Not set"
    try:
        base = MASTODON_URL or "https://mastodon.social"
        url = base + "/api/v1/statuses"
        headers = {"Authorization": "Bearer " + MASTODON_TOKEN}
        r = requests.post(url, headers=headers, data={"status": clean(text)[:500]}, timeout=30)
        if r.status_code == 200:
            return "✅ Mastodon: Posted!"
        return "❌ Mastodon: " + r.text[:60]
    except Exception as e:
        return "❌ Mastodon: " + str(e)[:60]


def post_reddit(text, title=None):
    if not REDDIT_CLIENT or not REDDIT_SECRET:
        return "⚪ Reddit: Not set"
    try:
        auth = requests.auth.HTTPBasicAuth(REDDIT_CLIENT, REDDIT_SECRET)
        login = {"grant_type": "password", "username": REDDIT_USER, "password": REDDIT_PASS}
        h = {"User-Agent": "PosterAgent/1.0"}
        tr = requests.post("https://www.reddit.com/api/v1/access_token", auth=auth, data=login, headers=h, timeout=30)
        if tr.status_code != 200:
            return "❌ Reddit: Auth fail"
        token = tr.json().get("access_token")
        ah = {"Authorization": "bearer " + token, "User-Agent": "PosterAgent/1.0"}
        t = title or clean(text)[:300]
        sub = REDDIT_SUB or "test"
        pd = {"sr": sub, "kind": "self", "title": t, "text": clean(text)}
        r = requests.post("https://oauth.reddit.com/api/submit", headers=ah, data=pd, timeout=30)
        if r.status_code == 200:
            return "✅ Reddit r/" + sub + ": Posted!"
        return "❌ Reddit: " + r.text[:60]
    except Exception as e:
        return "❌ Reddit: " + str(e)[:60]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📤 POSTER Agent v2.0\n\n"
        "Commands:\n"
        "/post [text] - All platforms\n"
        "/tg [text] - Telegram channel\n"
        "/fb [text] - Facebook\n"
        "/tw [text] - Twitter via IFTTT\n"
        "/li [text] - LinkedIn via IFTTT\n"
        "/pin [text] - Pinterest via IFTTT\n"
        "/mas [text] - Mastodon\n"
        "/red [title] | [text] - Reddit\n"
        "/status - Platform check\n\n"
        "📊 /status to see what's connected!"
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/post text - Post everywhere\n"
        "/tg text - Telegram\n"
        "/fb text - Facebook\n"
        "/tw text - Twitter\n"
        "/li text - LinkedIn\n"
        "/pin text - Pinterest\n"
        "/mas text - Mastodon\n"
        "/red Title | Text - Reddit\n"
        "/status - Check platforms"
    )


async def post_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /post Your content here")
        return
    content = " ".join(context.args)
    await update.message.reply_text("📤 Posting everywhere...")
    results = []
    results.append(post_telegram(content))
    results.append(post_facebook(content))
    results.append(post_ifttt("post_twitter", content[:280]))
    results.append(post_ifttt("post_linkedin", content))
    results.append(post_ifttt("post_pinterest", content))
    results.append(post_mastodon(content))
    results.append(post_reddit(content))
    report = "\n".join(results)
    ok = sum(1 for r in results if "✅" in r)
    await update.message.reply_text("📊 REPORT\n\n" + report + "\n\n✅ " + str(ok) + " posted!")


async def tg_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /tg Your text")
        return
    r = post_telegram(" ".join(context.args))
    await update.message.reply_text(r)


async def fb_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /fb Your text")
        return
    r = post_facebook(" ".join(context.args))
    await update.message.reply_text(r)


async def tw_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /tw Your tweet")
        return
    r = post_ifttt("post_twitter", " ".join(context.args)[:280])
    await update.message.reply_text(r)


async def li_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /li Your post")
        return
    r = post_ifttt("post_linkedin", " ".join(context.args))
    await update.message.reply_text(r)


async def pin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /pin Your text")
        return
    r = post_ifttt("post_pinterest", " ".join(context.args))
    await update.message.reply_text(r)


async def mas_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /mas Your toot")
        return
    r = post_mastodon(" ".join(context.args))
    await update.message.reply_text(r)


async def red_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /red Title | Content")
        return
    full = " ".join(context.args)
    if "|" in full:
        parts = full.split("|", 1)
        r = post_reddit(parts[1].strip(), parts[0].strip())
    else:
        r = post_reddit(full)
    await update.message.reply_text(r)


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = "📊 PLATFORMS\n\n"
    s += ("✅" if CHANNEL_ID else "❌") + " Telegram Channel\n"
    s += ("✅" if FB_TOKEN else "❌") + " Facebook\n"
    s += ("✅" if IFTTT_KEY else "❌") + " Twitter (IFTTT)\n"
    s += ("✅" if IFTTT_KEY else "❌") + " LinkedIn (IFTTT)\n"
    s += ("✅" if IFTTT_KEY else "❌") + " Pinterest (IFTTT)\n"
    s += ("✅" if MASTODON_TOKEN else "❌") + " Mastodon\n"
    s += ("✅" if REDDIT_CLIENT else "❌") + " Reddit\n"
    await update.message.reply_text(s)


def main():
    print("POSTER Agent v2.0 Starting...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("post", post_all))
    app.add_handler(CommandHandler("tg", tg_cmd))
    app.add_handler(CommandHandler("fb", fb_cmd))
    app.add_handler(CommandHandler("tw", tw_cmd))
    app.add_handler(CommandHandler("li", li_cmd))
    app.add_handler(CommandHandler("pin", pin_cmd))
    app.add_handler(CommandHandler("mas", mas_cmd))
    app.add_handler(CommandHandler("red", red_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    print("POSTER LIVE!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
