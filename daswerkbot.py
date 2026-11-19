import re
import asyncio
import requests

from bs4 import BeautifulSoup
from telegram import Bot
from telegram.request import HTTPXRequest

URL = "https://www.daswerk.org/program"

BOT_TOKEN = "YOUR_TOKEN"
CHAT_ID = -1003526726457

DATE_PATTERN = re.compile(
    r"(MO|DI|MI|DO|FR|SA|SO)\.\s*(\d{2})\.(\d{2})\.\s*//\s*(\d{2}):(\d{2})"
)


def scrape_events():
    print("Checking Das Werk website...")

    response = requests.get(
        URL,
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Read page text in order
    lines = [
        line.strip()
        for line in soup.stripped_strings
        if line.strip()
    ]

    events = []

    for i, line in enumerate(lines):
        match = DATE_PATTERN.search(line)

        if not match:
            continue

        title = None

        # Find the next meaningful line after the date
        for next_line in lines[i + 1:i + 5]:
            if DATE_PATTERN.search(next_line):
                break

            if next_line.upper() in ("TICKETS", "MORE INFOS"):
                continue

            if "TICKETS" in next_line.upper():
                continue

            if "MORE INFOS" in next_line.upper():
                continue

            title = next_line
            break

        if not title:
            continue

        date = (
            f"{match.group(2)}."
            f"{match.group(3)} "
            f"{match.group(4)}:"
            f"{match.group(5)}"
        )

        event = {
            "title": title,
            "date": date
        }

        if event not in events:
            events.append(event)

    return events


async def send_events():
    print("Starting Telegram bot...")

    request = HTTPXRequest(
        connection_pool_size=10,
        read_timeout=60,
        write_timeout=60,
        connect_timeout=60
    )

    bot = Bot(token=BOT_TOKEN, request=request)

    try:
        events = scrape_events()

        print(f"\nFound {len(events)} events.\n")

        for event in events:
            print(event["date"], "-", event["title"])

        for event in events:
            message = (
                "DAS WERK EVENT\n\n"
                "Event: Das Werk\n"
                f"Title: {event['title']}\n"
                f"Date: {event['date']}"
            )

            for attempt in range(3):
                try:
                    await bot.send_message(
                        chat_id=CHAT_ID,
                        text=message
                    )

                    print("Event sent:", event["title"])
                    break

                except Exception as error:
                    print(f"Attempt {attempt + 1}/3 failed:", error)

                    if attempt < 2:
                        await asyncio.sleep(3)

            await asyncio.sleep(1)

        print("\nFinished!")

    finally:
        await bot.shutdown()


if __name__ == "__main__":
    asyncio.run(send_events())
