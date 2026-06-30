"""
PixelShiftPro1bot - A Telegram bot for image conversion
Converts images between PNG, JPG, WEBP, BMP, and more
Ready for deployment on Railway using GitHub
"""

import os
import sys
import logging
from io import BytesIO
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from dotenv import load_dotenv
from PIL import Image

# Load environment variables
load_dotenv()

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

if not BOT_TOKEN:
    print("❌ BOT_TOKEN is not set in environment variables")
    sys.exit(1)

# Logging setup
log_level = logging.DEBUG if DEBUG_MODE else logging.INFO
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
BOT_NAME = "PixelShiftPro1bot"
BOT_VERSION = "1.0.0"

# Supported formats
SUPPORTED_FORMATS = ["PNG", "JPG", "JPEG", "WEBP", "BMP", "ICO", "GIF", "TIFF"]

# Quality settings
DEFAULT_QUALITY = 90

# User session storage
user_sessions = {}


def convert_image(image_data: bytes, target_format: str, quality: int = DEFAULT_QUALITY) -> tuple:
    """
    Convert an image to the specified format
    
    Args:
        image_data: Raw image bytes
        target_format: Target format (png, jpg, webp, etc.)
        quality: Quality for lossy formats (1-100)
    
    Returns:
        Tuple of (success, image_bytes_or_error_message, format_upper, original_format)
    """
    try:
        # Open image
        img = Image.open(BytesIO(image_data))
        
        # Get original format
        original_format = img.format or "Unknown"
        
        # Handle transparency for JPEG
        if target_format.lower() in ["jpg", "jpeg"] and img.mode in ["RGBA", "P", "LA"]:
            # Create white background
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "RGBA":
                # Use alpha channel as mask
                alpha = img.split()[3] if len(img.split()) > 3 else None
                if alpha:
                    background.paste(img, mask=alpha)
                else:
                    background.paste(img)
            else:
                background.paste(img)
            img = background
        
        # Convert to RGB for BMP (doesn't support RGBA)
        if target_format.lower() == "bmp" and img.mode in ["RGBA", "LA"]:
            img = img.convert("RGB")
        
        # Handle ICO format (specific sizes)
        if target_format.lower() == "ico":
            if img.size[0] > 256 or img.size[1] > 256:
                img = img.resize((256, 256), Image.Resampling.LANCZOS)
        
        # Save with proper parameters
        save_kwargs = {}
        format_upper = target_format.upper()
        
        if target_format.lower() in ["jpg", "jpeg"]:
            save_kwargs["quality"] = quality
            save_kwargs["optimize"] = True
            save_kwargs["progressive"] = True
        elif target_format.lower() == "webp":
            save_kwargs["quality"] = quality
            save_kwargs["method"] = 6
        elif target_format.lower() == "png":
            save_kwargs["optimize"] = True
            save_kwargs["compress_level"] = 6
        elif target_format.lower() == "tiff":
            save_kwargs["compression"] = "tiff_lzw"
        
        # Save to bytes
        output = BytesIO()
        img.save(output, format=format_upper, **save_kwargs)
        output.seek(0)
        
        return True, output.getvalue(), format_upper, original_format
        
    except Exception as e:
        logger.error(f"Conversion error: {e}")
        return False, f"Error converting image: {str(e)}", None, None


# ============ COMMAND HANDLERS ============

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    logger.info(f"✅ Start command from {user.id} ({user.username})")
    
    welcome_text = (
        f"🖼️ **Hello {user.first_name}!**\n\n"
        "Welcome to **PixelShiftPro1bot** - your professional image converter!\n\n"
        "📌 **How it works:**\n"
        "1. Use /convert to start\n"
        "2. Select your target format\n"
        "3. Upload your image\n"
        "4. Download your converted image!\n\n"
        "📊 **Supported Formats:**\n"
        "PNG, JPG, JPEG, WEBP, BMP, ICO, GIF, TIFF\n\n"
        "📊 **Commands:**\n"
        "/start - Show this menu\n"
        "/convert - Convert an image\n"
        "/formats - Show supported formats\n"
        "/about - Bot information\n"
        "/help - Get help"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Convert Image", callback_data="start_convert")],
        [InlineKeyboardButton("📋 Formats", callback_data="show_formats")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ])
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = (
        "🆘 **Help Guide**\n\n"
        "📖 **How to convert images:**\n\n"
        "1. Use /convert\n"
        "2. Choose target format\n"
        "3. Upload your image\n"
        "4. Download the converted image!\n\n"
        "✅ **Tips:**\n"
        "• You can convert multiple images\n"
        "• Large images may take a few seconds\n"
        "• Maximum file size: 20MB\n"
        "• All formats are high quality\n\n"
        "📊 **Commands:**\n"
        "/start - Main menu\n"
        "/convert - Convert image\n"
        "/formats - Show supported formats\n"
        "/help - This message"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /about command"""
    about_text = (
        f"🤖 **{BOT_NAME}**\n\n"
        f"📌 Version: `{BOT_VERSION}`\n"
        "⚡ Built with: `python-telegram-bot` & `Pillow`\n"
        "📅 Status: ✅ **Online**\n\n"
        "🔹 **Features:**\n"
        "• Convert between 8 image formats\n"
        "• High-quality output\n"
        "• Fast processing\n"
        "• User-friendly interface\n"
        "• Production-ready for Railway\n\n"
        f"💡 **Created for:** @{BOT_NAME}"
    )
    await update.message.reply_text(about_text, parse_mode="Markdown")


async def formats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /formats command"""
    formats_text = "📋 **Supported Image Formats:**\n\n"
    for fmt in SUPPORTED_FORMATS:
        formats_text += f"• `{fmt}`\n"
    
    await update.message.reply_text(formats_text, parse_mode="Markdown")


async def convert_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /convert command"""
    user_id = update.effective_user.id
    
    # Initialize session for this user
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "target_format": None,
            "waiting_for_image": False
        }
    
    # Show format selection
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("PNG", callback_data="format_PNG"),
         InlineKeyboardButton("JPG", callback_data="format_JPG")],
        [InlineKeyboardButton("JPEG", callback_data="format_JPEG"),
         InlineKeyboardButton("WEBP", callback_data="format_WEBP")],
        [InlineKeyboardButton("BMP", callback_data="format_BMP"),
         InlineKeyboardButton("ICO", callback_data="format_ICO")],
        [InlineKeyboardButton("GIF", callback_data="format_GIF"),
         InlineKeyboardButton("TIFF", callback_data="format_TIFF")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ])
    
    await update.message.reply_text(
        "🔄 **Start Image Conversion**\n\n"
        "Please select the **target format** you want to convert to:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


# ============ CALLBACK QUERY HANDLERS ============

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries from inline buttons"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "target_format": None,
            "waiting_for_image": False
        }
    
    if query.data == "start_convert":
        await convert_command(query.message, context)
        await query.message.delete()
    
    elif query.data == "show_formats":
        await formats_command(query.message, context)
    
    elif query.data == "help":
        await help_command(query.message, context)
    
    elif query.data == "cancel":
        user_sessions[user_id] = {
            "target_format": None,
            "waiting_for_image": False
        }
        await query.message.reply_text(
            "❌ **Operation cancelled.**\n\n"
            "Use /convert to start again.",
            parse_mode="Markdown"
        )
        await query.message.delete()
    
    elif query.data.startswith("format_"):
        target_format = query.data.replace("format_", "")
        user_sessions[user_id]["target_format"] = target_format
        user_sessions[user_id]["waiting_for_image"] = True
        
        await query.message.reply_text(
            f"✅ **Selected format:** `{target_format}`\n\n"
            "📤 **Now send me the image you want to convert.**\n"
            "You can send it as a photo or file.\n\n"
            "⚠️ Maximum file size: 20MB",
            parse_mode="Markdown"
        )
        await query.message.delete()


# ============ MESSAGE HANDLERS ============

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle image upload for conversion"""
    user_id = update.effective_user.id
    
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "target_format": None,
            "waiting_for_image": False
        }
    
    # Check if user is waiting for an image
    if not user_sessions[user_id].get("waiting_for_image", False):
        await update.message.reply_text(
            "❓ Use /convert to start image conversion.",
            parse_mode="Markdown"
        )
        return
    
    # Check if message has photo or document
    if not update.message.photo and not update.message.document:
        await update.message.reply_text(
            "⚠️ **Please send an image file.**\n\n"
            "You can send it as a photo or document.",
            parse_mode="Markdown"
        )
        return
    
    # Get target format
    target_format = user_sessions[user_id].get("target_format", "PNG")
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        "⏳ **Converting your image...**\n\n"
        f"📐 Target: `{target_format}`\n"
        "Please wait...",
        parse_mode="Markdown"
    )
    
    try:
        # Get file from message
        if update.message.photo:
            file = await update.message.photo[-1].get_file()
            file_data = await file.download_as_bytearray()
        else:
            file = await update.message.document.get_file()
            file_data = await file.download_as_bytearray()
        
        # Convert the image
        success, result, format_upper, original_format = convert_image(bytes(file_data), target_format)
        
        if not success:
            await processing_msg.edit_text(
                f"❌ **Conversion Failed:**\n\n{result}\n\n"
                "Please try again with a different image.",
                parse_mode="Markdown"
            )
            user_sessions[user_id]["waiting_for_image"] = False
            return
        
        converted_data = result
        
        # Calculate sizes
        original_size = len(file_data) / 1024
        new_size = len(converted_data) / 1024
        
        await processing_msg.delete()
        
        # Determine file extension
        extension = target_format.lower()
        if extension == "jpeg":
            extension = "jpg"
        
        output_filename = f"converted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extension}"
        
        # Send the converted image
        await update.message.reply_document(
            document=BytesIO(converted_data),
            filename=output_filename,
            caption=(
                f"✅ **Conversion Complete!**\n\n"
                f"📄 **Source:** `{original_format}` → **Target:** `{format_upper}`\n"
                f"📊 **Size:** `{original_size:.1f}KB` → `{new_size:.1f}KB`\n\n"
                f"🔄 Send another image to convert more!"
            ),
            parse_mode="Markdown"
        )
        
        # Reset waiting state
        user_sessions[user_id]["waiting_for_image"] = False
        
        # Show quick actions
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Convert Another", callback_data="start_convert")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="start_convert")]
        ])
        
        await update.message.reply_text(
            "🎯 **What would you like to do next?**",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        await processing_msg.edit_text(
            f"❌ **An error occurred:**\n\n{str(e)}\n\n"
            "Please try again.",
            parse_mode="Markdown"
        )
        user_sessions[user_id]["waiting_for_image"] = False


# ============ ERROR HANDLER ============

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")


# ============ MAIN ============

def main():
    """Main entry point"""
    logger.info(f"🚀 Starting {BOT_NAME}...")
    logger.info(f"📌 Version: {BOT_VERSION}")
    logger.info(f"🔧 Debug Mode: {DEBUG_MODE}")
    logger.info(f"🖼️ Supported Formats: {', '.join(SUPPORTED_FORMATS)}")
    
    try:
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add command handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("about", about_command))
        application.add_handler(CommandHandler("formats", formats_command))
        application.add_handler(CommandHandler("convert", convert_command))
        
        # Add message handler for images
        application.add_handler(MessageHandler(
            filters.PHOTO | filters.Document.IMAGE, 
            handle_image
        ))
        
        # Add callback query handler
        application.add_handler(CallbackQueryHandler(handle_callback))
        
        # Add error handler
        application.add_error_handler(error_handler)
        
        # Start polling
        logger.info("✅ Bot is running and listening for messages...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        raise


if __name__ == "__main__":
    main()
