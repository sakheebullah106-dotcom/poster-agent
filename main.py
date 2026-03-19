import os
import requests
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TELEGRAM_TOKEN = os.environ.get("POSTER_TOKEN")

FB_TOKEN = os.environ.get("FB_TOKEN")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
IG_ACCOUNT_ID = os.environ.get("IG_ACCOUNT_ID")

CHANNEL_ID = os.environ.get("CHANNEL_ID")

IFTTT_KEY = os.environ.get("IFTTT_KEY")

REDDIT_CLIENT = os.environ.get("REDDIT_CLIENT")
REDDIT_SECRET = os.environ.get("REDDIT_SECRET")
REDDIT_USER = os.environ.get("REDDIT_USER")
REDDIT_PASS = os.environ.get("REDDIT_PASS")
REDDIT_SUB = os.environ.get("REDDIT_SUB")

MASTODON_TOKEN = os.environ.get("MASTODON_TOKEN")
MASTODON_URL = os.environ.get("MASTODON_URL")

BLOGGER_ID = os.environ.get("BLOGGER_ID")
BLOGGER_KEY = os.environ.get("BLOGGER_KEY")

BUFFER_TOKEN = os.environ.get("BUFFER_TOKEN")


def clean_text(text):
    c = text.replace("**", "").replace("*", "")
    c = c.replace("###", "").replace("##", "").replace("#", "")
    return c.strip()


def short_text(text, limit=280):
    if len(text) <= limit:
        return text
    return text[:limit - 3] + "..."


def post_facebook(text):
    if not FB_TOKEN or not FB_PAGE_ID:
        return "⚪ Facebook: Not configured"
    try:
        url = "https://graph.facebook.com/" + FB_PAGE_ID + "/feed"
        data = {"message": clean_text(text), "access_token": FB_TOKEN}
        r = requests.post(url, data=data, timeout=30)
        if r.status_code == 200:
            return "✅ Facebook: Posted!"
        error = r.json().get("error", {}).get("message", "Error")
        return "❌ Facebook: " + error[:60]
    except Exception as e:
        return "❌ Facebook: " + str(e)[:60]


def post_instagram(text):
    if not FB_TOKEN or not IG_ACCOUNT_ID:
        return "⚪ Instagram: Not configured"
    try:
        caption = clean_text(text)
        if len(caption) > 2200:
            caption = caption[:2200]
        return "⚪ Instagram: Needs image URL (use /igpost)"
    except Exception as e:
        return "❌ Instagram: " + str(e)[:60]


def post_instagram_with_image(text, image_url):
    if not FB_TOKEN or not IG_ACCOUNT_ID:
        return "⚪ Instagram: Not configured"
    try:
        create_url = "https://graph.facebook.com/" + IG_ACCOUNT_ID + "/media"
        create_data = {
            "caption": clean_text(text),
            "image_url": image_url,
            "access_token": FB_TOKEN
        }
        r1 = requests.post(create_url, data=create_data, timeout=30)
        if r1.status_code != 200:
            return "❌ Instagram: " + r1.text[:60]
        media_id = r1.json().get("id")
        publish_url = "https://graph.facebook.com/" + IG_ACCOUNT_ID + "/media_publish"
        publish_data = {"creation_id": media_id, "access_token": FB_TOKEN}
        r2 = requests.post(publish_url, data=publish_data, timeout=30)
        if r2.status_code == 200:
            return "✅ Instagram: Posted!"
        return "❌ Instagram: " + r2.text[:60]
    except Exception as e:
        return "❌ Instagram: " + str(e)[:60]


def post_telegram_channel(text):
    if not CHANNEL_ID:
        return "⚪ Telegram: Not configured"
    try:
        url = "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage"
        data = {"chat_id": CHANNEL_ID, "text": clean_text(text)}
        r = requests.post(url, data=data, timeout=30)
        if r.status_code == 200:
            return "✅ Telegram: Posted!"
        return "❌ Telegram: " + r.text[:60]
    except Exception as e:
        return "❌ Telegram: " + str(e)[:60]


def post_ifttt(event_name, text):
    if not IFTTT_KEY:
        return "⚪ " + event_name + ": IFTTT not configured"
    try:
        url = "https://maker.ifttt.com/trigger/" + event_name + "/with/key/" + IFTTT_KEY
        data = {"value1": clean_text(text)}
        r = requests.post(url, json=data, timeout=30)
        if r.status_code == 200:
            platform = event_name.replace("post_", "").title()
            return "✅ " + platform + ": Posted via IFTTT!"
        return "❌ " + event_name + ": " + r.text[:60]
    except Exception as e:
        return "❌ " + event_name + ": " + str(e)[:60]


def post_twitter(text):
    return post_ifttt("post_twitter", short_text(text, 280))


def post_linkedin(text):
    return post_ifttt("post_linkedin", text)


def post_pinterest(text):
    return post_ifttt("post_pinterest", text)


def post_threads(text):
    return post_ifttt("post_threads", text)

def post_reddit(text, title=None):
    if not REDDIT_CLIENT or not REDDIT_SECRET:
        return "⚪ Reddit: Not configured"
    try:
        auth = requests.auth.HTTPBasicAuth(REDDIT_CLIENT, REDDIT_SECRET)
        login_data = {
            "grant_type": "password",
            "username": REDDIT_USER,
            "password": REDDIT_PASS
        }
        headers = {"User-Agent": "PosterAgent/1.0"}
        token_r = requests.post(
            "https://www.reddit.com/api/v1/access_token",
            auth=auth, data=login_data, headers=headers, timeout=30
        )
        if token_r.status_code != 200:
            return "❌ Reddit: Auth failed"
        token = token_r.json().get("access_token")
        api_headers = {
            "Authorization": "bearer " + token,
            "User-Agent": "PosterAgent/1.0"
        }
        post_title = title if title else clean_text(text)[:300]
        subreddit = REDDIT_SUB if REDDIT_SUB else "test"
        post_data = {
            "sr": subreddit,
            "kind": "self",
            "title": post_title,
            "text": clean_text(text)
        }
        r = requests.post(
            "https://oauth.reddit.com/api/submit",
            headers=api_headers, data=post_data, timeout=30
        )
        if r.status_code == 200:
            return "✅ Reddit: Posted to r/" + subreddit + "!"
        return "❌ Reddit: " + r.text[:60]
    except Exception as e:
        return "❌ Reddit: " + str(e)[:60]


def post_mastodon(text):
    if not MASTODON_TOKEN:
        return "⚪ Mastodon: Not configured"
    try:
        base = MASTODON_URL if MASTODON_URL else "https://mastodon.social"
        url = base + "/api/v1/statuses"
        headers = {"Authorization": "Bearer " + MASTODON_TOKEN}
        data = {"status": clean_text(text)[:500]}
        r = requests.post(url, headers=headers, data=data, timeout=30)
        if r.status_code == 200:
            return "✅ Mastodon: Posted!"
        return "❌ Mastodon: " + r.text[:60]
    except Exception as e:
        return "❌ Mastodon: " + str(e)[:60]


def post_blogger(text, title=None):
    if not BLOGGER_ID or not BLOGGER_KEY:
        return "⚪ Blogger: Not configured"
    try:
        post_title = title if title else clean_text(text)[:100]
        url = "https://www.googleapis.com/blogger/v3/blogs/" + BLOGGER_ID + "/posts/"
        params = {"key": BLOGGER_KEY}
        html_content = "<p>" + clean_text(text).replace("\n\n", "</p><p>").replace("\n", "<br>") + "</p>"
        data = {"kind": "blogger#post", "title": post_title, "content": html_content}
        r = requests.post(url, params=params, json=data, timeout=30)
        if r.status_code == 200:
            return "✅ Blogger: Published!"
        return "❌ Blogger: " + r.text[:60]
    except Exception as e:
        return "❌ Blogger: " + str(e)[:60]


def post_buffer(text):
    if not BUFFER_TOKEN:
        return "⚪ Buffer: Not configured"
    try:
        url = "https://api.bufferapp.com/1/profiles.json"
        params = {"access_token": BUFFER_TOKEN}
        r = requests.get(url, params=params, timeout=30)
        if r.status_code != 200:
            return "❌ Buffer: Auth failed"
        profiles = r.json()
        results = []
        for profile in profiles[:3]:
            profile_id = profile.get("id")
            create_url = "https://api.bufferapp.com/1/updates/create.json"
            post_data = {
                "text": clean_text(text),
                "profile_ids[]": profile_id,
                "access_token": BUFFER_TOKEN
            }
            pr = requests.post(create_url, data=post_data, timeout=30)
            service = profile.get("service", "unknown")
            if pr.status_code == 200:
                results.append("✅ Buffer→" + service)
            else:
                results.append("❌ Buffer→" + service)
        return " | ".join(results) if results else "⚪ Buffer: No profiles"
    except Exception as e:
        return "❌ Buffer: " + str(e)[:60]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📤 POSTER Agent v2.0\n"
        "Post to 13+ platforms FREE!\n\n"
        "📝 COMMANDS:\n"
        "/post [content] - ALL platforms\n"
        "/fb [text] - Facebook\n"
        "/ig [image_url] [caption] - Instagram\n"
        "/tg [text] - Telegram channel\n"
        "/tw [text] - Twitter/X\n"
        "/li [text] - LinkedIn\n"
        "/pin [text] - Pinterest\n"
        "/red [title] | [text] - Reddit\n"
        "/mas [text] - Mastodon\n"
        "/blog [title] | [text] - Blogger\n"
        "/buf [text] - Buffer (3 platforms)\n\n"
        "📊 /status - Check all platforms\n"
        "🆘 /help - All commands"
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📤 ALL COMMANDS:\n\n"
        "/post text - Post EVERYWHERE\n"
        "/fb text - Facebook only\n"
        "/ig image_url caption - Instagram\n"
        "/tg text - Telegram channel\n"
        "/tw text - Twitter/X via IFTTT\n"
        "/li text - LinkedIn via IFTTT\n"
        "/pin text - Pinterest via IFTTT\n"
        "/red Title | Content - Reddit\n"
        "/mas text - Mastodon\n"
        "/blog Title | Content - Blogger\n"
        "/buf text - Buffer\n"
        "/status - Platform status"
    )


async def post_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /post Your content here")
        return
    content = " ".join(context.args)
    await update.message.reply_text("📤 Posting to ALL platforms...\n⏳ 30 seconds wait...")
    results = []
    results.append(post_facebook(content))
    results.append(post_telegram_channel(content))
    results.append(post_twitter(content))
    results.append(post_linkedin(content))
    results.append(post_pinterest(content))
    results.append(post_reddit(content))
    results.append(post_mastodon(content))
    results.append(post_blogger(content))
    results.append(post_buffer(content))
    report = "\n".join(results)
    success = sum(1 for r in results if "✅" in r)
    total = sum(1 for r in results if "⚪" not in r)
    await update.message.reply_text(
        "📊 POSTING REPORT\n\n" + report + "\n\n"
        "✅ " + str(success) + " posted | "
        "⚪ " + str(len(results) - total) + " not configured"
    )


async def fb_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /fb Your text")
        return
    r = post_facebook(" ".join(context.args))
    await update.message.reply_text(r)


async def ig_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("❌ /ig https://image-url.jpg Your caption here")
        return
    image_url = context.args[0]
    caption = " ".join(context.args[1:])
    r = post_instagram_with_image(caption, image_url)
    await update.message.reply_text(r)


async def tg_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /tg Your text")
        return
    r = post_telegram_channel(" ".join(context.args))
    await update.message.reply_text(r)


async def tw_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /tw Your tweet")
        return
    r = post_twitter(" ".join(context.args))
    await update.message.reply_text(r)


async def li_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /li Your LinkedIn post")
        return
    r = post_linkedin(" ".join(context.args))
    await update.message.reply_text(r)


async def pin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /pin Your pin text")
        return
    r = post_pinterest(" ".join(context.args))
    await update.message.reply_text(r)


async def red_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /red Post Title | Post content here")
        return
    full = " ".join(context.args)
    if "|" in full:
        parts = full.split("|", 1)
        title = parts[0].strip()
        content = parts[1].strip()
    else:
        title = full[:100]
        content = full
    r = post_reddit(content, title)
    await update.message.reply_text(r)


async def mas_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /mas Your toot here")
        return
    r = post_mastodon(" ".join(context.args))
    await update.message.reply_text(r)


async def blog_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /blog Post Title | Post content")
        return
    full = " ".join(context.args)
    if "|" in full:
        parts = full.split("|", 1)
        title = parts[0].strip()
        content = parts[1].strip()
    else:
        title = full[:100]
        content = full
    r = post_blogger(content, title)
    await update.message.reply_text(r)


async def buf_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /buf Your text")
        return
    r = post_buffer(" ".join(context.args))
    await update.message.reply_text(r)


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = "📊 PLATFORM STATUS\n\n"
    s += "DIRECT APIs:\n"
    s += ("✅" if FB_TOKEN and FB_PAGE_ID else "❌") + " Facebook\n"
    s += ("✅" if FB_TOKEN and IG_ACCOUNT_ID else "❌") + " Instagram\n"
    s += ("✅" if CHANNEL_ID else "❌") + " Telegram Channel\n"
    s += ("✅" if REDDIT_CLIENT else "❌") + " Reddit\n"
    s += ("✅" if MASTODON_TOKEN else "❌") + " Mastodon\n"
    s += ("✅" if BLOGGER_ID else "❌") + " Blogger\n"
    s += "\nIFTTT WEBHOOKS:\n"
    s += ("✅" if IFTTT_KEY else "❌") + " Twitter/X\n"
    s += ("✅" if IFTTT_KEY else "❌") + " LinkedIn\n"
    s += ("✅" if IFTTT_KEY else "❌") + " Pinterest\n"
    s += ("✅" if IFTTT_KEY else "❌") + " Threads\n"
    s += "\nTHIRD PARTY:\n"
    s += ("✅" if BUFFER_TOKEN else "❌") + " Buffer\n"
    active = sum(1 for x in [
        FB_TOKEN and FB_PAGE_ID, CHANNEL_ID, IFTTT_KEY,
        REDDIT_CLIENT, MASTODON_TOKEN, BLOGGER_ID, BUFFER_TOKEN
    ] if x)
    s += "\n🔥 Active: " + str(active) + " platforms"
    await update.message.reply_text(s)


def main():
    print("POSTER Agent v2.0 Starting...")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    cmds = {
        "start": start, "help": help_cmd,
        "post": post_all, "fb": fb_cmd,
        "ig": ig_cmd, "tg": tg_cmd,
        "tw": tw_cmd, "li": li_cmd,
        "pin": pin_cmd, "red": red_cmd,
        "mas": mas_cmd, "blog": blog_cmd,
        "buf": buf_cmd, "status": status_cmd
    }
    for n, f in cmds.items():
        app.add_handler(CommandHandler(n, f))
    print("POSTER Agent v2.0 LIVE!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
