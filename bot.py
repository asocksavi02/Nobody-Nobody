import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from playwright.async_api import async_playwright

TOKEN = os.getenv("BOT_TOKEN")


# 🧾 Message builder
def build_message(phone):
    return f"""I am currently facing an issue where I am unable to log into my WhatsApp account. Each time I attempt to log in, I receive a message stating, "Login not available at the moment." This issue has persisted despite multiple attempts and troubleshooting steps on my end.

I would greatly appreciate your assistance in resolving this matter as soon as possible. Thank you for your prompt attention to this issue.

Phone Number: {phone}
"""


# 🌐 Form submission
async def submit_form(phone, email):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )

        page = await browser.new_page()

        await page.goto(
            "https://www.whatsapp.com/contact/?eea=1&subject=messenger&form_type=accessibility"
        )

        await page.wait_for_timeout(3000)

        # Fill inputs
        inputs = page.locator("input")
        if await inputs.count() < 3:
            raise Exception("Form fields not found")

        await inputs.nth(0).fill(phone)
        await inputs.nth(1).fill(email)
        await inputs.nth(2).fill(email)

        # Select Android
        try:
            await page.get_by_label("Android").click()
        except:
            pass

        # Fill message
        await page.locator("textarea").fill(build_message(phone))

        await page.wait_for_timeout(1500)

        # Submit
        await page.locator("button").last.click()

        await page.wait_for_timeout(3000)

        await browser.close()


# 🤖 Bot logic
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send your phone number (with country code)\nExample:\n+8801XXXXXXXXX"
    )
    context.user_data["step"] = "phone"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    step = context.user_data.get("step")

    if step == "phone":
        context.user_data["phone"] = text
        context.user_data["step"] = "email"

        await update.message.reply_text("Now send your email address")

    elif step == "email":
        phone = context.user_data.get("phone")
        email = text

        await update.message.reply_text("Submitting... ⏳")

        try:
            await submit_form(phone, email)
            await update.message.reply_text("✅ Submitted successfully!")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")

        context.user_data.clear()

    else:
        await update.message.reply_text("Type /start to begin")


# 🚀 Run bot
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()
