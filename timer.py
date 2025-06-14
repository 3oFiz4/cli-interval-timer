#!/usr/bin/env python3
import asyncio
import threading
import re
import sys
import os
import time
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich import box
from playsound import playsound
import keyboard
import json
from pathlib import Path

console = Console()
BASE_DIR = Path(__file__).parent
RINGTONE_FOLDER = "ringtone"
FINAL_ALARM = threading.Event()
PAUSED = threading.Event()
STOP_ALARM = threading.Event()
FORCE_QUIT = threading.Event()
TEMPLATE_FILE = "template.json"
PAUSED.clear()
STOP_ALARM.clear()
FORCE_QUIT.clear()

def load_templates():
    template_path = os.path.join(BASE_DIR, TEMPLATE_FILE)
    if not os.path.exists(template_path):
        return {}
    with open(template_path, 'r') as f:
        return json.load(f)

def save_templates(templates):
    template_path = os.path.join(BASE_DIR, TEMPLATE_FILE)
    with open(template_path, 'w') as f:
        json.dump(templates, f, indent=2)


def parse_time_string(time_str):
    total = 0
    matches = re.findall(r'(\d+)([hms])', time_str)
    for val, unit in matches:
        if unit == 'h': total += int(val) * 3600
        elif unit == 'm': total += int(val) * 60
        elif unit == 's': total += int(val)
    return total

def play_alarm(ringtone_name=None, repeat=False, mark_final=False):
    def _play():
        ringtone_path = BASE_DIR / RINGTONE_FOLDER
        if not os.path.exists(ringtone_path):
            console.print("[red]Ringtone folder not found.[/red]")
            return
        files = [f for f in os.listdir(ringtone_path) if f.lower().endswith(('.mp3', '.wav'))]
        if not files:
            console.print("[red]No ringtones found.[/red]")
            return
        if ringtone_name:
            candidates = [f for f in files if f.startswith(ringtone_name)]
            sound_file = candidates[0] if candidates else files[0]
        else:
            sound_file = files[0]
        full_path = ringtone_path / sound_file
        full_path = full_path
        if mark_final:
            FINAL_ALARM.set()
        if repeat:
            while not STOP_ALARM.is_set():
                playsound(str(full_path))
        else:
            playsound(str(full_path))
    threading.Thread(target=_play, daemon=True).start()

def parse_argument(arg):
    time_part = re.match(r'^[^a-zA-Z]*[hms\d]+', arg)
    if not time_part:
        raise ValueError(f"Invalid time format in: {arg}")
    time_str = time_part.group()
    duration = parse_time_string(time_str)
    label_match = re.search(r"'([^']*)'", arg)
    label = label_match.group(1) if label_match else "Timer"
    ringtone_match = re.search(r'\[([^\]]+)\]', arg)
    ringtone = ringtone_match.group(1) if ringtone_match else None
    return duration, label, ringtone

def create_full_table(status_list):
    table = Table(box=box.SIMPLE)
    table.add_column("Seq", style="bold")
    table.add_column("Label")
    table.add_column("Time Left")
    table.add_column("ETA")
    now = datetime.now()
    for idx, entry in enumerate(status_list):
        label = entry['label']
        remaining = entry['remaining']
        eta = entry['eta']
        is_done = entry['done']

        if is_done:
            t_str = "✅"
        else:
            color = "green"
            if remaining < 3:
                color = "red"
            elif remaining < 10:
                color = "yellow"
            t_str = f"[{color}]{remaining // 60:02d}:{remaining % 60:02d}[/{color}]"

        eta_str = eta.strftime("%H:%M:%S") if eta and not is_done else "-"
        table.add_row(str(idx + 1), label, t_str, eta_str)
    return table

async def run_timer(index, status_list, duration, label, ringtone, is_last, live):
    while duration >= 0:
        if FORCE_QUIT.is_set():
            return
        if PAUSED.is_set():
            await asyncio.sleep(0.5)
            continue

        eta = datetime.now() + timedelta(seconds=duration)
        status_list[index]['remaining'] = duration
        status_list[index]['eta'] = eta
        live.update(create_full_table(status_list))

        if duration == 0:
            break

        await asyncio.sleep(1)
        duration -= 1

    # Mark done and play alarm
    status_list[index]['remaining'] = 0
    status_list[index]['done'] = True
    status_list[index]['eta'] = None
    live.update(create_full_table(status_list))  # Final ✅ update
    play_alarm(ringtone, repeat=is_last, mark_final=is_last)



def hotkey_listener():
    def listen():
        while True:
            if keyboard.is_pressed('w'):
                if PAUSED.is_set():
                    PAUSED.clear()
                    console.print("[green]Resumed[/green]")
                else:
                    PAUSED.set()
                    console.print("[yellow]Paused[/yellow]")
                while keyboard.is_pressed('w'):
                    time.sleep(0.1)

            if FINAL_ALARM.is_set() and keyboard.is_pressed('esc'):
                STOP_ALARM.set()
                console.print("[red]Looping alarm stopped[/red]")
                break

            if keyboard.is_pressed('q'):
                FORCE_QUIT.set()
                STOP_ALARM.set()
                console.print("[red bold]Force quit.[/red bold]")
                break
            time.sleep(0.1)
    threading.Thread(target=listen, daemon=True).start()

async def main():
    if len(sys.argv) < 2:
        console.print("Usage: python timer.py <time1>;<time2>;...")
        return

    templates = load_templates()

    # Handle listing templates
    if "-l" in sys.argv:
        if not templates:
            console.print("[yellow]No templates found.[/yellow]")
        else:
            console.print("[bold underline]Available templates:[/bold underline]")
            for name, val in templates.items():
                console.print(f"{{{name}}}: {val}")
        return

    # Handle saving template
    if "--save-template" in sys.argv:
        idx = sys.argv.index("--save-template")
        if idx + 1 >= len(sys.argv):
            console.print("[red]Template name is missing after --save-template[/red]")
            return
        name = sys.argv[idx + 1]
        cleaned_args = [arg for arg in sys.argv[1:] if not arg.startswith("--") and arg != name]
        raw_input = " ".join(cleaned_args)
        templates[name] = raw_input
        save_templates(templates)
        console.print(f"[green]Template {{{name}}} saved.[/green]")
        return

    # Substitute template tags using curly braces instead of angle brackets
    input_sequence = " ".join(arg for arg in sys.argv[1:] if not arg.startswith("--"))
    for key, val in templates.items():
        input_sequence = input_sequence.replace(f"{{{key}}}", val)

    # Parse timers
    sequence = input_sequence.split(';')
    parsed = []
    for item in sequence:
        item = item.strip()
        if not item:
            continue
        try:
            parsed.append(parse_argument(item))
        except Exception as e:
            console.print(f"[red]Error parsing: {e}[/red]")
            return

    status_list = [{
        'label': label,
        'remaining': duration,
        'eta': None,
        'done': False
    } for duration, label, _ in parsed]

    hotkey_listener()
    with Live(console=console, refresh_per_second=10) as live:
        for i, (duration, label, ringtone) in enumerate(parsed):
            is_last = (i == len(parsed) - 1)
            await run_timer(i, status_list, duration, label, ringtone, is_last, live)
            live.update(create_full_table(status_list))

        if FINAL_ALARM.is_set():
            console.print("[bold green]Final alarm is looping. Press ESC to stop. Press W to pause/resume. Q to quit.[/bold green]")
        while not STOP_ALARM.is_set() and not FORCE_QUIT.is_set():
            live.update(create_full_table(status_list))
            await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        STOP_ALARM.set()
        console.print("\n[bold red]Interrupted[/bold red]")
