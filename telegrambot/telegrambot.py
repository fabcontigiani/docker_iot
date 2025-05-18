from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler
import logging, os

token=os.environ["TB_TOKEN"]
autorizados=[int(x) for x in os.environ["TB_AUTORIZADOS"].split(',')]

ELIGIENDO, SETPOINT, MODO, PERIODO, RELE = range(5)

logging.basicConfig(format='%(asctime)s - TelegramBot - %(levelname)s - %(message)s', level=logging.INFO)

async def sin_autorizacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("intento de conexión de: " + str(update.message.from_user.id))
    await context.bot.send_message(chat_id=update.effective_chat.id, text="no autorizado")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(update)
    logging.info("se conectó: " + str(update.message.from_user.id))
    if update.message.from_user.first_name:
        nombre=update.message.from_user.first_name
    else:
        nombre=""
    if update.message.from_user.last_name:
        apellido=update.message.from_user.last_name
    else:
        apellido=""
    await context.bot.send_message(update.message.chat.id, text="Bienvenido al Bot "+ nombre + " " + apellido)
    # await update.message.reply_text("Bienvenido al Bot "+ nombre + " " + apellido) # también funciona

async def acercade(update: Update, context):
    await context.bot.send_message(update.message.chat.id, text="Este bot fue creado para el curso de IoT FIO")

async def configurar(update: Update, context):
    await update.message.reply_text("Iniciando configuración, escriba 'cancelar' para salir."
                                    "\nElija una opción:",
                                    reply_markup=ReplyKeyboardMarkup(
                                         [['setpoint', 'modo'],
                                          ['periodo', 'rele']],
                                         one_time_keyboard=True,
                                         resize_keyboard=True
                                     ))
    return ELIGIENDO

async def eligiendo(update: Update, context):
    logging.info(f"Eligiendo: {update.message.text}")
    if 'setpoint' in update.message.text:
        logging.info("Se eligió setpoint")
        await update.message.reply_text("Ingrese el nuevo setpoint (float)")
        return SETPOINT
    elif 'modo' in update.message.text:
        logging.info("Se eligió modo")
        await update.message.reply_text("Ingrese el nuevo modo",
                                        reply_markup=ReplyKeyboardMarkup(
                                            [['automático'], ['manual']],
                                            one_time_keyboard=True,
                                            resize_keyboard=True
                                        ))
        return MODO
    elif 'periodo' in update.message.text:
        await update.message.reply_text("Ingrese el nuevo periodo (segundos, entero)")
        return PERIODO
    elif 'rele' in update.message.text:
        logging.info("Se eligió rele")
        #TODO: verificar que el rele se encuentra en modo manual
        await update.message.reply_text("Ingrese el nuevo estado del rele",
                                        reply_markup=ReplyKeyboardMarkup(
                                            [['cerrado (ON)'], ['abierto (OFF)']],
                                            one_time_keyboard=True,
                                            resize_keyboard=True
                                        ))
        return RELE
    else:
        logging.info("Opción no válida")
        await update.message.reply_text("Opción no válida, elija una opción:",
                                         reply_markup=ReplyKeyboardMarkup(
                                             [['setpoint', 'modo'],
                                              ['periodo', 'rele']],
                                             one_time_keyboard=True,
                                             resize_keyboard=True
                                         ))
        return ELIGIENDO

async def cancelar(update: Update, context):
    await context.bot.send_message(update.message.chat.id, text="Configuración cancelada",
                                   reply_markup=ReplyKeyboardRemove())
    logging.info("Configuración cancelada")
    return ConversationHandler.END

async def destello(update: Update, context):
    #TODO: implementar mensaje MQTT
    await update.message.reply_text("Se disparó el destello")

async def setpoint(update: Update, context):
    logging.info("Llamada a callback de setpoint")
    try:
        setpoint = float(update.message.text)
        await update.message.reply_text(f"Setpoint configurado a {setpoint}")
    except ValueError:
        await update.message.reply_text("Error: el valor ingresado no es un número válido.")
    return ConversationHandler.END

async def modo(update: Update, context):
    modo = update.message.text
    logging.info(f"Llamada a callback de modo: {modo}")
    if 'automático' in modo:
        await update.message.reply_text(f"Modo configurado a {modo}")
    elif 'manual' in modo:
        await update.message.reply_text(f"Modo configurado a {modo}")
    else:
        await update.message.reply_text("Error: modo no válido.")
    return ConversationHandler.END

async def periodo(update: Update, context):
    periodo = update.message.text
    logging.info(f"Llamada a callback de periodo: {periodo}")
    if periodo.isdigit():
        await update.message.reply_text(f"Periodo configurado a {periodo}")
    else:
        await update.message.reply_text("Error: periodo no válido.")
    return ConversationHandler.END

async def rele(update: Update, context):
    rele = update.message.text
    logging.info(f"Llamada a callback de rele: {rele}")
    if 'cerrado' in rele:
        await update.message.reply_text(f"Rele configurado a {rele}")
    elif 'abierto' in rele:
        await update.message.reply_text(f"Rele configurado a {rele}")
    else:
        await update.message.reply_text("Error: estado de rele no válido.")
    return ConversationHandler.END

def main():
    logging.info(autorizados)
    application = Application.builder().token(token).build()
    application.add_handler(MessageHandler((~filters.User(autorizados)), sin_autorizacion))
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('acercade', acercade))
    application.add_handler(CommandHandler('destello', destello))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('configurar', configurar)],
        states={
            ELIGIENDO: [MessageHandler(filters.TEXT & ~(filters.COMMAND | filters.Regex("^cancelar$")), eligiendo)],
            SETPOINT: [MessageHandler(filters.TEXT & ~(filters.COMMAND | filters.Regex("^cancelar$")), setpoint)],
            MODO: [MessageHandler(filters.TEXT & ~(filters.COMMAND | filters.Regex("^cancelar$")), modo)],
            PERIODO: [MessageHandler(filters.TEXT & ~(filters.COMMAND | filters.Regex("^cancelar$")), periodo)],
            RELE: [MessageHandler(filters.TEXT & ~(filters.COMMAND | filters.Regex("^cancelar$")), rele)],
        },
        fallbacks=[MessageHandler(filters.Regex("^cancelar$"), cancelar)]
    )

    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == '__main__':
    main()
