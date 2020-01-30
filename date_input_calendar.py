from calendar import Calendar
from datetime import date, datetime

from botx import Bot, Depends, HandlersCollector, Message, ReplyMessage
from app.db.repos.redis import RedisRepo


collector = HandlersCollector()


@collector.hidden_command_handler(command="/cal")
async def calendar(
    message: Message, bot: Bot, redis: RedisRepo = Depends(manager.get_redis)
) -> None:
    df = "%Y.%m.%d"
    _date = date.today()

    args = message.command.arguments
    if (len(args) == 2) and (args[0] in "<>"):
        _date = datetime.strptime(args[1], df).date()
    elif len(args) == 1:
        _date = datetime.strptime(args[0], df).date()
        await redis.set((cal_date, message.user_huid), _date)
        message.command.body = ""
        await next_step(message=message, bot=bot)
        return
    reply = ReplyMessage.from_message(messages.INPUT_DAY, message)

    # show date choice buttons as a calendar
    year_num = _date.year
    month_num = _date.month

    _date_str = _date.strftime(df)
    next_month = date(
        year=year_num + 1 if month_num == 12 else year_num,
        month=1 if month_num == 12 else month_num + 1,
        day=1,
    ).strftime(df)
    prev_month = date(
        year=year_num - 1 if month_num == 1 else year_num,
        month=12 if month_num == 1 else month_num - 1,
        day=1,
    ).strftime(df)
    reply.add_keyboard_button(command=f"/cal < {prev_month}", label="<")
    reply.add_keyboard_button(
        command="", label=messages.MONTHS[month_num], new_row=False
    )
    reply.add_keyboard_button(command=f"/cal > {next_month}", label=">", new_row=False)

    weeks = Calendar().monthdatescalendar(year=year_num, month=month_num)
    kb_args: List[Dict[str, Any]] = []
    for week in weeks:
        days: List[Dict[str, Any]] = []
        for day in week:
            show_day = True
            if day < date.today():
                show_day = False
            if (week == weeks[-1]) and (day.day < 7):
                show_day = False
            if (week == weeks[0]) and (day.day > 7):
                show_day = False

            if show_day:
                label = "{: >2d}".format(day.day)  # noqa
                command = f"/cal {day.year}.{day.month}.{day.day}"
            else:
                label = "  "
                command = ""
            days.append(
                {"command": command, "label": label, "new_row": not day.weekday()}
            )

        # deleting empty rows
        if any(i["command"] for i in days):
            kb_args += days
    for i in kb_args:
        reply.add_keyboard_button(**i)

    reply.add_keyboard_button(command="/cancel", label=messages.CANCEL)
    await bot.reply(reply)
